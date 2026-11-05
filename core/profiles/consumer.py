import logging
import os

from faststream import AckPolicy, FastStream
from faststream.kafka import KafkaBroker
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from app_logging import configure_logging
from db import PrimarySession, configure_sessions, create_primary_engine
from profiles.models import Profile


class ConsumerContextFilter(logging.Filter):
    def __init__(self, context):
        super().__init__()
        self.context = context

    def filter(self, record):
        message = self.context.get_local("message")

        if message is not None:
            raw = message.raw_message
            record.fields.update(
                topic=raw.topic,
                partition=raw.partition,
                offset=raw.offset,
            )

        return True


logger = logging.getLogger(__name__)
broker = KafkaBroker(os.environ["CORE_KAFKA_ADDR"], logger=logger)
app = FastStream(broker, logger=logger)

configure_logging(ConsumerContextFilter(broker.context))
configure_sessions(create_primary_engine())


@broker.subscriber(
    "auth.users",
    group_id="core",
    auto_offset_reset="earliest",
    ack_policy=AckPolicy.NACK_ON_ERROR,
    max_workers=int(os.environ["CORE_USER_EVENT_CONCURRENCY"]),
)
def handle_user_event(event: dict):
    with PrimarySession.begin() as session:
        if event["type"] == "created":
            session.execute(
                insert(Profile)
                .values(user_id=event["id"])
                .on_conflict_do_nothing(index_elements=[Profile.user_id])
            )
        elif event["type"] == "confirmed":
            session.execute(
                update(Profile)
                .where(Profile.user_id == event["id"])
                .values(email=event["email"])
            )
