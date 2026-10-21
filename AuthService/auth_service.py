# file: auth_service.py
# purpose: User authentication, session management, and role authorization
# author: Thiri Htet Thwe (Thiri)
# date: 2026-10-20
"""
User authentication, session tokens, and role-based authorization service.
"""


from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import sqlite3
from types import ModuleType
from typing import Dict, Optional, Tuple

ROLE_STAFF = "Staff"
ROLE_PROFESSOR = "Professor"
SESSION_HOURS = 24
HASH_ROUNDS = 200_000


class AuthError(Exception):
    """Base class for every authentication error."""


class InvalidCredentialsError(AuthError):
    """Email or password is missing, badly formed, or wrong."""


class InvalidSessionError(AuthError):
    """Session token is missing, unknown, or expired."""


class UserAlreadyExistsError(AuthError):
    """An account with this email already exists."""


@dataclass(slots=True)
class User:
    """A registered account. Only the salted hash of the password is kept."""

    user_id: str
    email: str
    password_hash: str
    salt: str
    role: str
    name: str = ""


def utc_now() -> datetime:
    """
    Return the current UTC time without a time zone attached.

    Returns:
        datetime: Current UTC time (naive, to match stored sessions).
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass(slots=True)
class Session:
    """A logged-in session, identified by a random token."""

    token: str
    user_id: str
    expires_at: datetime
    created_at: datetime = field(default_factory=utc_now)


def hash_password(
    password: str, salt: Optional[str] = None
) -> Tuple[str, str]:
    """
    Hash a password with PBKDF2-SHA256 and a random salt.

    Args:
        password (str): Plaintext password.
        salt (Optional[str]): Existing hex salt, or None to make a new one.

    Returns:
        Tuple[str, str]: (password_hash, salt), both as hex strings.
    """
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), HASH_ROUNDS
    )
    return digest.hex(), salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """
    Check a password against a stored hash in constant time.

    Args:
        password (str): Plaintext password to check.
        salt (str): Salt stored with the user.
        expected_hash (str): Hash stored with the user.

    Returns:
        bool: True if the password is correct.
    """
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, expected_hash)


def normalize_email(email: str) -> str:
    """
    Trim and lowercase an email, and reject obviously invalid ones.

    Args:
        email (str): Email typed by the user.

    Returns:
        str: Cleaned email.

    Raises:
        InvalidCredentialsError: If the email is empty or has no '@'.
    """
    if not isinstance(email, str) or "@" not in email.strip()[1:]:
        raise InvalidCredentialsError("A valid email is required.")
    return email.strip().lower()


class AuthService:
    """Owns User Data and sessions; the API gateway only calls its methods."""

    def __init__(self, conn: Optional[sqlite3.Connection] = None) -> None:
        """
        Load users and sessions from SQLite, or start empty in memory.

        Sample accounts are added separately by seed_users.py.

        Args:
            conn (Optional[sqlite3.Connection]): Database, or None.
        """
        self.conn = conn
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}
        if conn is not None:
            self.users = self._db().load_users(conn)
            self.sessions = self._db().load_sessions(conn)

    def register(
        self, email: str, password: str, role: str, name: str = ""
    ) -> User:
        """
        Create a new account and save it.

        Args:
            email (str): Unique email.
            password (str): Plaintext password.
            role (str): ROLE_STAFF or ROLE_PROFESSOR.
            name (str): Display name; defaults to the part before '@'.

        Returns:
            User: The new account.

        Raises:
            InvalidCredentialsError: If email, password, or role is invalid.
            UserAlreadyExistsError: If the email is already registered.
        """
        email = normalize_email(email)
        if not password:
            raise InvalidCredentialsError("Password must not be empty.")
        if role not in (ROLE_STAFF, ROLE_PROFESSOR):
            raise InvalidCredentialsError("Role must be Staff or Professor.")
        if email in self.users:
            raise UserAlreadyExistsError(f"User {email} already exists.")

        password_hash, salt = hash_password(password)
        user = User(
            user_id=f"USR-{secrets.token_hex(4).upper()}",
            email=email,
            password_hash=password_hash,
            salt=salt,
            role=role,
            name=name or email.split("@")[0],
        )
        self.users[email] = user
        if self.conn is not None:
            self._db().save_user(self.conn, user)
        return user

    def login(self, email: str, password: str) -> Tuple[User, Session]:
        """
        Check email and password, then start a new session.

        Args:
            email (str): Email typed by the user.
            password (str): Password typed by the user.

        Returns:
            Tuple[User, Session]: The user and their new session.

        Raises:
            InvalidCredentialsError: If the email or password is wrong.
        """
        user = self.users.get(normalize_email(email))
        # Same message for unknown email and wrong password, so an
        # attacker cannot find out which emails have accounts.
        if user is None or not verify_password(
            password or "", user.salt, user.password_hash
        ):
            raise InvalidCredentialsError("Incorrect email or password.")

        session = Session(
            token=secrets.token_urlsafe(32),
            user_id=user.user_id,
            expires_at=utc_now() + timedelta(hours=SESSION_HOURS),
        )
        self.sessions[session.token] = session
        if self.conn is not None:
            self._db().save_session(self.conn, session)
        return user, session

    def check_token(self, token: str) -> User:
        """
        Return the user who owns a valid session token.

        Args:
            token (str): Token from the Authorization header.

        Returns:
            User: The logged-in user.

        Raises:
            InvalidSessionError: If the token is missing, unknown, or expired.
        """
        session = self.sessions.get(token or "")
        if session is None:
            raise InvalidSessionError("Please log in first.")
        if utc_now() > session.expires_at:
            self.logout(token)
            raise InvalidSessionError("Session has expired.")

        for user in self.users.values():
            if user.user_id == session.user_id:
                return user
        raise InvalidSessionError("Session user not found.")

    def logout(self, token: str) -> None:
        """
        End a session. Unknown tokens are ignored.

        Args:
            token (str): Token to remove.
        """
        self.sessions.pop(token, None)
        if self.conn is not None:
            self._db().delete_session(self.conn, token)

    @staticmethod
    def _db() -> ModuleType:
        """
        Import the database module only when it is needed.

        database.py imports this file, so importing it at the top here
        would be a circular import.

        Returns:
            ModuleType: The database module.
        """
        # pylint: disable=import-outside-toplevel
        import database
        return database
