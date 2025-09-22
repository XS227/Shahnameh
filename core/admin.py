from django.contrib import admin
from .models import (
    TelegramProfile,
    Level, UserProgress,
    TokenWallet, MiningCategory, MiningCard, UserMiningCard,
    Task, UserTask,
    MiniGame, UserMiniGameScore,
    Airdrop, UserAirdropEntry, 
    Character, Skin, Purchase, 
    UserCharater, Settings, 
    UserEarnings, DailyCipher,
    HafizReading, BankAccount, Bank
)

@admin.register(UserCharater)
class UserCharaterAdmin(admin.ModelAdmin):
    list_display = ('character', 'level', 'engry')
    list_filter = ('character', 'level')


admin.site.register(TelegramProfile)
admin.site.register(Level)
admin.site.register(UserProgress)
admin.site.register(TokenWallet)
admin.site.register(MiningCategory)
# admin.site.register(MiningCard)
admin.site.register(UserMiningCard)
admin.site.register(MiniGame)
admin.site.register(UserMiniGameScore)
admin.site.register(Airdrop)
admin.site.register(UserAirdropEntry)
admin.site.register(Settings)
admin.site.register(UserEarnings)
admin.site.register(DailyCipher)
admin.site.register(HafizReading)

@admin.register(MiningCard)
class MiningCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'value', 'is_active',)
    list_filter = ('category', 'is_active')
    search_fields = ('title',)
    list_editable = ('is_active',)
    ordering = ('id',)



@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'description')
    search_fields = ('name',)

@admin.register(Skin)
class SkinAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'character', 'price', 'is_unlocked')
    list_filter = ('character', 'is_unlocked')
    search_fields = ('name',)

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('skin', 'purchase_date')
    list_filter = ('purchase_date',)




@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'reward', 'is_active', 'start_time', 'end_time']
    list_filter = ['type', 'is_active']
    search_fields = ['name', 'description']

@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ['user', 'task', 'completed', 'completed_at']
    list_filter = ['completed']


@admin.register(Bank)
class UserBankAdmin(admin.ModelAdmin):
    list_display = ['name', 'code',]