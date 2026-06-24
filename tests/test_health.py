import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_returns_ok():
    client = APIClient()
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["cache"] == "ok"
