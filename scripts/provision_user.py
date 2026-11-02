"""Provision accounts without exposing passwords in command arguments."""

import argparse
from getpass import getpass
import os
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "Database"))
sys.path.insert(0, str(BASE_DIR / "AuthService"))

import database as db  # noqa: E402
import auth_service as auth  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create an application account in DATABASE_URL."
    )
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--role",
        required=True,
        choices=(auth.ROLE_STAFF, auth.ROLE_PROFESSOR),
    )
    parser.add_argument("--name", default="")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url.startswith(("postgres://", "postgresql://")):
        parser.error(
            "Set DATABASE_URL to the target PostgreSQL database before "
            "running this production provisioning command."
        )

    password = getpass("New account password (12+ characters): ")
    confirmation = getpass("Confirm password: ")
    if len(password) < 12:
        parser.error("Password must contain at least 12 characters.")
    if password != confirmation:
        parser.error("The passwords do not match.")

    connection = db.get_connection(database_url)
    try:
        db.init_db(connection)
        service = auth.AuthService(connection)
        service.register(args.email, password, args.role, args.name)
    except auth.AuthError as exc:
        parser.exit(1, f"Could not provision account: {exc}\n")
    finally:
        connection.close()

    print(f"Provisioned {args.role} account for {args.email}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
