# 🤖 Faraz CRM & Marketing Telegram Bot
<!-- Language switch: [🇮🇷 فارسی](#-راهنمای-کامل-فارسی) | [🇬🇧 English](#-full-readme-english) -->

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.x-2ea44f)](https://docs.aiogram.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/Amirinventor2010/faraz_crm_bot?style=social)](https://github.com/Amirinventor2010/faraz_crm_bot/stargazers)

---

## 🇮🇷 راهنمای کامل (فارسی)

### 📌 معرفی
ربات تلگرام «فراز» یک بات مدیریتی برای **ثبت داده‌های تیم مارکتینگ و مشتریان، پایش KPI/SLA، دریافت بازخورد، و گزارش‌دهی** است. این پروژه با **Python 3.12 + Aiogram 3.x** توسعه یافته و برای استقرار تولیدی، **Docker Compose با معماری app + db (Postgres)** دارد. برای توسعهٔ سادهٔ محلی، می‌توانید از **SQLite** هم استفاده کنید.

### ✨ ویژگی‌ها
- **نقش‌ها:** مدیر / نیروی مارکتینگ / مشتری (منوهای اختصاصی و دسترسی‌های مجزا)
- **KPI/SLA:** تعریف/ویرایش، KPIهای **هفتگی/ماهانه** (رشد فالوور، لید/فروش هر کانال: اینستاگرام/واتساپ/دیوار/ترب، نرخ تعامل، ریچ، تعداد کمپین، …)
- **ثبت فعالیت‌های روزانه** و **بازخورد مشتری (امتیاز ۱–۵ + توضیح)** 
- **گزارش‌ها و هشدارها:** وضعیت سبز/زرد/قرمز، عدم فعالیت، فروش/رضایت زیر آستانه، اختلاف گزارش
- **خروجی‌گیری:** متن/CSV/Excel/PDF + امکان زمان‌بندی ارسال در تلگرام
- **قابل توسعه:** اتصال به n8n/API داخلی، مهاجرت آسان دیتابیس، ثبت لاگ کامل

### 🧱 تکنولوژی‌ها
Python 3.12، Aiogram 3.x، SQLAlchemy (async)، Pydantic، **Postgres (Docker)**، SQLite (لوکال).

---

## 📂 ساختار پروژه
```
faraz_crm_bot/
├─ app.py                   # نقطه شروع ربات
├─ config.py                # بارگذاری ENV و تنظیمات
├─ db/
│  ├─ base.py               # Session/Engine
│  ├─ models.py             # مدل‌ها
│  └─ crud.py               # توابع دیتابیسی
├─ handlers/                # هندلرهای نقش‌ها (admin/customer/staff/...)
├─ keyboards/               # کیبوردهای اینلاین/ریپلای
├─ services/                # سرویس‌ها (auth/kpi/...)
├─ utils/                   # ابزارها و UI/notify/constants/validators
├─ requirements.txt
├─ Dockerfile
├─ .dockerignore
├─ docker-compose.yml
└─ README.md
```

---

## ⚙️ متغیرهای محیطی (.env)
فایل `.env` را در **ریشه پروژه** (کنار `docker-compose.yml`) بسازید:

```dotenv
# --- Bot ---
BOT_TOKEN=xxxx:yyyy
ADMIN_TELEGRAM_IDS=5010464861,114917704

# --- Database (Production via Docker: Postgres) ---
DB_NAME=farazdb
DB_USER=bot
DB_PASSWORD=botpass
DB_URL=postgresql+asyncpg://bot:botpass@db:5432/farazdb

# --- Optional ---
REPORTS_GROUP_ID=-1002782690499
STAFF_TOPIC_ID=2
CLIENT_TOPIC_ID=4
```

> نکات:
> - **هرگز** `.env` را کامیت نکنید. در صورت افشا، توکن را **rotate** کنید.
> - برای توسعه محلی بدون Docker می‌توانید از SQLite استفاده کنید:
>   `DB_URL=sqlite+aiosqlite:///./faraz.sqlite3`

---

## 🧪 اجرای محلی (بدون Docker)
پیش‌نیاز: **Python 3.12**
```bash
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# Linux/Mac
source .venv/bin/activate

python -m pip install --upgrade pip wheel
pip install -r requirements.txt

# ساخت .env مطابق بالا (برای لوکال می‌توانید SQLite بگذارید)
# DB_URL=sqlite+aiosqlite:///./faraz.sqlite3

python app.py
```

> ویندوز و مشکل event loop؟ بدون تغییر کد این‌طور اجرا کنید:
```powershell
.\.venv\Scripts\python.exe -c "import asyncio, runpy; asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()); runpy.run_path('app.py')"
```

---

## 🚀 استقرار تولیدی با Docker (app + db/Postgres)
این پروژه با **Postgres** به‌صورت دو سرویس `app` و `db` اجرا می‌شود.

### 1) پیش‌نیاز
- Docker Desktop (Windows) یا Docker + Compose (Linux)
- دسترسی اینترنت سرور برای ارتباط بات با تلگرام

### 2) دریافت سورس روی سرور
```bash
git clone https://github.com/Amirinventor2010/faraz_crm_bot.git
cd faraz_crm_bot
```

### 3) ایجاد `.env` (طبق بخش بالا)

### 4) Build & Run
```bash
docker compose up -d --build
```

### 5) مشاهده لاگ‌ها
```bash
docker compose logs -f
```

### 6) توقف/شروع/ری‌استارت
```bash
docker compose stop
docker compose start
docker compose restart
```

### 7) آپدیت نسخه
```bash
git pull
docker compose up -d --build
```

---

## 💾 بکاپ/بازگردانی دیتابیس (Postgres)
> نام سرویس دیتابیس در Compose: `db`

**بکاپ (pg_dump):**
```bash
docker exec -t db pg_dump -U "$DB_USER" -d "$DB_NAME" -F c -f /tmp/faraz_$(date +%F_%H%M).dump
docker cp db:/tmp/faraz_$(date +%F_%H%M).dump ./backup/
```

**بازگردانی (pg_restore):**
```bash
docker cp ./backup/faraz_YYYY-MM-DD_HHMM.dump db:/tmp/restore.dump

docker exec -it db dropdb -U "$DB_USER" "$DB_NAME"
docker exec -it db createdb -U "$DB_USER" "$DB_NAME"
docker exec -it db pg_restore -U "$DB_USER" -d "$DB_NAME" -c /tmp/restore.dump

docker compose restart app
```

> اگر ترجیح می‌دهید از SQLite در Docker استفاده کنید (تک‌سرویس)، در `.env`:
> `DB_URL=sqlite+aiosqlite:///./data/faraz.sqlite3` و `/app/data` را به صورت bind/volume مانت کنید.

---

## 🛡️ نکات امنیتی و عملیاتی
- اسرار را **کامیت نکنید**: `.env` فقط روی سرور بماند. در صورت نشت، **rotate** کنید.
- اگر از گروه/تاپیک استفاده می‌کنید، بات باید ادمین گروه گزارش‌ها باشد.
- در ویندوز، برای bind mount، در Docker Desktop درایو پروژه را در **File Sharing** اضافه کنید.

---

## 🤝 مشارکت
Issue و PR پذیرفته می‌شود. لطفاً PEP8 و Type Hints رعایت شود.

## 📄 لایسنس
MIT

---

## 🇬🇧 Full README (English)

### 📌 Overview
Faraz Bot is a Telegram assistant to **collect marketing/customer data, track KPIs/SLAs, capture client feedback, and deliver reports**—all inside Telegram. Built with **Python 3.12 + Aiogram 3.x**, production-ready with **Docker Compose (app + db/Postgres)**. For simple local development, you may use **SQLite**.

### ✨ Features
- **Roles:** Admin / Marketing Staff / Client (separate menus & permissions)
- **KPI/SLA:** define & edit, **Weekly/Monthly KPIs** (follower growth; leads/sales per Instagram/WhatsApp/Divar/Torob; engagement rate; reach; campaigns…)
- **Daily activities** logging & **client feedback** (rating 1–5 + comment)
- **Reports & alerts:** green/yellow/red status; inactivity; low sales/satisfaction; mismatch
- **Exports:** text/CSV/Excel/PDF + scheduled posting in Telegram
- **Extensible:** n8n/internal APIs, easy DB migration, full auditing

### 🧱 Stack
Python 3.12, Aiogram 3.x, SQLAlchemy (async), Pydantic, **Postgres (Docker)**, SQLite (local).

---

## 📂 Project Layout
```
faraz_crm_bot/
├─ app.py
├─ config.py
├─ db/ (base.py, models.py, crud.py)
├─ handlers/ (admin/customer/staff/…)
├─ keyboards/
├─ services/ (auth.py, kpi.py, …)
├─ utils/ (constants.py, notify.py, ui.py, validators.py)
├─ requirements.txt
├─ Dockerfile
├─ .dockerignore
├─ docker-compose.yml
└─ README.md
```

---

## ⚙️ Environment (.env)
Create `.env` at repository root:

```dotenv
# --- Bot ---
BOT_TOKEN=xxxx:yyyy
ADMIN_TELEGRAM_IDS=5010464861,114917704

# --- Database (Production via Docker: Postgres) ---
DB_NAME=farazdb
DB_USER=bot
DB_PASSWORD=botpass
DB_URL=postgresql+asyncpg://bot:botpass@db:5432/farazdb

# --- Optional ---
REPORTS_GROUP_ID=-1002782690499
STAFF_TOPIC_ID=2
CLIENT_TOPIC_ID=4
```

> For local development without Docker, you may use SQLite:
> `DB_URL=sqlite+aiosqlite:///./faraz.sqlite3`

---

## 🧪 Local Run (without Docker)
Prereq: **Python 3.12**
```bash
python -m venv .venv
# Windows (PowerShell): .\.venv\Scripts\Activate.ps1
# Linux/Mac:            source .venv/bin/activate

python -m pip install --upgrade pip wheel
pip install -r requirements.txt

# Create .env (SQLite is fine locally)
# DB_URL=sqlite+aiosqlite:///./faraz.sqlite3

python app.py
```

> Windows event loop issue? Run without code change:
```powershell
.\.venv\Scripts\python.exe -c "import asyncio, runpy; asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()); runpy.run_path('app.py')"
```

---

## 🚀 Production with Docker (app + db/Postgres)
### 1) Prerequisite
- Docker Desktop (Windows) or Docker + Compose (Linux)

### 2) Get sources
```bash
git clone https://github.com/Amirinventor2010/faraz_crm_bot.git
cd faraz_crm_bot
```

### 3) Prepare `.env` (see above)

### 4) Build & Run
```bash
docker compose up -d --build
```

### 5) Logs
```bash
docker compose logs -f
```

### 6) Stop/Start/Restart
```bash
docker compose stop
docker compose start
docker compose restart
```

### 7) Update
```bash
git pull
docker compose up -d --build
```

---

## 💾 Postgres Backup/Restore
> Compose DB service name: `db`

**Backup (pg_dump):**
```bash
docker exec -t db pg_dump -U "$DB_USER" -d "$DB_NAME" -F c -f /tmp/faraz_$(date +%F_%H%M).dump
docker cp db:/tmp/faraz_$(date +%F_%H%M).dump ./backup/
```

**Restore (pg_restore):**
```bash
docker cp ./backup/faraz_YYYY-MM-DD_HHMM.dump db:/tmp/restore.dump
docker exec -it db dropdb -U "$DB_USER" "$DB_NAME"
docker exec -it db createdb -U "$DB_USER" "$DB_NAME"
docker exec -it db pg_restore -U "$DB_USER" -d "$DB_NAME" -c /tmp/restore.dump
docker compose restart app
```

---

## 🧩 Alternative: Single-service Docker with SQLite
- `.env`: `DB_URL=sqlite+aiosqlite:///./data/faraz.sqlite3`
- Mount `/app/data` via bind/volume to persist the SQLite file.

---

## 🔐 Security & Ops
- **Never commit secrets**; keep tokens in `.env` on server. If leaked, **rotate**.
- Ensure the bot is admin of the reports group if you use topics.
- On Windows bind mounts, share the drive in Docker Desktop (File Sharing).
