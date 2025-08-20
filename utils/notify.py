# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Optional
from datetime import datetime
from aiogram import Bot

# از کانفیگ پروژه: آیدی عددی گروه گزارش‌ها و آیدی تاپیک‌ها
from config import REPORTS_GROUP_ID, STAFF_TOPIC_ID, CLIENT_TOPIC_ID

log = logging.getLogger(__name__)

# -----------------------------
# ابزارهای کمکی
# -----------------------------
def _fmt_dt(dt: Optional[datetime] | Optional[str]) -> str:
    """نمایش تاریخ/ساعت به شکل خوانا؛ هم datetime و هم str (ISO) را قبول می‌کند."""
    if not dt:
        return "-"
    # اگر str ISO بود، تلاش به تبدیل
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return dt  # همون رشته را برگردون
    try:
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(dt)

async def _safe_send(bot: Bot, text: str, thread_id: Optional[int]) -> None:
    """
    اگر REPORTS_GROUP_ID ست باشد، پیام را می‌فرستد.
    اگر thread_id ست باشد، پیام در همان تاپیک ارسال می‌شود.
    هر خطایی اینجا قورت داده می‌شود تا جریان اصلی بات از کار نیفتد.
    """
    if not REPORTS_GROUP_ID:
        log.debug("REPORTS_GROUP_ID not set; skipping group notify.")
        return

    try:
        kwargs = {"chat_id": REPORTS_GROUP_ID, "text": text}
        if thread_id and int(thread_id) > 0:
            kwargs["message_thread_id"] = int(thread_id)
        await bot.send_message(**kwargs)
    except Exception as e:
        log.exception("Failed to send notify message to group: %s", e)

# -----------------------------
# اعلان: فعالیت نیروی مارکتینگ
# -----------------------------
async def notify_staff_activity(
    bot: Bot,
    activity=None,
    client=None,
    staff=None,
    *,
    # پارامترهای جایگزین در صورت عدم ارسال آبجکت
    client_name: Optional[str] = None,
    staff_name: Optional[str] = None,
    activity_type: Optional[str] = None,
    platform: Optional[str] = None,
    ts: Optional[datetime | str] = None,
    goal: Optional[str] = None,
    result: Optional[str] = None,
    evidence: Optional[str] = None,
) -> None:
    """
    اطلاع‌رسانی ثبت فعالیت جدید در تاپیک «گزارش نیروها».
    می‌توانی یا آبجکت‌های activity/client/staff را بدهی،
    یا با پارامترهای ستاره‌دار اطلاعات را پاس بدهی.
    """
    # از activity/client/staff استخراج کن، اگر داده نشده بود از پارامترهای صریح استفاده کن
    if activity is not None:
        ts = getattr(activity, "ts", getattr(activity, "created_at", ts))
        activity_type = getattr(activity, "activity_type", activity_type)
        platform = getattr(activity, "platform", platform)
        goal = getattr(activity, "goal", goal)
        result = getattr(activity, "initial_result", result)
        evidence = getattr(activity, "evidence_link", evidence)

    if staff is not None and not staff_name:
        staff_name = getattr(staff, "name", None) or f"ID={getattr(activity, 'staff_id', '-') if activity else '-'}"
    if client is not None and not client_name:
        client_name = getattr(client, "business_name", None) or f"ID={getattr(activity, 'client_id', '-') if activity else '-'}"

    ts_h = _fmt_dt(ts)
    typ = activity_type or "-"
    plat = platform or "-"

    extra = []
    if goal:
        extra.append(f"هدف: {goal}")
    if result:
        extra.append(f"نتیجه: {result}")
    if evidence:
        extra.append(f"مدرک: {evidence}")
    extra_h = " | ".join(extra) if extra else "-"

    text = (
        "🆕 ثبت فعالیت جدید\n"
        f"• نیرو: {staff_name or '-'}\n"
        f"• مشتری: {client_name or '-'}\n"
        f"• زمان: {ts_h}\n"
        f"• نوع/پلتفرم: {typ} / {plat}\n"
        f"• جزئیات: {extra_h}"
    )
    await _safe_send(bot, text, thread_id=STAFF_TOPIC_ID)

# سازگاری رو به عقب با نام‌های قبلی که در بعضی هندلرها استفاده شده
async def notify_activity(
    bot: Bot,
    *,
    client_name: Optional[str],
    staff_name: Optional[str],
    activity_type: Optional[str],
    platform: Optional[str],
    ts_str: Optional[str] = None,
    goal: Optional[str] = None,
    evidence: Optional[str] = None,
    result: Optional[str] = None,
) -> None:
    """
    Wrapper برای سازگاری با هندلرهایی که notify_activity(...) صدا می‌زنند.
    """
    await notify_staff_activity(
        bot,
        client_name=client_name,
        staff_name=staff_name,
        activity_type=activity_type,
        platform=platform,
        ts=ts_str,  # ممکن است ISO-string باشد
        goal=goal,
        result=result,
        evidence=evidence,
    )

# -----------------------------
# اعلان: بازخورد مشتری
# -----------------------------
async def notify_client_feedback(
    bot: Bot,
    feedback=None,
    client=None,
    *,
    client_name: Optional[str] = None,
    score: Optional[int] = None,
    comment: Optional[str] = None,
) -> None:
    """
    اطلاع‌رسانی ثبت بازخورد جدید در تاپیک «گزارش مشتری‌ها».
    """
    if feedback is not None:
        created = getattr(feedback, "created_at", None)
        score = int(getattr(feedback, "score", score) or 0)
        comment = getattr(feedback, "comment", comment)
    else:
        created = None

    if client is not None and not client_name:
        client_name = getattr(client, "business_name", None) or f"ID={getattr(feedback, 'client_id', '-') if feedback else '-'}"

    ts_h = _fmt_dt(created)
    stars = "⭐" * max(1, min(5, int(score or 0)))
    comment_h = comment or "-"

    text = (
        "💬 بازخورد مشتری\n"
        f"• مشتری: {client_name or '-'}\n"
        f"• زمان: {ts_h}\n"
        f"• امتیاز: {stars} ({score or 0}/5)\n"
        f"• توضیح: {comment_h}"
    )
    await _safe_send(bot, text, thread_id=CLIENT_TOPIC_ID)

# سازگاری با نام قبلی
async def notify_feedback(
    bot: Bot,
    *,
    client_name: Optional[str],
    score: int,
    comment: Optional[str] = None,
) -> None:
    """
    Wrapper برای سازگاری با هندلرهایی که notify_feedback(...) صدا می‌زنند.
    """
    await notify_client_feedback(
        bot,
        client_name=client_name,
        score=score,
        comment=comment,
    )
