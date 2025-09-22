# 🏰 Shahnameh Game Backend (Django) + Telegram Bot Integration

This project is the backend for the Shahnameh RPG game, built with **Django + Django REST Framework**, and integrated with **Telegram** using a custom bot. It supports JWT-based authentication, task progression, and bot interaction.

---

## 🚀 Features

- JWT-based authentication (`/register/`, `/login/`,`)
- 13-level progression system (WIP)
- REAL token economy and mining logic (WIP)
- Telegram bot integration:
  - User auto-registration via Telegram ID
  - Auto-login and token handling

---

## 🧰 Tech Stack

- **Backend**: Python, Django, Django REST Framework
- **Auth**: SimpleJWT (token-based auth)
- **Bot**: python-telegram-bot (async)
- **PostgreSQL**: recommended

---

## 📦 Installation & Setup

### 1. Clone the repo

```bash
cd shahname_game
2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
3. Install dependencies
pip install -r requirements.txt
pip install django djangorestframework djangorestframework-simplejwt python-telegram-bot requests
4. Apply migrations and run server
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
🤖 Setting Up the Telegram Bot
🔑 How to Create a Telegram Bot Token
Open Telegram and search for @BotFather

Type /start if you haven't already

Type /newbot and follow prompts:

Choose a name (e.g., Shahnameh RPG)

Choose a username (must end with bot, e.g., shahnameh_rpg_bot)

BotFather will give you a token like this:

Copy and paste this token into your telegram_bot.py:

BOT_TOKEN = "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ" (E.g)
📡 Running the Telegram Bot
python telegram_bot.py
Running the server 
python manage.py runserver
The bot will:

Auto-register or log in users using their Telegram ID




shahmeshgames.com