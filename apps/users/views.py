from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from core.permissions import HasPermission, Permission

from . import services
from .models import User
from .serializers import (
    ChangePhoneConfirmSerializer,
    ChangePhoneRequestSerializer,
    LoginSerializer,
    LogoutSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    RoleUpdateSerializer,
    TokenPairSerializer,
    UserSerializer,
    VerifyOtpSerializer,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=RegisterSerializer, responses={201: None})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            services.register_user(**serializer.validated_data)
        except services.AlreadyRegistered:
            return Response(
                {"detail": "Phone already registered"},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            {"detail": "OTP sent. Confirm to activate the account."},
            status=status.HTTP_201_CREATED,
        )


class VerifyOtpView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=VerifyOtpSerializer, responses={200: TokenPairSerializer})
    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.confirm_registration(**serializer.validated_data)
        if user is None:
            return Response(
                {"detail": "Invalid or expired code"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(services.issue_tokens(user), status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer, responses={200: TokenPairSerializer})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.authenticate_user(**serializer.validated_data)
        if user is None:
            return Response(
                {"detail": "Invalid credentials or inactive account"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(services.issue_tokens(user), status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=LogoutSerializer, responses={205: None})
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserSerializer})
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(request=ProfileUpdateSerializer, responses={200: UserSerializer})
    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class ChangePhoneRequestView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangePhoneRequestSerializer, responses={200: None})
    def post(self, request):
        serializer = ChangePhoneRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not services.request_phone_change(request.user, serializer.validated_data["new_phone"]):
            return Response({"detail": "Phone already taken"}, status=status.HTTP_409_CONFLICT)
        return Response({"detail": "OTP sent to the new phone."})


class ChangePhoneConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangePhoneConfirmSerializer, responses={200: UserSerializer})
    def post(self, request):
        serializer = ChangePhoneConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ok = services.confirm_phone_change(request.user, **serializer.validated_data)
        if not ok:
            return Response(
                {"detail": "Invalid code or phone taken"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(UserSerializer(request.user).data)


class UserListView(APIView):
    permission_classes = [HasPermission(Permission.MANAGE_USERS)]

    @extend_schema(responses={200: UserSerializer(many=True)})
    def get(self, request):
        users = User.objects.all()
        return Response(UserSerializer(users, many=True).data)


class UserRoleUpdateView(APIView):
    permission_classes = [HasPermission(Permission.MANAGE_USERS)]

    @extend_schema(request=RoleUpdateSerializer, responses={200: UserSerializer})
    def patch(self, request, user_id):
        serializer = RoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, pk=user_id)
        user.role = serializer.validated_data["role"]
        user.save(update_fields=["role"])
        return Response(UserSerializer(user).data)
