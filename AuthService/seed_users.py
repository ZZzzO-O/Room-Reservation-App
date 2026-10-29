# file: seed_users.py
# purpose: Sample Staff and Professor accounts for development and testing
# author: Thiri Htet Thwe (Thiri)
# date: 2026-10-21
"""Sample Staff and Professor accounts for development and testing."""


from auth_service import ROLE_PROFESSOR, ROLE_STAFF, AuthService

# Test-only passwords, listed in the Functional Test Plan. Real accounts are
# created with AuthService.register() and never written in source code.
TEST_ACCOUNTS = [
    ("staff1@cmkl.ac.th", "Test@1234", ROLE_STAFF, "CMKL Staff Member"),
    ("prof1@cmkl.ac.th", "Test@1234", ROLE_PROFESSOR, "CMKL Professor"),
]


def load_test_users(auth: AuthService) -> AuthService:
    """
    Create the test accounts, or reset them to their documented values.

    Only the emails in TEST_ACCOUNTS are touched; real accounts never are.

    Args:
        auth (AuthService): Service to add the accounts to.

    Returns:
        AuthService: The same service, now holding the test accounts.
    """
    for email, password, role, name in TEST_ACCOUNTS:
        if email in auth.users:
            # Reset to a known starting point on every server start, so
            # each test run begins from the documented credentials.
            auth.update_user(email, password, role, name)
        else:
            auth.register(email, password, role, name)
    return auth
