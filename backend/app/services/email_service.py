from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from loguru import logger

from app.core.config import settings


class EmailService:
    def __init__(self) -> None:
        self._enabled = all([
            settings.smtp_host,
            settings.smtp_user,
            settings.smtp_password,
        ])

    def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        if not self._enabled:
            logger.warning("SMTP не настроен, пропуск отправки email")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = settings.smtp_from_email or settings.smtp_user
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)

            logger.info(f"Email отправлен на {to_email}")
            return True

        except smtplib.SMTPException as e:
            logger.error(f"Не удалось отправить email на {to_email}: {e}")
            return False
        except OSError as e:
            logger.error(f"Ошибка SMTP-подключения для {to_email}: {e}")
            return False

    def send_owner_notification(
        self,
        name: str,
        email: str,
        phone: str,
        comment: str,
        sentiment: str,
    ) -> bool:
        if not settings.smtp_owner_email:
            logger.warning("SMTP_OWNER_EMAIL не настроен, пропуск уведомления владельца")
            return False

        subject = f"Новое сообщение из контактной формы от {name}"
        html = f"""
        <html><body>
        <h2>Новое сообщение из контактной формы</h2>
        <table>
        <tr><td><strong>Имя:</strong></td><td>{name}</td></tr>
        <tr><td><strong>Email:</strong></td><td>{email}</td></tr>
        <tr><td><strong>Телефон:</strong></td><td>{phone}</td></tr>
        <tr><td><strong>Тональность:</strong></td><td>{sentiment}</td></tr>
        </table>
        <h3>Комментарий:</h3>
        <p>{comment}</p>
        </body></html>
        """
        return self._send_email(settings.smtp_owner_email, subject, html)

    def send_user_copy(
        self,
        name: str,
        to_email: str,
        comment: str,
        sentiment: str,
    ) -> bool:
        subject = f"Спасибо за обращение, {name}"
        html = f"""
        <html><body>
        <h2>Спасибо, что написали нам!</h2>
        <p>Уважаемый(ая) {name},</p>
        <p>Мы получили ваше сообщение и свяжемся с вами в ближайшее время.</p>
        <h3>Ваше сообщение:</h3>
        <p>{comment}</p>
        <p><strong>Определённая тональность:</strong> {sentiment}</p>
        <br>
        <p>С уважением,<br>Команда AI Contact API</p>
        </body></html>
        """
        return self._send_email(to_email, subject, html)


email_service = EmailService()
