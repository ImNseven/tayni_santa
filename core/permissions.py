from enum import StrEnum

from rest_framework.permissions import BasePermission


class Permission(StrEnum):
    CREATE_WISHLIST = "create_wishlist"
    JOIN_EVENT = "join_event"
    MANAGE_EVENTS = "manage_events"
    MODERATE_CHAT = "moderate_chat"
    VIEW_REPORTS = "view_reports"
    MANAGE_USERS = "manage_users"


ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "USER": {Permission.CREATE_WISHLIST, Permission.JOIN_EVENT},
    "ORGANIZER": {
        Permission.CREATE_WISHLIST,
        Permission.JOIN_EVENT,
        Permission.MANAGE_EVENTS,
    },
    "MODERATOR": {
        Permission.CREATE_WISHLIST,
        Permission.JOIN_EVENT,
        Permission.MODERATE_CHAT,
        Permission.VIEW_REPORTS,
    },
    "SUPERADMIN": set(Permission),
}


def role_has_permission(role: str, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


def HasPermission(required: Permission):
    class _HasPermission(BasePermission):
        def has_permission(self, request, view):
            user = getattr(request, "user", None)
            if not user or not user.is_authenticated:
                return False
            return role_has_permission(user.role, required)

    return _HasPermission


class IsOwnerOrSuperadmin(BasePermission):
    default_owner_field = "owner_id"

    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "role", None) == "SUPERADMIN":
            return True
        owner_field = getattr(view, "owner_field", self.default_owner_field)
        return getattr(obj, owner_field, None) == request.user.id
