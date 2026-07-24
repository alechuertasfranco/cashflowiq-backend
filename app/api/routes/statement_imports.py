# app/api/routes/statement_imports.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.statement_import import StatementImport
from app.models.transaction import Transaction
from app.models.bank_account import BankAccount
from app.models.user import User
from app.schemas.statement_import import StatementImportCreate, StatementImportResponse
from app.dependencies.current_user import get_current_user, get_db
from app.services.account_monthly_balance_service import recompute_affected_accounts
from app.api.routes.transactions import _enrich

router = APIRouter(prefix="/statement-imports", tags=["Statement Imports"])


def _batch_response(db: Session, batch: StatementImport, include_transactions: bool) -> dict:
    """Serialize a StatementImport, optionally embedding its enriched transactions."""
    data = {
        "id": batch.id,
        "account_id": batch.account_id,
        "year": batch.year,
        "month": batch.month,
        "filename": batch.filename,
        "bank": batch.bank,
        "imported_count": batch.imported_count,
        "created_at": batch.created_at,
        "transactions": [],
    }
    if include_transactions:
        txs = (
            db.query(Transaction)
            .options(joinedload(Transaction.category), joinedload(Transaction.currency))
            .filter(Transaction.import_batch_id == batch.id)
            .order_by(Transaction.date.asc())
            .all()
        )
        data["transactions"] = [_enrich(tx) for tx in txs]
    return data


# ➕ CREATE IMPORT BATCH (bulk-create the reconciled "new" movements)
@router.post("", response_model=StatementImportResponse)
def create_statement_import(
    data: StatementImportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = (
        db.query(BankAccount)
        .filter(BankAccount.id == data.account_id, BankAccount.user_id == current_user.id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    batch = StatementImport(
        user_id=current_user.id,
        account_id=account.id,
        year=data.year,
        month=data.month,
        filename=data.filename,
        bank=data.bank,
        imported_count=0,
    )
    db.add(batch)
    db.flush()  # get batch.id without a separate commit

    affected_pairs: set[tuple[int, int, int]] = set()
    count = 0
    for item in data.items:
        tx_type = item.type.upper()
        if tx_type not in ("INCOME", "EXPENSE"):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported statement line type: {item.type}",
            )

        from_account_id = None
        to_account_id = None
        if tx_type == "INCOME":
            to_account_id = account.id
        else:  # EXPENSE
            from_account_id = account.id

        tx = Transaction(
            type=tx_type,
            amount=item.amount,
            description=item.description,
            date=item.date,
            user_id=current_user.id,
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            category_id=item.category_id,
            currency_id=account.currency_id,
            import_batch_id=batch.id,
        )
        db.add(tx)
        affected_pairs.add((account.id, item.date.year, item.date.month))
        count += 1

    batch.imported_count = count
    db.commit()
    db.refresh(batch)

    # Recompute snapshots for every affected (account, month) in one pass.
    recompute_affected_accounts(db, affected_pairs)

    return _batch_response(db, batch, include_transactions=True)


# 📥 LIST IMPORT BATCHES (history)
@router.get("", response_model=list[StatementImportResponse])
def list_statement_imports(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    batches = (
        db.query(StatementImport)
        .filter(StatementImport.user_id == current_user.id)
        .order_by(StatementImport.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [_batch_response(db, b, include_transactions=False) for b in batches]


# 🔍 GET SINGLE IMPORT BATCH (detail + its transactions)
@router.get("/{batch_id}", response_model=StatementImportResponse)
def get_statement_import(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    batch = (
        db.query(StatementImport)
        .filter(StatementImport.id == batch_id, StatementImport.user_id == current_user.id)
        .first()
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Statement import not found")
    return _batch_response(db, batch, include_transactions=True)


# ❌ DELETE IMPORT BATCH (undo — remove the batch and all its transactions)
@router.delete("/{batch_id}")
def delete_statement_import(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    batch = (
        db.query(StatementImport)
        .filter(StatementImport.id == batch_id, StatementImport.user_id == current_user.id)
        .first()
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Statement import not found")

    # Capture affected (account, month) pairs before the rows are gone.
    txs = (
        db.query(Transaction)
        .filter(Transaction.import_batch_id == batch.id)
        .all()
    )
    affected_pairs: set[tuple[int, int, int]] = {
        (batch.account_id, tx.date.year, tx.date.month) for tx in txs
    }

    # Deleting the batch cascades to its transactions (cascade="all, delete-orphan").
    db.delete(batch)
    db.commit()

    recompute_affected_accounts(db, affected_pairs)

    return {"message": "Deleted successfully"}
