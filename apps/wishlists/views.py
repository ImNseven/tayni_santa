from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from core.permissions import HasPermission, IsOwnerOrSuperadmin, Permission

from . import services
from .models import Wishlist, WishlistItem
from .serializers import WishlistItemSerializer, WishlistSerializer


class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrSuperadmin]
    owner_field = "user_id"

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), HasPermission(Permission.CREATE_WISHLIST)()]
        return super().get_permissions()

    def get_queryset(self):
        # при генерации схемы запроса нет, отдаём пустой queryset
        if getattr(self, "swagger_fake_view", False):
            return Wishlist.objects.none()
        qs = Wishlist.objects.all()
        if self.request.user.role != "SUPERADMIN":
            qs = qs.filter(user=self.request.user)
        return qs

    def perform_create(self, serializer):
        services.save_wishlist(serializer, self.request.user)

    def perform_update(self, serializer):
        services.save_wishlist(serializer, serializer.instance.user)


class WishlistItemViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistItemSerializer
    permission_classes = [IsAuthenticated]

    def _wishlist(self):
        qs = Wishlist.objects.all()
        if self.request.user.role != "SUPERADMIN":
            qs = qs.filter(user=self.request.user)
        return get_object_or_404(qs, pk=self.kwargs["wishlist_pk"])

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return WishlistItem.objects.none()
        return WishlistItem.objects.filter(wishlist=self._wishlist())

    def perform_create(self, serializer):
        serializer.save(wishlist=self._wishlist())
