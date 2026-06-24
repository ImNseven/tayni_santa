import pytest

from apps.wishlists.models import Wishlist


@pytest.mark.django_db
def test_create_wishlist_bound_to_user(auth, make_user):
    client = auth(make_user(phone="+12025560001"))
    resp = client.post("/api/wishlists", {"title": "Birthday"}, format="json")
    assert resp.status_code == 201
    wl = Wishlist.objects.get(id=resp.json()["id"])
    assert wl.user.phone == "+12025560001"


@pytest.mark.django_db
def test_list_returns_only_own(auth, make_user):
    owner = make_user(phone="+12025560002")
    other = make_user(phone="+12025560003")
    Wishlist.objects.create(user=other, title="Other's")
    client = auth(owner)
    Wishlist.objects.create(user=owner, title="Mine")

    resp = client.get("/api/wishlists")
    assert resp.status_code == 200
    titles = [w["title"] for w in resp.json()]
    assert titles == ["Mine"]


@pytest.mark.django_db
def test_marking_primary_unsets_previous(auth, make_user):
    user = make_user(phone="+12025560004")
    client = auth(user)
    a = Wishlist.objects.create(user=user, title="A", is_primary=True)
    resp = client.post("/api/wishlists", {"title": "B", "is_primary": True}, format="json")
    assert resp.status_code == 201

    a.refresh_from_db()
    assert a.is_primary is False
    assert Wishlist.objects.filter(user=user, is_primary=True).count() == 1


@pytest.mark.django_db
def test_item_crud(auth, make_user):
    user = make_user(phone="+12025560005")
    client = auth(user)
    wl = Wishlist.objects.create(user=user, title="Tech")

    bad = client.post(f"/api/wishlists/{wl.id}/items", {"url": "http://x"}, format="json")
    assert bad.status_code == 400

    ok = client.post(
        f"/api/wishlists/{wl.id}/items",
        {"title": "Keyboard", "price": "49.99"},
        format="json",
    )
    assert ok.status_code == 201
    item_id = ok.json()["id"]

    lst = client.get(f"/api/wishlists/{wl.id}/items")
    assert lst.status_code == 200 and len(lst.json()) == 1

    delete = client.delete(f"/api/wishlists/{wl.id}/items/{item_id}")
    assert delete.status_code == 204


@pytest.mark.django_db
def test_nested_items_appear_in_wishlist_detail(auth, make_user):
    user = make_user(phone="+12025560006")
    client = auth(user)
    wl = Wishlist.objects.create(user=user, title="Books")
    client.post(f"/api/wishlists/{wl.id}/items", {"title": "Dune"}, format="json")

    detail = client.get(f"/api/wishlists/{wl.id}")
    assert detail.status_code == 200
    assert [i["title"] for i in detail.json()["items"]] == ["Dune"]
