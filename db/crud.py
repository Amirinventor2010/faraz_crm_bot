from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select, update, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, Client, ClientKPI, Activity, Feedback, AuditLog
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
    u = res.scalar_one_or_none
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
# KPI
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


# --- for Staff reports ---
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


async def avg_feedback_for_staff_clients(session: AsyncSession, staff_id: int) -> Optional[float]:
    # میانگین رضایت برای تمام مشتریانی که به این نیرو تخصیص یافته‌اند
    sub = select(Client.id).where(Client.assigned_staff_id == staff_id).subquery()
    res = await session.execute(
        select(func.avg(Feedback.score)).where(Feedback.client_id.in_(select(sub)))
    )
    val = res.scalar()
    return float(val) if val is not None else None


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
async def list_staff_with_capacity(
    session: AsyncSession,
) -> List[Tuple[User, int, int]]:
    """
    نیروهای فعال با ظرفیت آزاد.
    خروجی: [(User, current_count, max_capacity)]
    max_capacity=0 → نامحدود
    """
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
    """
    کم‌بارترین نیروی فعال که ظرفیت دارد (max_capacity=0 نامحدود).
    """
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
