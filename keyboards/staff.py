from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from keyboards.common import BACK_TEXT  # متن دکمه بازگشت («⬅️ بازگشت»)

# -------------------------------
# پنل اصلی نیروی مارکتینگ
# -------------------------------
def staff_main_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📝 ثبت فعالیت جدید", callback_data="staff_add_activity")],
        [InlineKeyboardButton(text="📈 گزارش عملکرد من (به‌زودی)", callback_data="staff_my_report")],
        [InlineKeyboardButton(text="🗓 گزارش هفتگی مشتریان (به‌زودی)", callback_data="staff_clients_week")],
        [InlineKeyboardButton(text="⬅️ بازگشت به منوی ورود", callback_data="back_to_entry")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ------------------------------------------
# لیست مشتری‌ها برای انتخاب در فرم فعالیت
# ------------------------------------------
def clients_inline_kb(clients: list) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=c.business_name, callback_data=f"staff_pick_client:{c.id}")]
        for c in clients[:50]
    ]
    rows.append([InlineKeyboardButton(text="⬅️ بازگشت به پنل نیرو", callback_data="staff_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ---------------------------------------------------------
# انتخاب نوع فعالیت (برای فرم ثبت فعالیت روزانه نیرو)
#  - با handler: data = "act_type:<value>"
#  - یک گزینه «سایر (تایپی)» هم دارد
# ---------------------------------------------------------
def activity_types_inline_kb(types_list: list[str]) -> InlineKeyboardMarkup:
    # هر آیتمِ لیست به شکل یک دکمهٔ جدا
    rows = [
        [InlineKeyboardButton(text=t, callback_data=f"act_type:{t}")]
        for t in types_list[:20]
    ]
    # سایر (ورودی تایپی)
    rows.append([InlineKeyboardButton(text="✏️ سایر (تایپی)", callback_data="act_type:other")])
    # بازگشت
    rows.append([InlineKeyboardButton(text="⬅️ بازگشت", callback_data="staff_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ---------------------------------------------------------
# کیبورد بازگشت (Reply) برای مراحل فرم‌ها
# (اگر جایی back_reply_kb از keyboards.common را استفاده نکردی)
# ---------------------------------------------------------
def staff_back_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BACK_TEXT)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# ——— در صورت نیاز برای جریان‌های ادمین (تخصیص مشتری) نگه‌داشتیم ———
def assign_clients_inline_kb(clients: list) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=c.business_name, callback_data=f"assign_pick_client:{c.id}")]
        for c in clients[:50]
    ]
    rows.append([InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_setup")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def assign_staff_inline_kb(staff_list: list) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=s.name, callback_data=f"assign_pick_staff:{s.id}")]
        for s in staff_list[:50]
    ]
    rows.insert(0, [InlineKeyboardButton(text="🤖 تخصیص خودکار", callback_data="assign_auto")])
    rows.append([InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_setup")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
