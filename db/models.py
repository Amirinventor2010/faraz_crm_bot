from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, JSON, Text, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from utils.constants import STATUS_ACTIVE


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    role: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str | None]
    email: Mapped[str | None]
    skills: Mapped[dict | None] = mapped_column(JSON)
    max_capacity: Mapped[int | None]
    status: Mapped[str] = mapped_column(String(16), default=STATUS_ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # با __future__.annotations می‌تونیم به Client همین‌جا ارجاع بدیم
    clients: Mapped[list[Client]] = relationship(back_populates="assigned_staff")


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_name: Mapped[str] = mapped_column(String(200))
    industry: Mapped[str | None]
    contract_date: Mapped[str | None]
    platforms: Mapped[dict | None] = mapped_column(JSON)
    city: Mapped[str | None]
    sales_source: Mapped[str | None]
    feedback_channel: Mapped[str | None]
    contact_info: Mapped[dict | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default=STATUS_ACTIVE)
    assigned_staff_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    telegram_id: Mapped[int | None] = mapped_column(Integer, index=True)  # برای ورود مشتری
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ✅ اینجا مشکل بود — نباید داخل کوتیشن با | بیاد
    assigned_staff: Mapped[User | None] = relationship(back_populates="clients")


class ClientKPI(Base):
    """
    KPI هفتگی برای مشتری (بر اساس تعداد فعالیت هفتگی)
    """
    __tablename__ = "client_kpis"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    target_per_week: Mapped[int] = mapped_column(Integer, default=5)
    warn_ratio: Mapped[float] = mapped_column(Float, default=0.6)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    staff_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    activity_type: Mapped[str]
    platform: Mapped[str | None]
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    goal: Mapped[str | None]
    evidence_link: Mapped[str | None]
    initial_result: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    score: Mapped[int]
    comment: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None]
    action: Mapped[str]
    entity: Mapped[str]
    entity_id: Mapped[int | None]
    diff_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
