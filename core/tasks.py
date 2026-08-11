import os
import smtplib
from email.message import EmailMessage

import dramatiq
from dramatiq.brokers.redis import RedisBroker

broker = RedisBroker(url=os.environ["CORE_REDIS_URL"])
dramatiq.set_broker(broker)


@dramatiq.actor(queue_name="email", max_retries=3)
def send_ticket_email(recipient, event_name, ticket_type_name, quantity):
    message = EmailMessage()
    message["From"] = os.environ["CORE_EMAIL_FROM"]
    message["To"] = recipient
    message["Subject"] = "Your tickets"
    message.set_content(
        f"You bought {quantity} {ticket_type_name} ticket(s) for {event_name}."
    )

    with smtplib.SMTP(
        host=os.environ["CORE_SMTP_HOST"],
        port=int(os.environ["CORE_SMTP_PORT"]),
    ) as client:
        client.send_message(message)
