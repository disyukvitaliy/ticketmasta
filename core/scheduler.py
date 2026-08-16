import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app_logging import configure_logging
from tasks import expire_ticket_holds

configure_logging()

logger = logging.getLogger(__name__)


def main():
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        expire_ticket_holds.send,
        IntervalTrigger(minutes=1),
        name="expire_ticket_holds",
        replace_existing=True,
    )

    logger.info("Scheduler started")
    scheduler.start()


if __name__ == "__main__":
    main()
