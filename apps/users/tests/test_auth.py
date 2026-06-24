import pytest
from django.test import override_settings

from apps.users.models import User
from core.otp import send_otp


@pytest.mark.django_db
def test_register_creates_inactive_user(api):
    resp = api.post("/api/auth/register", {"phone": "+12025550111", "password": "secret123"})
    assert resp.status_code == 201
    user = User.objects.get(phone="+12025550111")
    assert user.is_active is False


@pytest.mark.django_db
def test_verify_activates_and_returns_tokens(api):
    api.post("/api/auth/register", {"phone": "+12025550112", "password": "secret123"})
    code = send_otp("+12025550112")
    resp = api.post("/api/auth/verify", {"phone": "+12025550112", "code": code})
    assert resp.status_code == 200
    assert "access" in resp.json() and "refresh" in resp.json()
    assert User.objects.get(phone="+12025550112").is_active is True


@pytest.mark.django_db
def test_verify_with_wrong_code_fails(api):
    api.post("/api/auth/register", {"phone": "+12025550113", "password": "secret123"})
    resp = api.post("/api/auth/verify", {"phone": "+12025550113", "code": "111111"})
    assert resp.status_code == 400
    assert User.objects.get(phone="+12025550113").is_active is False


@pytest.mark.django_db
def test_login_active_user(api, make_user):
    make_user(phone="+12025550114", password="secret123")
    resp = api.post("/api/auth/login", {"phone": "+12025550114", "password": "secret123"})
    assert resp.status_code == 200
    assert "access" in resp.json()


@pytest.mark.django_db
def test_login_inactive_user_rejected(api, make_user):
    make_user(phone="+12025550115", password="secret123", is_active=False)
    resp = api.post("/api/auth/login", {"phone": "+12025550115", "password": "secret123"})
    assert resp.status_code == 401


@pytest.mark.django_db
def test_protected_endpoint_requires_auth(api):
    assert api.get("/api/profile").status_code == 401


@pytest.mark.django_db
def test_refresh_then_logout_blacklists(api, make_user):
    make_user(phone="+12025550116", password="secret123")
    login = api.post("/api/auth/login", {"phone": "+12025550116", "password": "secret123"})
    refresh = login.json()["refresh"]

    r1 = api.post("/api/auth/token/refresh", {"refresh": refresh})
    assert r1.status_code == 200

    new_refresh = r1.json()["refresh"]
    out = api.post(
        "/api/auth/logout",
        {"refresh": new_refresh},
        HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}",
    )
    assert out.status_code == 205

    r2 = api.post("/api/auth/token/refresh", {"refresh": new_refresh})
    assert r2.status_code == 401


@override_settings(DEBUG=True, OTP_CHEAT_CODE="000000")
@pytest.mark.django_db
def test_cheat_code_completes_registration(api):
    api.post("/api/auth/register", {"phone": "+12025550117", "password": "secret123"})
    resp = api.post("/api/auth/verify", {"phone": "+12025550117", "code": "000000"})
    assert resp.status_code == 200
