# -*- coding: utf-8 -*-
"""
Desktop launcher for Classroom Reservation Application.
Serves the React frontend (dist/) and the Flask API Gateway on http://127.0.0.1:5000,
then opens the default web browser automatically.
"""

import os
import sys
import time
import webbrowser
import threading
from pathlib import Path

# Add project root to sys.path so modules import cleanly
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import Flask components
from flask import Flask, send_from_directory, jsonify, request
from ApiGateway.api_gateway import create_app

def setup_desktop_app():
    # If running from PyInstaller frozen exe, app.db should reside next to the .exe file
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        db_file = str(exe_dir / "app.db")
    else:
        db_file = str(BASE_DIR / "app.db")

    app = create_app(db_path=db_file)
    dist_dir = BASE_DIR / "reservation-app" / "dist"

    if dist_dir.exists() and (dist_dir / "index.html").exists():
        # Override root route to serve React UI index.html
        def serve_index():
            return send_from_directory(dist_dir, "index.html")
        app.view_functions['root'] = serve_index

        # Serve static assets (JS, CSS, SVGs)
        @app.route("/assets/<path:filename>")
        def serve_dist_assets(filename):
            return send_from_directory(dist_dir / "assets", filename)

        @app.route("/<file>.svg")
        def serve_dist_svg(file):
            return send_from_directory(dist_dir, f"{file}.svg")

        # Fallback 404 to index.html for client-side React routes (e.g. /login, /rooms)
        @app.errorhandler(404)
        def handle_spa_fallback(e):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Endpoint not found"}), 404
            return send_from_directory(dist_dir, "index.html")

    return app, db_file

def open_browser():
    time.sleep(1.2)
    print("  [+] Launching browser: http://127.0.0.1:5000 ...")
    webbrowser.open_new("http://127.0.0.1:5000")

def main():
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
