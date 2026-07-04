import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app


class AuthFlowTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = self.app.test_client()

    def test_landing_page_is_available_at_root(self):
        response = self.client.get("/", follow_redirects=False)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Plan Smarter", response.data)

    def test_dashboard_requires_login(self):
        response = self.client.get("/dashboard", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_profile_updates_are_saved_to_session_and_user_store(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = "user-1"
            sess["user_name"] = "Ada"
            sess["user_email"] = "ada@example.com"
            sess["profile"] = {
                "name": "Ada",
                "travel_style": "mid-range",
                "traveler_type": "solo",
                "home_country": "India",
                "currency": "INR",
                "interests": [],
                "favorite_destinations": [],
            }

        response = self.client.post(
            "/profile",
            data={
                "name": "Ada Lovelace",
                "travel_style": "luxury",
                "traveler_type": "solo",
                "home_country": "UK",
                "currency": "GBP",
                "interests": "Art, Books",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["profile"]["name"], "Ada Lovelace")
            self.assertEqual(sess["profile"]["currency"], "GBP")


if __name__ == "__main__":
    unittest.main()
