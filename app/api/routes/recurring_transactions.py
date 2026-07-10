# app/api/routes/recurring_transactions.py

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.recurring_transaction import RecurringTransaction
from app.models.transaction import Transaction
from app.schemas.recurring_transaction import (
    RecurringTransactionCreate,
    RecurringTransactionUpdate,
    RecurringTransactionResponse,
)
from app.dependencies.current_user import get_current_user, get_db
from app.models.user import User
from app.services.recurring_executor import (
    run_due_recurring_transactions,
    advance_date,
    retreat_date,
)

router = APIRouter(prefix="/recurring-transactions", tags=["Recurring Transactions"])


def _is_current_period_registered(db: Session, rule: RecurringTransaction) -> bool:
    """A rule counts as 'registered' for its current period only when an actual
    transaction linked to it exists for that period — never inferred from dates alone.

    Registration advances next_execution_date forward by one period, so the
    just-registered transaction's date lands in [prev_date, next_execution_date).
    If the user deletes that transaction, this returns False again.

    Once next_execution_date itself has arrived/passed, that window is stale — it
    describes the period that was already paid ahead of time, not the new period
    that just became due. Without this check, a rule paid early stays "Registrado"
    forever once the month rolls over, hiding the button to register the new period.
    """
    if rule.next_execution_date <= datetime.utcnow():
        return False

    prev_date = retreat_date(rule.next_execution_date, rule.frequency)
    exists = (
        db.query(Transaction.id)
        .filter(
            Transaction.recurring_transaction_id == rule.id,
            Transaction.date >= prev_date,
            Transaction.date < rule.next_execution_date,
        )
        .first()
    )
    return exists is not None


def _enrich_recurring(rule: RecurringTransaction, db: Session) -> dict:
    """Convert a RecurringTransaction ORM object to a dict and inject currency fields."""
    data = RecurringTransactionResponse.model_validate(rule).model_dump()
    if rule.currency is not None:
        data["currency_code"] = rule.currency.code
        data["currency_symbol"] = rule.currency.symbol
    data["current_period_registered"] = _is_current_period_registered(db, rule)
    return data


def _get_or_404(db: Session, rule_id: int, user_id: int) -> RecurringTransaction:
    rule = (
        db.query(RecurringTransaction)
        .options(
            joinedload(RecurringTransaction.category),
            joinedload(RecurringTransaction.currency),
        )
        .filter(
            RecurringTransaction.id == rule_id,
            RecurringTransaction.user_id == user_id,
        )
        .first()
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Recurring transaction not found")
    return rule


# GET /recurring-transactions
@router.get("", response_model=list[RecurringTransactionResponse])
def list_recurring_transactions(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rules = (
        db.query(RecurringTransaction)
        .options(
            joinedload(RecurringTransaction.category),
            joinedload(RecurringTransaction.currency),
        )
        .filter(RecurringTransaction.user_id == current_user.id)
        .order_by(RecurringTransaction.next_execution_date.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [_enrich_recurring(r, db) for r in rules]


# POST /recurring-transactions
@router.post("", response_model=RecurringTransactionResponse)
def create_recurring_transaction(
    data: RecurringTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx_type = data.type.upper()
    if tx_type not in ("INCOME", "EXPENSE"):
        raise HTTPException(status_code=400, detail="type must be INCOME or EXPENSE")

    freq = data.frequency.upper()
    if freq not in ("DAILY", "WEEKLY", "MONTHLY", "YEARLY"):
        raise HTTPException(
            status_code=400,
            detail="frequency must be DAILY, WEEKLY, MONTHLY, or YEARLY",
        )

    rule = RecurringTransaction(
        name=data.name,
        amount=data.amount,
        type=tx_type,
        frequency=freq,
        next_execution_date=data.next_execution_date,
        end_date=data.end_date,
        is_active=True,
        category_id=data.category_id,
        user_id=current_user.id,
        account_id=data.account_id,
        credit_card_id=data.credit_card_id,
        currency_id=data.currency_id,
        notification_days_before=data.notification_days_before,
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    # Immediately process the rule if it is already due
    run_due_recurring_transactions(db)

    # Re-fetch to reflect any date advancement that just happened
    return _enrich_recurring(_get_or_404(db, rule.id, current_user.id), db)


# PUT /recurring-transactions/{id}
@router.put("/{rule_id}", response_model=RecurringTransactionResponse)
def update_recurring_transaction(
    rule_id: int,
    data: RecurringTransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = _get_or_404(db, rule_id, current_user.id)

    if data.name is not None:
        rule.name = data.name
    if 'amount' in data.model_fields_set:
        rule.amount = data.amount
    if data.type is not None:
        tx_type = data.type.upper()
        if tx_type not in ("INCOME", "EXPENSE"):
            raise HTTPException(status_code=400, detail="type must be INCOME or EXPENSE")
        rule.type = tx_type
    if data.frequency is not None:
        freq = data.frequency.upper()
        if freq not in ("DAILY", "WEEKLY", "MONTHLY", "YEARLY"):
            raise HTTPException(
                status_code=400,
                detail="frequency must be DAILY, WEEKLY, MONTHLY, or YEARLY",
            )
        rule.frequency = freq
    if data.next_execution_date is not None:
        rule.next_execution_date = data.next_execution_date
    if data.end_date is not None:
        rule.end_date = data.end_date
    if data.is_active is not None:
        rule.is_active = data.is_active
    if data.category_id is not None:
        rule.category_id = data.category_id
    # account_id / credit_card_id are mutually exclusive payment sources; honor
    # explicit nulls (via model_fields_set) so switching one clears the other.
    if 'account_id' in data.model_fields_set:
        rule.account_id = data.account_id
    if 'credit_card_id' in data.model_fields_set:
        rule.credit_card_id = data.credit_card_id
    if 'currency_id' in data.model_fields_set:
        rule.currency_id = data.currency_id
    if 'notification_days_before' in data.model_fields_set:
        rule.notification_days_before = data.notification_days_before

    db.commit()

    # Re-fetch with all eager loads to populate currency.
    return _enrich_recurring(_get_or_404(db, rule_id, current_user.id), db)


# POST /recurring-transactions/{id}/advance
@router.post("/{rule_id}/advance", response_model=RecurringTransactionResponse)
def advance_recurring_transaction(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Advance next_execution_date by one frequency period. Called by the mobile app
    after it registers the transaction triggered by a local notification."""
    rule = _get_or_404(db, rule_id, current_user.id)

    next_date = advance_date(rule.next_execution_date, rule.frequency)
    rule.next_execution_date = next_date

    if rule.end_date is not None and next_date.date() > rule.end_date:
        rule.is_active = False

    db.commit()
    return _enrich_recurring(_get_or_404(db, rule_id, current_user.id), db)


# DELETE /recurring-transactions/{id}
@router.delete("/{rule_id}")
def delete_recurring_transaction(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = (
        db.query(RecurringTransaction)
        .filter(
            RecurringTransaction.id == rule_id,
            RecurringTransaction.user_id == current_user.id,
        )
        .first()
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Recurring transaction not found")

    # Past transactions generated by this rule must survive its deletion — the FK has
    # no ondelete action, so unlink them first or db.delete() raises IntegrityError.
    db.query(Transaction).filter(
        Transaction.recurring_transaction_id == rule.id
    ).update({Transaction.recurring_transaction_id: None})

    db.delete(rule)
    db.commit()

    return {"message": "Deleted successfully"}
