import os
import smtplib
from email.message import EmailMessage


def send(recipient, subject, content):
    message = EmailMessage()
    message["From"] = os.environ["CORE_EMAIL_FROM"]
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(content)

    with smtplib.SMTP(
        host=os.environ["CORE_SMTP_HOST"],
        port=int(os.environ["CORE_SMTP_PORT"]),
    ) as client:
        client.send_message(message)
