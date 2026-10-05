"""
ACRIP Authentication & Registration Integration Test Suite
==========================================================
Verifies:
1. Existing user / admin login with JWT issuance
2. New user registration (POST /api/v1/auth/register)
3. New user login with newly created account
4. New user dashboard access with JWT
5. Duplicate email registration rejection
6. Password mismatch rejection
7. Weak/short password rejection
8. Invalid email rejection
9. Direct access to protected endpoints without token is rejected (401)
10. GET /auth/me with valid JWT token
11. Logout behavior
"""

import os
import uuid
import unittest
from fastapi.testclient import TestClient

from app.database.session import Base, SessionLocal, engine
from app.models.models import User, UserRole
from app.seed import seed_database
from app.main import app


class TestAuthRegistration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        try:
            seed_database()
        except Exception:
            pass

    def test_01_existing_admin_login(self):
        """Verify existing admin user can log in successfully."""
        res = self.client.post("/api/v1/auth/login", json={
            "email": "admin@acriplatform.com",
            "password": "Admin@123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["email"], "admin@acriplatform.com")
        self.assertEqual(data["user"]["role"], "super_admin")

    def test_02_new_user_registration(self):
        """Verify new user can register with full_name, email, password, confirm_password."""
        unique_email = f"newuser_{uuid.uuid4().hex[:8]}@example.com"
        res = self.client.post("/api/v1/auth/register", json={
            "full_name": "Test Builder",
            "email": unique_email,
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "department": "Engineering"
        })
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("id", data)
        self.assertEqual(data["email"], unique_email.lower())
        self.assertEqual(data["full_name"], "Test Builder")
        self.assertEqual(data["role"], "viewer")
        self.assertTrue(data["is_active"])
        # Ensure password hash is not exposed
        self.assertNotIn("password", data)
        self.assertNotIn("hashed_password", data)

    def test_03_new_user_login(self):
        """Verify new registered user can log in and obtain valid JWT token."""
        unique_email = f"logintest_{uuid.uuid4().hex[:8]}@example.com"
        password = "ValidPassword123!"

        # Register
        reg_res = self.client.post("/api/v1/auth/register", json={
            "full_name": "Login Tester",
            "email": unique_email,
            "password": password,
            "confirm_password": password
        })
        self.assertEqual(reg_res.status_code, 201)

        # Login
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": unique_email,
            "password": password
        })
        self.assertEqual(login_res.status_code, 200)
        login_data = login_res.json()
        self.assertIn("access_token", login_data)
        self.assertEqual(login_data["user"]["email"], unique_email.lower())
        self.assertEqual(login_data["user"]["role"], "viewer")

    def test_04_new_user_dashboard_access_and_me(self):
        """Verify new user token grants access to /auth/me and protected dashboard."""
        unique_email = f"dashuser_{uuid.uuid4().hex[:8]}@example.com"
        password = "DashPassword123!"

        # Register
        self.client.post("/api/v1/auth/register", json={
            "full_name": "Dashboard Tester",
            "email": unique_email,
            "password": password,
            "confirm_password": password
        })

        # Login
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": unique_email,
            "password": password
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Check /auth/me
        me_res = self.client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["email"], unique_email.lower())
        self.assertEqual(me_res.json()["role"], "viewer")

        # Check protected dashboard endpoint
        dash_res = self.client.get("/api/v1/dashboard/kpi", headers=headers)
        self.assertEqual(dash_res.status_code, 200)

    def test_05_duplicate_email_registration_rejected(self):
        """Verify duplicate email registration fails with clear user-friendly message."""
        unique_email = f"duplicate_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "full_name": "First User",
            "email": unique_email,
            "password": "Password123!",
            "confirm_password": "Password123!"
        }
        res1 = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res1.status_code, 201)

        # Attempt to register again with same email
        res2 = self.client.post("/api/v1/auth/register", json={
            "full_name": "Second User",
            "email": unique_email.upper(),  # test case-insensitivity
            "password": "Password123!",
            "confirm_password": "Password123!"
        })
        self.assertEqual(res2.status_code, 400)
        self.assertIn("already exists", res2.json()["detail"].lower())

    def test_06_duplicate_seeded_admin_email_rejected(self):
        """Verify registration with existing admin email fails gracefully."""
        res = self.client.post("/api/v1/auth/register", json={
            "full_name": "Imposter Admin",
            "email": "ADMIN@acriplatform.com",
            "password": "Password123!",
            "confirm_password": "Password123!"
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("already exists", res.json()["detail"].lower())

    def test_07_password_mismatch_rejected(self):
        """Verify registration with mismatched confirm_password fails."""
        res = self.client.post("/api/v1/auth/register", json={
            "full_name": "Mismatch Tester",
            "email": f"mismatch_{uuid.uuid4().hex[:8]}@example.com",
            "password": "Password123!",
            "confirm_password": "DifferentPassword!"
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("passwords do not match", res.json()["detail"].lower())

    def test_08_short_password_rejected(self):
        """Verify password shorter than 6 characters is rejected."""
        res = self.client.post("/api/v1/auth/register", json={
            "full_name": "Short Pass",
            "email": f"short_{uuid.uuid4().hex[:8]}@example.com",
            "password": "123",
            "confirm_password": "123"
        })
        # Pydantic or endpoint validation failure (400 or 422)
        self.assertIn(res.status_code, [400, 422])

    def test_09_invalid_email_format_rejected(self):
        """Verify invalid email string is rejected."""
        res = self.client.post("/api/v1/auth/register", json={
            "full_name": "Invalid Email",
            "email": "not-an-email",
            "password": "Password123!",
            "confirm_password": "Password123!"
        })
        self.assertEqual(res.status_code, 422)

    def test_10_wrong_password_login_rejected(self):
        """Verify login rejection with 401 when wrong password is supplied."""
        res = self.client.post("/api/v1/auth/login", json={
            "email": "admin@acriplatform.com",
            "password": "DefinitelyWrongPassword!"
        })
        self.assertEqual(res.status_code, 401)
        self.assertIn("incorrect", res.json()["detail"].lower())

    def test_11_direct_access_protected_endpoint_without_token_rejected(self):
        """Verify direct access to protected routes without Authorization header returns 401."""
        res = self.client.get("/api/v1/auth/me")
        self.assertEqual(res.status_code, 401)

        res_kpi = self.client.get("/api/v1/dashboard/kpi")
        self.assertEqual(res_kpi.status_code, 401)

    def test_12_logout_and_subsequent_protected_route(self):
        """Verify logout endpoint returns success."""
        # Login admin
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "admin@acriplatform.com",
            "password": "Admin@123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Logout
        logout_res = self.client.post("/api/v1/auth/logout", headers=headers)
        self.assertEqual(logout_res.status_code, 200)

        # Unauthenticated request fails
        unauth_res = self.client.get("/api/v1/dashboard/kpi")
        self.assertEqual(unauth_res.status_code, 401)
