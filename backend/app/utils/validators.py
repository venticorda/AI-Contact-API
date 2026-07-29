from __future__ import annotations

import re


def validate_phone(phone: str) -> bool:
    pattern = r"^\+?1?\d{7,15}$"
    return bool(re.match(pattern, phone.strip()))


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))
