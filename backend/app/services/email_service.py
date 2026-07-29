from __future__ import annotations

import base64
import json
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger

from app.core.config import settings


class EmailService:
    def __init__(self) -> None:
        self._available = bool(settings.gmail_token_json) and bool(
            settings.gmail_from_email
        )

    def send_owner_notification(
        self,
        name: str,
        email: str,
        phone: str,
        comment: str,
        sentiment: str,
    ) -> bool:
        if not settings.smtp_owner_email:
            logger.warning(
                "SMTP_OWNER_EMAIL не настроен, пропуск уведомления владельца"
            )
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
        return self._send(settings.smtp_owner_email, subject, html)

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
        return self._send(to_email, subject, html)

    def _send(self, to_email: str, subject: str, html_body: str) -> bool:
        if not self._available:
            logger.warning(
                "Gmail API не настроен (GMAIL_TOKEN_JSON / GMAIL_FROM_EMAIL)"
            )
            return False
        try:
            token_data = json.loads(
                base64.b64decode(settings.gmail_token_json).decode()
            )
            creds = Credentials.from_authorized_user_info(token_data)

            if creds.expired and creds.refresh_token:
                creds.refresh(Request())

            service = build("gmail", "v1", credentials=creds)

            msg = MIMEText(html_body, "html", "utf-8")
            msg["To"] = to_email
            msg["Subject"] = subject
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

            service.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()

            logger.info(f"Email отправлен на {to_email} через Gmail API")
            return True

        except HttpError as e:
            logger.error(f"Ошибка Gmail API для {to_email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка Gmail API для {to_email}: {e}")
            return False


email_service = EmailService()
