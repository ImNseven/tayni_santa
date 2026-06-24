from rest_framework import serializers

from apps.wishlists.serializers import WishlistSerializer

from .models import Event, EventParticipant


class EventSerializer(serializers.ModelSerializer):
    organizer = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Event
        fields = (
            "id",
            "organizer",
            "title",
            "description",
            "status",
            "min_price",
            "max_price",
            "start_date",
            "end_date",
            "reg_deadline",
            "created_at",
        )
        read_only_fields = ("id", "organizer", "status", "created_at")

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        deadline = attrs.get("reg_deadline")
        if start and end and start >= end:
            raise serializers.ValidationError("start_date must be before end_date")
        if deadline and start and deadline > start:
            raise serializers.ValidationError("reg_deadline must be on or before start_date")
        if attrs.get("min_price", 0) > attrs.get("max_price", 0):
            raise serializers.ValidationError("min_price must not exceed max_price")
        return attrs


class ParticipantSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source="user.phone", read_only=True)

    class Meta:
        model = EventParticipant
        fields = ("id", "phone", "wishlist", "gift_sent")


class JoinSerializer(serializers.Serializer):
    wishlist_id = serializers.UUIDField(required=False, allow_null=True)


class AddParticipantSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    wishlist_id = serializers.UUIDField(required=False, allow_null=True)


class GiftSentSerializer(serializers.Serializer):
    gift_sent = serializers.BooleanField()


class MyAssignmentSerializer(serializers.Serializer):
    ward_phone = serializers.CharField()
    ward_wishlist = WishlistSerializer(allow_null=True)
