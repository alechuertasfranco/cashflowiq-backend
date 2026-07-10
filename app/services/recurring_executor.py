# app/services/recurring_executor.py
#
# Execution engine for recurring transactions.
#
# Design:
#   - run_due_recurring_transactions(db) processes all due rules synchronously
#     against a caller-supplied SQLAlchemy session.  Routers and the scheduler
#     both call this function.
#   - start_daily_scheduler() is called once at app startup. It fires
#     run_due_recurring_transactions immediately (to catch rules missed while the
#     server was down) and then repeats every 24 hours using a background thread.
#     No third-party scheduler library is required — only stdlib threading.

import calendar
import logging
import threading
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.recurring_transaction import RecurringTransaction
from app.models.transaction import Transaction
from app.models.bank_account import BankAccount
from app.models.credit_card import CreditCard

logger = logging.getLogger(__name__)

# Seconds between automatic scheduler runs (86400 = 24 hours)
_SCHEDULER_INTERVAL_SECONDS = 86400


def _add_months(dt: datetime, months: int) -> datetime:
    """Add a number of months to a datetime, clamping to the last day of the target month."""
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def advance_date(current: datetime, frequency: str) -> datetime:
    """Return the next execution date based on frequency."""
    if frequency == "DAILY":
        return current + timedelta(days=1)
    if frequency == "WEEKLY":
        return current + timedelta(weeks=1)
    if frequency == "MONTHLY":
        return _add_months(current, 1)
    if frequency == "YEARLY":
        return _add_months(current, 12)
    raise ValueError(f"Unknown frequency: {frequency}")


def retreat_date(current: datetime, frequency: str) -> datetime:
    """Return the previous execution date — the inverse of advance_date."""
    if frequency == "DAILY":
        return current - timedelta(days=1)
    if frequency == "WEEKLY":
        return current - timedelta(weeks=1)
    if frequency == "MONTHLY":
        return _add_months(current, -1)
    if frequency == "YEARLY":
        return _add_months(current, -12)
    raise ValueError(f"Unknown frequency: {frequency}")


def _resolve_currency(db: Session, rule: RecurringTransaction) -> int:
    """
    Return the currency_id to use for the generated transaction.
    Priority: rule.currency_id → linked account → linked credit card.
    Raises ValueError if currency cannot be determined.
    """
    if rule.currency_id is not None:
        return rule.currency_id

    if rule.account_id is not None:
        account = db.query(BankAccount).filter(BankAccount.id == rule.account_id).first()
        if account:
            return account.currency_id

    if rule.credit_card_id is not None:
        card = db.query(CreditCard).filter(CreditCard.id == rule.credit_card_id).first()
        if card:
            return card.currency_id

    raise ValueError(
        f"RecurringTransaction id={rule.id}: cannot determine currency_id "
        "(no currency_id, account_id, or credit_card_id set)"
    )


def run_due_recurring_transactions(db: Session) -> int:
    """
    Process all active recurring rules whose next_execution_date is today or earlier.

    For each due rule:
      1. Create a Transaction row.
      2. Advance next_execution_date by the rule's frequency.
      3. If end_date is set and the advanced date would exceed it, set is_active=False.

    Returns the number of transactions created.
    """
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    due_rules = (
        db.query(RecurringTransaction)
        .filter(
            # SQLAlchemy overloads `==`/`is` differently to build query
            # expressions — `is True`/`is None` here would perform a plain
            # Python identity check instead of a SQL comparison and silently
            # break the filter.
            RecurringTransaction.is_active == True,  # noqa: E712  pylint: disable=singleton-comparison
            RecurringTransaction.next_execution_date <= today + timedelta(days=1),
            RecurringTransaction.notification_days_before == None,  # noqa: E711  pylint: disable=singleton-comparison
        )
        .all()
    )

    created_count = 0

    for rule in due_rules:
        try:
            currency_id = _resolve_currency(db, rule)
        except ValueError as exc:
            logger.warning("Skipping recurring rule: %s", exc)
            continue

        # Map account fields the same way the transactions router does
        from_account_id = None
        from_credit_card_id = None
        to_account_id = None

        if rule.type == "INCOME":
            to_account_id = rule.account_id
        else:  # EXPENSE
            if rule.credit_card_id:
                from_credit_card_id = rule.credit_card_id
            else:
                from_account_id = rule.account_id

        tx = Transaction(
            type=rule.type,
            amount=rule.amount,
            description=rule.name,
            date=rule.next_execution_date,
            user_id=rule.user_id,
            from_account_id=from_account_id,
            from_credit_card_id=from_credit_card_id,
            to_account_id=to_account_id,
            category_id=rule.category_id,
            currency_id=currency_id,
            is_recurring=True,
            is_fixed=True,
            recurring_transaction_id=rule.id,
        )
        db.add(tx)

        # Advance next_execution_date
        next_date = advance_date(rule.next_execution_date, rule.frequency)
        rule.next_execution_date = next_date

        # Deactivate if end_date is reached
        if rule.end_date is not None:
            if next_date.date() > rule.end_date:
                rule.is_active = False
                logger.info(
                    "RecurringTransaction id=%d '%s' reached end_date — deactivated.",
                    rule.id,
                    rule.name,
                )

        created_count += 1
        logger.info(
            "Created transaction for recurring rule id=%d '%s' (next: %s).",
            rule.id,
            rule.name,
            rule.next_execution_date.date(),
        )

    if created_count:
        db.commit()

    return created_count


def _scheduler_loop(interval_seconds: int) -> None:
    """Background thread: run due recurring transactions once per interval."""
    while True:
        db = SessionLocal()
        try:
            count = run_due_recurring_transactions(db)
            logger.info("Recurring executor: %d transaction(s) created.", count)
        except Exception:  # pylint: disable=broad-exception-caught
            # Must not let any unexpected error kill this daemon thread —
            # it needs to keep retrying on its 24h interval regardless.
            logger.exception("Recurring executor encountered an error.")
            db.rollback()
        finally:
            db.close()

        threading.Event().wait(interval_seconds)


def start_daily_scheduler() -> None:
    """
    Launch the background scheduler thread.
    Called once from the FastAPI startup event in main.py.
    The thread is daemonised so it does not block process shutdown.
    """
    thread = threading.Thread(
        target=_scheduler_loop,
        args=(_SCHEDULER_INTERVAL_SECONDS,),
        daemon=True,
        name="recurring-executor",
    )
    thread.start()
    logger.info(
        "Recurring transaction scheduler started (interval=%ds).",
        _SCHEDULER_INTERVAL_SECONDS,
    )
