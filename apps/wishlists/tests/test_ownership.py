import pytest

from apps.wishlists.models import Wishlist


@pytest.mark.django_db
def test_cannot_read_others_wishlist(auth, make_user):
    other = make_user(phone="+12025561001")
    wl = Wishlist.objects.create(user=other, title="Secret")
    client = auth(make_user(phone="+12025561002"))

    assert client.get(f"/api/wishlists/{wl.id}").status_code == 404


@pytest.mark.django_db
def test_cannot_edit_others_wishlist(auth, make_user):
    other = make_user(phone="+12025561003")
    wl = Wishlist.objects.create(user=other, title="Secret")
    client = auth(make_user(phone="+12025561004"))

    resp = client.patch(f"/api/wishlists/{wl.id}", {"title": "Hacked"}, format="json")
    assert resp.status_code == 404
    wl.refresh_from_db()
    assert wl.title == "Secret"


@pytest.mark.django_db
def test_cannot_add_item_to_others_wishlist(auth, make_user):
    other = make_user(phone="+12025561005")
    wl = Wishlist.objects.create(user=other, title="Secret")
    client = auth(make_user(phone="+12025561006"))

    resp = client.post(f"/api/wishlists/{wl.id}/items", {"title": "X"}, format="json")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_superadmin_can_read_any_wishlist(auth, make_user, superadmin):
    other = make_user(phone="+12025561007")
    wl = Wishlist.objects.create(user=other, title="Visible to admin")
    client = auth(superadmin)

    assert client.get(f"/api/wishlists/{wl.id}").status_code == 200
