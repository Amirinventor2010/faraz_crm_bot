# keyboards/customer.py
from aiogram.utils.keyboard import InlineKeyboardBuilder

def customer_main_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="ثبت بازخورد", callback_data="cust_feedback")
    kb.button(text="گزارش خلاصه", callback_data="cust_summary")
    kb.adjust(1)
    return kb.as_markup()