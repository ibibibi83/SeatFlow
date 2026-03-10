"""
Background scheduler for automatic reservation expiry.

Uses APScheduler to run a sweep every 60 seconds that transitions
PENDING reservations whose 'expires_at' timestamp has passed to EXPIRED.
The scheduler is started and stopped via the FastAPI lifespan hook in main.py.
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Module-level scheduler instance so start/stop can be called from main.py
_scheduler: BackgroundScheduler | None = None


def _expiry_sweep() -> None:
    """
    Periodic job: expire stale reservations.

    Opens its own database session so it can run safely in a background thread
    without touching the per-request session used by FastAPI routes.
    """
    from app.db.session import SessionLocal
    from app.services.reservation_service import ReservationService

    db = SessionLocal()
    try:
        count = ReservationService(db).expire_stale_reservations()
        if count:
            logger.info("[Scheduler] Expired %d reservation(s).", count)
    except Exception:
        logger.exception("[Scheduler] Error during expiry sweep.")
    finally:
        db.close()


def start_scheduler() -> None:
    """Start the background scheduler. Called once on application startup."""
    global _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        func=_expiry_sweep,
        trigger=IntervalTrigger(seconds=60),
        id="expiry_sweep",
        max_instances=1,   # never run two sweeps at the same time
        coalesce=True,     # skip missed runs instead of queuing them
    )
    _scheduler.start()
    logger.info("[Scheduler] Started – expiry sweep every 60 seconds.")


def stop_scheduler() -> None:
    """Stop the background scheduler. Called once on application shutdown."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Stopped.")