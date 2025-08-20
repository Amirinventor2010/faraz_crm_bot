# -*- coding: utf-8 -*-
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest

async def edit_or_send(obj, text: str, reply_markup=None, force_new: bool = False):
    """
    اگر obj یک CallbackQuery باشد:
      - در صورت امکان پیام قبلی را ویرایش می‌کنیم (فقط برای inline keyboards).
      - اگر reply_markup از نوع ReplyKeyboardMarkup باشد یا force_new=True:
        پیام جدید می‌فرستیم و پیام قبلی را حذف می‌کنیم.
    اگر obj یک Message باشد، پیام جدید ارسال می‌شود.
    """
    is_reply_kb = isinstance(reply_markup, ReplyKeyboardMarkup)

    if isinstance(obj, types.CallbackQuery):
        msg = obj.message
        # ویرایش فقط وقتی منطقی است که کیبورد Reply نباشد
        if not force_new and not is_reply_kb:
            try:
                return await msg.edit_text(text, reply_markup=reply_markup)
            except TelegramBadRequest:
                # ممکن است قابل ویرایش نباشد (قدیمی/فوروارد/...)
                pass
        sent = await msg.answer(text, reply_markup=reply_markup)
        try:
            await msg.delete()
        except Exception:
            pass
        return sent

    elif isinstance(obj, types.Message):
        return await obj.answer(text, reply_markup=reply_markup)

    else:
        raise TypeError("Unsupported object for edit_or_send")
