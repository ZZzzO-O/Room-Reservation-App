# -*- coding: utf-8 -*-
# file: desktop_app.py
# purpose: Desktop launcher for Classroom Reservation Application
# author: Su Pyae Pyae Aung (Micky)
"""
Desktop launcher for Classroom Reservation Application.

Serves the React frontend (dist/) and the Flask API Gateway on
http://127.0.0.1:5000, then opens the default web browser automatically.
"""

from pathlib import Path
import os
import sys
import threading
import time
from typing import Tuple
import webbrowser

# Add project root to sys.path so modules import cleanly
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)  # pylint: disable=protected-access
else:
    BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import Flask components
from flask import Flask, jsonify, request, send_from_directory
from ApiGateway.api_gateway import create_app


def setup_desktop_app() -> Tuple[Flask, str]:
    """
    Configure Flask app with API Gateway and React frontend static assets.

    Returns:
        Tuple[Flask, str]: The configured Flask application and database path.
    """
    # Keep local database defaults while allowing hosts to provide persistent
    # storage outside the application directory.
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        default_db_file = exe_dir / "app.db"
    else:
        default_db_file = BASE_DIR / "app.db"
    db_file = os.environ.get("DB_PATH", str(default_db_file))

    app = create_app(db_path=db_file)
    dist_dir = BASE_DIR / "reservation-app" / "dist"

    if dist_dir.exists() and (dist_dir / "index.html").exists():
        # Serve React UI index.html with no-cache headers
        def serve_index():
            resp = send_from_directory(dist_dir, "index.html")
            resp.headers["Cache-Control"] = (
                "no-cache, no-store, must-revalidate"
            )
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
            return resp

        # Dynamically locate whichever endpoint handles GET on "/" from the
        # URL map rather than hardcoding the function name 'root'. This
        # guarantees the desktop app displays the React UI even if the
        # gateway's health-check function is renamed (e.g. to health_check).
        root_endpoints = [
            rule.endpoint
            for rule in app.url_map.iter_rules()
            if rule.rule == "/" and "GET" in rule.methods
        ]

        original_health_fn = None
        if root_endpoints:
            for endpoint in root_endpoints:
                if endpoint in app.view_functions:
                    original_health_fn = app.view_functions[endpoint]
                    app.view_functions[endpoint] = serve_index
        else:
            # If the gateway defines no root GET route, register "/" directly
            app.add_url_rule("/", "serve_index", serve_index, methods=["GET"])

        # Also preserve 'root' endpoint mapping if present for compatibility
        if "root" in app.view_functions:
            app.view_functions["root"] = serve_index

        # Keep gateway health-check accessible on /api/health if not registered
        has_api_health = any(
            rule.rule == "/api/health" for rule in app.url_map.iter_rules()
        )
        if not has_api_health and original_health_fn:
            app.add_url_rule(
                "/api/health",
                "gateway_health",
                original_health_fn,
                methods=["GET"],
            )

        # Serve static assets (JS, CSS, SVGs)
        @app.route("/assets/<path:filename>")
        def serve_dist_assets(filename):
            return send_from_directory(dist_dir / "assets", filename)

        @app.route("/<file>.svg")
        def serve_dist_svg(file):
            return send_from_directory(dist_dir, f"{file}.svg")

        @app.route("/manifest.webmanifest")
        def serve_web_manifest():
            return send_from_directory(dist_dir, "manifest.webmanifest")

        @app.route("/service-worker.js")
        def serve_service_worker():
            response = send_from_directory(dist_dir, "service-worker.js")
            response.headers["Cache-Control"] = "no-cache"
            response.headers["Service-Worker-Allowed"] = "/"
            return response

        @app.route("/icons/<path:filename>")
        def serve_pwa_icons(filename):
            return send_from_directory(dist_dir / "icons", filename)

        # Fallback 404 to index.html for client-side routes (e.g. /login)
        @app.errorhandler(404)
        def handle_spa_fallback(_error):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Endpoint not found"}), 404
            return send_from_directory(dist_dir, "index.html")

    return app, db_file


def open_browser() -> None:
    """Wait for server startup and open the app in the default web browser."""
    time.sleep(1.2)
    print("  [+] Launching browser: http://127.0.0.1:5000 ...")
    webbrowser.open_new("http://127.0.0.1:5000")


def main() -> None:
    """Launch the classroom reservation desktop application server."""
    print("=" * 65)
    print("   CMKL UNIVERSITY - CLASSROOM RESERVATION APPLICATION")
    print("   Team Vibranium (SEN-201 Final Software Demo)")
    print("=" * 65)

    app, db_file = setup_desktop_app()
    print(f"  [+] Database connected: {db_file}")
    print("  [+] Web UI & API Gateway online at: http://127.0.0.1:5000")
    print("  [+] Press Ctrl+C in this terminal to exit.")
    print("=" * 65)

    # Launch browser in a background thread so it doesn't block the server
    threading.Thread(target=open_browser, daemon=True).start()

    # Start Flask server
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
