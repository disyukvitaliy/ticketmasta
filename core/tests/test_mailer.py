from unittest.mock import patch

import mailer


def test_send(monkeypatch):
    monkeypatch.setenv("CORE_EMAIL_FROM", "tickets@example.com")
    monkeypatch.setenv("CORE_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("CORE_SMTP_PORT", "2525")

    with patch("mailer.smtplib.SMTP") as smtp:
        mailer.send("buyer@example.com", "Your tickets", "Your order is confirmed.")

    smtp.assert_called_once_with(host="smtp.example.com", port=2525)
    message = smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
    assert message["From"] == "tickets@example.com"
    assert message["To"] == "buyer@example.com"
    assert message["Subject"] == "Your tickets"
    assert message.get_content() == "Your order is confirmed.\n"
