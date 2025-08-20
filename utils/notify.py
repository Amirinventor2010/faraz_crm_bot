# -*- coding: utf-8 -*-
from typing import Optional
from aiogram import Bot
from datetime import datetime

from config import REPORTS_GROUP_ID, STAFF_TOPIC_ID, CLIENT_TOPIC_ID

def _fmt_dt(dt: Optional[datetime]) -> str:
    if not dt:
        return "-"
    try:
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(dt)

async def _safe_send(bot: Bot, text: str, thread_id: Optional[int]):
    """
    اگر REPORTS_GROUP_ID ست باشد، پیام را می‌فرستد.
    اگر thread_id ست باشد، در همان تاپیک ارسال می‌شود.
    """
    if not REPORTS_GROUP_ID:
        return
    kwargs = {}
    if thread_id:
        kwargs["message_thread_id"] = thread_id
    try:
        await bot.send_message(chat_id=REPORTS_GROUP_ID, text=text, **kwargs)
    except Exception:
        # نمی‌خواهیم ثبت فعالیت/بازخورد به‌خاطر خطای ارسال گروه fail شود
        pass

async def notify_staff_activity(bot: Bot, activity, client=None, staff=None):
    """
    اطلاع‌رسانی ثبت فعالیت جدید در تاپیک «گزارش نیروها»
    """
    ts = getattr(activity, "ts", getattr(activity, "created_at", None))
    ts_h = _fmt_dt(ts)
    typ = getattr(activity, "activity_type", "-")
    plat = getattr(activity, "platform", "-")
    goal = getattr(activity, "goal", None)
    res  = getattr(activity, "initial_result", None)
    evd  = getattr(activity, "evidence_link", None)

    staff_name = getattr(staff, "name", None) or f"ID={getattr(activity, 'staff_id', '-')}"
    client_name = getattr(client, "business_name", None) or f"ID={getattr(activity, 'client_id', '-')}"

    extra = []
    if goal: extra.append(f"هدف: {goal}")
    if res:  extra.append(f"نتیجه: {res}")
    if evd:  extra.append(f"مدرک: {evd}")
    extra_h = " | ".join(extra) if extra else "-"

    text = (
        "🆕 ثبت فعالیت جدید\n"
        f"• نیرو: {staff_name}\n"
        f"• مشتری: {client_name}\n"
        f"• زمان: {ts_h}\n"
        f"• نوع/پلتفرم: {typ} / {plat}\n"
        f"• جزئیات: {extra_h}"
    )
    await _safe_send(bot, text, thread_id=STAFF_TOPIC_ID)

async def notify_client_feedback(bot: Bot, feedback, client=None):
    """
    اطلاع‌رسانی ثبت بازخورد جدید در تاپیک «گزارش مشتری‌ها»
    """
    ts_h = _fmt_dt(getattr(feedback, "created_at", None))
    score = int(getattr(feedback, "score", 0) or 0)
    stars = "⭐" * max(1, min(5, score))
    comment = getattr(feedback, "comment", None) or "-"

    client_name = getattr(client, "business_name", None) or f"ID={getattr(feedback, 'client_id', '-')}"

    text = (
        "🆕 بازخورد مشتری\n"
        f"• مشتری: {client_name}\n"
        f"• زمان: {ts_h}\n"
        f"• امتیاز: {stars} ({score}/5)\n"
        f"• توضیح: {comment}"
    )
    await _safe_send(bot, text, thread_id=CLIENT_TOPIC_ID)
