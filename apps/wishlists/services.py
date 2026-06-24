from django.db import transaction

from .models import Wishlist


@transaction.atomic
def save_wishlist(serializer, user) -> Wishlist:
    wishlist = serializer.save(user=user)
    if wishlist.is_primary:
        Wishlist.objects.filter(user=user).exclude(pk=wishlist.pk).update(is_primary=False)
    return wishlist
