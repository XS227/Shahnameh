from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.urls import reverse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token
import requests

try:  # pragma: no cover - optional web3 dependency
    from eth_account.messages import encode_defunct
except ModuleNotFoundError:  # pragma: no cover - degrade gracefully in local shells
    encode_defunct = None

try:  # pragma: no cover - optional web3 dependency
    from web3 import Web3
except ModuleNotFoundError:  # pragma: no cover - degrade gracefully in local shells
    Web3 = None

from .serializers import (RegisterSerializer, CharacterSerializer,
                          UserCharaterSerializer, TaskSerializer,UserCharaterSerializer,
                          SettingsSerializer,MiningCardSerializer,HafizReadingSerializer,
                          BankSerializer, BankAccountSerializer)
from .utils import verify_telegram_auth
from . import models
import random
import datetime


def _season_two_roadmap():
    """Centralised roadmap content so multiple pages stay in sync."""

    return [
        {
            "phase": "Phase 1 – Foundations (Weeks 1-4)",
            "phase_fa": "فاز ۱ – زیربناها (هفته‌های ۴-۱)",
            "summary": (
                "Stabilise the live game experience while preparing the lore-driven "
                "Season 2 onboarding journey."
            ),
            "summary_fa": (
                "تجربه زنده بازی را پایدار می‌کنیم و همزمان مسیر ورود داستان‌محور فصل دوم را آماده می‌سازیم."
            ),
            "items": [
                {
                    "title": "Lore-driven onboarding update",
                    "title_fa": "به‌روزرسانی ورود داستان‌محور",
                    "description": (
                        "Revamp the first-time user flow with narrated scenes that recap "
                        "Season 1 and foreshadow the coming faction conflict."
                    ),
                    "description_fa": (
                        "مسیر ورود بازیکنان جدید را با روایت صحنه‌هایی که فصل اول را مرور می‌کند و نبرد فرقه‌ها را نوید می‌دهد بازطراحی می‌کنیم."
                    ),
                },
                {
                    "title": "Economy audit & balancing",
                    "title_fa": "ممیزی و توازن اقتصاد",
                    "description": (
                        "Benchmark in-game resource sinks, token emission, and mining "
                        "rates to ensure sustainable growth before new features launch."
                    ),
                    "description_fa": (
                        "نرخ مصرف منابع، انتشار توکن و استخراج را پایش می‌کنیم تا پیش از عرضه قابلیت‌های جدید، رشد پایداری تضمین شود."
                    ),
                },
                {
                    "title": "Telegram bot quality-of-life",
                    "title_fa": "بهبود تجربه بات تلگرام",
                    "description": (
                        "Improve latency, add inline help, and surface player progression "
                        "stats from the legacy bot workflows."
                    ),
                    "description_fa": (
                        "تأخیر را کاهش می‌دهیم، راهنمای درون‌خط اضافه می‌کنیم و آمار پیشرفت بازیکنان را از فرایندهای قدیمی نمایان می‌سازیم."
                    ),
                },
            ],
        },
        {
            "phase": "Phase 2 – Faction Warfare (Weeks 5-8)",
            "phase_fa": "فاز ۲ – نبرد فرقه‌ها (هفته‌های ۸-۵)",
            "summary": (
                "Deliver the headline Season 2 feature that asks players to align with "
                "one of three factions."
            ),
            "summary_fa": (
                "ویژگی اصلی فصل دوم را عرضه می‌کنیم؛ جایی که بازیکنان باید به یکی از سه فرقه بپیوندند."
            ),
            "items": [
                {
                    "title": "Faction reputation system",
                    "title_fa": "سامانه اعتبار فرقه‌ای",
                    "description": (
                        "Introduce weekly objectives tied to faction reputation that "
                        "unlock cosmetics, buffs, and leaderboard recognition."
                    ),
                    "description_fa": (
                        "اهداف هفتگی مرتبط با اعتبار فرقه را اضافه می‌کنیم که ظواهر ویژه، تقویت‌ها و جایگاه در جدول برترین‌ها را آزاد می‌سازد."
                    ),
                },
                {
                    "title": "Cooperative faction raids",
                    "title_fa": "یورش‌های مشارکتی فرقه‌ای",
                    "description": (
                        "Launch asynchronous raid encounters where communities pool "
                        "resources to defeat enemies inspired by epic Shahnameh tales."
                    ),
                    "description_fa": (
                        "یورش‌های غیرهمزمانی را راه‌اندازی می‌کنیم که در آن انجمن‌ها منابع خود را برای شکست دشمنان الهام‌گرفته از شاهنامه ترکیب می‌کنند."
                    ),
                },
                {
                    "title": "Seasonal NFT drop",
                    "title_fa": "عرضه NFT فصلی",
                    "description": (
                        "Mint a limited run of lore artifacts that provide cosmetic "
                        "variants in-game and utility for the mining mini-game."
                    ),
                    "description_fa": (
                        "مجموعه‌ای محدود از آثار داستانی را ضرب می‌کنیم که ظاهرهای تازه در بازی و مزایای ویژه در مینی‌گیم استخراج می‌دهند."
                    ),
                },
            ],
        },
        {
            "phase": "Phase 3 – Creator & Community Tools (Weeks 9-12)",
            "phase_fa": "فاز ۳ – ابزار خالقان و جامعه (هفته‌های ۱۲-۹)",
            "summary": (
                "Empower community storytellers and guild leads with shareable content "
                "and moderation tools."
            ),
            "summary_fa": (
                "راویان جامعه و رهبران انجمن‌ها را با محتوای قابل اشتراک و ابزار مدیریت توانمند می‌کنیم."
            ),
            "items": [
                {
                    "title": "Quest builder beta",
                    "title_fa": "بتای سازنده مأموریت",
                    "description": (
                        "Allow verified lore keepers to craft side quests with custom "
                        "dialogue, rewards, and puzzle layouts."
                    ),
                    "description_fa": (
                        "به نگهبانان روایت تأییدشده اجازه می‌دهیم مأموریت‌های فرعی با دیالوگ، پاداش و معماهای اختصاصی بسازند."
                    ),
                },
                {
                    "title": "Community analytics dashboards",
                    "title_fa": "داشبوردهای تحلیلی جامعه",
                    "description": (
                        "Provide faction captains with participation metrics, retention "
                        "trends, and token sink/source visibility."
                    ),
                    "description_fa": (
                        "به رهبران فرقه‌ها شاخص‌های مشارکت، روند نگهداشت و دید شفافی از منابع و مصارف توکن می‌دهیم."
                    ),
                },
                {
                    "title": "Moderation escalation channel",
                    "title_fa": "کانال ارجاع نظارت",
                    "description": (
                        "Launch a Discord and Telegram escalation workflow for player "
                        "reports that syncs with support tooling."
                    ),
                    "description_fa": (
                        "کانال ارجاعی در دیسکورد و تلگرام ایجاد می‌کنیم تا گزارش‌های بازیکنان با ابزار پشتیبانی همگام شود."
                    ),
                },
            ],
        },
        {
            "phase": "Phase 4 – Finale & Handover (Weeks 13-16)",
            "phase_fa": "فاز ۴ – پایان و انتقال (هفته‌های ۱۶-۱۳)",
            "summary": (
                "Close the season with a high-stakes narrative event and prepare for "
                "long-term live-ops cadence."
            ),
            "summary_fa": (
                "فصل را با رویدادی داستانی و پرهیجان جمع‌بندی می‌کنیم و برای روند عملیات زنده بلندمدت آماده می‌شویم."
            ),
            "items": [
                {
                    "title": "World boss multi-stage event",
                    "title_fa": "رویداد چندمرحله‌ای رئیس جهانی",
                    "description": (
                        "Trigger a server-wide encounter that requires cross-faction "
                        "coordination and unlocks epilogue cinematics."
                    ),
                    "description_fa": (
                        "نبردی سراسری راه می‌اندازیم که هماهنگی بین فرقه‌ای می‌طلبد و میان‌پرده پایانی را آزاد می‌کند."
                    ),
                },
                {
                    "title": "Season review & rewards",
                    "title_fa": "مرور فصل و پاداش‌ها",
                    "description": (
                        "Distribute achievement badges, roll out leaderboard rewards, "
                        "and publish a community impact report."
                    ),
                    "description_fa": (
                        "نشان‌های دستاورد را توزیع می‌کنیم، پاداش جدول برترین‌ها را می‌پردازیم و گزارش اثر جامعه را منتشر می‌کنیم."
                    ),
                },
                {
                    "title": "Season 3 pre-production",
                    "title_fa": "پیش‌تولید فصل سوم",
                    "description": (
                        "Document learnings, lock feature priorities, and begin art/"
                        "narrative exploration for the next arc."
                    ),
                    "description_fa": (
                        "آموخته‌ها را مستند می‌کنیم، اولویت قابلیت‌ها را تثبیت می‌کنیم و کاوش هنری و داستانی فصل بعد را آغاز می‌نماییم."
                    ),
                },
            ],
        },
    ]


def _format_usd(value):
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    absolute = abs(numeric)
    suffix = ""

    if absolute >= 1_000_000_000:
        numeric /= 1_000_000_000
        suffix = "B"
    elif absolute >= 1_000_000:
        numeric /= 1_000_000
        suffix = "M"
    elif absolute >= 1_000:
        numeric /= 1_000
        suffix = "K"

    if suffix:
        return f"${numeric:.2f}{suffix}"

    if absolute >= 1:
        return f"${numeric:,.2f}"

    return f"${numeric:,.4f}"


def _format_percent(value):
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    if abs(numeric) <= 1:
        numeric *= 100

    return f"{numeric:+.2f}%"


def _format_timestamp(value):
    if value in (None, ""):
        return None

    dt = None

    if isinstance(value, (int, float)):
        dt = datetime.datetime.fromtimestamp(float(value), tz=timezone.utc)
    elif isinstance(value, str):
        iso_value = value.replace("Z", "+00:00")
        try:
            dt = datetime.datetime.fromisoformat(iso_value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            dt = None

    if not dt:
        return value

    local_dt = dt.astimezone(timezone.get_current_timezone())
    return local_dt.strftime("%d %b %Y · %H:%M %Z")


def fetch_realshahnameh_token():
    endpoint = "https://dyor.io/api/jettonsservice/getjettondetails"
    params = {
        "network": "mainnet",
        "account": "EQDhq_DjQUMJqfXLP8K8J6SlOvon08XQQK0T49xon2e0xU8p",
    }

    try:
        response = requests.get(endpoint, params=params, timeout=12)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:  # pragma: no cover - network dependent
        return {"error": str(exc)}
    except ValueError:  # pragma: no cover - unexpected payload
        return {"error": "Invalid response payload from DYOR."}

    result = payload.get("result") or payload.get("data") or payload
    jetton = result.get("jetton") if isinstance(result, dict) else {}
    metrics = result.get("metrics") if isinstance(result, dict) else {}

    if isinstance(jetton, dict):
        metrics = {**jetton.get("metrics", {}), **metrics}
    else:
        jetton = {}

    price_usd = (
        metrics.get("price_usd")
        or metrics.get("priceUSD")
        or result.get("price_usd")
        or result.get("priceUSD")
        or jetton.get("price_usd")
        or jetton.get("priceUSD")
    )
    price_ton = (
        metrics.get("price_ton")
        or metrics.get("priceTON")
        or result.get("price_ton")
    )
    change_24h = (
        metrics.get("price_change24h")
        or metrics.get("priceChange24h")
        or metrics.get("price_change")
        or metrics.get("priceChange")
        or result.get("price_change24h")
    )
    market_cap = metrics.get("market_cap") or metrics.get("marketCap") or result.get("market_cap")
    volume_24h = (
        metrics.get("volume_24h")
        or metrics.get("volume24h")
        or metrics.get("volume")
        or result.get("volume_24h")
    )
    liquidity = (
        metrics.get("liquidity_locked")
        or metrics.get("liquidity")
        or metrics.get("tvl")
        or result.get("tvl")
    )
    last_updated = (
        metrics.get("updated_at")
        or metrics.get("updatedAt")
        or result.get("updated_at")
        or result.get("updatedAt")
        or payload.get("timestamp")
    )

    formatted = {
        "name": jetton.get("name") or result.get("name") or "REAL Shahnameh",
        "symbol": jetton.get("symbol") or result.get("symbol") or "REAL",
        "price_usd": _format_usd(price_usd),
        "price_ton": None,
        "price_change_24h": _format_percent(change_24h),
        "market_cap": _format_usd(market_cap),
        "volume_24h": _format_usd(volume_24h),
        "liquidity_locked": _format_usd(liquidity),
        "last_updated": _format_timestamp(last_updated),
        "raw": payload,
    }

    if price_ton is not None:
        try:
            formatted["price_ton"] = f"{float(price_ton):.6f} TON"
        except (TypeError, ValueError):
            formatted["price_ton"] = str(price_ton)

    return formatted




def legacy_repo_overview(request):
    context = {
        "page_title": "Legacy Repository Overview",
        "page_title_fa": "مرور مخزن قدیمی",
        "intro": (
            "A curated summary of the original Shahnameh-TON codebase so new "
            "contributors can understand the foundation this Django project builds upon."
        ),
        "intro_fa": (
            "خلاصه‌ای گزیده از مخزن اولیه شاهنامه بر بستر TON تا همکاران تازه‌وارد با پایه‌های این پروژه جنگو آشنا شوند."
        ),
        "page_intro": "Key components from the Shahnameh-TON legacy stack in one glance.",
        "page_intro_fa": "نگاهی سریع به اجزای کلیدی پشته قدیمی شاهنامه بر بستر TON.",
        "feature_groups": [
            {
                "title": "Core Game Services",
                "title_fa": "خدمات اصلی بازی",
                "items": [
                    {
                        "text": "Django REST Framework APIs for registration, authentication, and player profiles.",
                        "text_fa": "رابط‌های REST جنگو برای ثبت‌نام، احراز هویت و پروفایل بازیکنان."
                    },
                    {
                        "text": "Turn-based puzzle mini-game endpoint used for daily engagement quests.",
                        "text_fa": "نقطه پایانی مینی‌گیم معمای نوبتی که برای مأموریت‌های روزانه به کار می‌رود."
                    },
                    {
                        "text": "Task and reward management with activation windows and completion tracking.",
                        "text_fa": "مدیریت مأموریت و پاداش با بازه‌های فعال‌سازی و رهگیری تکمیل."
                    }
                ]
            },
            {
                "title": "Blockchain & Economy Integration",
                "title_fa": "یکپارچگی بلاک‌چین و اقتصاد",
                "items": [
                    {
                        "text": "Token mining logic that pairs on-chain rewards with in-app stamina systems.",
                        "text_fa": "منطق استخراج توکن که پاداش‌های روی زنجیره را با سیستم استقامت درون برنامه پیوند می‌دهد."
                    },
                    {
                        "text": "Banking abstractions for handling user wallets, deposits, and withdrawals.",
                        "text_fa": "لایه‌های بانکی برای مدیریت کیف‌پول، واریز و برداشت کاربران."
                    },
                    {
                        "text": "Utility helpers for verifying Telegram sign-in payloads prior to minting rewards.",
                        "text_fa": "ابزارهای کمکی برای تأیید داده‌های ورود تلگرام پیش از صدور پاداش."
                    }
                ]
            },
            {
                "title": "Telegram Bot Companion",
                "title_fa": "همراه بات تلگرام",
                "items": [
                    {
                        "text": "Automated user provisioning using Telegram IDs as credential seeds.",
                        "text_fa": "راه‌اندازی خودکار کاربران با استفاده از شناسه تلگرام به عنوان بذر اعتبار."
                    },
                    {
                        "text": "Two-way messaging endpoints so players can receive notifications and issue commands.",
                        "text_fa": "نقاط پایانی پیام‌رسانی دوسویه برای دریافت اعلان‌ها و اجرای دستورات توسط بازیکنان."
                    },
                    {
                        "text": "Celery task scheduling for broadcasting quests and mining updates in real time.",
                        "text_fa": "زمان‌بندی وظایف سلری برای پخش مأموریت‌ها و به‌روزرسانی‌های استخراج به‌صورت آنی."
                    }
                ]
            }
        ],
        "technical_highlights": [
            {
                "text": "Python 3.11+, Django, Django REST Framework, Celery, Redis, and PostgreSQL (recommended).",
                "text_fa": "پایتون ۳.۱۱ به بالا، جنگو، DRF، سلری، ردیس و پایگاه‌داده پیشنهادی PostgreSQL."
            },
            {
                "text": "JWT-based security using SimpleJWT plus Telegram auth verification utilities.",
                "text_fa": "امنیت مبتنی بر JWT با استفاده از SimpleJWT و ابزارهای اعتبارسنجی ورود تلگرام."
            },
            {
                "text": "Docker-ready settings and environment variable strategy for multistage deployments.",
                "text_fa": "پیکربندی آماده برای Docker و راهبرد متغیرهای محیطی جهت استقرار چندمرحله‌ای."
            }
        ],
        "migration_notes": [
            {
                "text": "Preserve API compatibility for mobile clients by proxying legacy endpoints where possible.",
                "text_fa": "سازگاری API با کلاینت‌های موبایل را با پروکسی کردن نقاط پایانی قدیمی حفظ کنید."
            },
            {
                "text": "Move long-running tasks into Celery beat schedules to avoid blocking HTTP responses.",
                "text_fa": "وظایف طولانی را به زمان‌بندی سلری منتقل کنید تا پاسخ‌های HTTP مسدود نشوند."
            },
            {
                "text": "Centralise shared schemas in this monorepo to reduce duplication across services.",
                "text_fa": "شِماهای مشترک را در همین مونو-ریپو متمرکز کنید تا از تکرار بین سرویس‌ها کاسته شود."
            }
        ],
        "repository_timeline": [
            {
                "text": "2023 – Telegram bot prototype shipping basic quest tracking and wallet binding.",
                "text_fa": "۲۰۲۳ – نمونه اولیه بات تلگرام با رهگیری مأموریت و اتصال کیف‌پول عرضه شد."
            },
            {
                "text": "Early 2024 – Legacy TON stack open-sourced with REST APIs and Celery workers.",
                "text_fa": "اوایل ۲۰۲۴ – پشته قدیمی TON با APIهای REST و کارگرهای سلری متن‌باز شد."
            },
            {
                "text": "Late 2024 – Django consolidation with modern auth, staging configs, and docs refresh.",
                "text_fa": "اواخر ۲۰۲۴ – یکپارچه‌سازی جنگو با احراز هویت نوین، پیکربندی استیجینگ و به‌روزرسانی مستندات."
            }
        ],
        "handoff_resources": [
            {
                "text": "Archived Notion runbooks covering incident response and release rituals.",
                "text_fa": "رون‌بوک‌های آرشیو شده در نُوشن درباره واکنش به حوادث و آیین‌های انتشار."
            },
            {
                "text": "Figma library with UI kits for bot flows, dashboards, and lore cards.",
                "text_fa": "کتابخانه فیگما با کیت‌های رابط کاربری برای جریان‌های بات، داشبوردها و کارت‌های داستانی."
            },
            {
                "text": "Postmortem archive highlighting technical learnings from Season 1 incidents.",
                "text_fa": "آرشیو پسامورتوم که آموخته‌های فنی رخدادهای فصل اول را برجسته می‌کند."
            }
        ],
        "current_year": timezone.now().year
    }

    return render(request, "legacy_overview.html", context)



def whitepaper_overview(request):
    context = {
        "page_title": "Shahnameh Whitepaper Digest",
        "page_title_fa": "چکیده وایت‌پیپر شاهنامه",
        "summary": (
            "The Shahnameh whitepaper frames the experience as a lore-rich on-chain RPG "
            "where community-driven storytelling powers the token economy. This digest "
            "highlights the pillars most relevant to the current Django stack."
        ),
        "summary_fa": (
            "وایت‌پیپر شاهنامه تجربه‌ای نقش‌آفرینی و زنجیره‌ای با تکیه بر روایت اصیل معرفی می‌کند که اقتصاد توکن توسط جامعه هدایت می‌شود. این چکیده مهم‌ترین ستون‌های مرتبط با پشته فعلی جنگو را برجسته می‌کند."
        ),
        "page_intro": "Explore the pillars behind the Shahnameh token economy and lore-first design.",
        "page_intro_fa": "با ستون‌های پشتیبان اقتصاد توکن شاهنامه و طراحی روایت‌محور آشنا شوید.",
        "pillars": [
            {
                "title": "Lore-first Design",
                "title_fa": "طراحی با اولویت روایت",
                "details": (
                    "Every mechanic connects back to Ferdowsi's epic tales. Seasonal arcs "
                    "translate major stories into collaborative events, ensuring cultural "
                    "authenticity while introducing newcomers to the lore."
                ),
                "details_fa": (
                    "تمام مکانیک‌ها ریشه در داستان‌های حماسی فردوسی دارد. روایت‌های فصلی قصه‌های بزرگ را به رویدادهای مشارکتی تبدیل می‌کنند تا هم اصالت فرهنگی حفظ شود و هم تازه‌واردان با جهان داستان آشنا شوند."
                )
            },
            {
                "title": "Player-owned Economy",
                "title_fa": "اقتصاد در مالکیت بازیکنان",
                "details": (
                    "Dual-token design distinguishes governance influence from gameplay "
                    "rewards. On-chain actions feed into off-chain progression loops, "
                    "creating meaningful stakes for daily play."
                ),
                "details_fa": (
                    "طراحی دوگانه توکن، نفوذ حاکمیتی را از پاداش‌های گیم‌پلی جدا می‌کند. فعالیت‌های روی زنجیره وارد چرخه پیشرفت خارج از زنجیره می‌شود و برای بازی روزانه اهمیت واقعی ایجاد می‌کند."
                )
            },
            {
                "title": "Community Governance",
                "title_fa": "حاکمیت جامعه‌محور",
                "details": (
                    "Story councils curate future quests, approve creator-made adventures, "
                    "and manage treasury proposals that fund community projects."
                ),
                "details_fa": (
                    "شورای داستان مأموریت‌های آینده را برمی‌گزیند، ماجراجویی‌های ساخته‌شده توسط خالقان را تأیید می‌کند و پیشنهادهای خزانه را برای پروژه‌های جامعه مدیریت می‌نماید."
                )
            }
        ],
        "economy_breakdown": {
            "utility_token": {
                "text": "Simorgh Shards (SHD) fuel crafting, quest unlocks, and faction boosts.",
                "text_fa": "شکافه‌های سیمرغ (SHD) برای ساخت، آزادسازی مأموریت و تقویت فرقه‌ها مصرف می‌شود."
            },
            "governance_token": {
                "text": "Crown of Heroes (CRH) grants voting power over story arcs and economy levers.",
                "text_fa": "تاج قهرمانان (CRH) حق رأی بر روایت فصل‌ها و اهرم‌های اقتصادی را می‌دهد."
            },
            "sink_examples": [
                {
                    "text": "Upgrading caravan caravans for cross-season persistence.",
                    "text_fa": "ارتقای کاروان‌ها برای پایداری میان فصل‌ها."
                },
                {
                    "text": "Accessing elite raids and cooperative faction contracts.",
                    "text_fa": "دسترسی به حملات نخبگان و قراردادهای مشارکتی فرقه‌ای."
                },
                {
                    "text": "Commissioning lore-artifacts from community creators.",
                    "text_fa": "سفارش آثار داستانی از خالقان جامعه."
                }
            ],
            "source_examples": [
                {
                    "text": "Faction events tied to canonical battles.",
                    "text_fa": "رویدادهای فرقه‌ای الهام‌گرفته از نبردهای اصیل."
                },
                {
                    "text": "Creator quests that reach community quality thresholds.",
                    "text_fa": "مأموریت‌های خالقان که به استاندارد کیفی جامعه می‌رسند."
                },
                {
                    "text": "Cross-platform referrals that bring new players into the world.",
                    "text_fa": "ارجاع‌های میان‌پلتفرمی که بازیکنان تازه را وارد جهان می‌کند."
                }
            ]
        },
        "player_journey": [
            {
                "text": "Discover Shahnameh through social channels or the Telegram bot and claim a hero soul.",
                "text_fa": "از طریق شبکه‌های اجتماعی یا بات تلگرام با شاهنامه آشنا شوید و روح قهرمان خود را دریافت کنید."
            },
            {
                "text": "Complete narrative-driven tutorials to unlock mining rigs and cooperative quests.",
                "text_fa": "آموزش‌های داستانی را کامل کنید تا دستگاه‌های استخراج و مأموریت‌های تعاملی باز شود."
            },
            {
                "text": "Form or join a guild to compete in faction warfare and shape upcoming storylines.",
                "text_fa": "یک انجمن بسازید یا به آن بپیوندید تا در نبرد فرقه‌ای رقابت کنید و روایت‌های آینده را شکل دهید."
            }
        ],
        "tokenomics_highlights": [
            {
                "label": "Staking rewards cadence",
                "label_fa": "ریتم پاداش استیکینگ",
                "value": "Epoch-based distribution every 14 days with lore-driven seasonal boosts.",
                "value_fa": "توزیع مبتنی بر اپوک هر ۱۴ روز با تقویت‌های فصلی و روایت‌محور."
            },
            {
                "label": "Treasury allocation",
                "label_fa": "سهم خزانه",
                "value": "15% reserved for community grants, art commissions, and guild tooling.",
                "value_fa": "۱۵٪ برای کمک‌های جامعه، سفارش‌های هنری و ابزار انجمن ذخیره می‌شود."
            },
            {
                "label": "Inflation controls",
                "label_fa": "کنترل تورم",
                "value": "Dynamic sink multipliers adjust emission whenever shard velocity spikes.",
                "value_fa": "ضریب‌های مصرف پویا هنگام جهش سرعت گردش شارد، انتشار را تنظیم می‌کند."
            }
        ],
        "lore_sources": [
            {
                "text": "Digitised manuscripts curated by the National Library of Iran.",
                "text_fa": "نسخه‌های دیجیتال‌شده کتابخانه ملی ایران."
            },
            {
                "text": "Academic commentary from Tehran University’s Shahnameh studies faculty.",
                "text_fa": "تفاسیر دانشگاهی دانشکده مطالعات شاهنامه دانشگاه تهران."
            },
            {
                "text": "Community oral histories collected during Season 1 guild summits.",
                "text_fa": "تاریخ‌های شفاهی جامعه که در گردهمایی‌های انجمن فصل اول گردآوری شد."
            }
        ],
        "season_two_roadmap": _season_two_roadmap(),
        "current_year": timezone.now().year
    }

    return render(request, "whitepaper.html", context)



def season_two_roadmap_page(request):
    context = {
        "page_title": "Season 2 Roadmap",
        "page_title_fa": "نقشه راه فصل دوم",
        "page_intro": (
            "Season 2 doubles down on community-driven storytelling and competitive faction play. "
            "The roadmap below mirrors the live operations plan shared internally so everyone can rally around the same milestones."
        ),
        "page_intro_fa": (
            "فصل دوم تمرکز بیشتری بر روایت جامعه‌محور و رقابت فرقه‌ها دارد. نقشه راه زیر همان برنامه عملیات زنده داخلی است تا همه حول یک جدول زمانی مشترک هم‌راستا شوند."
        ),
        "season_two_roadmap": _season_two_roadmap(),
        "operational_focus": [
            {
                "text": "Weekly health reviews measuring retention, revenue, and community satisfaction.",
                "text_fa": "بازبینی سلامت هفتگی برای سنجش نگهداشت، درآمد و رضایت جامعه."
            },
            {
                "text": "Cross-team war room for launch weeks to keep live ops, support, and engineering aligned.",
                "text_fa": "اتاق بحران میان تیمی برای هفته‌های لانچ تا عملیات زنده، پشتیبانی و مهندسی هماهنگ بمانند."
            },
            {
                "text": "Transparent changelog cadence so players understand balancing decisions in real time.",
                "text_fa": "ریتم شفاف یادداشت تغییرات تا بازیکنان تصمیم‌های ترازسازی را به‌صورت لحظه‌ای درک کنند."
            }
        ],
        "community_programs": [
            {
                "text": "Lorekeeper mentorship sessions that help storytellers refine quests before publication.",
                "text_fa": "جلسات مربی‌گری نگهبانان روایت برای صیقل مأموریت‌ها پیش از انتشار."
            },
            {
                "text": "Faction ambassador spotlights celebrating player leadership and contributions.",
                "text_fa": "معرفی سفیران فرقه برای تقدیر از رهبری و تلاش بازیکنان."
            },
            {
                "text": "Seasonal art contests with on-chain rewards and in-game showcase placements.",
                "text_fa": "مسابقات هنری فصلی با پاداش روی زنجیره و نمایش درون بازی."
            }
        ],
        "alignment_cadence": [
            {
                "text": "Weekly cross-discipline sync reviewing build stability, live ops metrics, and narrative beats.",
                "text_fa": "هم‌آهنگی هفتگی میان‌رشته‌ای برای بررسی پایداری بیلد، شاخص‌های عملیات زنده و ضرب‌آهنگ روایت."
            },
            {
                "text": "Monthly stakeholder brief circulated to investors, guild leaders, and moderators.",
                "text_fa": "گزارش ماهانه برای سرمایه‌گذاران، رهبران انجمن و ناظران ارسال می‌شود."
            },
            {
                "text": "Mid-season retrospective capturing action items before finale sprints.",
                "text_fa": "بازنگری میانه فصل برای ثبت اقدامات پیش از اسپرینت‌های پایانی."
            }
        ],
        "readiness_checklist": [
            {
                "text": "Staging environment mirrors production integrations for bot, wallet, and analytics hooks.",
                "text_fa": "محیط استیجینگ یکسان با یکپارچه‌سازی تولید برای بات، کیف‌پول و قلاب‌های تحلیلی است."
            },
            {
                "text": "Release notes localised in English and Persian with screenshot reviews.",
                "text_fa": "یادداشت‌های انتشار با بازبینی اسکرین‌شات به انگلیسی و فارسی بومی‌سازی شده‌اند."
            },
            {
                "text": "Support roster confirmed with escalation paths to engineering and lore teams.",
                "text_fa": "لیست کشیک پشتیبانی با مسیر ارجاع به تیم‌های مهندسی و روایت تأیید شده است."
            }
        ],
        "communications_plan": [
            {
                "text": "Pre-season teaser campaign on Telegram, X, and DYOR spotlighting faction rivalry.",
                "text_fa": "کمپین پیش‌فصل در تلگرام، ایکس و DYOR رقابت فرقه‌ها را برجسته می‌کند."
            },
            {
                "text": "Weekly lore drops summarised in email newsletters with links to new quests.",
                "text_fa": "افشای هفتگی روایت در خبرنامه ایمیلی با لینک مأموریت‌های تازه خلاصه می‌شود."
            },
            {
                "text": "Live finale stream with multilingual hosts and real-time reward reveals.",
                "text_fa": "پخش زنده فینال با مجریان چندزبانه و نمایش فوری پاداش‌ها برگزار می‌شود."
            }
        ],
        "current_year": timezone.now().year
    }

    return render(request, "roadmap.html", context)


def marketing_home(request):
    token_response = fetch_realshahnameh_token()
    token_error = None
    token_stats = {}

    if isinstance(token_response, dict) and token_response.get("error"):
        token_error = token_response["error"]
    elif isinstance(token_response, dict):
        token_stats = token_response

    social_links = [
        {
            "label_en": "Website",
            "label_fa": "وب‌سایت",
            "url": "https://shahnameh.io",
            "icon": "globe",
            "external": True,
        },
        {
            "label_en": "White paper",
            "label_fa": "وایت‌پیپر",
            "url": reverse("whitepaper"),
            "icon": "document",
            "external": False,
        },
        {
            "label_en": "X",
            "label_fa": "ایکس",
            "url": "https://x.com/ShahnamehTON",
            "icon": "x",
            "external": True,
        },
        {
            "label_en": "Github",
            "label_fa": "گیت‌هاب",
            "url": "https://github.com/Shahnameh-TON",
            "icon": "github",
            "external": True,
        },
        {
            "label_en": "Instagram",
            "label_fa": "اینستاگرام",
            "url": "https://instagram.com/shahnameh.ton",
            "icon": "instagram",
            "external": True,
        },
        {
            "label_en": "Telegram Bot",
            "label_fa": "بات تلگرام",
            "url": "https://t.me/shahnameshbot",
            "icon": "telegram",
            "external": True,
        },
        {
            "label_en": "Official Persian TG Channel",
            "label_fa": "کانال رسمی فارسی تلگرام",
            "url": "https://t.me/shahnameh_announcements",
            "icon": "telegram",
            "external": True,
        },
        {
            "label_en": "Telegram Group",
            "label_fa": "گروه تلگرام",
            "url": "https://t.me/shahnamehcommunity",
            "icon": "telegram",
            "external": True,
        },
        {
            "label_en": "YouTube",
            "label_fa": "یوتیوب",
            "url": "https://www.youtube.com/@ShahnamehTON",
            "icon": "youtube",
            "external": True,
        },
    ]

    context = {
        "token_stats": token_stats,
        "token_error": token_error,
        "season_two_roadmap": _season_two_roadmap(),
        "social_links": social_links,
        "current_year": timezone.now().year,
    }

    return render(request, "index.html", context)




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
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)

    if not bot_token:
        return Response(
            {"error": "Telegram bot token is not configured."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

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

def puzzle_board(request):
    board = request.session.get('board')
    if not board:
        board = generate_solvable_board()
        request.session['board'] = board

    win = is_solved(board)
    return render(request, 'board.html', {'board': board, 'win': win})

def move_tile(request, row, col):
    board = request.session.get('board')
    if not board:
        return redirect('puzzle')

    row, col = int(row), int(col)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for dr, dc in directions:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 3 and 0 <= nc < 3 and board[nr][nc] is None:
            board[nr][nc], board[row][col] = board[row][col], None
            break

    request.session['board'] = board
    return redirect('puzzle')


@csrf_exempt
def reset_board(request):
    if request.method == 'POST':
        request.session['board'] = generate_solvable_board()
    return redirect('puzzle')


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

        if encode_defunct is None or Web3 is None:
            return Response(
                {"error": "Web3 libraries are not installed in this environment."},
                status=503,
            )

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