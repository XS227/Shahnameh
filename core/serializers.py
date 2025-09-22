from django.contrib.auth.models import User
from rest_framework import serializers
from .models import (Character, Skin, 
                Purchase,UserCharater, Task , UserTask, UserCharater, Settings, MiningCard, HafizReading,MiningCategory,
                Bank, BankAccount)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        return user



# serializers.py



class SkinSerializer(serializers.ModelSerializer):
    is_unlocked = serializers.SerializerMethodField()

    class Meta:
        model = Skin
        fields = ['id', 'name', 'price', 'image_url', 'is_unlocked']

    def get_is_unlocked(self, skin):
        user = self.context.get('user')
        if not user or user.is_anonymous:
            return False
        return Purchase.objects.filter(user=user, skin=skin).exists()

class SkinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skin
        fields = ['id', 'name', 'price', 'image_url', 'is_unlocked']



class CharacterSerializer(serializers.ModelSerializer):
    skins = SkinSerializer(many=True, read_only=True)

    class Meta:
        model = Character
        fields = ['id', 'name', 'description', 'image_character', 'skins']


class UserCharaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCharater
        fields = ['id', 'character', 'level', 'engry']


class TaskSerializer(serializers.ModelSerializer):
    completed = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'name', 'description', 'type', 'reward', 'url', 'completed']

    def get_completed(self, obj):
        user = self.context.get('request').user
        return UserTask.objects.filter(user=user, task=obj, completed=True).exists()
    

class UserCharaterSerializer(serializers.ModelSerializer):
    character_display = serializers.CharField(source='get_character_display', read_only=True)

    class Meta:
        model = UserCharater
        fields = ['id', 'character', 'character_display', 'coins', 'level', 'engry']


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = '__all__'



class MiningCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MiningCategory
        fields = ['id', 'name', 'description']

class MiningCardSerializer(serializers.ModelSerializer):
    category = MiningCategorySerializer(read_only=True)

    class Meta:
        model = MiningCard
        fields = ['id', 'category', 'title', 'value', 'is_active', 'image', 'profit_per']

class HafizReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = HafizReading
        fields = ['id', 'title', 'arabic_text', 'translation', 'date_to_show']



class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = '__all__'

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ['id', 'bank', 'account_number', 'account_holder', 'iban', 'comment']
        extra_kwargs = {
            'iban': {'required': False},
            'comment': {'required': False},
        }