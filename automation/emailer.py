"""Send complaint emails over SMTP. Set DRY_RUN=true to print instead of sending."""
import os
import smtplib
from email.message import EmailMessage


def send_email(to, subject, body):
    if os.getenv("DRY_RUN", "true").lower() == "true":
        print(f"[DRY RUN] To: {to}\nSubject: {subject}\n\n{body}\n")
        return True
    msg = EmailMessage()
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", "587"))) as s:
        s.starttls()
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        s.send_message(msg)
    return True
