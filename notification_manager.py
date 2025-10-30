# notification_manager.py
import smtplib


class NotificationManager:
    def __init__(self, from_email=None, password=None, smtp=None):
        self.from_email = from_email
        self.password = password
        self.smtp = smtp

    def can_send(self):
        # return True if SMTP creds are present
        return all([self.from_email, self.password, self.smtp])

    def send_email(self, message, to_email):
        if not self.can_send():
            raise RuntimeError("SMTP not configured. Set FROM_EMAIL, EMAIL_PASSWORD and SMTP in .env")

        with smtplib.SMTP(self.smtp, port=587) as connection:
            connection.starttls()
            connection.login(user=self.from_email, password=self.password)
            connection.sendmail(
                from_addr=self.from_email,
                to_addrs=to_email,
                msg=message
            )
