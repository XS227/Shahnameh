# 🏰 Shahnameh Game Backend (Django) + Telegram Bot Integration

This project powers the Shahnameh RPG experience, combining **Django + Django REST Framework** services with a **Telegram bot** companion. It now also ships with an updated marketing landing page that surfaces the official DYOR resources for the REAL token and Shahnameh dApp.

---

## 🚀 Features

- JWT-based authentication endpoints (`/register/`, `/login/`, `/refresh/`)
- 13-level progression system (WIP)
- REAL token economy and mining logic (WIP)
- Telegram bot integration:
  - User auto-registration via Telegram ID
  - Auto-login and token handling
  - Embedded Telegram login widget (`templates/login.html`)
- Static marketing landing page (`templates/index.html`) with DYOR resource links and social hubs

---

## 🧰 Tech Stack

- **Backend**: Python, Django, Django REST Framework
- **Auth**: SimpleJWT (token-based auth)
- **Bot**: python-telegram-bot (async)
- **Database**: PostgreSQL recommended (SQLite provided for development)

---

## 🌐 Landing & Community Resources

- **Landing page**: open `templates/index.html` locally or serve via `python -m http.server`
- **DYOR Game Listing**: https://dyor.io/dapps/games/shahnameh
- **REAL Token Dashboard**: https://dyor.io/token/EQDhq_DjQUMJqfXLP8K8J6SlOvon08XQQK0T49xon2e0xU8p
- **Telegram Bot**: https://t.me/shahnameshbot
- **Telegram Announcements**: https://t.me/shahnameh_announcements
- **Telegram Guild Chat**: https://t.me/shahnamehcommunity

---

## 📦 Installation & Setup

1. **Clone the repo**
   ```bash
   git clone <repo>
   cd Shahnameh
   ```
2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Apply migrations & run the server**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver
   ```

---

## 🤖 Telegram Bot Setup

1. Create a bot via [@BotFather](https://t.me/BotFather) and grab the API token.
2. Update `telegram_bot.py` with your token or export it as an environment variable.
3. Launch the bot locally:
   ```bash
   python telegram_bot.py
   ```
4. The bot will automatically register returning players, log them in, and sync quest progress with the backend.

---

## 🧪 Helpful Commands

- Run the Django unit tests:
  ```bash
  python manage.py test
  ```
- Start the development server:
  ```bash
  python manage.py runserver
  ```
- Serve the static landing pages for review:
  ```bash
  python -m http.server 8000
  ```

---

Crafted with ❤️ by Setaei Labs — bringing legendary tales into the on-chain era.
