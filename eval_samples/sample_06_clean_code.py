"""사용자 관리 모듈 — 깨끗한 코드 (오탐 테스트용)"""

from dataclasses import dataclass
from typing import Optional


MAX_USERNAME_LENGTH = 50
MIN_PASSWORD_LENGTH = 8


@dataclass
class User:
    id: int
    username: str
    email: str
    is_active: bool = True


def validate_username(username: str) -> bool:
    if not username or len(username) > MAX_USERNAME_LENGTH:
        return False
    return username.isalnum()


def validate_password(password: str) -> bool:
    if len(password) < MIN_PASSWORD_LENGTH:
        return False
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_upper and has_digit


def find_user_by_id(users: list[User], user_id: int) -> Optional[User]:
    for user in users:
        if user.id == user_id:
            return user
    return None


def get_active_users(users: list[User]) -> list[User]:
    return [user for user in users if user.is_active]
