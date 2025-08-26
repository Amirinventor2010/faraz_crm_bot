from __future__ import annotations
from typing import Optional, Dict, Tuple, List
from datetime import date
from db import crud
from utils.validators import parse_numeric

# ================================
#  فهرست KPI ها + نام فارسی/اسلاگ
# ================================
WEEKLY_METRICS: List[Tuple[str, str]] = [
    ("رشد فالوور", "ig_followers_growth"),
    ("تعداد لید اینستاگرام", "ig_leads"),
    ("تعداد کمپین اجرا", "campaigns_count"),
    ("تعداد فروش اینستا", "ig_sales"),
    ("تعداد فروش حضوری", "offline_sales"),
    ("ریچ پیج", "ig_reach"),
    ("تعداد لید واتساپ", "wa_leads"),
    ("تعداد فروش واتساپ", "wa_sales"),
    ("تعداد لید دیوار", "divar_leads"),
    ("تعداد فروش دیوار", "divar_sales"),
    ("تعداد لید ترب", "torob_leads"),
    ("تعداد فروش ترب", "torob_sales"),
]

MONTHLY_METRICS: List[Tuple[str, str]] = [
    ("نرخ تعامل", "engagement_rate"),
    ("رشد فالوور", "ig_followers_growth"),
    ("تعداد کمپین اجرا شده", "campaigns_count"),
    ("تعداد فروش اینستا", "ig_sales"),
    ("تعداد فروش حضوری", "offline_sales"),
    ("ریچ پیج", "ig_reach"),
    ("تعداد لید واتساپ", "wa_leads"),
    ("تعداد فروش واتساپ", "wa_sales"),
    ("تعداد لید دیوار", "divar_leads"),
    ("تعداد فروش دیوار", "divar_sales"),
    ("تعداد لید ترب", "torob_leads"),
    ("تعداد فروش ترب", "torob_sales"),
]

_FA_MAP: Dict[str, str] = {slug: fa for fa, slug in (WEEKLY_METRICS + MONTHLY_METRICS)}

def get_metrics(scope: str) -> List[Tuple[str, str]]:
    return WEEKLY_METRICS if scope == "weekly" else MONTHLY_METRICS

def fa_name(metric_slug: str) -> str:
    return _FA_MAP.get(metric_slug, metric_slug)

def scope_fa(scope: str) -> str:
    return "هفتگی" if scope == "weekly" else "ماهانه"

def get_period_bounds(scope: str, when: Optional[date] = None, week_start: int = 0) -> Tuple[date, date]:
    if scope == "weekly":
        return crud.get_week_bounds(when, week_start)
    if scope == "monthly":
        return crud.get_month_bounds(when)
    raise ValueError("invalid scope")

# =========================================
#  ثبت/آپدیت KPI و گزارش دوره
# =========================================
async def upsert_value(
    session,
    *,
    scope: str,
    metric: str,
    value_text: str,
    when: Optional[date] = None,
    client_id: Optional[int] = None,
    created_by_user_id: Optional[int] = None,
    week_start: int = 0,
):
    value = parse_numeric(value_text)
    start_d, end_d = get_period_bounds(scope, when=when, week_start=week_start)
    rec = await crud.upsert_kpi_record(
        session,
        scope=scope,
        metric=metric,
        value=value,
        period_start=start_d,
        period_end=end_d,
        client_id=client_id,
        created_by_user_id=created_by_user_id,
    )
    return rec, start_d, end_d, value

async def report_dict(
    session,
    *,
    scope: str,
    when: Optional[date] = None,
    client_id: Optional[int] = None,
    week_start: int = 0,
) -> Tuple[Dict[str, float], date, date]:
    start_d, end_d = get_period_bounds(scope, when=when, week_start=week_start)
    data = await crud.kpi_report_dict(
        session,
        scope=scope,
        period_start=start_d,
        period_end=end_d,
        client_id=client_id,
    )
    return data, start_d, end_d

def format_report_text(scope: str, period_start: date, period_end: date, data: Dict[str, float]) -> str:
    lines = [f"📊 گزارش KPI مارکتینگ {scope_fa(scope)}\n({period_start} تا {period_end})"]
    if not data:
        lines.append("— داده‌ای ثبت نشده است —")
        return "\n".join(lines)
    # مرتب‌سازی بر اساس نام فارسی KPI
    for slug, val in sorted(data.items(), key=lambda kv: fa_name(kv[0])):
        lines.append(f"• {fa_name(slug)}: {val}")
    return "\n".join(lines)
