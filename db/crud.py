from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User, Client, Activity, Feedback, AuditLog
from utils.constants import ROLE_STAFF, STATUS_ACTIVE

# ---------- Users ----------
async def get_user_by_telegram_id(session: AsyncSession, tg_id: int):
    res = await session.execute(select(User).where(User.telegram_id == tg_id))
    return res.scalar_one_or_none()

async def get_user_by_id(session: AsyncSession, user_id: int):
    res = await session.execute(select(User).where(User.id == user_id))
    return res.scalar_one_or_none()

async def create_user(session: AsyncSession, **data) -> User:
    user = User(**data)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def list_staff_active(session: AsyncSession):
    res = await session.execute(
        select(User).where(User.role == ROLE_STAFF, User.status == STATUS_ACTIVE)
    )
    return list(res.scalars())

# ---------- Clients ----------
async def create_client(session: AsyncSession, **data) -> Client:
    client = Client(**data)
    session.add(client)
    await session.commit()
    await session.refresh(client)
    return client

async def get_client_by_id(session: AsyncSession, client_id: int) -> Client | None:
    res = await session.execute(select(Client).where(Client.id == client_id))
    return res.scalar_one_or_none()

async def get_client_by_telegram_id(session: AsyncSession, tg_id: int) -> Client | None:
    res = await session.execute(select(Client).where(Client.telegram_id == tg_id))
    return res.scalar_one_or_none()

async def list_clients_active(session: AsyncSession):
    res = await session.execute(
        select(Client).where(Client.status == STATUS_ACTIVE)
    )
    return list(res.scalars())

async def list_clients_for_staff(session: AsyncSession, staff_id: int):
    res = await session.execute(
        select(Client).where(Client.assigned_staff_id == staff_id, Client.status == STATUS_ACTIVE)
    )
    return list(res.scalars())

async def assign_client_to_staff(session: AsyncSession, client_id: int, staff_id: int):
    await session.execute(
        update(Client).where(Client.id == client_id).values(assigned_staff_id=staff_id)
    )
    await session.commit()

async def count_clients_for_staff(session: AsyncSession, staff_id: int) -> int:
    res = await session.execute(
        select(func.count()).select_from(Client).where(Client.assigned_staff_id == staff_id)
    )
    return int(res.scalar() or 0)

async def pick_staff_by_capacity(session: AsyncSession) -> User | None:
    staff_list = await list_staff_active(session)
    if not staff_list:
        return None
    best, best_load = None, None
    for s in staff_list:
        load = await count_clients_for_staff(session, s.id)
        cap = s.max_capacity or 0
        if cap <= load:
            continue
        if best is None or load < best_load or (load == best_load and (s.max_capacity or 0) > (best.max_capacity or 0)):
            best, best_load = s, load
    return best

# ---------- Activities ----------
async def create_activity(session: AsyncSession, **data) -> Activity:
    act = Activity(**data)
    session.add(act)
    await session.commit()
    await session.refresh(act)
    return act

# ---------- Feedback ----------
async def create_feedback(session: AsyncSession, **data) -> Feedback:
    fb = Feedback(**data)
    session.add(fb)
    await session.commit()
    await session.refresh(fb)
    return fb

# ---------- Audit ----------
async def log_action(session: AsyncSession, **data) -> AuditLog:
    log = AuditLog(**data)
    session.add(log)
    await session.commit()
    return log
