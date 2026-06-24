import pytest
from rest_framework.test import APIClient

from apps.users.models import Role, User


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def make_user(db):
    def _make(phone="+10000000001", password="secret123", role=Role.USER, is_active=True):
        return User.objects.create_user(
            phone=phone, password=password, role=role, is_active=is_active
        )

    return _make


@pytest.fixture
def superadmin(db):
    return User.objects.create_superuser(phone="+19999999999", password="admin12345")


@pytest.fixture
def auth():
    def _auth(user):
        from apps.users.services import issue_tokens

        client = APIClient()
        tokens = issue_tokens(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        return client

    return _auth
