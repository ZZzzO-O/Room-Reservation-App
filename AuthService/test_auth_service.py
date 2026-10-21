# file: test_auth_service.py
# purpose: Unit tests for auth_service.py (OBJ-01 authentication cases)
# author: Thiri Htet Thwe (Thiri)
# date: 2026-10-20
"""
Unit test suite for authentication service, password hashing, and sessions.
"""


from datetime import timedelta
import unittest

import auth_service as auth
from seed_users import load_test_users

STAFF_EMAIL = "staff1@cmkl.ac.th"
PASSWORD = "Test@1234"


class AuthTestCase(unittest.TestCase):
    """Each test gets a fresh in-memory AuthService with the test users."""

    def setUp(self) -> None:
        """Create a new AuthService (no database) with the test accounts."""
        self.auth = load_test_users(auth.AuthService())


class TestPasswords(AuthTestCase):
    """Password hashing."""

    def test_hash_is_salted(self) -> None:
        """Same password, different salt, different hash."""
        hash1, salt1 = auth.hash_password("abc")
        hash2, salt2 = auth.hash_password("abc")
        self.assertNotEqual(salt1, salt2)
        self.assertNotEqual(hash1, hash2)

    def test_verify_password(self) -> None:
        """Correct password passes; wrong one fails."""
        pwd_hash, salt = auth.hash_password("abc")
        self.assertTrue(auth.verify_password("abc", salt, pwd_hash))
        self.assertFalse(auth.verify_password("abd", salt, pwd_hash))

    def test_starts_empty_without_seed(self) -> None:
        """AuthService itself adds no sample accounts."""
        self.assertEqual(auth.AuthService().users, {})

    def test_seed_is_safe_to_run_twice(self) -> None:
        """Seeding again does not raise or duplicate accounts."""
        load_test_users(self.auth)
        self.assertEqual(len(self.auth.users), 2)

    def test_password_not_stored_in_plain_text(self) -> None:
        """The stored user keeps only the hash."""
        user = self.auth.users[STAFF_EMAIL]
        self.assertNotIn(PASSWORD, (user.password_hash, user.salt))


class TestLogin(AuthTestCase):
    """Test plan 1.1 - 1.3: logging in."""

    def test_1_1_registered_user_logs_in(self) -> None:
        """1.1: Correct email and password create a session."""
        user, session = self.auth.login(STAFF_EMAIL, PASSWORD)
        self.assertEqual(user.role, auth.ROLE_STAFF)
        self.assertIn(session.token, self.auth.sessions)

    def test_email_is_case_insensitive(self) -> None:
        """Upper-case email with spaces still works."""
        user, _ = self.auth.login("  STAFF1@CMKL.AC.TH ", PASSWORD)
        self.assertEqual(user.email, STAFF_EMAIL)

    def test_1_2_unregistered_email_rejected(self) -> None:
        """1.2: Unknown email gives the generic login error."""
        with self.assertRaisesRegex(
            auth.InvalidCredentialsError, "Incorrect email or password"
        ):
            self.auth.login("guest@gmail.com", PASSWORD)

    def test_1_3_wrong_password_rejected(self) -> None:
        """1.3: Wrong password gives the same generic error."""
        with self.assertRaisesRegex(
            auth.InvalidCredentialsError, "Incorrect email or password"
        ):
            self.auth.login(STAFF_EMAIL, "Wrong123")
        self.assertEqual(self.auth.sessions, {})

    def test_empty_fields_rejected(self) -> None:
        """Blank email or password is rejected."""
        for email, password in (("", PASSWORD), (STAFF_EMAIL, "")):
            with self.assertRaises(auth.InvalidCredentialsError):
                self.auth.login(email, password)


class TestSessions(AuthTestCase):
    """Test plan 1.4 - 1.5: tokens and logging out."""

    def setUp(self) -> None:
        """Log the staff user in."""
        super().setUp()
        _, session = self.auth.login(STAFF_EMAIL, PASSWORD)
        self.token = session.token

    def test_valid_token_returns_user(self) -> None:
        """A live token identifies the user."""
        self.assertEqual(self.auth.check_token(self.token).email, STAFF_EMAIL)

    def test_1_4_missing_or_unknown_token_rejected(self) -> None:
        """1.4: No token, or a made-up token, is rejected."""
        for token in ("", "made-up-token"):
            with self.assertRaises(auth.InvalidSessionError):
                self.auth.check_token(token)

    def test_1_5_token_rejected_after_logout(self) -> None:
        """1.5: After logout the old token no longer works."""
        self.auth.logout(self.token)
        with self.assertRaises(auth.InvalidSessionError):
            self.auth.check_token(self.token)

    def test_expired_token_rejected_and_removed(self) -> None:
        """An expired session is rejected and deleted."""
        self.auth.sessions[self.token].expires_at = (
            auth.utc_now() - timedelta(minutes=1)
        )
        with self.assertRaisesRegex(auth.InvalidSessionError, "expired"):
            self.auth.check_token(self.token)
        self.assertNotIn(self.token, self.auth.sessions)

    def test_logout_unknown_token_is_safe(self) -> None:
        """Logging out an unknown token does nothing."""
        self.auth.logout("not-a-token")


class TestRegister(AuthTestCase):
    """Creating accounts."""

    def test_register_new_user(self) -> None:
        """A new user can log in after registering."""
        self.auth.register("new@cmkl.ac.th", "pw123", auth.ROLE_PROFESSOR)
        user, _ = self.auth.login("new@cmkl.ac.th", "pw123")
        self.assertEqual(user.name, "new")

    def test_invalid_registrations_rejected(self) -> None:
        """Duplicate email, bad email, empty password, bad role."""
        cases = [
            (STAFF_EMAIL, "pw", auth.ROLE_STAFF,
             auth.UserAlreadyExistsError),
            ("not-an-email", "pw", auth.ROLE_STAFF,
             auth.InvalidCredentialsError),
            ("@cmkl.ac.th", "pw", auth.ROLE_STAFF,
             auth.InvalidCredentialsError),
            ("a@cmkl.ac.th", "", auth.ROLE_STAFF,
             auth.InvalidCredentialsError),
            ("a@cmkl.ac.th", "pw", "Admin", auth.InvalidCredentialsError),
        ]
        for email, password, role, expected_error in cases:
            with self.subTest(email=email, role=role):
                with self.assertRaises(expected_error):
                    self.auth.register(email, password, role)


if __name__ == "__main__":
    unittest.main()
