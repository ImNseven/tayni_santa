from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from core.otp import send_otp, verify_otp

User = get_user_model()


class AlreadyRegistered(Exception):
    pass


def issue_tokens(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def register_user(phone: str, password: str):
    user, created = User.objects.get_or_create(phone=phone, defaults={"is_active": False})
    if not created and user.is_active:
        raise AlreadyRegistered("Phone already registered")
    user.set_password(password)
    user.is_active = False
    user.save()
    send_otp(phone, purpose="auth")
    return user


def confirm_registration(phone: str, code: str):
    if not verify_otp(phone, code, purpose="auth"):
        return None
    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        return None
    if not user.is_active:
        user.is_active = True
        user.save(update_fields=["is_active"])
    return user


def authenticate_user(phone: str, password: str):
    return authenticate(username=phone, password=password)


def request_phone_change(user, new_phone: str) -> bool:
    if User.objects.filter(phone=new_phone).exclude(pk=user.pk).exists():
        return False
    send_otp(new_phone, purpose="change_phone")
    return True


def confirm_phone_change(user, new_phone: str, code: str) -> bool:
    if User.objects.filter(phone=new_phone).exclude(pk=user.pk).exists():
        return False
    if not verify_otp(new_phone, code, purpose="change_phone"):
        return False
    user.phone = new_phone
    user.save(update_fields=["phone"])
    return True
