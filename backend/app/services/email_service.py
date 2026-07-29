from __future__ import annotations

import base64
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger

from app.core.config import settings

MAILGUN_BASE_URL = "https://api.mailgun.net/v3"
ELASTICEMAIL_API_URL = "https://api.elasticemail.com/v2/email/send"
HASKIMAIL_API_URL = "https://api.haskimail.ru/email"


class EmailService:
    def __init__(self) -> None:
        self._gmail_available = bool(settings.gmail_token_json) and bool(
            settings.gmail_from_email
        )
        self._haskimail_available = bool(settings.haskimail_server_token) and bool(
            settings.haskimail_from_email
        )
        self._elasticemail_available = bool(settings.elasticemail_api_key) and bool(
            settings.elasticemail_from_email
        )
        self._mailgun_available = bool(settings.mailgun_api_key) and bool(
            settings.mailgun_domain
        )
        self._smtp_available = all([
            settings.smtp_host,
            settings.smtp_user,
            settings.smtp_password,
        ])

    def _send_via_gmail(self, to_email: str, subject: str, html_body: str) -> bool:
        if not self._gmail_available:
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

    def _send_via_haskimail(
        self, to_email: str, subject: str, html_body: str
    ) -> bool:
        if not self._haskimail_available:
            return False
        try:
            with httpx.Client(timeout=15) as client:
                response = client.post(
                    HASKIMAIL_API_URL,
                    headers={
                        "X-Haski-Server-Token": settings.haskimail_server_token,
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    json={
                        "From": settings.haskimail_from_email,
                        "To": to_email,
                        "Subject": subject,
                        "HtmlBody": html_body,
                        "MessageStream": settings.haskimail_channel_id,
                    },
                )
                if response.status_code in (200, 201, 202):
                    logger.info(
                        f"Email отправлен на {to_email} через HaskiMail"
                    )
                    return True
                logger.error(
                    f"Ошибка HaskiMail для {to_email}: {response.status_code} {response.text[:300]}"
                )
                return False
        except Exception as e:
            logger.error(f"Ошибка HaskiMail для {to_email}: {e}")
            return False

    def _send_via_elasticemail(
        self, to_email: str, subject: str, html_body: str
    ) -> bool:
        if not self._elasticemail_available:
            return False
        try:
            with httpx.Client(timeout=15) as client:
                response = client.post(
                    ELASTICEMAIL_API_URL,
                    data={
                        "apikey": settings.elasticemail_api_key,
                        "from": settings.elasticemail_from_email,
                        "fromName": "AI Contact API",
                        "to": to_email,
                        "subject": subject,
                        "bodyHtml": html_body,
                        "isTransactional": "true",
                    },
                )
                data = response.json()
                if data.get("success"):
                    logger.info(
                        f"Email отправлен на {to_email} через ElasticEmail"
                    )
                    return True
                logger.error(
                    f"Ошибка ElasticEmail для {to_email}: {data.get('error', response.text)}"
                )
                return False
        except Exception as e:
            logger.error(f"Ошибка ElasticEmail для {to_email}: {e}")
            return False

    def _send_via_mailgun(self, to_email: str, subject: str, html_body: str) -> bool:
        domain = settings.mailgun_domain
        try:
            with httpx.Client(timeout=15) as client:
                response = client.post(
                    f"{MAILGUN_BASE_URL}/{domain}/messages",
                    auth=("api", settings.mailgun_api_key),
                    data={
                        "from": f"AI Contact API <noreply@{domain}>",
                        "to": to_email,
                        "subject": subject,
                        "html": html_body,
                    },
                )
                if response.status_code != 200:
                    logger.error(
                        f"Ошибка Mailgun для {to_email}: {response.json().get('message', response.text)}"
                    )
                    return False
                logger.info(f"Email отправлен на {to_email} через Mailgun")
                return True
        except Exception as e:
            logger.error(f"Ошибка Mailgun для {to_email}: {e}")
            return False

    def _send_via_smtp(self, to_email: str, subject: str, html_body: str) -> bool:
        if not self._smtp_available:
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

            logger.info(f"Email отправлен на {to_email} через SMTP")
            return True

        except smtplib.SMTPException as e:
            logger.error(f"Не удалось отправить email на {to_email}: {e}")
            return False
        except OSError as e:
            logger.error(f"Ошибка SMTP-подключения для {to_email}: {e}")
            return False

    def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        if self._gmail_available:
            return self._send_via_gmail(to_email, subject, html_body)
        if self._haskimail_available:
            return self._send_via_haskimail(to_email, subject, html_body)
        if self._elasticemail_available:
            return self._send_via_elasticemail(to_email, subject, html_body)
        if self._mailgun_available:
            return self._send_via_mailgun(to_email, subject, html_body)
        if self._smtp_available:
            return self._send_via_smtp(to_email, subject, html_body)

        logger.warning("Ни один способ отправки не настроен, пропуск email")
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
