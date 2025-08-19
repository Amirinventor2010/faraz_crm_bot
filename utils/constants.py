ROLE_ADMIN = "ADMIN"
ROLE_STAFF = "STAFF"

STATUS_ACTIVE = "ACTIVE"
STATUS_INACTIVE = "INACTIVE"

# انواع فعالیت پیشنهادی (برای کیبورد نیرو)
ACTIVITY_TYPES = [
    "پست",
    "استوری",
    "کمپین",
    "تبلیغ",
    "پیام مستقیم",
    "سایر",
]

# آستانه‌های رنگ KPI (واقعی/هدف)
KPI_YELLOW_RATIO = 0.6  # 60% تا زیر 100% = زرد
KPI_RED_RATIO = 0.0     # 0% تا زیر 60%        = قرمز

# هشدارها
INACTIVITY_WARN_DAYS = 3   # اگر بیش از 3 روز فعالیت ثبت نشده باشد
FEEDBACK_WARN_SCORE = 3.0  # اگر میانگین امتیاز < 3 باشد

# متن دکمه بازگشت reply
BACK_TEXT = "⬅️ بازگشت"
