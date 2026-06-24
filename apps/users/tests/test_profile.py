import pytest

from core.otp import send_otp


@pytest.mark.django_db
def test_get_profile(auth, make_user):
    client = auth(make_user(phone="+12025550301"))
    resp = client.get("/api/profile")
    assert resp.status_code == 200
    assert resp.json()["phone"] == "+12025550301"


@pytest.mark.django_db
def test_update_avatar_and_description(auth, make_user):
    client = auth(make_user(phone="+12025550302"))
    resp = client.patch(
        "/api/profile", {"avatar": "http://x/a.png", "description": "hi"}, format="json"
    )
    assert resp.status_code == 200
    assert resp.json()["avatar"] == "http://x/a.png"
    assert resp.json()["description"] == "hi"


@pytest.mark.django_db
def test_role_is_not_writable_via_profile(auth, make_user):
    user = make_user(phone="+12025550303")
    client = auth(user)
    client.patch("/api/profile", {"role": "SUPERADMIN"}, format="json")
    user.refresh_from_db()
    assert user.role == "USER"


@pytest.mark.django_db
def test_change_phone_via_otp(auth, make_user):
    user = make_user(phone="+12025550304")
    client = auth(user)

    req = client.post("/api/profile/change-phone/request", {"new_phone": "+12025550999"})
    assert req.status_code == 200

    code = send_otp("+12025550999", purpose="change_phone")
    confirm = client.post(
        "/api/profile/change-phone/confirm",
        {"new_phone": "+12025550999", "code": code},
    )
    assert confirm.status_code == 200
    user.refresh_from_db()
    assert user.phone == "+12025550999"
