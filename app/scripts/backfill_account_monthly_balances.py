# app/scripts/backfill_account_monthly_balances.py
#
# One-time (but safely re-runnable) backfill for the account_monthly_balances
# snapshot table. For every BankAccount, finds the account's earliest ever
# transaction and recomputes the full closed-month snapshot chain from that
# month forward to (but not including) the current UTC calendar month.
#
# Idempotent: re-running this recomputes the same closed months to the same
# values, so it's safe to run again any time (e.g. after a manual data fix)
# to fully resync all snapshots from scratch.
#
# Usage (from cashflowiq-backend/):
#   python -m app.scripts.backfill_account_monthly_balances
#
# This script does NOT touch credit_card_id / investment_fund_id snapshot
# rows — bank accounts only.

import logging
from datetime import datetime, timezone

from sqlalchemy import func, or_

from app.db.session import SessionLocal
from app.models.bank_account import BankAccount
from app.models.transaction import Transaction
from app.services.account_monthly_balance_service import recompute_account_from_month

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _months_in_range(start_year: int, start_month: int, end_year: int, end_month: int) -> int:
    """Count how many (year, month) steps lie in [start, end) — for summary logging only."""
    return (end_year - start_year) * 12 + (end_month - start_month)


def run_backfill() -> None:
    db = SessionLocal()
    accounts_processed = 0
    accounts_skipped = 0
    snapshot_rows_written = 0

    try:
        accounts = db.query(BankAccount).all()
        now = datetime.now(timezone.utc)
        current_year, current_month = now.year, now.month

        for account in accounts:
            min_date = (
                db.query(func.min(Transaction.date))
                .filter(
                    or_(
                        Transaction.from_account_id == account.id,
                        Transaction.to_account_id == account.id,
                    )
                )
                .scalar()
            )

            if min_date is None:
                logger.info(
                    "Account id=%d '%s': no transactions found, skipping.",
                    account.id,
                    account.name,
                )
                accounts_skipped += 1
                continue

            months_expected = max(
                0,
                _months_in_range(min_date.year, min_date.month, current_year, current_month),
            )

            recompute_account_from_month(db, account, min_date.year, min_date.month)
            db.commit()

            snapshot_rows_written += months_expected
            accounts_processed += 1
            logger.info(
                "Account id=%d '%s': recomputed %d closed month(s) starting %04d-%02d.",
                account.id,
                account.name,
                months_expected,
                min_date.year,
                min_date.month,
            )

        logger.info(
            "Backfill complete: %d account(s) processed, %d account(s) skipped "
            "(no transactions), %d snapshot row(s) created/updated total.",
            accounts_processed,
            accounts_skipped,
            snapshot_rows_written,
        )
    except Exception:
        logger.exception("Backfill failed — rolling back current transaction.")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_backfill()
