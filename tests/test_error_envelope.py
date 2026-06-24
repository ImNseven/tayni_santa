import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_unauthenticated_error_envelope():
    resp = APIClient().get("/api/profile")
    assert resp.status_code == 401
    body = resp.json()
    assert body["status_code"] == 401
    assert "error" in body


@pytest.mark.django_db
def test_validation_error_envelope(make_user):
    from apps.users.services import issue_tokens

    user = make_user(phone="+12025590001", role="ORGANIZER")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(user)['access']}")

    resp = client.post("/api/events", {"title": "x"}, format="json")
    assert resp.status_code == 400
    assert resp.json()["status_code"] == 400
    assert "error" in resp.json()
