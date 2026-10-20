# file: auth_service.py
# purpose: User authentication, session management, and role authorization
# author: Thiri Htet Thwe (Thiri)
# date: 2026-10-20

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import secrets
from typing import Dict, Optional

ROLE_STAFF = "Staff"
ROLE_PROFESSOR = "Professor"
DEFAULT_SESSION_TTL_HOURS = 24


class AuthError(Exception):
    """Base class for all authentication and authorization errors."""


class InvalidCredentialsError(AuthError):
    """Raised when email or password is missing, invalid, or incorrect."""


class UserNotFoundError(AuthError):
    """Raised when a user account cannot be found."""


class UserAlreadyExistsError(AuthError):
    """Raised when attempting to register an existing email."""


class InvalidSessionError(AuthError):
    """Raised when a session token is missing, expired, or invalid."""


class PermissionDeniedError(AuthError):
    """Raised when a user lacks the required role for an operation."""


@dataclass(slots=True)
class User:
    """A registered user account with credentials and authorization role."""

    user_id: str
    email: str
    password_hash: str
    salt: str
    role: str
    name: str = ""


@dataclass(slots=True)
class Session:
    """An active authenticated session identified by a cryptosecure token."""

    token: str
    user_id: str
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)


def hash_password(
    password: str, salt: Optional[str] = None
) -> tuple[str, str]:
    """
    Hash a plaintext password using SHA-256 with a random cryptographic salt.

    Args:
        password (str): Plaintext password to hash.
        salt (Optional[str]): Existing hex salt, or None to generate new salt.

    Returns:
        tuple[str, str]: Tuple of (password_hash, salt).
    """
    if salt is None:
        salt = secrets.token_hex(16)
    combined = (salt + password).encode("utf-8")
    pwd_hash = hashlib.sha256(combined).hexdigest()
    return pwd_hash, salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """
    Check if a plaintext password matches the salted hash in constant time.

    Args:
        password (str): Plaintext candidate password.
        salt (str): Stored user salt.
        expected_hash (str): Stored cryptographic hash.

    Returns:
        bool: True if passwords match, False otherwise.
    """
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, expected_hash)


def validate_email(email: str) -> str:
    """
    Validate and normalize an email address.

    Args:
        email (str): Candidate email address.

    Returns:
        str: Lowercased, stripped email string.

    Raises:
        InvalidCredentialsError: If email is empty or missing '@'.
    """
    if not isinstance(email, str) or not email.strip():
        raise InvalidCredentialsError("Email must not be empty.")
    normalized = email.strip().lower()
    if "@" not in normalized or normalized.startswith("@"):
        raise InvalidCredentialsError("Invalid email address format.")
    return normalized


def register_user(
    users: Dict[str, User],
    email: str,
    password: str,
    role: str,
    name: str = "",
    user_id: Optional[str] = None,
) -> User:
    """
    Register a new user in the User Data store.

    Args:
        users (Dict[str, User]): User store keyed by normalized email.
        email (str): Unique user email address.
        password (str): Plaintext account password.
        role (str): System role (e.g., "Staff" or "Professor").
        name (str): Full display name of the user.
        user_id (Optional[str]): Custom user ID, or generated hex ID.

    Returns:
        User: Newly registered user record.

    Raises:
        InvalidCredentialsError: If email or password is empty.
        UserAlreadyExistsError: If email is already registered.
    """
    clean_email = validate_email(email)
    if not isinstance(password, str) or not password:
        raise InvalidCredentialsError("Password must not be empty.")
    if clean_email in users:
        raise UserAlreadyExistsError(f"User {clean_email} already exists.")
    if role not in (ROLE_STAFF, ROLE_PROFESSOR):
        raise InvalidCredentialsError(
            f"Role must be '{ROLE_STAFF}' or '{ROLE_PROFESSOR}'."
        )

    pwd_hash, salt = hash_password(password)
    uid = user_id or f"USR-{secrets.token_hex(4).upper()}"
    user = User(
        user_id=uid,
        email=clean_email,
        password_hash=pwd_hash,
        salt=salt,
        role=role,
        name=name or clean_email.split("@")[0],
    )
    users[clean_email] = user
    return user


def get_user_by_email(users: Dict[str, User], email: str) -> User:
    """
    Retrieve a user by their email address.

    Args:
        users (Dict[str, User]): User store keyed by email.
        email (str): Target email address.

    Returns:
        User: Matching user record.

    Raises:
        UserNotFoundError: If no account exists with this email.
    """
    clean_email = validate_email(email)
    if clean_email not in users:
        raise UserNotFoundError("User account not found.")
    return users[clean_email]


def authenticate(
    users: Dict[str, User],
    sessions: Dict[str, Session],
    email: str,
    password: str,
    ttl_hours: int = DEFAULT_SESSION_TTL_HOURS,
) -> tuple[User, Session]:
    """
    Authenticate email & password and issue an active session token.

    Args:
        users (Dict[str, User]): User data store.
        sessions (Dict[str, Session]): Active sessions keyed by token.
        email (str): Candidate email address.
        password (str): Candidate plaintext password.
        ttl_hours (int): Number of hours the session remains valid.

    Returns:
        tuple[User, Session]: Authenticated user and new session.

    Raises:
        InvalidCredentialsError: If credentials do not match or are empty.
    """
    if not isinstance(email, str) or not email.strip():
        raise InvalidCredentialsError("Email and password are required.")
    if not isinstance(password, str) or not password:
        raise InvalidCredentialsError("Email and password are required.")

    clean_email = validate_email(email)
    user = users.get(clean_email)
    if not user:
        raise InvalidCredentialsError("Incorrect email or password.")

    if not verify_password(password, user.salt, user.password_hash):
        raise InvalidCredentialsError("Incorrect email or password.")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
    session = Session(
        token=token,
        user_id=user.user_id,
        expires_at=expires_at,
    )
    sessions[token] = session
    return user, session


def validate_session(
    users: Dict[str, User],
    sessions: Dict[str, Session],
    token: str,
) -> User:
    """
    Validate a session token and return the associated user profile.

    Args:
        users (Dict[str, User]): User data store.
        sessions (Dict[str, Session]): Active session store.
        token (str): Bearer session token.

    Returns:
        User: Currently authenticated user.

    Raises:
        InvalidSessionError: If token is missing, expired, or invalid.
    """
    if not isinstance(token, str) or not token.strip():
        raise InvalidSessionError("Authentication token is required.")

    session = sessions.get(token.strip())
    if not session:
        raise InvalidSessionError("Invalid or expired session.")

    if datetime.utcnow() > session.expires_at:
        del sessions[token.strip()]
        raise InvalidSessionError("Session has expired.")

    # Find user by user_id
    for user in users.values():
        if user.user_id == session.user_id:
            return user

    raise InvalidSessionError("Session user not found.")


def terminate_session(sessions: Dict[str, Session], token: str) -> None:
    """
    Log out a user by invalidating their active session token.

    Args:
        sessions (Dict[str, Session]): Active session store.
        token (str): Token to revoke.

    Returns:
        None
    """
    if token in sessions:
        del sessions[token]


def seed_default_users(users: Dict[str, User]) -> Dict[str, User]:
    """
    Seed standard CMKL staff and professor test accounts.

    Includes accounts defined in Vibranium Functional Test Plan:
    - staff1@cmkl.ac.th (Staff, Password: Test@1234)
    - prof1@cmkl.ac.th  (Professor, Password: Test@1234)

    Args:
        users (Dict[str, User]): Destination user store.

    Returns:
        Dict[str, User]: Seeded user store.
    """
    test_accounts = [
        ("staff1@cmkl.ac.th", "Test@1234", ROLE_STAFF, "CMKL Staff Member"),
        ("prof1@cmkl.ac.th", "Test@1234", ROLE_PROFESSOR, "CMKL Professor"),
    ]
    for email, pwd, role, name in test_accounts:
        if email not in users:
            register_user(users, email, pwd, role, name)
    return users
