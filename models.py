import uuid
from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String)
    mode: Mapped[str] = mapped_column(String, default="personal")
    timezone: Mapped[str] = mapped_column(String, default="Australia/Brisbane")
    plan: Mapped[str] = mapped_column(String, default="free")
    plan_expires: Mapped[datetime | None] = mapped_column(DateTime)
    apns_token: Mapped[str | None] = mapped_column(String)
    gmail_access_token: Mapped[str | None] = mapped_column(Text)
    gmail_refresh_token: Mapped[str | None] = mapped_column(Text)
    gmail_token_expiry: Mapped[datetime | None] = mapped_column(DateTime)
    gmail_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    calendar_access_token: Mapped[str | None] = mapped_column(Text)
    calendar_refresh_token: Mapped[str | None] = mapped_column(Text)
    calendar_token_expiry: Mapped[datetime | None] = mapped_column(DateTime)
    calendar_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    context_notes: Mapped[str | None] = mapped_column(Text)
    last_dispatch_run: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ThreadMessage(Base):
    __tablename__ = "thread_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String, default="standard")
    source_skill: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    due: Mapped[str | None] = mapped_column(String)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False)
    why: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, default=0)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    done_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class TeamSignal(Base):
    __tablename__ = "team_signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    recipient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id"))
    message: Mapped[str | None] = mapped_column(Text)
    is_seen: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AgentActivity(Base):
    __tablename__ = "agent_activity"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    skill: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    detail: Mapped[str | None] = mapped_column(Text)
    result: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# --- Intelligence loop tables (Session 4) ---


class UserModel(Base):
    __tablename__ = "user_model"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    voice_patterns: Mapped[dict] = mapped_column(JSON, default=dict)
    relationship_graph: Mapped[dict] = mapped_column(JSON, default=dict)
    productive_windows: Mapped[dict] = mapped_column(JSON, default=dict)
    completion_rates: Mapped[dict] = mapped_column(JSON, default=dict)
    notif_response_rates: Mapped[dict] = mapped_column(JSON, default=dict)
    defer_patterns: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    surface: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    content_id: Mapped[str | None] = mapped_column(String)
    action_taken: Mapped[str] = mapped_column(String, nullable=False)
    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    mode: Mapped[str | None] = mapped_column(String)
    health_context: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RelationshipGraph(Base):
    __tablename__ = "relationship_graph"
    __table_args__ = (UniqueConstraint("user_id", "contact_email"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    contact_email: Mapped[str] = mapped_column(String, nullable=False)
    importance_score: Mapped[float] = mapped_column(Float, default=5.0)
    avg_reply_time_hrs: Mapped[float | None] = mapped_column(Float)
    reply_rate: Mapped[float | None] = mapped_column(Float)
    total_interactions: Mapped[int] = mapped_column(Integer, default=0)
    last_interaction: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Pattern(Base):
    __tablename__ = "patterns"
    __table_args__ = (UniqueConstraint("user_id", "week_of"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    best_productive_hours: Mapped[dict | None] = mapped_column(JSON)
    deferred_categories: Mapped[dict | None] = mapped_column(JSON)
    notif_response_windows: Mapped[dict | None] = mapped_column(JSON)
    draft_acceptance_rate: Mapped[float | None] = mapped_column(Float)
    email_ranking_accuracy: Mapped[float | None] = mapped_column(Float)
    week_of = mapped_column(Date)


class SentEmailsCache(Base):
    __tablename__ = "sent_emails_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    recipient: Mapped[str | None] = mapped_column(String)
    recipient_type: Mapped[str | None] = mapped_column(String)
    subject: Mapped[str | None] = mapped_column(String)
    body_summary: Mapped[str | None] = mapped_column(Text)
    word_count: Mapped[int | None] = mapped_column(Integer)
    formality_score: Mapped[float | None] = mapped_column(Float)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime)


class CollectivePattern(Base):
    __tablename__ = "collective_patterns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mode: Mapped[str | None] = mapped_column(String)
    pattern_type: Mapped[str | None] = mapped_column(String)
    pattern_data: Mapped[dict | None] = mapped_column(JSON)
    sample_size: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[float | None] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


# --- Orchestration backbone tables (Session 6) ---


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    data_sources: Mapped[dict] = mapped_column(JSON, default=list)
    reasoning_model: Mapped[str] = mapped_column(String, default="claude")
    trigger_type: Mapped[str] = mapped_column(String, default="dispatch")
    trigger_config: Mapped[dict] = mapped_column(JSON, default=dict)
    output_routing: Mapped[str] = mapped_column(String, default="thread")
    system_prompt: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class SkillExecution(Base):
    __tablename__ = "skill_executions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("skills.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    input_context: Mapped[dict | None] = mapped_column(JSON)
    output_result: Mapped[str | None] = mapped_column(Text)
    model_used: Mapped[str | None] = mapped_column(String)
    surface_delivered: Mapped[str | None] = mapped_column(String)
    user_action: Mapped[str | None] = mapped_column(String)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ApiConnection(Base):
    __tablename__ = "api_connections"
    __table_args__ = (UniqueConstraint("user_id", "service"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    service: Mapped[str] = mapped_column(String, nullable=False)
    access_token: Mapped[str | None] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    scopes: Mapped[dict] = mapped_column(JSON, default=list)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Note(Base):
    __tablename__ = "notes"
    __table_args__ = (
        Index("ix_notes_content_fts", func.to_tsvector("english", "content"), postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(ARRAY(String), server_default="{}")
    source: Mapped[str] = mapped_column(String, default="thread")
    context_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ModelRoute(Base):
    __tablename__ = "model_routes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_type: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text)
    cost_per_1m_input: Mapped[float | None] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
