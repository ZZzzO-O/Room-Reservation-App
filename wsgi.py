"""WSGI entry point for production application servers."""

from desktop_app import setup_desktop_app

app, _db_file = setup_desktop_app()
