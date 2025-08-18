from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from utils.constants import BACK_TEXT

def entry_menu_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="🔐 ورود به پنل مدیر", callback_data="enter_admin"),
        ],
        [
            InlineKeyboardButton(text="👨‍💼 ورود به پنل نیرو", callback_data="enter_staff"),
        ],
        [
            InlineKeyboardButton(text="👤 ورود به پنل مشتری", callback_data="enter_customer"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def back_reply_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BACK_TEXT)]],
        resize_keyboard=True
    )

def confirm_inline_kb(ok_cb: str, cancel_cb: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="✅ تأیید و ثبت", callback_data=ok_cb),
            InlineKeyboardButton(text="❌ لغو", callback_data=cancel_cb),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
