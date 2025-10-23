from django.urls import path
from .views import (RegisterView, profile_view,telegram_login_page, bot_login, claim_cipher,
                    CharacterListView, DailyTaskListView, CompleteTaskView, UserCharacterListCreateView,
                    UserCharacterCoinUpdateView,
                    SettingsAPIView, MiningActionView, MiningView, DailyHafezTaskView, complete_hafez_task,
                    AllTasksStatusView, BootsEnegry, UnlockSkinView,BankAccountDetailAPIView, BankAccountListCreateAPIView,
                    CreateBankAccountView, puzzle_board
                    )
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .bot_views import SendTelegramMessageView,MessageHistoryView


urlpatterns = [
    path('', views.api_overview, name='api-overview'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', profile_view, name='profile'),
    path('telegram_login_page/', telegram_login_page, name='telegram_login_page'),
    path('bot_login/', bot_login, name='bot_login'),
    path('characters/', CharacterListView.as_view(), name='character_list'),
    path('puzzle/', puzzle_board, name='puzzle'),
    path('move/<int:row>/<int:col>/', views.move_tile, name='move'),
    path('reset/', views.reset_board, name='reset'),
    path('tasks/', DailyTaskListView.as_view(), name='daily-tasks'),
    path('tasks/<int:task_id>/complete/', CompleteTaskView.as_view(), name='complete-task'),
    path('user_characters/', UserCharacterListCreateView.as_view(), name='character-list-create'),
    path('user_characters/<int:pk>/increase_coins/', UserCharacterCoinUpdateView.as_view(), name='character-increase-coins'),
    path('settings/', SettingsAPIView.as_view(), name='settings-api'),
    path("send-message/", SendTelegramMessageView.as_view(), name="send-message"),
    path("chat-history/<int:user_id>/", MessageHistoryView.as_view(), name="chat-history"),
    path('profit/', views.ClaimProfitView.as_view(), name='profit'),
    path('claim-cipher/<int:pk>/', claim_cipher, name='claim_cipher'),
    path('mining/', MiningView.as_view(), name='mining-list'),  # GET all mining cards
    path('mining_card/', MiningActionView.as_view(), name='mining'),
    path('daily-hafez-task/', DailyHafezTaskView.as_view(), name='daily-hafez-task'),
    path('complete-hafez-task/', complete_hafez_task, name='complete-hafez-task'),
    path('task-status/', AllTasksStatusView.as_view(), name='task-status'),
    path('boost-energy/', BootsEnegry.as_view(), name='boost-energy'),
    path('unlock_skin/', UnlockSkinView.as_view(), name='unlock-skin'),
    # path('api/banks/', BankListCreateAPIView.as_view(), name='bank-list-create'),
    # path('api/banks/<int:pk>/', BankDetailAPIView.as_view(), name='bank-detail'),
    
    path('bank-accounts/', BankAccountListCreateAPIView.as_view(), name='bankaccount-list-create'),
    path('bank-accounts/<int:pk>/', BankAccountDetailAPIView.as_view(), name='bankaccount-detail'),
    path('bank/<int:pk>/create-account/', CreateBankAccountView.as_view(), name='create-bank-account'),
]




    

