from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import WishlistItemViewSet, WishlistViewSet

router = SimpleRouter(trailing_slash=False)
router.register("wishlists", WishlistViewSet, basename="wishlist")

item_list = WishlistItemViewSet.as_view({"get": "list", "post": "create"})
item_detail = WishlistItemViewSet.as_view(
    {
        "get": "retrieve",
        "patch": "partial_update",
        "put": "update",
        "delete": "destroy",
    }
)

urlpatterns = [
    *router.urls,
    path("wishlists/<uuid:wishlist_pk>/items", item_list, name="wishlist-items"),
    path("wishlists/<uuid:wishlist_pk>/items/<uuid:pk>", item_detail, name="wishlist-item"),
]
