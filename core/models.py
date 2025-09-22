from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
import math



TASK_TYPES = [
        ('watch_ad', 'Watch Ad'),
        ('read_hafez', 'Read Hafez'),
        ('join_tg', 'Join Telegram'),
        ('follow_social', 'Follow Social Media')
    ]


class TelegramProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telegram_id = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return f"{self.user.username} ({self.telegram_id})"
    


# 1. Level System
class Level(models.Model):
    number = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Level {self.number}: {self.name}"


class UserProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    current_level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True)
    experience = models.PositiveIntegerField(default=0)


# 2. Token & Mining
class TokenWallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    real_tokens = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    last_mined = models.DateTimeField(null=True, blank=True)


class MiningCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class MiningCard(models.Model):
    category = models.ForeignKey(MiningCategory, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    value = models.FloatField()
    image = models.ImageField(upload_to='uploads/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    profit_per =  models.IntegerField(blank=True, null=True)    


class UserMiningCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(MiningCard, on_delete=models.CASCADE)
    obtained_at = models.DateTimeField(auto_now_add=True)


class HafizReading(models.Model):
    title = models.CharField(max_length=100)
    arabic_text = models.TextField()
    translation = models.TextField(blank=True)
    date_to_show = models.DateField(unique=True)

    def __str__(self):
        return self.title


# 3. Daily Tasks
class Task(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=TASK_TYPES)
    reward = models.PositiveIntegerField()
    url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    reading = models.ForeignKey(HafizReading, null=True, blank=True, on_delete=models.SET_NULL)



    def is_available_now(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return True

    def __str__(self):
        return self.name


class UserTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    @staticmethod
    def has_completed(user, task):
        return UserTask.objects.filter(user=user, task=task, completed=True).exists()

    def __str__(self):
        return f"{self.user.username} - {self.task.name} - {'Done' if self.completed else 'Pending'}"


# 4. Mini-Games
class MiniGame(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    reward = models.PositiveIntegerField()


class UserMiniGameScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(MiniGame, on_delete=models.CASCADE)
    score = models.PositiveIntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)


# 5. Airdrops
class Airdrop(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    points_required = models.PositiveIntegerField()
    is_active = models.BooleanField(default=False)


class UserAirdropEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    airdrop = models.ForeignKey(Airdrop, on_delete=models.CASCADE)
    claimed = models.BooleanField(default=False)
    claimed_at = models.DateTimeField(blank=True, null=True)


    
    
class Character(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image_character = models.ImageField(upload_to='uploads/', null=True, blank=True)

    def __str__(self):
        return self.name

class Skin(models.Model):
    character = models.ForeignKey(Character, related_name='skins', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    is_unlocked = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=6, decimal_places=2) 
    image_url = models.ImageField(upload_to='uploads/', null=True, blank=True)

    def __str__(self):
        return f'{self.name} for {self.character.name}'


class Purchase(models.Model):
    # user = models.ForeignKey(User, related_name='purchases', on_delete=models.CASCADE)
    skin = models.ForeignKey(Skin, related_name='purchases', on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.skin.is_unlocked:
            self.skin.is_unlocked = True
            self.skin.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username} purchased {self.skin.name}'
    





class DailyCipher(models.Model):
    # charter = models.ForeignKey(UserCharater)
    date = models.DateField(unique=True)
    cipher = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.date} - {self.cipher}"



class UserCharater(models.Model): #1
    CHARACTER_CHOICES = [
        ('fourse_aladin', 'Fourse Aladin'),
        ('king_q', 'King Q'),
        ('nashmieh', 'Nashmieh'),
        ('arshine', 'Arshine'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    character = models.CharField(max_length=20, choices=CHARACTER_CHOICES)
    coins = models.PositiveIntegerField(blank=True, null=True, default=0)
    level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(11)],
        default=1
    )
    engry = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        default=1000
    )
    last_energy_update = models.DateTimeField(default=timezone.now)
    last_mining_time = models.DateTimeField(null=True, blank=True)
    # claimed_ciphers = models.ManyToManyField('DailyCipher', blank=True)

    def update_energy(self):
        now = timezone.now()
        minutes_passed = int((now - self.last_energy_update).total_seconds() // 60)

        if minutes_passed > 0 and self.engry < 1000:
            new_energy = min(self.engry + minutes_passed, 1000)
            self.engry = new_energy
            self.last_energy_update = now
            self.save()

    def __str__(self):
        return f"{self.user.username} - {self.get_character_display()} (Level {self.level})"

    

class Settings(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    vibration = models.BooleanField(default=True)
    sound = models.BooleanField(default=True)
    music = models.BooleanField(default=True)
    effects = models.BooleanField(default=True)
    rotate = models.BooleanField(default=True)



class ChatMessage(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('bot', 'Bot'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.message[:30]}"


class UserEarnings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='earnings')
    profit_per_hour = models.IntegerField(default=100) 
    last_claimed = models.DateTimeField(default=timezone.now)
    total_collected = models.IntegerField(default=0)

    def calculate_pending_profit(self):
        now = timezone.now()
        hours_passed = (now - self.last_claimed).total_seconds() / 3600
        return math.floor(hours_passed * self.profit_per_hour)

    def claim_profit(self):
        profit = self.calculate_pending_profit()
        self.total_collected += profit
        self.last_claimed = timezone.now()
        self.save()
        return profit
    




class Bank(models.Model):
    name = models.CharField(max_length=100,unique=True)
    code = models.CharField(max_length=10,unique=True)  

    def __str__(self):
        return self.name


class BankAccount(models.Model):
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=16)
    account_holder = models.CharField(max_length=100)
    iban = models.CharField(max_length=30)
    comment = models.CharField(max_length=4000)

    def __str__(self):
        return f"{self.account_holder} - {self.bank.name}"
    

class WalletUser(models.Model):
    wallet_address = models.CharField(max_length=42, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.wallet_address