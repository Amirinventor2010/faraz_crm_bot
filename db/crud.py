from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple
from calendar import monthrange

from sqlalchemy import select, update, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, Client, ClientKPI, Activity, Feedback, AuditLog, Sale, KPIRecord
from utils.constants import ROLE_STAFF, STATUS_ACTIVE
from config import ADMIN_TELEGRAM_IDS


# ---------------------------
# Admin helpers
# ---------------------------
def _is_admin_tg(tg_id: int) -> bool:
    ids = ADMIN_TELEGRAM_IDS
    if isinstance(ids, (list, tuple, set)):
        norm = {str(x).strip() for x in ids if str(x).strip()}
    else:
        norm = {s.strip() for s in str(ids).split(",") if s.strip()}
    return str(tg_id) in norm


async def is_admin_tgid(session: AsyncSession, tg_id: int) -> bool:
    if _is_admin_tg(tg_id):
        return True
    res = await session.execute(select(User).where(User.telegram_id == tg_id))
    u = res.scalar_one_or_none()
    return bool(u and u.role == "ADMIN")


# ---------------------------
# User
# ---------------------------
async def create_user(session: AsyncSession, **data) -> User:
    user = User(**data)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_telegram_id(session: AsyncSession, tg_id: int) -> Optional[User]:
    res = await session.execute(select(User).where(User.telegram_id == tg_id))
    return res.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    res = await session.execute(select(User).where(User.id == user_id))
    return res.scalar_one_or_none()


async def list_staff_active(session: AsyncSession) -> List[User]:
    res = await session.execute(
        select(User).where(User.role == ROLE_STAFF, User.status == STATUS_ACTIVE)
    )
    return list(res.scalars())


# ---------------------------
# Client
# ---------------------------
async def create_client(session: AsyncSession, **data) -> Client:
    client = Client(**data)
    session.add(client)
    await session.commit()
    await session.refresh(client)
    return client


async def get_client_by_id(session: AsyncSession, client_id: int) -> Optional[Client]:
    res = await session.execute(select(Client).where(Client.id == client_id))
    return res.scalar_one_or_none()


async def get_client_by_telegram_id(session: AsyncSession, tg_id: int) -> Optional[Client]:
    res = await session.execute(select(Client).where(Client.telegram_id == tg_id))
    return res.scalar_one_or_none()


async def list_all_clients(session: AsyncSession) -> List[Client]:
    res = await session.execute(select(Client))
    return list(res.scalars())


async def list_clients_for_staff(session: AsyncSession, staff_id: int) -> List[Client]:
    res = await session.execute(select(Client).where(Client.assigned_staff_id == staff_id))
    return list(res.scalars())


async def assign_client_to_staff(session: AsyncSession, client_id: int, staff_id: int) -> None:
    await session.execute(
        update(Client).where(Client.id == client_id).values(assigned_staff_id=staff_id)
    )
    await session.commit()


async def count_clients_for_staff(session: AsyncSession, staff_id: int) -> int:
    res = await session.execute(
        select(func.count()).select_from(Client).where(Client.assigned_staff_id == staff_id)
    )
    return int(res.scalar() or 0)


# ---------------------------
# KPI (Client Target Weekly)
# ---------------------------
async def upsert_client_kpi(
    session: AsyncSession, client_id: int, target_per_week: int, warn_ratio: float = 0.6
) -> ClientKPI:
    res = await session.execute(select(ClientKPI).where(ClientKPI.client_id == client_id))
    row = res.scalar_one_or_none()
    if row:
        row.target_per_week = target_per_week
        row.warn_ratio = warn_ratio
        await session.commit()
        await session.refresh(row)
        return row
    k = ClientKPI(client_id=client_id, target_per_week=target_per_week, warn_ratio=warn_ratio)
    session.add(k)
    await session.commit()
    await session.refresh(k)
    return k


async def get_client_kpi(session: AsyncSession, client_id: int) -> Optional[ClientKPI]:
    res = await session.execute(select(ClientKPI).where(ClientKPI.client_id == client_id))
    return res.scalar_one_or_none()


# ---------------------------
# Activity
# ---------------------------
async def create_activity(session: AsyncSession, **data) -> Activity:
    activity = Activity(**data)
    session.add(activity)
    await session.commit()
    await session.refresh(activity)
    return activity


async def count_activities_for_client(session: AsyncSession, client_id: int) -> int:
    res = await session.execute(
        select(func.count()).select_from(Activity).where(Activity.client_id == client_id)
    )
    return int(res.scalar() or 0)


async def count_activities_in_range(
    session: AsyncSession, client_id: int, start_dt: datetime, end_dt: datetime
) -> int:
    res = await session.execute(
        select(func.count()).select_from(Activity).where(
            Activity.client_id == client_id,
            Activity.ts >= start_dt,
            Activity.ts < end_dt
        )
    )
    return int(res.scalar() or 0)


async def last_activity_ts(session: AsyncSession, client_id: int) -> Optional[datetime]:
    res = await session.execute(
        select(Activity.ts).where(Activity.client_id == client_id).order_by(desc(Activity.ts)).limit(1)
    )
    return res.scalar_one_or_none()


# --- گزارش نیرو ---
async def count_activities_in_range_by_staff(
    session: AsyncSession, staff_id: int, start_dt: datetime, end_dt: datetime
) -> int:
    res = await session.execute(
        select(func.count()).select_from(Activity).where(
            Activity.staff_id == staff_id,
            Activity.ts >= start_dt,
            Activity.ts < end_dt
        )
    )
    return int(res.scalar() or 0)


async def last_activity_ts_for_staff(session: AsyncSession, staff_id: int) -> Optional[datetime]:
    res = await session.execute(
        select(Activity.ts).where(Activity.staff_id == staff_id).order_by(desc(Activity.ts)).limit(1)
    )
    return res.scalar_one_or_none()


async def list_recent_activities_for_client(
    session: AsyncSession, client_id: int, limit: int = 10
) -> List[Activity]:
    order_col = getattr(Activity, "ts", Activity.created_at)
    res = await session.execute(
        select(Activity).where(Activity.client_id == client_id).order_by(desc(order_col)).limit(limit)
    )
    return list(res.scalars())


async def list_recent_activities_for_staff(
    session: AsyncSession, staff_id: int, limit: int = 10
) -> List[Activity]:
    order_col = getattr(Activity, "ts", Activity.created_at)
    res = await session.execute(
        select(Activity).where(Activity.staff_id == staff_id).order_by(desc(order_col)).limit(limit)
    )
    return list(res.scalars())


# ---------------------------
# Feedback
# ---------------------------
async def create_feedback(session: AsyncSession, **data) -> Feedback:
    fb = Feedback(**data)
    session.add(fb)
    await session.commit()
    await session.refresh(fb)
    return fb


async def avg_feedback_for_client(session: AsyncSession, client_id: int) -> Optional[float]:
    res = await session.execute(
        select(func.avg(Feedback.score)).where(Feedback.client_id == client_id)
    )
    val = res.scalar()
    return float(val) if val is not None else None


async def list_recent_feedback_for_client(
    session: AsyncSession, client_id: int, limit: int = 10
) -> List[Feedback]:
    res = await session.execute(
        select(Feedback).where(Feedback.client_id == client_id).order_by(desc(Feedback.created_at)).limit(limit)
    )
    return list(res.scalars())


async def avg_feedback_for_staff_clients(session: AsyncSession, staff_id: int) -> Optional[float]:
    subq = select(Client.id).where(Client.assigned_staff_id == staff_id)
    res = await session.execute(
        select(func.avg(Feedback.score)).where(Feedback.client_id.in_(subq))
    )
    val = res.scalar()
    return float(val) if val is not None else None


# ---------------------------
# Sales
# ---------------------------
async def create_sale(session: AsyncSession, **data) -> Sale:
    s = Sale(**data)
    session.add(s)
    await session.commit()
    await session.refresh(s)
    return s


async def sum_sales_in_range(session: AsyncSession, client_id: int, start_dt: datetime, end_dt: datetime) -> float:
    res = await session.execute(
        select(func.coalesce(func.sum(Sale.amount), 0.0)).where(
            Sale.client_id == client_id,
            Sale.ts >= start_dt,
            Sale.ts < end_dt
        )
    )
    return float(res.scalar() or 0.0)


async def sum_sales_in_range_for_staff(session: AsyncSession, staff_id: int, start_dt: datetime, end_dt: datetime) -> float:
    subq = select(Client.id).where(Client.assigned_staff_id == staff_id)
    res = await session.execute(
        select(func.coalesce(func.sum(Sale.amount), 0.0)).where(
            Sale.client_id.in_(subq),
            Sale.ts >= start_dt,
            Sale.ts < end_dt
        )
    )
    return float(res.scalar() or 0.0)


async def list_recent_sales_for_client(session: AsyncSession, client_id: int, limit: int = 10) -> List[Sale]:
    res = await session.execute(
        select(Sale).where(Sale.client_id == client_id).order_by(desc(Sale.ts)).limit(limit)
    )
    return list(res.scalars())


# ---------------------------
# Audit
# ---------------------------
async def log_action(session: AsyncSession, **data) -> AuditLog:
    log = AuditLog(**data)
    session.add(log)
    await session.commit()
    return log


# ---------------------------
# Capacity helpers (Assign)
# ---------------------------
async def list_staff_with_capacity(session: AsyncSession) -> List[Tuple[User, int, int]]:
    staff = await list_staff_active(session)
    result = []
    for s in staff:
        cur_cnt = await count_clients_for_staff(session, s.id)
        cap = int(s.max_capacity or 0)
        has_capacity = (cap == 0) or (cur_cnt < cap)
        if has_capacity:
            result.append((s, cur_cnt, cap))
    return result


async def pick_staff_by_capacity(session: AsyncSession) -> Optional[User]:
    staff_list = await list_staff_active(session)
    candidates = []
    for s in staff_list:
        cur_cnt = await count_clients_for_staff(session, s.id)
        cap = int(s.max_capacity or 0)
        has_capacity = (cap == 0) or (cur_cnt < cap)
        if has_capacity:
            candidates.append((cur_cnt, s.id, s))
    if not candidates:
        return None
    candidates.sort(key=lambda t: (t[0], t[1]))
    return candidates[0][2]


# =========================================
# 📆 مرزهای دوره (هفتگی/ماهانه) — جدید
# =========================================
def get_week_bounds(when: date | None = None, week_start: int = 0) -> tuple[date, date]:
    """
    week_start: Monday=0 ... Sunday=6. اگر شنبه‌محور می‌خواهی: 5
    """
    today = when or date.today()
    diff = (today.weekday() - week_start) % 7
    start = today - timedelta(days=diff)
    end = start + timedelta(days=6)
    return start, end


def get_month_bounds(when: date | None = None) -> tuple[date, date]:
    today = when or date.today()
    start = today.replace(day=1)
    end = today.replace(day=monthrange(today.year, today.month)[1])
    return start, end


# =========================================
# 📈 Marketing KPI Records — جدید
# =========================================
async def upsert_kpi_record(
    session: AsyncSession,
    *,
    scope: str,                 # "weekly" | "monthly"
    metric: str,                # slug
    value: float,
    period_start: date,
    period_end: date,
    client_id: int | None = None,
    created_by_user_id: int | None = None,
) -> KPIRecord:
    res = await session.execute(
        select(KPIRecord).where(
            KPIRecord.client_id == client_id,
            KPIRecord.scope == scope,
            KPIRecord.metric == metric,
            KPIRecord.period_start == period_start,
            KPIRecord.period_end == period_end,
        )
    )
    rec = res.scalar_one_or_none()
    if rec:
        rec.value = value
        rec.created_by_user_id = created_by_user_id
        rec.created_at = datetime.utcnow()
        await session.commit()
        await session.refresh(rec)
        return rec

    rec = KPIRecord(
        client_id=client_id,
        scope=scope,
        metric=metric,
        value=value,
        period_start=period_start,
        period_end=period_end,
        created_by_user_id=created_by_user_id,
    )
    session.add(rec)
    await session.commit()
    await session.refresh(rec)
    return rec


async def get_kpi_record(
    session: AsyncSession,
    *,
    scope: str,
    metric: str,
    period_start: date,
    period_end: date,
    client_id: int | None = None,
) -> Optional[KPIRecord]:
    res = await session.execute(
        select(KPIRecord).where(
            KPIRecord.client_id == client_id,
            KPIRecord.scope == scope,
            KPIRecord.metric == metric,
            KPIRecord.period_start == period_start,
            KPIRecord.period_end == period_end,
        )
    )
    return res.scalar_one_or_none()


async def list_kpi_records_for_period(
    session: AsyncSession,
    *,
    scope: str,
    period_start: date,
    period_end: date,
    client_id: int | None = None,
) -> List[KPIRecord]:
    res = await session.execute(
        select(KPIRecord).where(
            KPIRecord.client_id == client_id,
            KPIRecord.scope == scope,
            KPIRecord.period_start == period_start,
            KPIRecord.period_end == period_end,
        ).order_by(KPIRecord.metric)
    )
    return list(res.scalars())


async def kpi_report_dict(
    session: AsyncSession,
    *,
    scope: str,
    period_start: date,
    period_end: date,
    client_id: int | None = None,
) -> dict[str, float]:
    rows = await list_kpi_records_for_period(
        session,
        scope=scope,
        period_start=period_start,
        period_end=period_end,
        client_id=client_id,
    )
    return {r.metric: float(r.value) for r in rows}
