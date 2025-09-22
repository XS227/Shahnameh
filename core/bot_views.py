# core/bot_views.py

import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import ChatMessage

TELEGRAM_BOT_TOKEN = "7671321115:AAG9Y1HLn1o_S2Dz6dF8e-ro238dU8KFXdQ"
TELEGRAM_CHAT_ID = "6303109284"

class SendTelegramMessageView(APIView):
    def post(self, request):
        try:
            message = request.data.get("message")
            user_id = request.data.get("user_id")

            if not message:
                return Response({"error": "Message is required"}, status=400)
            if not user_id:
                return Response({"error": "User ID is required"}, status=400)

            user = User.objects.get(id=user_id)

            # Save user message
            ChatMessage.objects.create(user=user, sender="user", message=message)

            # Send to Telegram
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
            }

            response = requests.post(url, data=payload)

            if response.status_code == 200:
                bot_reply = "✅ Message received by bot!"
                # Save bot reply
                # ChatMessage.objects.create(user=user, sender="bot", message=bot_reply)
                return Response({"message": "Message sent successfully!"}, status=200)
            else:
                return Response({"error": "Failed to send message"}, status=500)

        except Exception as e:
            print("ERROR:", e)  # This prints the error to the terminal
            return Response({"error": str(e)}, status=500)


class MessageHistoryView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        # Get both user messages and bot replies (including "received by bot")
        messages = ChatMessage.objects.filter(user=user).order_by("timestamp")

        # Return both user and bot messages
        return Response([
            {
                "sender": msg.sender,
                "message": msg.message,
                "timestamp": msg.timestamp
            }
            for msg in messages if msg.sender in ["user", "bot"]
        ])
