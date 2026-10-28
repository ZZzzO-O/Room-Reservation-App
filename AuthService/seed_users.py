# file: seed_users.py
# purpose: Sample Staff and Professor accounts for development and testing
# author: Thiri Htet Thwe (Thiri)
# date: 2026-10-21
"""Sample Staff and Professor accounts for development and testing."""


from auth_service import (
    ROLE_PROFESSOR,
    ROLE_STAFF,
    AuthService,
    hash_password,
)

# Test-only passwords, listed in the Functional Test Plan. Real accounts are
# created with AuthService.register() and never written in source code.
TEST_ACCOUNTS = [
    ("staff1@cmkl.ac.th", "Test@1234", ROLE_STAFF, "CMKL Staff Member"),
    ("prof1@cmkl.ac.th", "Test@1234", ROLE_PROFESSOR, "CMKL Professor"),
]


def load_test_users(auth: AuthService) -> AuthService:
    """
    Register the test accounts that do not exist yet.

    Args:
        auth (AuthService): Service to add the accounts to.

    Returns:
        AuthService: The same service, now holding the test accounts.
    """
    for email, password, role, name in TEST_ACCOUNTS:
        user = auth.users.get(email)
        if user is None:
            auth.register(email, password, role, name)
            continue

        # The database may persist an older version of these public test
        # accounts. Keep their documented credentials reliable on every
        # development-server restart without creating duplicate users.
        user.password_hash, user.salt = hash_password(password)
        user.role = role
        user.name = name
        if auth.conn is not None:
            auth._db().save_user(auth.conn, user)
    return auth
