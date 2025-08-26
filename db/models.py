from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import (
    String, ForeignKey, DateTime, Date, JSON, Text, Integer, Float,
    UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from utils.constants import STATUS_ACTIVE


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    role: Mapped[str] = mapped_column(String(16))
    name: Mapped[str | None] = mapped_column(String(128))
    phone: Mapped[str | None] = mapped_column(String(64))
    email: Mapped[str | None] = mapped_column(String(128))
    skills: Mapped[dict | None] = mapped_column(JSON)
    max_capacity: Mapped[int | None] = mapped_column(Integer, default=0)  # 0 = نامحدود
    status: Mapped[str] = mapped_column(String(16), default=STATUS_ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_name: Mapped[str] = mapped_column(String(128))
    industry: Mapped[str | None] = mapped_column(String(64))
    contract_date: Mapped[str | None] = mapped_column(String(32))  # ساده برای MVP
    platforms: Mapped[dict | None] = mapped_column(JSON)
    city: Mapped[str | None] = mapped_column(String(64))
    sales_source: Mapped[str | None] = mapped_column(String(64))
    feedback_channel: Mapped[str | None] = mapped_column(String(64))
    contact_info: Mapped[dict | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default=STATUS_ACTIVE)
    telegram_id: Mapped[int | None]
    assigned_staff_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    assigned_staff: Mapped["User"] = relationship("User", primaryjoin="User.id==Client.assigned_staff_id")


class ClientKPI(Base):
    __tablename__ = "client_kpis"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    target_per_week: Mapped[int] = mapped_column(Integer, default=0)
    warn_ratio: Mapped[float] = mapped_column(Float, default=0.6)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    staff_id: Mapped[int] = mapped_column(ForeKey("users.id"), index=True) if False else mapped_column(ForeignKey("users.id"), index=True)
    activity_type: Mapped[str] = mapped_column(String(64))
    platform: Mapped[str | None] = mapped_column(String(64))
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    goal: Mapped[str | None] = mapped_column(String(256))
    evidence_link: Mapped[str | None] = mapped_column(String(512))
    initial_result: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    score: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0)  # مبلغ فروش
    source: Mapped[str | None] = mapped_column(String(64))     # منبع/کانال فروش
    note: Mapped[str | None] = mapped_column(String(256))
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


# ============================
#   📈 KPI مارکتینگ (جدید)
# ============================
class KPIRecord(Base):
    __tablename__ = "kpi_records"
    __table_args__ = (
        UniqueConstraint("client_id", "scope", "metric", "period_start", "period_end", name="uq_kpi_period"),
        Index("ix_kpi_lookup", "scope", "metric", "period_start", "period_end"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # اگر KPI سراسری شرکت است: client_id = None
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), nullable=True, index=True)

    scope: Mapped[str] = mapped_column(String(16))  # "weekly" | "monthly"
    metric: Mapped[str] = mapped_column(String(64), index=True)

    value: Mapped[float] = mapped_column(Float, default=0.0)

    period_start: Mapped[date] = mapped_column(Date, index=True)
    period_end:   Mapped[date] = mapped_column(Date, index=True)

    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
