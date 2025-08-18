from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_main_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="⚙️ راه‌اندازی اولیه", callback_data="admin_setup")],
        [InlineKeyboardButton(text="📊 گزارش‌ها (به‌زودی)", callback_data="admin_reports_soon")],
        [InlineKeyboardButton(text="📤 خروجی و دانلود (به‌زودی)", callback_data="admin_export_soon")],
        [InlineKeyboardButton(text="⬅️ بازگشت به منوی ورود", callback_data="back_to_entry")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_setup_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="➕ ثبت نیروی مارکتینگ/مدیر", callback_data="admin_add_staff")],
        [InlineKeyboardButton(text="➕ ثبت مشتری", callback_data="admin_add_client")],
        [InlineKeyboardButton(text="🔗 تخصیص مشتری به نیرو", callback_data="admin_assign")],
        [InlineKeyboardButton(text="⬅️ بازگشت به پنل مدیر", callback_data="admin_back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
