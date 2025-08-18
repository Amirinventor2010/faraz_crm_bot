from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def staff_main_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📝 ثبت فعالیت جدید", callback_data="staff_add_activity")],
        [InlineKeyboardButton(text="📈 گزارش عملکرد من (به‌زودی)", callback_data="staff_my_report")],
        [InlineKeyboardButton(text="🗓 گزارش هفتگی مشتریان (به‌زودی)", callback_data="staff_clients_week")],
        [InlineKeyboardButton(text="⬅️ بازگشت به منوی ورود", callback_data="back_to_entry")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def clients_inline_kb(clients: list) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=c.business_name, callback_data=f"staff_pick_client:{c.id}")]
        for c in clients[:50]
    ]
    rows.append([InlineKeyboardButton(text="⬅️ بازگشت به پنل نیرو", callback_data="staff_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

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
