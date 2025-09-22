from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token  
import requests
from eth_account.messages import encode_defunct
from web3 import Web3

from .serializers import (RegisterSerializer, CharacterSerializer, 
                          UserCharaterSerializer, TaskSerializer,UserCharaterSerializer,
                          SettingsSerializer,MiningCardSerializer,HafizReadingSerializer,
                          BankSerializer, BankAccountSerializer)
from .utils import verify_telegram_auth  
from . import models
import random
import datetime




class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    user = request.user
    return Response({
        'username': user.username,
        'email': user.email,
        'id': user.id,
    })
    
    

    
@csrf_exempt
@api_view(['POST'])
def bot_login(request):
    data = request.data
    bot_token = "7585286219:AAGltBgrhw7MZy_9U3gDyjifCJ7D7LPewAk"

    if not verify_telegram_auth(data, bot_token):
        return Response({"error": "Invalid Telegram data"}, status=status.HTTP_400_BAD_REQUEST)

    telegram_id = data.get("id")
    username = data.get("username", f"user_{telegram_id}")
    first_name = data.get("first_name", "")

    user, created = User.objects.get_or_create(
        username=telegram_id,
        defaults={"first_name": first_name}
    )

    user.last_login = now()
    user.save()

    token, _ = Token.objects.get_or_create(user=user)

    return Response({"token": token.key, "user": username})



class UnlockSkinView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data 
            user_id = data.get('user_id')
            skin_id = data.get('skin_id')

            if not user_id or not skin_id:
                return Response({'error': 'user_id and skin_id are required'}, status=status.HTTP_400_BAD_REQUEST)

            user = get_object_or_404(User, id=user_id)
            skin = get_object_or_404(models.Skin, id=skin_id)

            if models.Purchase.objects.filter(user=user, skin=skin).exists():
                return Response({'message': 'Skin already unlocked'}, status=status.HTTP_200_OK)

            models.Purchase.objects.create(user=user, skin=skin)

            return Response({
                'message': f'Skin "{skin.name}" unlocked for user {user.username}',
                'skin_id': skin.id,
                'character': skin.character.name
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def telegram_login_page(request):
    return render(request, 'login.html')

def dashboard_page(request):
    return HttpResponse("Login Successfully")


class CharacterListView(APIView):
    # permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        characters = models.Character.objects.all()
        serializer = CharacterSerializer(characters, many=True, context={'user': request.user})
        return Response(serializer.data)
    


class UserCharaterCreateAPIView(APIView):
    def post(self, request):
        serializer = UserCharaterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

def generate_solvable_board():
    while True:
        board = list(range(1, 9)) + [None]
        random.shuffle(board)
        if is_solvable(board):
            return [board[i:i+3] for i in range(0, 9, 3)]

def is_solvable(tiles):
    tiles = [tile for tile in tiles if tile is not None]
    inversions = 0
    for i in range(len(tiles)):
        for j in range(i + 1, len(tiles)):
            if tiles[i] > tiles[j]:
                inversions += 1
    return inversions % 2 == 0

def is_solved(board):
    expected = list(range(1, 9)) + [None]
    flat = [cell for row in board for cell in row]
    return flat == expected

def index(request):
    board = request.session.get('board')
    if not board:
        board = generate_solvable_board()
        request.session['board'] = board

    win = is_solved(board)
    return render(request, 'board.html', {'board': board, 'win': win})

def move_tile(request, row, col):
    board = request.session.get('board')
    if not board:
        return redirect('index')

    row, col = int(row), int(col)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for dr, dc in directions:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 3 and 0 <= nc < 3 and board[nr][nc] is None:
            board[nr][nc], board[row][col] = board[row][col], None
            break

    request.session['board'] = board
    return redirect('index')


@csrf_exempt
def reset_board(request):
    if request.method == 'POST':
        request.session['board'] = generate_solvable_board()
    return redirect('index')


class DailyTaskListView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        
        tasks = models.Task.objects.filter(is_active=True).filter(
            Q(start_time__lte=now) | Q(start_time__isnull=True),
            Q(end_time__gte=now) | Q(end_time__isnull=True)
        )

        serializer = TaskSerializer(tasks, many=True, context={'request': request})
        return Response(serializer.data)


class CompleteTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        user = request.user
        try:
            task = models.Task.objects.get(id=task_id)
            now = timezone.now()

            if not task.is_available_now():
                return Response({'error': 'Task is not currently available.'}, status=status.HTTP_400_BAD_REQUEST)

            if models.UserTask.objects.filter(user=user, task=task, completed=True).exists():
                return Response({'error': 'Task already completed.'}, status=status.HTTP_400_BAD_REQUEST)

            models.UserTask.objects.create(user=user, task=task, completed=True, completed_at=now)

            wallet, _ = models.TokenWallet.objects.get_or_create(user=user)
            wallet.real_tokens += task.reward
            wallet.save()

            return Response({'success': True, 'reward': task.reward})

        except models.Task.DoesNotExist:
            return Response({'error': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)
        

class UserCharacterListCreateView(APIView):
    def get(self, request):
        characters = models.UserCharater.objects.all()
        serializer = UserCharaterSerializer(characters, many=True)
        return Response(serializer.data)
    
    def post(self, request, pk):
        try:
            character = models.UserCharater.objects.get(id=pk)
            amount = request.data.get("amount", 0)
            character.coins = (character.coins or 0) + int(amount)
            character.engry = (character.engry) - int(amount)
            character.save()
            return Response(UserCharaterSerializer(character).data, status=status.HTTP_200_OK)
        except models.UserCharater.DoesNotExist:
            return Response({"error": "Character not found"}, status=status.HTTP_404_NOT_FOUND)
        

class SettingsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        setting = models.Settings.objects.get(id=1)
        serializer = SettingsSerializer(setting)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = SettingsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        setting = get_object_or_404(models.Settings, id=1) 
        serializer = SettingsSerializer(setting, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class ClaimProfitView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_user_earnings(self, user):
        earnings, _ = models.UserEarnings.objects.get_or_create(
            user=user,
            defaults={"last_claimed": timezone.now()},
        )
        return earnings

    def get(self, request):
        earnings = self._get_user_earnings(request.user)
        pending = earnings.calculate_pending_profit()
        return Response({"pending_profit": pending})

    def post(self, request):
        earnings = self._get_user_earnings(request.user)
        claimed = earnings.claim_profit()
        return Response({"claimed": claimed, "total_collected": earnings.total_collected})
    

@api_view(["POST"])
def claim_cipher(request, pk):
    # breakpoint()
    player = models.UserCharater.objects.get(id=2)
    cipher_input = request.data.get("cipher", "").strip().upper()
    today = timezone.now().date()

    DAILY_CIPHERS = {
        datetime.date(2025, 5, 17): "",
    }

    correct_cipher = 'TAP'
    if correct_cipher and cipher_input == correct_cipher:
        player.coins += 1000
        player.save()
        return Response({"success": True, "message": "Cipher correct! 1000 coins added.", "new_coins": player.coins})
    return Response({"success": False, "message": "Incorrect cipher."})



class MiningActionView(APIView):
    MINING_ENERGY_COST = 20 
    COOLDOWN_SECONDS = 30    

    def post(self, request):
        player =  models.UserCharater.objects.get(id=2)
        card_id = request.data.get("card_id")

        if not card_id:
            return Response({"success": False, "message": "Mining card ID required."}, status=status.HTTP_400_BAD_REQUEST)

        card = get_object_or_404(models.MiningCard, pk=card_id, is_active=True)
        player.update_energy()

        now = timezone.now()
        last_mining = getattr(player, 'last_mining_time', None)
        if last_mining and (now - last_mining).total_seconds() < self.COOLDOWN_SECONDS:
            remaining = self.COOLDOWN_SECONDS - (now - last_mining).total_seconds()
            return Response({"success": False, "message": f"Mining cooldown active. Try again in {int(remaining)} seconds."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        if player.engry < self.MINING_ENERGY_COST:
            return Response({"success": False, "message": "Not enough energy to mine."}, status=status.HTTP_400_BAD_REQUEST)

        player.engry -= self.MINING_ENERGY_COST

        base_coins = int(card.value * player.level * random.uniform(0.8, 1.2))
        if random.random() < 0.20:
            coins_gained = base_coins * 2
            bonus = True
        else:
            coins_gained = base_coins
            bonus = False

        player.coins += coins_gained
        player.last_energy_update = now
        player.last_mining_time = now  
        player.save()

        leveled_up = False
        if player.coins >= player.level * 10000 and player.level < 13:  
            player.level += 1
            player.save()
            leveled_up = True

        return Response({
            "success": True,
            "message": f"Mining successful! You gained {coins_gained} coins{' (bonus!)' if bonus else ''}.",
            "new_coins": player.coins,
            "remaining_energy": player.engry,
            "level": player.level,
            "leveled_up": leveled_up,
            "cooldown_seconds": self.COOLDOWN_SECONDS
        })
    


class MiningView(APIView):
    def get(self, request, *args, **kwargs):
        mining_cards = models.MiningCard.objects.filter(is_active=True)
        serializer = MiningCardSerializer(mining_cards, many=True)
        return Response(serializer.data)






def get_crypto_data(request):
    api_key = "39211ffac43f544f1e333bc532cb4c45b886f7a3"  
    url = "https://your-crypto-api.com/v1/prices" 
    headers = {
        "Authorization": f"Bearer {api_key}", 
        "Accept": "application/json"
    }

    params = {
        "symbol": "BTC,ETH", 
        "convert": "USD"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return JsonResponse(response.json())
    else:
        return JsonResponse({"error": "Failed to fetch data", "status": response.status_code}, status=500)



class DailyHafezTaskView(APIView):
    def get(self, request):
        try:
            # breakpoint()
            # user = 1
            user = models.User.objects.get(id=1)
            today = timezone.now().date()

            try:
                reading = models.HafizReading.objects.get(date_to_show=today)
            except models.HafizReading.DoesNotExist:
                return Response({"message": "No Hafez reading for today."}, status=404)

            try:
                task = models.Task.objects.get(type='read_hafez', is_active=True)
            except models.Task.DoesNotExist:
                return Response({"message": "No active reading task."}, status=404)

            user_task, created = models.UserTask.objects.get_or_create(user=user, task=task)

            return Response({
                "task": {
                    "name": task.name,
                    "description": task.description,
                    "reward": task.reward,
                    "completed": user_task.completed
                },
                "reading": {
                    "title": reading.title,
                    "arabic_text": reading.arabic_text,
                    "translation": reading.translation
                }
            })
        except Exception as e:
            return JsonResponse({'failed': False, 'message': str(e)})    

@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def complete_hafez_task(request):
    user = models.User.objects.get(id=1)
    try:
        task = models.Task.objects.get(type='read_hafez', is_active=True)
        task_reward = int(task.reward)
    except models.Task.DoesNotExist:
        return Response({"message": "Task not found"}, status=404)

    user_task, created = models.UserTask.objects.get_or_create(user=user, task=task)

    if user_task.completed:
        return Response({"message": "Already completed"}, status=400)
    
    player =  models.UserCharater.objects.get(id=2)
    player.coins += task_reward
    player.save()

    user_task.completed = True
    user_task.completed_at = timezone.now()
    user_task.save()
    return Response({"message": "Task marked as complete", "reward": task.reward})




class JoinTelegramTaskView(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        user = models.User.objects.get(id=1)
        try:
            task = models.Task.objects.get(type='join_tg', is_active=True)
        except models.Task.DoesNotExist:
            return Response({"message": "No active Telegram task."}, status=404)

        user_task, created = models.UserTask.objects.get_or_create(user=user, task=task)

        if user_task.completed:
            return Response({"message": "Already joined Telegram."}, status=400)

        user_task.completed = True
        user_task.completed_at = timezone.now()
        user_task.save()

        return Response({"message": "Telegram task completed!"})
    

class AllTasksStatusView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        tasks = models.Task.objects.filter(is_active=True)
        user = models.User.objects.get(id=1)

        task_list = []
        for task in tasks:
            completed = models.UserTask.objects.filter(user=user, task=task, completed=True).exists()
            task_data = {
                "name": task.name,
                "description": task.description,
                "type": task.type,
                "reward": task.reward,
                "url": task.url,
                "completed": completed,
            }

            if task.type == "read_hafez" and task.reading:
                task_data["reading"] = {
                    "title": task.reading.title,
                    "arabic_text": task.reading.arabic_text,
                    "translation": task.reading.translation,
                }

            task_list.append(task_data)

        return Response({"tasks": task_list})


class BootsEnegry(APIView):
    def post(self, request):
        try:
            player = models.UserCharater.objects.get(id=2)

            boots_price = request.data.get('coins')
            if not boots_price:
                return Response({"success": False, "error": "Coins value not provided"}, status=400)

            boots_price = int(boots_price)

            if boots_price == 1000:
                if player.coins < 1000:
                    return Response({"success": False, "error": "Not enough coins"}, status=400)

                player.engry = 1000 
                player.coins -= boots_price
                player.save()

                return Response({'success': True, 'energy': player.engry})
            else:
                return Response({"success": False, "error": "Invalid boots_price value"}, status=400)

        except models.UserCharater.DoesNotExist:
            return Response({"success": False, "error": "Character not found"}, status=404)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=500)


class CompleteWatchAdTaskView(APIView):
    def post(self, request):
        user = models.User.objects.get(id=1)
        task = models.Task.objects.filter(type='watch_ad', is_active=True).first()
        if not task:
            return Response({'success': False, 'message': 'No ad task active'})

        if models.UserTask.has_completed(user, task):
            return Response({'success': False, 'message': 'Already completed'})

        models.UserTask.objects.create(user=user, task=task, completed=True, completed_at=timezone.now())

        user_character = models.UserCharater.objects.get(user=user)
        user_character.coins += task.reward
        user_character.save()

        return Response({'success': True, 'reward': task.reward, 'coins': user_character.coins})


class UnlockSkinView(APIView):


    def post(self, request):
        skin_id = request.data.get("skin_id")
        user = request.user

        try:
            skin = models.Skin.objects.get(id=skin_id)
            user_char = models.UserCharater.objects.get(id=2)
            if skin.is_unlocked:
                return Response({"success": False, "error": "Skin already unlocked."}, status=400)
            if user_char.coins < skin.price:
                return Response({"success": False, "error": "Not enough coins."}, status=400)
            user_char.coins -= int(skin.price)
            skin.is_unlocked = True
            user_char.save()
            skin.save()
            return Response({"success": True, "message": "Skin unlocked!"})
        except Exception as e:
            return Response({"success": False, "error": "Character not found."}, status=404)
        

# ---------------- BANK ACCOUNT ----------------

class BankAccountListCreateAPIView(APIView):
    def get(self, request):
        accounts = models.Bank.objects.all()
        serializer = BankSerializer(accounts, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BankSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BankAccountDetailAPIView(APIView):
    def get(self, request, pk):
        account = get_object_or_404(models.BankAccount, pk=pk)
        serializer = BankAccountSerializer(account)
        return Response(serializer.data)
    
    def put(self, request, pk):
        account = get_object_or_404(models.BankAccount, pk=pk)
        serializer = BankAccountSerializer(account, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        account = get_object_or_404(models.BankAccount, pk=pk)
        account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


class CreateBankAccountView(APIView):
    def post(self, request, pk):
        # breakpoint()
        bank = get_object_or_404(models.Bank, pk=pk)
        data = request.data.copy()
        data["bank"] = bank.pk 

        serializer = BankAccountSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class WalletLoginAPIView(APIView):
    def post(self, request):
        address = request.data.get("address")
        signature = request.data.get("signature")
        message = request.data.get("message")

        if not address or not signature or not message:
            return Response({"error": "Missing data"}, status=400)

        message_encoded = encode_defunct(text=message)
        try:
            recovered_address = Web3().eth.account.recover_message(message_encoded, signature=signature)
            if recovered_address.lower() == address.lower():
                wallet_user, created = models.WalletUser.objects.get_or_create(wallet_address=address.lower())
                return Response({
                    "status": "verified",
                    "wallet": wallet_user.wallet_address,
                    "created": created  
                })
            else:
                return Response({"error": "Signature mismatch"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)