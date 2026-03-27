"""테스트 코드 — 오탐하면 안 되는 하드코딩 값들"""

import unittest


TEST_DB_URL = "sqlite:///test.db"
MOCK_API_KEY = "test-key-not-real-000000"
DUMMY_PASSWORD = "test_password_123"


class TestUserAuth(unittest.TestCase):
    def setUp(self):
        self.test_user = {
            "username": "testuser",
            "password": DUMMY_PASSWORD,
            "email": "test@example.com",
        }

    def test_login_success(self):
        result = self.mock_login(self.test_user["username"], self.test_user["password"])
        self.assertTrue(result)

    def test_login_failure(self):
        result = self.mock_login("wrong", "wrong")
        self.assertFalse(result)

    def mock_login(self, username, password):
        return username == "testuser" and password == DUMMY_PASSWORD


if __name__ == "__main__":
    unittest.main()
