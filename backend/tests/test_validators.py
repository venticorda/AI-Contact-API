import pytest
from pydantic import ValidationError

from app.api.schemas.contact import ContactRequest


class TestContactRequestValidation:
    def test_valid_contact(self) -> None:
        data = {
            "name": "Иван Петров",
            "phone": "+79261234567",
            "email": "ivan@example.com",
            "comment": "Это валидный комментарий с достаточным количеством символов.",
        }
        contact = ContactRequest(**data)
        assert contact.name == "Иван Петров"
        assert contact.phone == "+79261234567"

    def test_name_too_short(self) -> None:
        with pytest.raises(ValidationError):
            ContactRequest(
                name="А",
                phone="+79261234567",
                email="ivan@example.com",
                comment="Это валидный комментарий с достаточным количеством символов.",
            )

    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            ContactRequest(
                name="А" * 101,
                phone="+79261234567",
                email="ivan@example.com",
                comment="Это валидный комментарий с достаточным количеством символов.",
            )

    def test_invalid_phone(self) -> None:
        with pytest.raises(ValidationError):
            ContactRequest(
                name="Иван",
                phone="abc",
                email="ivan@example.com",
                comment="Это валидный комментарий с достаточным количеством символов.",
            )

    def test_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            ContactRequest(
                name="Иван",
                phone="+79261234567",
                email="not-an-email",
                comment="Это валидный комментарий с достаточным количеством символов.",
            )

    def test_comment_too_short(self) -> None:
        with pytest.raises(ValidationError):
            ContactRequest(
                name="Иван",
                phone="+79261234567",
                email="ivan@example.com",
                comment="Коротко",
            )

    def test_comment_too_long(self) -> None:
        with pytest.raises(ValidationError):
            ContactRequest(
                name="Иван",
                phone="+79261234567",
                email="ivan@example.com",
                comment="X" * 3001,
            )
