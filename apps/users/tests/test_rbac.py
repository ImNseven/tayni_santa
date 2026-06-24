import pytest

from apps.users.models import Role
from core.permissions import Permission, role_has_permission


def test_role_permission_matrix():
    assert role_has_permission("USER", Permission.JOIN_EVENT)
    assert not role_has_permission("USER", Permission.MANAGE_EVENTS)
    assert role_has_permission("ORGANIZER", Permission.MANAGE_EVENTS)
    assert role_has_permission("MODERATOR", Permission.MODERATE_CHAT)
    assert not role_has_permission("MODERATOR", Permission.MANAGE_EVENTS)
    assert not role_has_permission("ORGANIZER", Permission.MODERATE_CHAT)
    assert all(role_has_permission("SUPERADMIN", p) for p in Permission)


@pytest.mark.django_db
def test_user_cannot_list_users(auth, make_user):
    client = auth(make_user())
    assert client.get("/api/users").status_code == 403


@pytest.mark.django_db
def test_superadmin_can_list_users(auth, superadmin):
    client = auth(superadmin)
    assert client.get("/api/users").status_code == 200


@pytest.mark.django_db
def test_superadmin_promotes_user_to_organizer(auth, superadmin, make_user):
    target = make_user(phone="+12025550201")
    client = auth(superadmin)
    resp = client.patch(f"/api/users/{target.id}/role", {"role": Role.ORGANIZER})
    assert resp.status_code == 200
    target.refresh_from_db()
    assert target.role == Role.ORGANIZER


@pytest.mark.django_db
def test_user_cannot_change_roles(auth, make_user):
    target = make_user(phone="+12025550202")
    client = auth(make_user(phone="+12025550203"))
    resp = client.patch(f"/api/users/{target.id}/role", {"role": Role.ORGANIZER})
    assert resp.status_code == 403
