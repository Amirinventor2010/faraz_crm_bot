from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def customer_main_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🗳 ثبت بازخورد", callback_data="customer_add_feedback")],
        [InlineKeyboardButton(text="📋 گزارش خلاصه من", callback_data="customer_summary")],
        [InlineKeyboardButton(text="⬅️ بازگشت به منوی ورود", callback_data="back_to_entry")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def feedback_score_kb() -> InlineKeyboardMarkup:
    # امتیاز 1 تا 5
    row = [
        InlineKeyboardButton(text=str(i), callback_data=f"fb_score:{i}")
        for i in range(1, 6)
    ]
    rows = [row, [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="customer_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=rows)
