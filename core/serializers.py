"""REST framework serializers for the Shahnameh core domain."""

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    Bank,
    BankAccount,
    Character,
    HafizReading,
    MiningCard,
    MiningCategory,
    Purchase,
    Settings,
    Skin,
    Task,
    UserCharater,
    UserTask,
)


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer used for registering a new Django auth user."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class SkinSerializer(serializers.ModelSerializer):
    """Expose a skin along with whether it is unlocked for the requesting user."""

    is_unlocked = serializers.SerializerMethodField()

    class Meta:
        model = Skin
        fields = ["id", "name", "price", "image_url", "is_unlocked"]

    def get_is_unlocked(self, skin):
        user = self.context.get("user")
        if not user or user.is_anonymous:
            return False
        return Purchase.objects.filter(user=user, skin=skin).exists()


class CharacterSerializer(serializers.ModelSerializer):
    skins = SkinSerializer(many=True, read_only=True)

    class Meta:
        model = Character
        fields = ["id", "name", "description", "image_character", "skins"]


class UserCharaterSerializer(serializers.ModelSerializer):
    """Serialize the player's character selection and progression."""

    character_display = serializers.CharField(
        source="get_character_display", read_only=True
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = UserCharater
        fields = [
            "id",
            "user",
            "character",
            "character_display",
            "coins",
            "level",
            "engry",
        ]
        read_only_fields = ["character_display"]


class TaskSerializer(serializers.ModelSerializer):
    completed = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ["id", "name", "description", "type", "reward", "url", "completed"]

    def get_completed(self, obj):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        return UserTask.objects.filter(
            user=request.user, task=obj, completed=True
        ).exists()


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = "__all__"


class MiningCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MiningCategory
        fields = ["id", "name", "description"]


class MiningCardSerializer(serializers.ModelSerializer):
    category = MiningCategorySerializer(read_only=True)

    class Meta:
        model = MiningCard
        fields = [
            "id",
            "category",
            "title",
            "value",
            "is_active",
            "image",
            "profit_per",
        ]


class HafizReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = HafizReading
        fields = ["id", "title", "arabic_text", "translation", "date_to_show"]


class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = "__all__"


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = [
            "id",
            "bank",
            "account_number",
            "account_holder",
            "iban",
            "comment",
        ]
        extra_kwargs = {
            "iban": {"required": False},
            "comment": {"required": False},
        }
