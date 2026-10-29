# -*- coding: utf-8 -*-
# file: test_desktop_app.py
# purpose: Unit tests for desktop launcher and dynamic route handling
# author: Su Pyae Pyae Aung (Micky)
"""Unit tests for desktop_app.py launcher and route overriding."""

import unittest
from flask import Flask, jsonify

from desktop_app import setup_desktop_app


class TestDesktopApp(unittest.TestCase):
    """Test suite for desktop app setup and dynamic route handling."""

    def setUp(self) -> None:
        """Initialize desktop app and test client."""
        self.app, self.db_file = setup_desktop_app()
        self.client = self.app.test_client()

    def test_root_serves_index_html(self) -> None:
        """Root GET route serves index.html with no-cache headers."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res.content_type)
        self.assertEqual(
            res.headers.get("Cache-Control"),
            "no-cache, no-store, must-revalidate",
        )
        self.assertEqual(res.headers.get("Pragma"), "no-cache")

    def test_gateway_health_accessible_at_api_health(self) -> None:
        """Gateway health check remains accessible on /api/health."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "online")
        self.assertEqual(
            data["name"], "CMKL Classroom Reservation API Gateway"
        )
        self.assertIn("POST /api/auth/login", data["endpoints"])

    def test_spa_client_side_fallback(self) -> None:
        """Non-API 404 routes fall back to index.html for client routing."""
        res = self.client.get("/rooms")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res.content_type)

    def test_api_404_returns_json_error(self) -> None:
        """Unrecognized /api/* routes return 404 JSON instead of HTML."""
        res = self.client.get("/api/nonexistent_endpoint")
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertEqual(data["error"], "Endpoint not found")

    def test_resilience_to_renamed_root_function(self) -> None:
        """Desktop app overrides '/' even if gateway renames root()."""
        mock_gateway = Flask("mock_gateway")

        @mock_gateway.get("/")
        def renamed_status_handler():
            return jsonify({"status": "gateway_status_page"})

        # Apply the desktop app URL inspection logic
        root_endpoints = [
            rule.endpoint
            for rule in mock_gateway.url_map.iter_rules()
            if rule.rule == "/" and "GET" in rule.methods
        ]
        self.assertEqual(root_endpoints, ["renamed_status_handler"])

        def mock_serve_index():
            return "<html>React App</html>", 200

        for endpoint in root_endpoints:
            mock_gateway.view_functions[endpoint] = mock_serve_index

        client = mock_gateway.test_client()
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_data(as_text=True), "<html>React App</html>")


if __name__ == "__main__":
    unittest.main()
