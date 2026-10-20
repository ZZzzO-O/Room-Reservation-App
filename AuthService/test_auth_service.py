# file: test_auth_service.py
# purpose: Unit tests for auth_service.py (OBJ-01 authentication cases)
# author: Thiri Htet Thwe (Thiri)
# date: 2026-10-20

from datetime import datetime, timedelta
import unittest

import auth_service as auth


class AuthTestCase(unittest.TestCase):
    """Base test case initializing fresh user and session data stores."""

    def setUp(self) -> None:
        """Create fresh user and session data stores and seed test users."""
        self.users = {}
        self.sessions = {}
        auth.seed_default_users(self.users)


class TestAuthentication(AuthTestCase):
    """Test suite covering user authentication and credential verification."""

    def test_tc01_login_valid_staff(self) -> None:
        """TC-01: Valid staff credentials authenticate and create session."""
        user, session = auth.authenticate(
            self.users, self.sessions, "staff1@cmkl.ac.th", "Test@1234"
        )
        self.assertEqual(user.email, "staff1@cmkl.ac.th")
        self.assertEqual(user.role, auth.ROLE_STAFF)
        self.assertIn(session.token, self.sessions)
        self.assertGreater(session.expires_at, datetime.utcnow())

    def test_tc02_login_valid_professor(self) -> None:
        """TC-02: Valid professor credentials authenticate and return role."""
        user, session = auth.authenticate(
            self.users, self.sessions, "prof1@cmkl.ac.th", "Test@1234"
        )
        self.assertEqual(user.email, "prof1@cmkl.ac.th")
        self.assertEqual(user.role, auth.ROLE_PROFESSOR)
        self.assertIn(session.token, self.sessions)

    def test_tc03_login_unregistered_email(self) -> None:
        """TC-03: Unregistered email is rejected without revealing status."""
        with self.assertRaises(auth.InvalidCredentialsError):
            auth.authenticate(
                self.users, self.sessions, "guest@gmail.com", "Test@1234"
            )
        self.assertEqual(len(self.sessions), 0)

    def test_tc04_login_wrong_password(self) -> None:
        """TC-04: Wrong password is rejected with identical error."""
        with self.assertRaises(auth.InvalidCredentialsError):
            auth.authenticate(
                self.users, self.sessions, "staff1@cmkl.ac.th", "WrongPass"
            )
        self.assertEqual(len(self.sessions), 0)

    def test_tc05_login_empty_fields(self) -> None:
        """TC-05: Empty or whitespace email and password are rejected."""
        for bad_email in ("", "   ", None):
            with self.assertRaises(auth.InvalidCredentialsError):
                auth.authenticate(
                    self.users, self.sessions, bad_email, "Test@1234"
                )
        for bad_pwd in ("", None):
            with self.assertRaises(auth.InvalidCredentialsError):
                auth.authenticate(
                    self.users, self.sessions, "staff1@cmkl.ac.th", bad_pwd
                )

    def test_case_insensitive_email(self) -> None:
        """Check: email authentication is case-insensitive."""
        user, _ = auth.authenticate(
            self.users, self.sessions, "STAFF1@CMKL.AC.TH", "Test@1234"
        )
        self.assertEqual(user.email, "staff1@cmkl.ac.th")


class TestSessionManagement(AuthTestCase):
    """Test suite covering token validation, expiry, and logout."""

    def setUp(self) -> None:
        """Create an active session for testing."""
        super().setUp()
        self.user, self.session = auth.authenticate(
            self.users, self.sessions, "staff1@cmkl.ac.th", "Test@1234"
        )

    def test_tc06_validate_active_session(self) -> None:
        """TC-06: Active session token resolves to authenticated user."""
        validated_user = auth.validate_session(
            self.users, self.sessions, self.session.token
        )
        self.assertEqual(validated_user.email, "staff1@cmkl.ac.th")

    def test_missing_or_blank_token_raises(self) -> None:
        """Check: missing or blank token raises InvalidSessionError."""
        for bad_token in ("", "   ", None):
            with self.assertRaises(auth.InvalidSessionError):
                auth.validate_session(self.users, self.sessions, bad_token)

    def test_nonexistent_token_raises(self) -> None:
        """Check: random nonexistent token raises InvalidSessionError."""
        with self.assertRaises(auth.InvalidSessionError):
            auth.validate_session(
                self.users, self.sessions, "invalid-token-12345"
            )

    def test_expired_session_raises(self) -> None:
        """Check: expired token is purged and raises InvalidSessionError."""
        self.session.expires_at = datetime.utcnow() - timedelta(minutes=5)
        with self.assertRaises(auth.InvalidSessionError):
            auth.validate_session(
                self.users, self.sessions, self.session.token
            )
        self.assertNotIn(self.session.token, self.sessions)

    def test_logout_terminates_session(self) -> None:
        """Check: terminate_session removes active token."""
        auth.terminate_session(self.sessions, self.session.token)
        self.assertNotIn(self.session.token, self.sessions)
        with self.assertRaises(auth.InvalidSessionError):
            auth.validate_session(
                self.users, self.sessions, self.session.token
            )

    def test_logout_nonexistent_token_is_safe(self) -> None:
        """Check: logging out nonexistent token does not raise."""
        auth.terminate_session(self.sessions, "already-logged-out")


class TestUserRegistration(AuthTestCase):
    """Test suite covering user registration and validation."""

    def test_register_new_user_stores_user(self) -> None:
        """Check: registering valid user adds account."""
        new_user = auth.register_user(
            self.users,
            "newprof@cmkl.ac.th",
            "SecurePass#2026",
            auth.ROLE_PROFESSOR,
            "New Professor",
        )
        self.assertEqual(new_user.email, "newprof@cmkl.ac.th")
        self.assertEqual(new_user.role, auth.ROLE_PROFESSOR)
        self.assertIn("newprof@cmkl.ac.th", self.users)

    def test_duplicate_email_registration_rejected(self) -> None:
        """Check: duplicate email registration raises UserAlreadyExists."""
        with self.assertRaises(auth.UserAlreadyExistsError):
            auth.register_user(
                self.users,
                "staff1@cmkl.ac.th",
                "AnotherPassword1",
                auth.ROLE_STAFF,
            )

    def test_invalid_email_format_rejected(self) -> None:
        """Check: email without @ symbol is rejected."""
        with self.assertRaises(auth.InvalidCredentialsError):
            auth.register_user(
                self.users, "invalid-email", "Pass123", auth.ROLE_STAFF
            )

    def test_invalid_role_rejected(self) -> None:
        """Check: unsupported role string is rejected."""
        with self.assertRaises(auth.InvalidCredentialsError):
            auth.register_user(
                self.users,
                "admin@cmkl.ac.th",
                "Pass123",
                "SuperAdmin",
            )

    def test_get_user_by_email_success(self) -> None:
        """Check: get_user_by_email returns correct user."""
        user = auth.get_user_by_email(self.users, "staff1@cmkl.ac.th")
        self.assertEqual(user.user_id, self.users["staff1@cmkl.ac.th"].user_id)

    def test_get_user_by_email_missing_raises(self) -> None:
        """Check: get_user_by_email for missing account raises."""
        with self.assertRaises(auth.UserNotFoundError):
            auth.get_user_by_email(self.users, "missing@cmkl.ac.th")

    def test_register_empty_password_rejected(self) -> None:
        """Check: registration with empty password raises."""
        for bad_pwd in ("", None):
            with self.assertRaises(auth.InvalidCredentialsError):
                auth.register_user(
                    self.users, "user@cmkl.ac.th", bad_pwd, auth.ROLE_STAFF
                )


if __name__ == "__main__":
    unittest.main()
