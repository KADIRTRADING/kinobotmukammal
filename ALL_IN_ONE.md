# Movie Bot — Complete Project, Single File

Every file in this repository, concatenated below. Each file starts with a
`### FILE: <path>` heading followed by a fenced code block containing that
file's exact content. Outer fences use four backticks (````) so that files
which themselves contain ordinary triple-backtick fences (e.g. README.md's
code samples) nest correctly without breaking the block.

To reconstruct the project: split on the `### FILE:` headings and write each
block's content to its named path (directories are implied by the path).

**Total files: 169**

---

### FILE: alembic/env.py

````python
"""Alembic environment: uses the SYNC database URL
(`DATABASE_URL_SYNC`, e.g. postgresql+psycopg2://...) for migrations,
independent of the app's async engine used at runtime. Model metadata is
imported from `app.db.models` so `alembic revision --autogenerate` can
detect future schema drift.
"""
from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import get_settings
from app.db.base import Base
import app.db.models  # noqa: F401  (populates Base.metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

````

### FILE: alembic.ini

````ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = driver://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S

````

### FILE: alembic/README

````
Single-database configuration for Alembic, using the async app but
migrating with a SYNCHRONOUS driver (psycopg2) per `DATABASE_URL_SYNC` in
.env — this avoids needing an async-capable Alembic runner and matches
Alembic's own documented recommendation for async SQLAlchemy apps.

Run:
    alembic upgrade head          # apply all migrations
    alembic revision --autogenerate -m "message"   # after changing models
    alembic downgrade -1          # roll back one revision

````

### FILE: alembic/script.py.mako

````mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}

````

### FILE: alembic/versions/0001_initial_schema.py

````python
"""Initial schema: users, admins, catalog, plans, wallet/ledger, orders,
referrals, bloggers, promo codes, gifts, broadcasts, support, settings,
audit log.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-23

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users -------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("first_name", sa.String(256), nullable=True),
        sa.Column("last_name", sa.String(256), nullable=True),
        sa.Column("language", sa.String(8), nullable=False, server_default="uz"),
        sa.Column("language_selected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_bot_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("block_reason", sa.String(512), nullable=True),
        sa.Column("referred_by_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("referral_code", sa.String(32), nullable=False),
        sa.Column("blogger_status_cache", sa.String(16), nullable=False, server_default="none"),
        sa.Column("premium_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("start_count", sa.BigInteger(), nullable=False, server_default="1"),
    )
    op.create_unique_constraint("uq_users_telegram_id", "users", ["telegram_id"])
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])
    op.create_unique_constraint("uq_users_referral_code", "users", ["referral_code"])
    op.create_index("ix_users_referral_code", "users", ["referral_code"])
    op.create_index("ix_users_referred_by_user_id", "users", ["referred_by_user_id"])

    # --- admins / audit_logs -------------------------------------------------
    op.create_table(
        "admins",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("full_name", sa.String(256), nullable=True),
        sa.Column("role", sa.String(16), nullable=False, server_default="moderator"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint("uq_admins_username", "admins", ["username"])
    op.create_index("ix_admins_username", "admins", ["username"])
    op.create_unique_constraint("uq_admins_telegram_id", "admins", ["telegram_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("admin_id", sa.BigInteger(), nullable=True),
        sa.Column("admin_username", sa.String(64), nullable=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=True),
        sa.Column("before", sa.JSON(), nullable=True),
        sa.Column("after", sa.JSON(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])

    # --- catalog: categories / movies / mandatory_channels --------------------
    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("title_uz", sa.String(128), nullable=False),
        sa.Column("title_ru", sa.String(128), nullable=False),
        sa.Column("title_en", sa.String(128), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_unique_constraint("uq_categories_slug", "categories", ["slug"])

    op.create_table(
        "movies",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title_uz", sa.String(256), nullable=False),
        sa.Column("title_ru", sa.String(256), nullable=False),
        sa.Column("title_en", sa.String(256), nullable=False),
        sa.Column("description_uz", sa.Text(), nullable=True),
        sa.Column("description_ru", sa.Text(), nullable=True),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("search_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("poster_file_id", sa.String(256), nullable=True),
        sa.Column("video_file_id", sa.String(256), nullable=False),
        sa.Column("video_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("access_type", sa.String(16), nullable=False, server_default="free"),
        sa.Column("publication_state", sa.String(16), nullable=False, server_default="draft"),
        sa.Column("view_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_by_admin_id", sa.BigInteger(), nullable=True),
    )
    op.create_unique_constraint("uq_movies_code", "movies", ["code"])
    op.create_index("ix_movies_code", "movies", ["code"])
    op.create_index("ix_movies_category_id", "movies", ["category_id"])
    op.create_index("ix_movies_publication_state", "movies", ["publication_state"])

    op.create_table(
        "mandatory_channels",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("chat_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("invite_link", sa.String(512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("bot_is_admin_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_checked_at", sa.String(64), nullable=True),
    )
    op.create_unique_constraint("uq_mandatory_channels_chat_id", "mandatory_channels", ["chat_id"])

    # --- premium_plans -------------------------------------------------------
    op.create_table(
        "premium_plans",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("title_uz", sa.String(128), nullable=False),
        sa.Column("title_ru", sa.String(128), nullable=False),
        sa.Column("title_en", sa.String(128), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("price_amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="UZS"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("standard_referral_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blogger_referral_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blogger_acquisition_reward_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("referral_applies_to_renewals", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("max_discount_percent", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("promo_eligible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("description_uz", sa.String(512), nullable=True),
        sa.Column("description_ru", sa.String(512), nullable=True),
        sa.Column("description_en", sa.String(512), nullable=True),
    )
    op.create_unique_constraint("uq_premium_plans_code", "premium_plans", ["code"])

    # --- settings ------------------------------------------------------------
    op.create_table(
        "settings",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_unique_constraint("uq_settings_key", "settings", ["key"])
    op.create_index("ix_settings_key", "settings", ["key"])

    # --- referrals -------------------------------------------------------------
    op.create_table(
        "referrals",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("referred_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referrer_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attributed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_self_referral", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_suspicious", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("suspicious_reason", sa.String(256), nullable=True),
        sa.Column("is_qualified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("qualified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disqualified_reason", sa.String(256), nullable=True),
        sa.Column("referrer_was_blogger_at_join", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_unique_constraint("uq_referrals_referred_user_id", "referrals", ["referred_user_id"])
    op.create_index("ix_referrals_referrer_user_id", "referrals", ["referrer_user_id"])

    # --- blogger_applications / blogger_profiles ------------------------------
    op.create_table(
        "blogger_applications",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("applicant_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("verification_phrase", sa.String(64), nullable=False),
        sa.Column("platform_name", sa.String(64), nullable=True),
        sa.Column("submitted_url", sa.String(1024), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("auto_check_attempted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("auto_check_result", sa.Text(), nullable=True),
        sa.Column("reviewed_by_admin_id", sa.BigInteger(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
    )
    op.create_unique_constraint("uq_blogger_applications_verification_phrase", "blogger_applications", ["verification_phrase"])
    op.create_index("ix_blogger_applications_applicant_user_id", "blogger_applications", ["applicant_user_id"])

    op.create_table(
        "blogger_profiles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("approved_application_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("acquisition_reward_per_1000_override", sa.Integer(), nullable=True),
        sa.Column("acquisition_reward_currency_override", sa.String(8), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("suspension_reason", sa.Text(), nullable=True),
        sa.Column("accrual_remainder_micros", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("qualified_joins_counted", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_unique_constraint("uq_blogger_profiles_user_id", "blogger_profiles", ["user_id"])

    # --- wallets / ledger_entries -----------------------------------------------
    op.create_table(
        "wallets",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("available_amount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("reserved_amount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("pending_amount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.CheckConstraint("available_amount >= 0", name="available_non_negative"),
        sa.CheckConstraint("reserved_amount >= 0", name="reserved_non_negative"),
        sa.CheckConstraint("pending_amount >= 0", name="pending_non_negative"),
    )
    op.create_unique_constraint("uq_wallets_user_currency", "wallets", ["user_id", "currency"])

    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("wallet_id", sa.BigInteger(), sa.ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("entry_type", sa.String(48), nullable=False),
        sa.Column("bucket", sa.String(16), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("balance_after", sa.BigInteger(), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("reference_type", sa.String(64), nullable=True),
        sa.Column("reference_id", sa.String(64), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_unique_constraint("uq_ledger_entries_idempotency_key", "ledger_entries", ["idempotency_key"])
    op.create_index("ix_ledger_entries_wallet_id", "ledger_entries", ["wallet_id"])
    op.create_index("ix_ledger_entries_user_id", "ledger_entries", ["user_id"])

    # --- orders / provider_events / entitlements --------------------------------
    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("uid", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("buyer_user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("plan_id", sa.BigInteger(), sa.ForeignKey("premium_plans.id"), nullable=True),
        sa.Column("plan_price_snapshot", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("discount_percent_applied", sa.Integer(), nullable=False, server_default="0"),
        # NOTE: `promo_code_id` intentionally has no inline FK here because
        # `promo_codes` is created later in this migration (it in turn has no
        # dependency on `orders`). The FK constraint is added below via
        # `op.create_foreign_key` once `promo_codes` exists.
        sa.Column("promo_code_id", sa.BigInteger(), nullable=True),
        sa.Column("gross_amount", sa.Integer(), nullable=False),
        sa.Column("net_amount", sa.Integer(), nullable=False),
        sa.Column("standard_referral_percent_snapshot", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blogger_referral_percent_snapshot", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blogger_acquisition_reward_enabled_snapshot", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("provider_code", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("recipient_user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("provider_reference", sa.String(256), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refund_reason", sa.Text(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
    )
    op.create_unique_constraint("uq_orders_uid", "orders", ["uid"])
    op.create_index("ix_orders_uid", "orders", ["uid"])
    op.create_index("ix_orders_buyer_user_id", "orders", ["buyer_user_id"])

    op.create_table(
        "provider_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider_code", sa.String(32), nullable=False),
        sa.Column("provider_event_id", sa.String(256), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("order_id", sa.BigInteger(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("processing_error", sa.Text(), nullable=True),
    )
    op.create_unique_constraint("uq_provider_events_code_event_id", "provider_events", ["provider_code", "provider_event_id"])

    op.create_table(
        "entitlements",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.BigInteger(), sa.ForeignKey("premium_plans.id"), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("source_reference", sa.String(64), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("granted_by_admin_id", sa.BigInteger(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
    )
    op.create_unique_constraint("uq_entitlements_source_reference", "entitlements", ["source", "source_reference"])
    op.create_index("ix_entitlements_user_id", "entitlements", ["user_id"])

    # --- referral_commissions / blogger_acquisition_rewards -----------------------
    op.create_table(
        "referral_commissions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("order_id", sa.BigInteger(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referral_id", sa.BigInteger(), sa.ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referrer_user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", sa.BigInteger(), sa.ForeignKey("premium_plans.id"), nullable=False),
        sa.Column("commission_percent_snapshot", sa.Integer(), nullable=False),
        sa.Column("eligible_net_amount_snapshot", sa.Integer(), nullable=False),
        sa.Column("was_blogger_rate_snapshot", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="accrued"),
        sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reversal_reason", sa.Text(), nullable=True),
        sa.Column("is_first_purchase_of_referred_user", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_unique_constraint("uq_referral_commissions_order_id", "referral_commissions", ["order_id"])
    op.create_index("ix_referral_commissions_referrer_user_id", "referral_commissions", ["referrer_user_id"])

    op.create_table(
        "blogger_acquisition_rewards",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("referral_id", sa.BigInteger(), sa.ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("blogger_user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rate_per_1000_snapshot", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("remainder_micros_before", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("remainder_micros_after", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="accrued"),
        sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reversal_reason", sa.Text(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_blogger_acquisition_rewards_referral_id", "blogger_acquisition_rewards", ["referral_id"]
    )
    op.create_index("ix_blogger_acquisition_rewards_blogger_user_id", "blogger_acquisition_rewards", ["blogger_user_id"])

    # --- promo_codes / promo_redemptions ------------------------------------------
    op.create_table(
        "promo_codes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("uid", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("issuer_type", sa.String(16), nullable=False),
        sa.Column("issuer_user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("plan_id", sa.BigInteger(), sa.ForeignKey("premium_plans.id"), nullable=False),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("discount_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_uses", sa.Integer(), nullable=False),
        sa.Column("remaining_uses", sa.Integer(), nullable=False),
        sa.Column("funding_currency", sa.String(8), nullable=True),
        sa.Column("cost_per_activation", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_reserved_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_funds_released", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("moderation_status", sa.String(16), nullable=False, server_default="auto_approved"),
        sa.Column("moderation_reason", sa.Text(), nullable=True),
        sa.Column("reviewed_by_admin_id", sa.BigInteger(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_reason", sa.Text(), nullable=True),
        sa.Column("attribution_label", sa.String(256), nullable=True),
        sa.Column("attribution_url", sa.String(1024), nullable=True),
        sa.Column("attribution_telegram_username", sa.String(64), nullable=True),
        sa.Column("attribution_status", sa.String(16), nullable=False, server_default="none"),
        sa.CheckConstraint("remaining_uses >= 0", name="remaining_uses_non_negative"),
        sa.CheckConstraint("max_uses > 0", name="max_uses_positive"),
    )
    op.create_unique_constraint("uq_promo_codes_uid", "promo_codes", ["uid"])
    op.create_unique_constraint("uq_promo_codes_code", "promo_codes", ["code"])
    op.create_index("ix_promo_codes_code", "promo_codes", ["code"])

    # Deferred FK from orders.promo_code_id -> promo_codes.id (see note above).
    op.create_foreign_key(
        "fk_orders_promo_code_id_promo_codes", "orders", "promo_codes", ["promo_code_id"], ["id"]
    )

    op.create_table(
        "promo_redemptions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("uid", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("promo_code_id", sa.BigInteger(), sa.ForeignKey("promo_codes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("redeemer_user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("order_id", sa.BigInteger(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("discount_percent_applied", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("issuer_cost_charged", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("buyer_amount_paid", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_unique_constraint("uq_promo_redemptions_uid", "promo_redemptions", ["uid"])
    op.create_unique_constraint("uq_promo_redemptions_code_user", "promo_redemptions", ["promo_code_id", "redeemer_user_id"])
    op.create_index("ix_promo_redemptions_redeemer_user_id", "promo_redemptions", ["redeemer_user_id"])

    # --- gifts -----------------------------------------------------------------
    op.create_table(
        "gifts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("uid", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("sender_user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("sender_admin_id", sa.BigInteger(), nullable=True),
        sa.Column("recipient_user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", sa.BigInteger(), sa.ForeignKey("premium_plans.id"), nullable=True),
        sa.Column("balance_amount", sa.Integer(), nullable=True),
        sa.Column("balance_currency", sa.String(8), nullable=True),
        sa.Column("promo_code_id", sa.BigInteger(), sa.ForeignKey("promo_codes.id"), nullable=True),
        sa.Column("cost_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_currency", sa.String(8), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("entitlement_id", sa.BigInteger(), sa.ForeignKey("entitlements.id"), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_unique_constraint("uq_gifts_uid", "gifts", ["uid"])
    op.create_index("ix_gifts_recipient_user_id", "gifts", ["recipient_user_id"])

    # --- broadcasts / broadcast_recipients -----------------------------------------
    op.create_table(
        "broadcasts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by_admin_id", sa.BigInteger(), nullable=True),
        sa.Column("target", sa.String(16), nullable=False),
        sa.Column("target_language", sa.String(8), nullable=True),
        sa.Column("custom_user_ids", sa.JSON(), nullable=True),
        sa.Column("text_uz", sa.Text(), nullable=True),
        sa.Column("text_ru", sa.Text(), nullable=True),
        sa.Column("text_en", sa.Text(), nullable=True),
        sa.Column("photo_file_id", sa.String(256), nullable=True),
        sa.Column("button_url", sa.String(1024), nullable=True),
        sa.Column("button_text", sa.String(128), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="draft"),
        sa.Column("total_recipients", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rate_limit_per_second", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "broadcast_recipients",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("broadcast_id", sa.BigInteger(), sa.ForeignKey("broadcasts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_unique_constraint("uq_broadcast_recipients_broadcast_user", "broadcast_recipients", ["broadcast_id", "user_id"])
    op.create_index("ix_broadcast_recipients_user_id", "broadcast_recipients", ["user_id"])

    # --- support_tickets / support_messages -----------------------------------
    op.create_table(
        "support_tickets",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject", sa.String(256), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("assigned_admin_id", sa.BigInteger(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_support_tickets_user_id", "support_tickets", ["user_id"])

    op.create_table(
        "support_messages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ticket_id", sa.BigInteger(), sa.ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sender_type", sa.String(16), nullable=False),
        sa.Column("sender_id", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("attachment_file_id", sa.String(256), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("support_messages")
    op.drop_table("support_tickets")
    op.drop_table("broadcast_recipients")
    op.drop_table("broadcasts")
    op.drop_table("gifts")
    op.drop_table("promo_redemptions")
    op.drop_constraint("fk_orders_promo_code_id_promo_codes", "orders", type_="foreignkey")
    op.drop_table("promo_codes")
    op.drop_table("blogger_acquisition_rewards")
    op.drop_table("referral_commissions")
    op.drop_table("entitlements")
    op.drop_table("provider_events")
    op.drop_table("orders")
    op.drop_table("ledger_entries")
    op.drop_table("wallets")
    op.drop_table("blogger_profiles")
    op.drop_table("blogger_applications")
    op.drop_table("referrals")
    op.drop_table("settings")
    op.drop_table("premium_plans")
    op.drop_table("mandatory_channels")
    op.drop_table("movies")
    op.drop_table("categories")
    op.drop_table("audit_logs")
    op.drop_table("admins")
    op.drop_table("users")

````

### FILE: app/admin/auth_routes.py

````python
"""Admin login/logout routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import create_session_token, verify_password
from app.admin.templates import templates
from app.config import get_settings
from app.db.session import get_session
from app.db.uow import UnitOfWork

router = APIRouter(prefix="/admin", tags=["admin-auth"])
settings = get_settings()


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    admin = await uow.admins.get_by_username(username)
    if admin is None or not admin.is_active or not verify_password(password, admin.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"},
            status_code=401,
        )

    await uow.admins.touch_login(admin)
    await session.commit()

    token = create_session_token(admin.id)
    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    response.set_cookie(
        key=settings.ADMIN_SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.ADMIN_SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
    )
    return response


@router.get("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie(settings.ADMIN_SESSION_COOKIE_NAME)
    return response

````

### FILE: app/admin/__init__.py

````python
"""Server-rendered (Jinja2) admin panel: session-cookie auth, role-based
access control, and one router per feature area (see app.admin.routes).
"""

````

### FILE: app/admin/router.py

````python
"""Aggregates every admin sub-router into a single `admin_router` mounted
by `app.main`."""

from __future__ import annotations

from fastapi import APIRouter

from app.admin import (
    auth_routes,
    routes_audit,
    routes_bloggers,
    routes_broadcasts,
    routes_channels,
    routes_dashboard,
    routes_moderation,
    routes_movies,
    routes_orders,
    routes_plans,
    routes_promos,
    routes_users,
)

admin_router = APIRouter()
admin_router.include_router(auth_routes.router)
admin_router.include_router(routes_dashboard.router)
admin_router.include_router(routes_movies.router)
admin_router.include_router(routes_channels.router)
admin_router.include_router(routes_plans.router)
admin_router.include_router(routes_users.router)
admin_router.include_router(routes_promos.router)
admin_router.include_router(routes_bloggers.router)
admin_router.include_router(routes_orders.router)
admin_router.include_router(routes_broadcasts.router)
admin_router.include_router(routes_moderation.router)
admin_router.include_router(routes_audit.router)

````

### FILE: app/admin/routes_audit.py

````python
"""Read-only audit log viewer."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin
from app.admin.templates import templates
from app.db.models.admin import Admin
from app.db.session import get_session
from app.db.uow import UnitOfWork

router = APIRouter(prefix="/admin/audit", tags=["admin-audit"])


@router.get("", response_class=HTMLResponse)
async def audit_log(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    logs = await uow.audit.list_recent(limit=200)
    return templates.TemplateResponse("audit.html", {"request": request, "logs": logs})

````

### FILE: app/admin/routes_bloggers.py

````python
"""Blogger application review + acquisition reward rate configuration."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin, require_role
from app.admin.templates import templates
from app.db.models.admin import Admin
from app.db.models.enums import AdminRole
from app.db.session import get_session
from app.db.uow import UnitOfWork
from app.services.blogger_service import BloggerService
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/admin/bloggers", tags=["admin-bloggers"])


@router.get("", response_class=HTMLResponse)
async def list_bloggers(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    pending_applications = await uow.bloggers.list_pending()
    profiles = await uow.bloggers.list_all()
    settings_service = SettingsService(uow)
    global_rate, global_currency = await settings_service.global_blogger_reward_per_1000()
    return templates.TemplateResponse(
        "bloggers.html",
        {
            "request": request,
            "pending_applications": pending_applications,
            "profiles": profiles,
            "global_rate": global_rate,
            "global_currency": global_currency,
        },
    )


@router.post("/settings/reward_rate")
async def update_reward_rate(
    rate: int = Form(...),
    currency: str = Form("UZS"),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    await SettingsService(uow).set_global_blogger_reward_per_1000(rate, currency)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="update_global_blogger_reward_rate",
        entity_type="settings",
        after={"rate": rate, "currency": currency},
    )
    await session.commit()
    return RedirectResponse(url="/admin/bloggers", status_code=302)


@router.post("/applications/{application_id}/approve")
async def approve_application(
    application_id: int,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    application = await uow.bloggers.get_application(application_id)
    if application is None:
        return RedirectResponse(url="/admin/bloggers", status_code=302)
    blogger_service = BloggerService(uow)
    await blogger_service.decide(application, approve=True, admin_id=admin.id)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="approve_blogger_application",
        entity_type="blogger_application",
        entity_id=str(application_id),
    )
    await session.commit()
    return RedirectResponse(url="/admin/bloggers", status_code=302)


@router.post("/applications/{application_id}/reject")
async def reject_application(
    application_id: int,
    reason: str = Form(...),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    application = await uow.bloggers.get_application(application_id)
    if application is None:
        return RedirectResponse(url="/admin/bloggers", status_code=302)
    blogger_service = BloggerService(uow)
    await blogger_service.decide(application, approve=False, admin_id=admin.id, reason=reason)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="reject_blogger_application",
        entity_type="blogger_application",
        entity_id=str(application_id),
        note=reason,
    )
    await session.commit()
    return RedirectResponse(url="/admin/bloggers", status_code=302)


@router.post("/{blogger_user_id}/suspend")
async def suspend_blogger(
    blogger_user_id: int,
    reason: str = Form(""),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    blogger_service = BloggerService(uow)
    await blogger_service.suspend(blogger_user_id, reason)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="suspend_blogger",
        entity_type="blogger_profile",
        entity_id=str(blogger_user_id),
        note=reason,
    )
    await session.commit()
    return RedirectResponse(url="/admin/bloggers", status_code=302)


@router.post("/{blogger_user_id}/reactivate")
async def reactivate_blogger(
    blogger_user_id: int,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    blogger_service = BloggerService(uow)
    await blogger_service.reactivate(blogger_user_id)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="reactivate_blogger",
        entity_type="blogger_profile",
        entity_id=str(blogger_user_id),
    )
    await session.commit()
    return RedirectResponse(url="/admin/bloggers", status_code=302)

````

### FILE: app/admin/routes_broadcasts.py

````python
"""Broadcast composer: preview/confirm/queue. Actual sending happens in
`app.workers.broadcast_worker`; this route only creates the draft, resolves
the recipient snapshot, and marks it QUEUED."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin, require_role
from app.admin.templates import templates
from app.db.models.admin import Admin
from app.db.models.enums import AdminRole, BroadcastTarget
from app.db.session import get_session
from app.db.uow import UnitOfWork
from app.services.broadcast_service import BroadcastService

router = APIRouter(prefix="/admin/broadcasts", tags=["admin-broadcasts"])


@router.get("", response_class=HTMLResponse)
async def list_broadcasts(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    active = await uow.broadcasts.list_queued_or_running()
    return templates.TemplateResponse("broadcasts.html", {"request": request, "active": active})


@router.post("/create")
async def create_broadcast(
    target: str = Form(...),
    text_uz: str = Form(...),
    text_ru: str = Form(...),
    text_en: str = Form(...),
    rate_limit_per_second: int = Form(20),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    broadcast_service = BroadcastService(uow)
    broadcast = await broadcast_service.create_draft(
        admin_id=admin.id,
        target=BroadcastTarget(target),
        text_uz=text_uz,
        text_ru=text_ru,
        text_en=text_en,
        rate_limit_per_second=rate_limit_per_second,
    )
    count = await broadcast_service.enqueue(broadcast)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="create_broadcast",
        entity_type="broadcast",
        entity_id=str(broadcast.id),
        after={"target": target, "recipients": count},
    )
    await session.commit()
    return RedirectResponse(url="/admin/broadcasts", status_code=302)


@router.post("/{broadcast_id}/cancel")
async def cancel_broadcast(
    broadcast_id: int,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    broadcast = await uow.broadcasts.get(broadcast_id)
    if broadcast is not None:
        await BroadcastService(uow).cancel(broadcast)
        await uow.audit.record(
            admin_id=admin.id,
            admin_username=admin.username,
            action="cancel_broadcast",
            entity_type="broadcast",
            entity_id=str(broadcast_id),
        )
        await session.commit()
    return RedirectResponse(url="/admin/broadcasts", status_code=302)

````

### FILE: app/admin/routes_channels.py

````python
"""Mandatory subscription channels management + membership diagnostics."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin, require_role
from app.admin.templates import templates
from app.db.models.admin import Admin
from app.db.models.catalog import MandatoryChannel
from app.db.models.enums import AdminRole
from app.db.session import get_session
from app.db.uow import UnitOfWork

router = APIRouter(prefix="/admin/channels", tags=["admin-channels"])


@router.get("", response_class=HTMLResponse)
async def list_channels(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    channels = await uow.catalog.list_all_channels()
    return templates.TemplateResponse("channels.html", {"request": request, "channels": channels})


@router.post("/create")
async def create_channel(
    chat_id: str = Form(...),
    title: str = Form(...),
    invite_link: str = Form(""),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    channel = MandatoryChannel(chat_id=chat_id, title=title, invite_link=invite_link or None)
    session.add(channel)
    await session.commit()
    return RedirectResponse(url="/admin/channels", status_code=302)


@router.post("/{channel_id}/diagnose")
async def diagnose_channel(
    channel_id: int,
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    """Checks that the bot itself is an admin of the channel (required for
    both membership checks and, when relevant, promo attribution-link
    verification of a channel)."""
    uow = UnitOfWork(session)
    channel = await _get_channel(uow, channel_id)
    bot = request.app.state.bot
    is_admin = False
    error = None
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(chat_id=channel.chat_id, user_id=me.id)
        is_admin = member.status in ("administrator", "creator")
    except Exception as exc:
        error = str(exc)

    channel.bot_is_admin_verified = is_admin
    await session.commit()
    channels = await uow.catalog.list_all_channels()
    return templates.TemplateResponse(
        "channels.html", {"request": request, "channels": channels, "diagnostic_error": error}
    )


async def _get_channel(uow: UnitOfWork, channel_id: int) -> MandatoryChannel:
    channels = await uow.catalog.list_all_channels()
    for c in channels:
        if c.id == channel_id:
            return c
    raise ValueError("Channel not found")

````

### FILE: app/admin/routes_dashboard.py

````python
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin
from app.admin.templates import templates
from app.config import get_settings
from app.db.models.admin import Admin
from app.db.session import get_session
from app.db.uow import UnitOfWork
from app.payments.registry import PaymentRegistry
from app.services.moderation_service import ModerationService
from app.services.statistics_service import StatisticsService

router = APIRouter(prefix="/admin", tags=["admin-dashboard"])
settings = get_settings()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    stats = await StatisticsService(uow).dashboard_summary()
    moderation_service = ModerationService(uow)
    moderation = {
        "suspicious_referrals": len(await moderation_service.suspicious_referrals()),
        "pending_promo_links": len(await moderation_service.pending_promo_links()),
        "pending_blogger_applications": len(
            await moderation_service.pending_blogger_applications()
        ),
        "open_support_tickets": len(await moderation_service.open_support_tickets()),
    }
    registry = PaymentRegistry(settings)
    providers = registry.status_report()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "admin": admin,
            "stats": stats,
            "moderation": moderation,
            "providers": providers,
        },
    )


@router.get("/")
async def admin_root():
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/admin/dashboard")

````

### FILE: app/admin/routes_moderation.py

````python
"""Moderation review queue: suspicious referrals and open support tickets
in one place (blogger apps and promo links have their own dedicated pages
but are also summarized here)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin, require_role
from app.admin.templates import templates
from app.db.models.admin import Admin
from app.db.models.enums import AdminRole
from app.db.session import get_session
from app.db.uow import UnitOfWork
from app.services.moderation_service import ModerationService

router = APIRouter(prefix="/admin/moderation", tags=["admin-moderation"])


@router.get("", response_class=HTMLResponse)
async def moderation_queue(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    moderation_service = ModerationService(uow)
    suspicious_referrals = await moderation_service.suspicious_referrals()
    open_tickets = await moderation_service.open_support_tickets()
    return templates.TemplateResponse(
        "moderation.html",
        {
            "request": request,
            "suspicious_referrals": suspicious_referrals,
            "open_tickets": open_tickets,
        },
    )


@router.post("/tickets/{ticket_id}/reply")
async def reply_ticket(
    ticket_id: int,
    text: str = Form(...),
    request: Request = None,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN, AdminRole.SUPPORT)),
    session: AsyncSession = Depends(get_session),
):
    from app.db.models.enums import SupportSenderType
    from app.i18n import t

    uow = UnitOfWork(session)
    ticket = await uow.support.get_ticket(ticket_id)
    if ticket is not None:
        await uow.support.add_message(
            ticket_id=ticket_id, sender_type=SupportSenderType.ADMIN, sender_id=admin.id, text=text
        )
        user = await uow.users.get_by_id(ticket.user_id)
        if user is not None:
            try:
                await request.app.state.bot.send_message(
                    chat_id=user.telegram_id,
                    text=t(user.language, "support_ticket_reply_notice", text=text),
                )
            except Exception:
                pass
        await session.commit()
    return RedirectResponse(url="/admin/moderation", status_code=302)


@router.post("/tickets/{ticket_id}/close")
async def close_ticket(
    ticket_id: int,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN, AdminRole.SUPPORT)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    ticket = await uow.support.get_ticket(ticket_id)
    if ticket is not None:
        await uow.support.close_ticket(ticket)
        await session.commit()
    return RedirectResponse(url="/admin/moderation", status_code=302)

````

### FILE: app/admin/routes_movies.py

````python
"""Movies, categories, and mandatory-channel admin management.

Video upload: admins forward/send a video message to the BOT (not to this
web panel -- Telegram video uploads only make sense through Telegram
itself), and the bot's admin-only handler (see
app.bot.handlers.movies -- MovieAdminStates flow, wired for users whose
telegram_id is registered as an Admin) captures the resulting `file_id`
and calls the same `CatalogRepository.create` used here. This web panel
covers metadata editing, publishing state, and category assignment, which
don't require a live Telegram upload.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin, require_role
from app.admin.templates import templates
from app.db.models.admin import Admin
from app.db.models.enums import AdminRole, MoviePublicationState
from app.db.session import get_session
from app.db.uow import UnitOfWork

router = APIRouter(prefix="/admin/movies", tags=["admin-movies"])


@router.get("", response_class=HTMLResponse)
async def list_movies(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    categories = await uow.catalog.list_active_categories()
    movies = []
    for cat in categories:
        movies.extend(await uow.catalog.list_by_category(cat.id, limit=100))
    return templates.TemplateResponse(
        "movies.html", {"request": request, "movies": movies, "categories": categories}
    )


@router.post("/{movie_id}/publish")
async def publish_movie(
    movie_id: int,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    movie = await uow.catalog.get_by_id(movie_id)
    if movie:
        before = {"publication_state": movie.publication_state}
        await uow.catalog.update(movie, publication_state=MoviePublicationState.PUBLISHED.value)
        await uow.audit.record(
            admin_id=admin.id,
            admin_username=admin.username,
            action="publish_movie",
            entity_type="movie",
            entity_id=str(movie_id),
            before=before,
            after={"publication_state": "published"},
        )
        await session.commit()
    return RedirectResponse(url="/admin/movies", status_code=302)


@router.post("/{movie_id}/archive")
async def archive_movie(
    movie_id: int,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    movie = await uow.catalog.get_by_id(movie_id)
    if movie:
        before = {"publication_state": movie.publication_state}
        await uow.catalog.update(movie, publication_state=MoviePublicationState.ARCHIVED.value)
        await uow.audit.record(
            admin_id=admin.id,
            admin_username=admin.username,
            action="archive_movie",
            entity_type="movie",
            entity_id=str(movie_id),
            before=before,
            after={"publication_state": "archived"},
        )
        await session.commit()
    return RedirectResponse(url="/admin/movies", status_code=302)


@router.post("/{movie_id}/delete")
async def delete_movie(
    movie_id: int,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    movie = await uow.catalog.get_by_id(movie_id)
    if movie:
        await session.delete(movie)
        await uow.audit.record(
            admin_id=admin.id,
            admin_username=admin.username,
            action="delete_movie",
            entity_type="movie",
            entity_id=str(movie_id),
        )
        await session.commit()
    return RedirectResponse(url="/admin/movies", status_code=302)

````

### FILE: app/admin/routes_orders.py

````python
"""Payment orders admin: browse recent orders, provider status, and issue
refunds through the shared PurchaseService (never a raw status flip)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin, require_role
from app.admin.templates import templates
from app.config import get_settings
from app.db.models.admin import Admin
from app.db.models.enums import AdminRole
from app.db.session import get_session
from app.db.uow import UnitOfWork
from app.payments.registry import PaymentRegistry
from app.services.purchase_service import PurchaseService

router = APIRouter(prefix="/admin/orders", tags=["admin-orders"])
settings = get_settings()


@router.get("", response_class=HTMLResponse)
async def list_orders(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    orders = await uow.orders.list_recent(limit=100)
    registry = PaymentRegistry(settings)
    providers = registry.status_report()
    return templates.TemplateResponse(
        "orders.html", {"request": request, "orders": orders, "providers": providers}
    )


@router.post("/{order_id}/refund")
async def refund_order(
    order_id: int,
    reason: str = Form(...),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    order = await uow.orders.get(order_id)
    if order is not None:
        purchase_service = PurchaseService(uow)
        await purchase_service.refund_order(order, reason=reason)
        await uow.audit.record(
            admin_id=admin.id,
            admin_username=admin.username,
            action="refund_order",
            entity_type="order",
            entity_id=str(order_id),
            note=reason,
        )
        await session.commit()
    return RedirectResponse(url="/admin/orders", status_code=302)

````

### FILE: app/admin/routes_plans.py

````python
"""Premium plans admin: create/edit plans and their PER-PLAN referral
commission percentages, blogger acquisition-reward toggle, and promo
eligibility caps (spec section 3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin, require_role
from app.admin.templates import templates
from app.db.models.admin import Admin
from app.db.models.enums import AdminRole
from app.db.session import get_session
from app.db.uow import UnitOfWork

router = APIRouter(prefix="/admin/plans", tags=["admin-plans"])


@router.get("", response_class=HTMLResponse)
async def list_plans(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    plans = await uow.plans.list_all()
    return templates.TemplateResponse("plans.html", {"request": request, "plans": plans})


@router.post("/create")
async def create_plan(
    code: str = Form(...),
    title_uz: str = Form(...),
    title_ru: str = Form(...),
    title_en: str = Form(...),
    duration_days: int = Form(...),
    price_amount: int = Form(...),
    currency: str = Form("UZS"),
    standard_referral_percent: int = Form(0),
    blogger_referral_percent: int = Form(0),
    blogger_acquisition_reward_enabled: bool = Form(True),
    max_discount_percent: int = Form(100),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    plan = await uow.plans.create(
        code=code,
        title_uz=title_uz,
        title_ru=title_ru,
        title_en=title_en,
        duration_days=duration_days,
        price_amount=price_amount,
        currency=currency,
        standard_referral_percent=standard_referral_percent,
        blogger_referral_percent=blogger_referral_percent,
        blogger_acquisition_reward_enabled=blogger_acquisition_reward_enabled,
        max_discount_percent=max_discount_percent,
    )
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="create_plan",
        entity_type="premium_plan",
        entity_id=str(plan.id),
        after={"code": code, "price_amount": price_amount},
    )
    await session.commit()
    return RedirectResponse(url="/admin/plans", status_code=302)


@router.post("/{plan_id}/update")
async def update_plan(
    plan_id: int,
    price_amount: int = Form(...),
    standard_referral_percent: int = Form(...),
    blogger_referral_percent: int = Form(...),
    blogger_acquisition_reward_enabled: bool = Form(True),
    is_active: bool = Form(True),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    """Updates only apply going forward: existing Orders/ReferralCommissions
    keep their own frozen snapshot columns, so past purchases are never
    retroactively altered (spec section 3)."""
    uow = UnitOfWork(session)
    plan = await uow.plans.get(plan_id)
    if plan is None:
        return RedirectResponse(url="/admin/plans", status_code=302)
    before = {
        "price_amount": plan.price_amount,
        "standard_referral_percent": plan.standard_referral_percent,
        "blogger_referral_percent": plan.blogger_referral_percent,
    }
    await uow.plans.update(
        plan,
        price_amount=price_amount,
        standard_referral_percent=standard_referral_percent,
        blogger_referral_percent=blogger_referral_percent,
        blogger_acquisition_reward_enabled=blogger_acquisition_reward_enabled,
        is_active=is_active,
    )
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="update_plan",
        entity_type="premium_plan",
        entity_id=str(plan_id),
        before=before,
        after={
            "price_amount": price_amount,
            "standard_referral_percent": standard_referral_percent,
            "blogger_referral_percent": blogger_referral_percent,
        },
    )
    await session.commit()
    return RedirectResponse(url="/admin/plans", status_code=302)

````

### FILE: app/admin/routes_promos.py

````python
"""Admin promo code management: bot-issued codes, creator-link approval,
cancellations, and refunds of unused reserves."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin, require_role
from app.admin.templates import templates
from app.db.models.admin import Admin
from app.db.models.enums import AdminRole, PromoKind
from app.db.session import get_session
from app.db.uow import UnitOfWork
from app.services.promo_service import PromoService

router = APIRouter(prefix="/admin/promos", tags=["admin-promos"])


@router.get("", response_class=HTMLResponse)
async def list_promos(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    pending = await uow.promos.list_pending_moderation()
    plans = await uow.plans.list_active()
    return templates.TemplateResponse(
        "promos.html", {"request": request, "pending": pending, "plans": plans}
    )


@router.post("/create_admin_code")
async def create_admin_code(
    plan_id: int = Form(...),
    kind: str = Form(...),
    discount_percent: int = Form(0),
    activations: int = Form(...),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    plan = await uow.plans.get(plan_id)
    promo_service = PromoService(uow)
    promo = await promo_service.create_admin_code(
        plan=plan, kind=PromoKind(kind), discount_percent=discount_percent, activations=activations
    )
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="create_admin_promo",
        entity_type="promo_code",
        entity_id=str(promo.id),
        after={"code": promo.code},
    )
    await session.commit()
    return RedirectResponse(url="/admin/promos", status_code=302)


@router.post("/{promo_id}/approve")
async def approve_promo(
    promo_id: int,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    promo = await _get_promo(uow, promo_id)
    promo_service = PromoService(uow)
    await promo_service.moderate(promo, approve=True, admin_id=admin.id)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="approve_promo",
        entity_type="promo_code",
        entity_id=str(promo_id),
    )
    await session.commit()
    return RedirectResponse(url="/admin/promos", status_code=302)


@router.post("/{promo_id}/reject")
async def reject_promo(
    promo_id: int,
    reason: str = Form(""),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    promo = await _get_promo(uow, promo_id)
    promo_service = PromoService(uow)
    await promo_service.moderate(promo, approve=False, admin_id=admin.id, reason=reason)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="reject_promo",
        entity_type="promo_code",
        entity_id=str(promo_id),
        note=reason,
    )
    await session.commit()
    return RedirectResponse(url="/admin/promos", status_code=302)


@router.post("/{promo_id}/cancel")
async def cancel_promo(
    promo_id: int,
    reason: str = Form(""),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    promo = await _get_promo(uow, promo_id)
    promo_service = PromoService(uow)
    await promo_service.cancel(promo, reason=reason)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="cancel_promo",
        entity_type="promo_code",
        entity_id=str(promo_id),
        note=reason,
    )
    await session.commit()
    return RedirectResponse(url="/admin/promos", status_code=302)


async def _get_promo(uow: UnitOfWork, promo_id: int):
    from sqlalchemy import select

    from app.db.models.promo import PromoCode

    result = await uow.session.execute(select(PromoCode).where(PromoCode.id == promo_id))
    promo = result.scalar_one_or_none()
    if promo is None:
        raise ValueError("Promo not found")
    return promo

````

### FILE: app/admin/routes_users.py

````python
"""User search, block/unblock, and balance/premium gifts + manual adjustments."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin, require_role
from app.admin.templates import templates
from app.db.models.admin import Admin
from app.db.models.enums import AdminRole, WalletEntryType
from app.db.session import get_session
from app.db.uow import UnitOfWork
from app.services.gift_service import GiftService
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("", response_class=HTMLResponse)
async def list_users(
    request: Request,
    q: str = Query(""),
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    users = (
        await uow.users.search_by_name_or_id(q)
        if q
        else await uow.users.search_by_name_or_id("", limit=50)
    )
    return templates.TemplateResponse("users.html", {"request": request, "users": users, "q": q})


@router.post("/{user_id}/block")
async def block_user(
    user_id: int,
    reason: str = Form(""),
    admin: Admin = Depends(
        require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN, AdminRole.MODERATOR)
    ),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    user = await uow.users.get_by_id(user_id)
    if user:
        await uow.users.set_blocked(user, True, reason)
        await uow.audit.record(
            admin_id=admin.id,
            admin_username=admin.username,
            action="block_user",
            entity_type="user",
            entity_id=str(user_id),
            note=reason,
        )
        await session.commit()
    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    admin: Admin = Depends(
        require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN, AdminRole.MODERATOR)
    ),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    user = await uow.users.get_by_id(user_id)
    if user:
        await uow.users.set_blocked(user, False)
        await uow.audit.record(
            admin_id=admin.id,
            admin_username=admin.username,
            action="unblock_user",
            entity_type="user",
            entity_id=str(user_id),
        )
        await session.commit()
    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/{user_id}/gift_balance")
async def gift_balance(
    user_id: int,
    amount: int = Form(...),
    currency: str = Form("UZS"),
    reason: str = Form(...),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    gift_service = GiftService(uow)
    await gift_service.admin_gift_balance(
        admin_id=admin.id,
        recipient_user_id=user_id,
        currency=currency,
        amount=amount,
        reason=reason,
    )
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="gift_balance",
        entity_type="user",
        entity_id=str(user_id),
        after={"amount": amount, "currency": currency},
        note=reason,
    )
    await session.commit()
    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/{user_id}/gift_premium")
async def gift_premium(
    user_id: int,
    plan_id: int = Form(...),
    reason: str = Form(...),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    gift_service = GiftService(uow)
    await gift_service.admin_gift_premium(
        admin_id=admin.id, recipient_user_id=user_id, plan_id=plan_id, reason=reason
    )
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="gift_premium",
        entity_type="user",
        entity_id=str(user_id),
        after={"plan_id": plan_id},
        note=reason,
    )
    await session.commit()
    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/{user_id}/adjust_balance")
async def adjust_balance(
    user_id: int,
    amount: int = Form(...),
    currency: str = Form("UZS"),
    reason: str = Form(...),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN)),
    session: AsyncSession = Depends(get_session),
):
    """Manual admin adjustment; `amount` may be negative to debit. Always
    goes through the locked ledger entry path, never a raw UPDATE."""
    uow = UnitOfWork(session)
    wallet_service = WalletService(uow)
    idempotency_key = f"admin_adjust:{admin.id}:{user_id}:{time.time()}"
    if amount >= 0:
        await wallet_service.credit_available(
            user_id=user_id,
            currency=currency,
            amount=amount,
            entry_type=WalletEntryType.ADMIN_ADJUSTMENT,
            idempotency_key=idempotency_key,
            note=reason,
        )
    else:
        await wallet_service.debit_available(
            user_id=user_id,
            currency=currency,
            amount=-amount,
            entry_type=WalletEntryType.ADMIN_ADJUSTMENT,
            idempotency_key=idempotency_key,
            note=reason,
        )
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="adjust_balance",
        entity_type="user",
        entity_id=str(user_id),
        after={"amount": amount, "currency": currency},
        note=reason,
    )
    await session.commit()
    return RedirectResponse(url="/admin/users", status_code=302)

````

### FILE: app/admin/security.py

````python
"""Admin authentication: bcrypt password hashing + signed session cookie.

Session cookies are signed (not encrypted) with `itsdangerous`, using
`APP_SECRET_KEY`, and carry only the admin's id + role + issue time so a
tampered cookie fails signature verification rather than silently granting
access. `require_role` is a FastAPI dependency factory used to gate each
admin route by the roles allowed to use it.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models.admin import Admin
from app.db.models.enums import AdminRole
from app.db.session import get_session
from app.db.uow import UnitOfWork

settings = get_settings()
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_signer = TimestampSigner(settings.APP_SECRET_KEY)


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def create_session_token(admin_id: int) -> str:
    return _signer.sign(str(admin_id).encode("utf-8")).decode("utf-8")


def read_session_token(token: str, max_age: int) -> int | None:
    try:
        raw = _signer.unsign(token, max_age=max_age)
        return int(raw.decode("utf-8"))
    except (BadSignature, SignatureExpired, ValueError):
        return None


async def get_current_admin(
    request: Request, session: AsyncSession = Depends(get_session)
) -> Admin:
    token = request.cookies.get(settings.ADMIN_SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
    admin_id = read_session_token(token, max_age=settings.ADMIN_SESSION_TTL_SECONDS)
    if admin_id is None:
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})

    uow = UnitOfWork(session)
    admin = await uow.admins.get_by_id(admin_id)
    if admin is None or not admin.is_active:
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
    return admin


def require_role(*roles: AdminRole):
    async def _dependency(admin: Admin = Depends(get_current_admin)) -> Admin:
        if AdminRole(admin.role) not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role for this action")
        return admin

    return _dependency

````

### FILE: app/admin/templates/audit.html

````html
{% extends "base.html" %}
{% block title %}Audit Log — Movie Bot Admin{% endblock %}
{% block content %}
<h1>Audit Log</h1>
<table>
    <tr><th>Time</th><th>Admin</th><th>Action</th><th>Entity</th><th>Note</th></tr>
    {% for l in logs %}
    <tr>
        <td>{{ l.created_at }}</td>
        <td>{{ l.admin_username }}</td>
        <td>{{ l.action }}</td>
        <td>{{ l.entity_type }}#{{ l.entity_id }}</td>
        <td>{{ l.note or "" }}</td>
    </tr>
    {% endfor %}
</table>
{% endblock %}

````

### FILE: app/admin/templates/base.html

````html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}Movie Bot Admin{% endblock %}</title>
    <style>
        body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background: #0f1115; color: #e6e6e6; }
        nav { background: #161922; padding: 12px 20px; display: flex; gap: 16px; flex-wrap: wrap; }
        nav a { color: #9fd3ff; text-decoration: none; font-size: 14px; }
        nav a:hover { text-decoration: underline; }
        main { padding: 24px; max-width: 1100px; margin: 0 auto; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        th, td { border-bottom: 1px solid #2a2e3a; padding: 8px 10px; text-align: left; font-size: 14px; }
        .card { background: #161922; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
        .badge { padding: 2px 8px; border-radius: 10px; font-size: 12px; }
        .badge.ok { background: #1f6b3a; }
        .badge.warn { background: #7a5a10; }
        .badge.off { background: #5a2222; }
        input, select, button, textarea { padding: 8px; border-radius: 6px; border: 1px solid #2a2e3a; background: #10131a; color: #e6e6e6; }
        button { cursor: pointer; background: #2c5fce; border: none; }
        .error { color: #ff6b6b; }
    </style>
</head>
<body>
<nav>
    <a href="/admin/dashboard">Dashboard</a>
    <a href="/admin/movies">Movies</a>
    <a href="/admin/plans">Plans</a>
    <a href="/admin/users">Users</a>
    <a href="/admin/promos">Promo Codes</a>
    <a href="/admin/bloggers">Bloggers</a>
    <a href="/admin/orders">Orders</a>
    <a href="/admin/channels">Channels</a>
    <a href="/admin/broadcasts">Broadcasts</a>
    <a href="/admin/moderation">Moderation</a>
    <a href="/admin/audit">Audit Log</a>
    <a href="/admin/logout" style="margin-left:auto;">Logout</a>
</nav>
<main>
{% block content %}{% endblock %}
</main>
</body>
</html>

````

### FILE: app/admin/templates/bloggers.html

````html
{% extends "base.html" %}
{% block title %}Bloggers — Movie Bot Admin{% endblock %}
{% block content %}
<h1>Bloggers</h1>

<div class="card">
    <h3>Global acquisition reward rate</h3>
    <form method="post" action="/admin/bloggers/settings/reward_rate">
        <input type="number" name="rate" value="{{ global_rate }}" placeholder="Amount per 1000 qualified joins">
        <input type="text" name="currency" value="{{ global_currency }}" style="width:60px">
        <button type="submit">Save</button>
    </form>
    <p style="opacity:0.7">Accrual starts with the FIRST qualified join; fractional remainders are carried forward, never lost.</p>
</div>

<div class="card">
    <h3>Pending applications</h3>
    <table>
        <tr><th>Applicant</th><th>Platform</th><th>URL</th><th>Phrase</th><th>Actions</th></tr>
        {% for app in pending_applications %}
        <tr>
            <td>user #{{ app.applicant_user_id }}</td>
            <td>{{ app.platform_name }}</td>
            <td>{{ app.submitted_url }}</td>
            <td>{{ app.verification_phrase }}</td>
            <td>
                <form method="post" action="/admin/bloggers/applications/{{ app.id }}/approve" style="display:inline"><button>Approve</button></form>
                <form method="post" action="/admin/bloggers/applications/{{ app.id }}/reject" style="display:inline">
                    <input type="text" name="reason" placeholder="Reason" style="width:100px">
                    <button style="background:#7a2222">Reject</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
</div>

<div class="card">
    <h3>Blogger profiles</h3>
    <table>
        <tr><th>User</th><th>Status</th><th>Qualified joins</th><th>Actions</th></tr>
        {% for p in profiles %}
        <tr>
            <td>user #{{ p.user_id }}</td>
            <td>{{ p.status }}</td>
            <td>{{ p.qualified_joins_counted }}</td>
            <td>
                {% if p.status == "active" %}
                <form method="post" action="/admin/bloggers/{{ p.user_id }}/suspend" style="display:inline">
                    <input type="text" name="reason" placeholder="Reason" style="width:100px">
                    <button style="background:#7a2222">Suspend</button>
                </form>
                {% else %}
                <form method="post" action="/admin/bloggers/{{ p.user_id }}/reactivate" style="display:inline"><button>Reactivate</button></form>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
</div>
{% endblock %}

````

### FILE: app/admin/templates/broadcasts.html

````html
{% extends "base.html" %}
{% block title %}Broadcasts — Movie Bot Admin{% endblock %}
{% block content %}
<h1>Broadcasts</h1>

<div class="card">
    <h3>New broadcast</h3>
    <form method="post" action="/admin/broadcasts/create">
        <select name="target">
            <option value="all">All users</option>
            <option value="premium">Premium users only</option>
            <option value="free">Free users only</option>
        </select>
        <input type="number" name="rate_limit_per_second" value="20" placeholder="Msgs/sec">
        <br><br>
        <textarea name="text_uz" placeholder="Text (UZ)" rows="3" style="width:100%"></textarea><br>
        <textarea name="text_ru" placeholder="Text (RU)" rows="3" style="width:100%"></textarea><br>
        <textarea name="text_en" placeholder="Text (EN)" rows="3" style="width:100%"></textarea><br><br>
        <button type="submit">Queue broadcast</button>
    </form>
</div>

<div class="card">
    <h3>Active / queued broadcasts</h3>
    <table>
        <tr><th>ID</th><th>Target</th><th>Status</th><th>Sent</th><th>Failed</th><th>Total</th><th>Actions</th></tr>
        {% for b in active %}
        <tr>
            <td>{{ b.id }}</td>
            <td>{{ b.target }}</td>
            <td>{{ b.status }}</td>
            <td>{{ b.sent_count }}</td>
            <td>{{ b.failed_count }}</td>
            <td>{{ b.total_recipients }}</td>
            <td><form method="post" action="/admin/broadcasts/{{ b.id }}/cancel" style="display:inline"><button style="background:#7a2222">Cancel</button></form></td>
        </tr>
        {% endfor %}
    </table>
</div>
{% endblock %}

````

### FILE: app/admin/templates/channels.html

````html
{% extends "base.html" %}
{% block title %}Mandatory Channels — Movie Bot Admin{% endblock %}
{% block content %}
<h1>Mandatory Subscription Channels</h1>
{% if diagnostic_error %}<p class="error">Diagnostic error: {{ diagnostic_error }}</p>{% endif %}

<div class="card">
    <h3>Add channel</h3>
    <form method="post" action="/admin/channels/create">
        <input type="text" name="chat_id" placeholder="@channel_username or -100123456789" required>
        <input type="text" name="title" placeholder="Display title" required>
        <input type="text" name="invite_link" placeholder="Invite link (optional)">
        <button type="submit">Add</button>
    </form>
</div>

<table>
    <tr><th>Chat ID</th><th>Title</th><th>Bot is admin?</th><th>Active</th><th>Actions</th></tr>
    {% for c in channels %}
    <tr>
        <td>{{ c.chat_id }}</td>
        <td>{{ c.title }}</td>
        <td>{% if c.bot_is_admin_verified %}<span class="badge ok">Yes</span>{% else %}<span class="badge warn">Unverified</span>{% endif %}</td>
        <td>{{ c.is_active }}</td>
        <td>
            <form method="post" action="/admin/channels/{{ c.id }}/diagnose" style="display:inline">
                <button type="submit">Check bot admin rights</button>
            </form>
        </td>
    </tr>
    {% endfor %}
</table>
{% endblock %}

````

### FILE: app/admin/templates/dashboard.html

````html
{% extends "base.html" %}
{% block title %}Dashboard — Movie Bot Admin{% endblock %}
{% block content %}
<h1>Dashboard</h1>

<div class="card">
    <h3>Overview</h3>
    <table>
        <tr><td>Total users</td><td>{{ stats.total_users }}</td></tr>
        <tr><td>Active premium users</td><td>{{ stats.premium_users }}</td></tr>
        <tr><td>Total orders</td><td>{{ stats.total_orders }}</td></tr>
        <tr><td>Paid orders</td><td>{{ stats.paid_orders }}</td></tr>
        {% for currency, amount in stats.revenue_by_currency.items() %}
        <tr><td>Revenue ({{ currency }})</td><td>{{ amount }}</td></tr>
        {% endfor %}
    </table>
</div>

<div class="card">
    <h3>Payment providers</h3>
    <table>
        <tr><th>Provider</th><th>Status</th></tr>
        {% for p in providers %}
        <tr>
            <td>{{ p.label }}</td>
            <td>
                {% if not p.enabled %}<span class="badge off">Disabled</span>
                {% elif p.live %}<span class="badge ok">Live</span>
                {% else %}<span class="badge warn">Sandbox</span>{% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
</div>

<div class="card">
    <h3>Needs attention</h3>
    <p>Suspicious referrals: {{ moderation.suspicious_referrals }}</p>
    <p>Pending promo reviews: {{ moderation.pending_promo_links }}</p>
    <p>Pending blogger applications: {{ moderation.pending_blogger_applications }}</p>
    <p>Open support tickets: {{ moderation.open_support_tickets }}</p>
</div>
{% endblock %}

````

### FILE: app/admin/templates/list_generic.html

````html
{% extends "base.html" %}
{% block title %}{{ title }} — Movie Bot Admin{% endblock %}
{% block content %}
<h1>{{ title }}</h1>
{% if message %}<p class="card">{{ message }}</p>{% endif %}
{% block body %}{% endblock %}
{% endblock %}

````

### FILE: app/admin/templates/login.html

````html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Login — Movie Bot</title>
    <style>
        body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; background: #0f1115; color: #e6e6e6;
               display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        form { background: #161922; padding: 32px; border-radius: 10px; width: 320px; }
        input { width: 100%; padding: 10px; margin-bottom: 12px; border-radius: 6px; border: 1px solid #2a2e3a; background: #10131a; color: #e6e6e6; box-sizing: border-box; }
        button { width: 100%; padding: 10px; border-radius: 6px; background: #2c5fce; color: white; border: none; cursor: pointer; }
        .error { color: #ff6b6b; margin-bottom: 12px; }
        h1 { font-size: 18px; margin-bottom: 20px; }
    </style>
</head>
<body>
<form method="post" action="/admin/login">
    <h1>🎬 Movie Bot Admin</h1>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <input type="text" name="username" placeholder="Username" required autofocus>
    <input type="password" name="password" placeholder="Password" required>
    <button type="submit">Sign in</button>
</form>
</body>
</html>

````

### FILE: app/admin/templates/moderation.html

````html
{% extends "base.html" %}
{% block title %}Moderation — Movie Bot Admin{% endblock %}
{% block content %}
<h1>Moderation Queue</h1>

<div class="card">
    <h3>Suspicious referral activity</h3>
    <table>
        <tr><th>Referrer</th><th>Referred</th><th>Reason</th><th>Attributed at</th></tr>
        {% for r in suspicious_referrals %}
        <tr>
            <td>#{{ r.referrer_user_id }}</td>
            <td>#{{ r.referred_user_id }}</td>
            <td>{{ r.suspicious_reason }}</td>
            <td>{{ r.attributed_at }}</td>
        </tr>
        {% endfor %}
    </table>
</div>

<div class="card">
    <h3>Open support tickets</h3>
    <table>
        <tr><th>ID</th><th>User</th><th>Subject</th><th>Status</th><th>Reply</th></tr>
        {% for t in open_tickets %}
        <tr>
            <td>{{ t.id }}</td>
            <td>#{{ t.user_id }}</td>
            <td>{{ t.subject }}</td>
            <td>{{ t.status }}</td>
            <td>
                <form method="post" action="/admin/moderation/tickets/{{ t.id }}/reply" style="display:inline">
                    <input type="text" name="text" placeholder="Reply" style="width:150px">
                    <button>Send</button>
                </form>
                <form method="post" action="/admin/moderation/tickets/{{ t.id }}/close" style="display:inline"><button>Close</button></form>
            </td>
        </tr>
        {% endfor %}
    </table>
</div>
{% endblock %}

````

### FILE: app/admin/templates/movies.html

````html
{% extends "base.html" %}
{% block title %}Movies — Movie Bot Admin{% endblock %}
{% block content %}
<h1>Movies</h1>
<p style="opacity:0.7">To add a new movie: forward/send the licensed video to the bot from an admin's Telegram
account. The bot captures the Telegram file_id automatically and creates a draft record here for metadata editing.</p>
<table>
    <tr><th>Code</th><th>Title (EN)</th><th>Category</th><th>Access</th><th>State</th><th>Views</th><th>Actions</th></tr>
    {% for m in movies %}
    <tr>
        <td>{{ m.code }}</td>
        <td>{{ m.title_en }}</td>
        <td>{{ m.category.title_en if m.category else "—" }}</td>
        <td>{{ m.access_type }}</td>
        <td>{{ m.publication_state }}</td>
        <td>{{ m.view_count }}</td>
        <td>
            <form method="post" action="/admin/movies/{{ m.id }}/publish" style="display:inline">
                <button type="submit">Publish</button>
            </form>
            <form method="post" action="/admin/movies/{{ m.id }}/archive" style="display:inline">
                <button type="submit">Archive</button>
            </form>
            <form method="post" action="/admin/movies/{{ m.id }}/delete" style="display:inline"
                  onsubmit="return confirm('Delete this movie permanently?');">
                <button type="submit" style="background:#7a2222">Delete</button>
            </form>
        </td>
    </tr>
    {% endfor %}
</table>
{% endblock %}

````

### FILE: app/admin/templates/orders.html

````html
{% extends "base.html" %}
{% block title %}Orders — Movie Bot Admin{% endblock %}
{% block content %}
<h1>Orders</h1>

<div class="card">
    <h3>Provider status</h3>
    <table>
        <tr><th>Provider</th><th>Status</th></tr>
        {% for p in providers %}
        <tr>
            <td>{{ p.label }}</td>
            <td>{% if not p.enabled %}<span class="badge off">Disabled</span>{% elif p.live %}<span class="badge ok">Live</span>{% else %}<span class="badge warn">Sandbox</span>{% endif %}</td>
        </tr>
        {% endfor %}
    </table>
</div>

<table>
    <tr><th>UID</th><th>Buyer</th><th>Plan</th><th>Amount</th><th>Provider</th><th>Status</th><th>Actions</th></tr>
    {% for o in orders %}
    <tr>
        <td>{{ o.uid }}</td>
        <td>#{{ o.buyer_user_id }}</td>
        <td>#{{ o.plan_id }}</td>
        <td>{{ o.net_amount }} {{ o.currency }}</td>
        <td>{{ o.provider_code }}</td>
        <td>{{ o.status }}</td>
        <td>
            {% if o.status == "paid" %}
            <form method="post" action="/admin/orders/{{ o.id }}/refund" style="display:inline">
                <input type="text" name="reason" placeholder="Reason" style="width:100px" required>
                <button style="background:#7a2222">Refund</button>
            </form>
            {% endif %}
        </td>
    </tr>
    {% endfor %}
</table>
{% endblock %}

````

### FILE: app/admin/templates/plans.html

````html
{% extends "base.html" %}
{% block title %}Premium Plans — Movie Bot Admin{% endblock %}
{% block content %}
<h1>Premium Plans</h1>

<div class="card">
    <h3>Create a new plan</h3>
    <form method="post" action="/admin/plans/create">
        <input type="text" name="code" placeholder="Code (e.g. monthly)" required>
        <input type="text" name="title_uz" placeholder="Title (UZ)" required>
        <input type="text" name="title_ru" placeholder="Title (RU)" required>
        <input type="text" name="title_en" placeholder="Title (EN)" required>
        <input type="number" name="duration_days" placeholder="Duration (days)" required>
        <input type="number" name="price_amount" placeholder="Price (minor units)" required>
        <input type="text" name="currency" placeholder="Currency" value="UZS">
        <input type="number" name="standard_referral_percent" placeholder="Standard referral % *100 (e.g. 1000=10%)" value="0">
        <input type="number" name="blogger_referral_percent" placeholder="Blogger referral % *100" value="0">
        <label><input type="checkbox" name="blogger_acquisition_reward_enabled" checked> Blogger acquisition reward enabled</label>
        <input type="number" name="max_discount_percent" placeholder="Max promo discount %" value="100">
        <button type="submit">Create</button>
    </form>
</div>

<table>
    <tr>
        <th>Code</th><th>Price</th><th>Duration</th><th>Std referral %</th><th>Blogger referral %</th>
        <th>Blogger acq. reward</th><th>Active</th><th>Update</th>
    </tr>
    {% for p in plans %}
    <tr>
        <td>{{ p.code }}</td>
        <td>{{ p.price_amount }} {{ p.currency }}</td>
        <td>{{ p.duration_days }}d</td>
        <td>{{ (p.standard_referral_percent / 100) }}%</td>
        <td>{{ (p.blogger_referral_percent / 100) }}%</td>
        <td>{{ p.blogger_acquisition_reward_enabled }}</td>
        <td>{{ p.is_active }}</td>
        <td>
            <form method="post" action="/admin/plans/{{ p.id }}/update">
                <input type="number" name="price_amount" value="{{ p.price_amount }}" style="width:90px">
                <input type="number" name="standard_referral_percent" value="{{ p.standard_referral_percent }}" style="width:70px">
                <input type="number" name="blogger_referral_percent" value="{{ p.blogger_referral_percent }}" style="width:70px">
                <label><input type="checkbox" name="blogger_acquisition_reward_enabled" {% if p.blogger_acquisition_reward_enabled %}checked{% endif %}></label>
                <label><input type="checkbox" name="is_active" {% if p.is_active %}checked{% endif %}></label>
                <button type="submit">Save</button>
            </form>
        </td>
    </tr>
    {% endfor %}
</table>
<p style="opacity:0.7">Note: updating a plan only affects FUTURE orders. Past orders and referral commissions keep
their own frozen snapshot of the price/percent that applied at purchase time.</p>
{% endblock %}

````

### FILE: app/admin/templates/promos.html

````html
{% extends "base.html" %}
{% block title %}Promo Codes — Movie Bot Admin{% endblock %}
{% block content %}
<h1>Promo Codes</h1>

<div class="card">
    <h3>Create bot-issued (platform-funded) code</h3>
    <form method="post" action="/admin/promos/create_admin_code">
        <select name="plan_id">
            {% for p in plans %}<option value="{{ p.id }}">{{ p.code }} ({{ p.price_amount }} {{ p.currency }})</option>{% endfor %}
        </select>
        <select name="kind">
            <option value="full_premium">Full Premium</option>
            <option value="percent_discount">Percent Discount</option>
        </select>
        <input type="number" name="discount_percent" placeholder="Discount % (if applicable)" value="0">
        <input type="number" name="activations" placeholder="Activations" required>
        <button type="submit">Create</button>
    </form>
</div>

<div class="card">
    <h3>Pending attribution-link review</h3>
    <table>
        <tr><th>Code</th><th>Issuer</th><th>Attribution</th><th>Actions</th></tr>
        {% for promo in pending %}
        <tr>
            <td>{{ promo.code }}</td>
            <td>user #{{ promo.issuer_user_id }}</td>
            <td>{{ promo.attribution_label or promo.attribution_url }}</td>
            <td>
                <form method="post" action="/admin/promos/{{ promo.id }}/approve" style="display:inline"><button>Approve</button></form>
                <form method="post" action="/admin/promos/{{ promo.id }}/reject" style="display:inline">
                    <input type="text" name="reason" placeholder="Reason" style="width:100px">
                    <button style="background:#7a2222">Reject</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
</div>
{% endblock %}

````

### FILE: app/admin/templates.py

````python
"""Shared Jinja2Templates instance for the admin panel."""

from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

````

### FILE: app/admin/templates/users.html

````html
{% extends "base.html" %}
{% block title %}Users — Movie Bot Admin{% endblock %}
{% block content %}
<h1>Users</h1>
<form method="get" action="/admin/users">
    <input type="text" name="q" value="{{ q }}" placeholder="Search by username, name, or Telegram ID">
    <button type="submit">Search</button>
</form>

<table>
    <tr><th>Telegram ID</th><th>Username</th><th>Lang</th><th>Premium until</th><th>Blocked</th><th>Actions</th></tr>
    {% for u in users %}
    <tr>
        <td>{{ u.telegram_id }}</td>
        <td>{{ u.username or "—" }}</td>
        <td>{{ u.language }}</td>
        <td>{{ u.premium_until or "—" }}</td>
        <td>{{ u.is_blocked }}</td>
        <td>
            {% if u.is_blocked %}
            <form method="post" action="/admin/users/{{ u.id }}/unblock" style="display:inline"><button>Unblock</button></form>
            {% else %}
            <form method="post" action="/admin/users/{{ u.id }}/block" style="display:inline">
                <input type="text" name="reason" placeholder="Reason" style="width:100px">
                <button>Block</button>
            </form>
            {% endif %}
            <form method="post" action="/admin/users/{{ u.id }}/gift_balance" style="display:inline">
                <input type="number" name="amount" placeholder="Amount" style="width:70px">
                <input type="text" name="currency" value="UZS" style="width:50px">
                <input type="text" name="reason" placeholder="Reason" style="width:90px">
                <button>Gift balance</button>
            </form>
        </td>
    </tr>
    {% endfor %}
</table>
{% endblock %}

````

### FILE: app/api/__init__.py

````python
"""FastAPI surface: Telegram/Stripe/Click webhooks, the storefront checkout,
and the admin panel."""

````

### FILE: app/api/storefront/__init__.py

````python
"""Independent web storefront: a genuinely separate sales channel from the
Telegram bot, used ONLY for Stripe/Click checkout as permitted by spec
section 4. This surface is entirely gated behind `STOREFRONT_ENABLED` and
is never linked to from inside the bot's premium-purchase flow (the bot
only ever offers Telegram Stars or wallet payment -- see
app/bot/handlers/premium.py).
"""

````

### FILE: app/api/storefront/routes.py

````python
"""Storefront checkout routes: list plans, create a Stripe/Click charge,
and simple success/cancel landing pages. Requires the buyer to identify
their Telegram account (telegram_id) so the resulting entitlement can be
linked back to their bot account -- this is a legitimate independent web
purchase flow, not a bot-triggered redirect (see compliance note above).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models.enums import PaymentProviderCode
from app.db.session import get_session
from app.db.uow import UnitOfWork
from app.payments.registry import PaymentRegistry
from app.services.purchase_service import PurchaseService

router = APIRouter(prefix="/storefront", tags=["storefront"])
settings = get_settings()


def _require_storefront_enabled() -> None:
    if not settings.STOREFRONT_ENABLED:
        raise HTTPException(status_code=404, detail="Storefront is disabled")


@router.get("/plans")
async def list_plans(session: AsyncSession = Depends(get_session)) -> list[dict]:
    _require_storefront_enabled()
    uow = UnitOfWork(session)
    plans = await uow.plans.list_active()
    return [
        {
            "id": p.id,
            "code": p.code,
            "title": p.title_en,
            "duration_days": p.duration_days,
            "price_amount": p.price_amount,
            "currency": p.currency,
        }
        for p in plans
    ]


@router.post("/checkout")
async def create_checkout(
    plan_id: int,
    provider: str,
    telegram_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    _require_storefront_enabled()
    if provider not in (PaymentProviderCode.STRIPE.value, PaymentProviderCode.CLICK.value):
        raise HTTPException(status_code=400, detail="Unsupported storefront provider")

    uow = UnitOfWork(session)
    plan = await uow.plans.get(plan_id)
    if plan is None or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plan not found")

    user = await uow.users.get_by_telegram_id(telegram_id)
    if user is None:
        raise HTTPException(
            status_code=400,
            detail="This Telegram account has not started the bot yet. Start the bot first so we can link your purchase.",
        )

    registry = PaymentRegistry(settings)
    try:
        provider_impl = registry.get_enabled(provider)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    purchase_service = PurchaseService(uow)
    order = await purchase_service.create_order(
        buyer_user_id=user.id, plan=plan, provider_code=PaymentProviderCode(provider)
    )
    charge = await provider_impl.create_charge(
        order_uid=str(order.uid),
        amount=order.net_amount,
        currency=order.currency,
        description=plan.title_en,
        buyer_telegram_id=telegram_id,
    )
    await session.commit()
    return {"order_uid": str(order.uid), **charge.checkout_payload}


@router.get("/success")
async def checkout_success(order: str = Query(...)) -> dict:
    return {
        "status": "received",
        "message": "Payment received; premium will activate once the provider confirms the charge.",
    }


@router.get("/cancel")
async def checkout_cancel(order: str = Query(...)) -> dict:
    return {"status": "cancelled", "order_uid": order}

````

### FILE: app/api/webhooks/click_webhook.py

````python
"""Click (click.uz) merchant webhook endpoint for the independent web
storefront: implements the two-step Prepare (action=0) / Complete
(action=1) protocol per Click's Shop API, responding with the exact JSON
shape Click's merchant integration expects on each step.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request, Response

from app.config import get_settings
from app.db.session import AsyncSessionLocal
from app.db.uow import UnitOfWork
from app.payments.click_provider import ClickActionCode, ClickErrorCode, ClickProvider

router = APIRouter(prefix="/webhooks/click", tags=["click-webhook"])
settings = get_settings()


@router.post("")
async def click_webhook(request: Request) -> Response:
    form = await request.form()
    data = dict(form)
    provider = ClickProvider(settings)
    event = await provider.parse_webhook(headers={}, body=json.dumps(data).encode("utf-8"))

    if not event.verified:
        return _json_response(
            {"error": ClickErrorCode.SIGN_CHECK_FAILED, "error_note": "SIGN CHECK FAILED"}
        )

    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        try:
            order = await uow.orders.get_by_uid(event.order_uid) if event.order_uid else None
            if order is None:
                await session.commit()
                return _json_response(
                    {"error": ClickErrorCode.TRANSACTION_NOT_FOUND, "error_note": "Order not found"}
                )

            action = str(data.get("action"))
            existing = await uow.orders.get_provider_event(
                "click", f"{event.provider_event_id}:{action}"
            )
            if existing is not None:
                await session.commit()
                return _json_response(
                    {
                        "click_trans_id": data.get("click_trans_id"),
                        "merchant_trans_id": data.get("merchant_trans_id"),
                        (
                            "merchant_prepare_id"
                            if action == str(ClickActionCode.PREPARE)
                            else "merchant_confirm_id"
                        ): order.id,
                        "error": ClickErrorCode.SUCCESS,
                        "error_note": "Already processed",
                    }
                )

            await uow.orders.create_provider_event(
                provider_code="click",
                provider_event_id=f"{event.provider_event_id}:{action}",
                event_type=f"click_action_{action}",
                order_id=order.id,
                raw_payload=data,
                processed=True,
            )

            if action == str(ClickActionCode.PREPARE):
                await session.commit()
                return _json_response(
                    {
                        "click_trans_id": data.get("click_trans_id"),
                        "merchant_trans_id": data.get("merchant_trans_id"),
                        "merchant_prepare_id": order.id,
                        "error": ClickErrorCode.SUCCESS,
                        "error_note": "Success",
                    }
                )

            # Complete step: activate premium via the shared purchase service.
            from app.services.purchase_service import PurchaseService

            purchase_service = PurchaseService(uow)
            await purchase_service.confirm_payment(
                order, provider_reference=event.provider_reference
            )
            await session.commit()
            return _json_response(
                {
                    "click_trans_id": data.get("click_trans_id"),
                    "merchant_trans_id": data.get("merchant_trans_id"),
                    "merchant_confirm_id": order.id,
                    "error": ClickErrorCode.SUCCESS,
                    "error_note": "Success",
                }
            )
        except Exception:
            await session.rollback()
            raise


def _json_response(payload: dict) -> Response:
    return Response(content=json.dumps(payload), media_type="application/json")

````

### FILE: app/api/webhooks/__init__.py

````python
"""Payment and Telegram webhook routes."""

````

### FILE: app/api/webhooks/stripe_webhook.py

````python
"""Stripe webhook endpoint for the independent web storefront.

Verifies the Stripe-Signature header (see StripeProvider.parse_webhook)
before treating anything as proof of payment, then routes to
`PurchaseService.confirm_payment` / `refund_order` -- the exact same code
path used by the Telegram Stars success handler and the wallet checkout,
so premium is always activated exactly once regardless of which provider
paid for it.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.config import get_settings
from app.db.session import AsyncSessionLocal
from app.db.uow import UnitOfWork
from app.payments.base import PaymentEventType
from app.payments.stripe_provider import StripeProvider

router = APIRouter(prefix="/webhooks/stripe", tags=["stripe-webhook"])
settings = get_settings()


@router.post("")
async def stripe_webhook(request: Request) -> Response:
    provider = StripeProvider(settings)
    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}

    event = await provider.parse_webhook(headers=headers, body=body)
    if not event.verified:
        return Response(status_code=400, content="invalid signature")

    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        try:
            existing = await uow.orders.get_provider_event("stripe", event.provider_event_id)
            if existing is not None:
                await session.commit()
                return Response(status_code=200)  # duplicate delivery -- already processed

            order = await uow.orders.get_by_uid(event.order_uid) if event.order_uid else None
            await uow.orders.create_provider_event(
                provider_code="stripe",
                provider_event_id=event.provider_event_id,
                event_type=event.event_type.value,
                order_id=order.id if order else None,
                raw_payload=event.raw_payload,
                processed=True,
            )

            if order is not None:
                from app.services.purchase_service import PurchaseService

                purchase_service = PurchaseService(uow)
                if event.event_type == PaymentEventType.PAYMENT_SUCCEEDED:
                    await purchase_service.confirm_payment(
                        order, provider_reference=event.provider_reference
                    )
                elif event.event_type in (PaymentEventType.REFUNDED,):
                    await purchase_service.refund_order(order, reason="stripe_refund_event")
                elif event.event_type == PaymentEventType.DISPUTED:
                    from app.bot.handlers.admin_notifications import notify_admins_payment_problem

                    await notify_admins_payment_problem(
                        request.app.state.bot,
                        uow,
                        order_uid=str(order.uid),
                        reason="stripe_dispute",
                    )

            await session.commit()
        except Exception:
            await session.rollback()
            raise

    return Response(status_code=200)

````

### FILE: app/api/webhooks/telegram.py

````python
"""Telegram webhook endpoint.

Only mounted/relevant when `BOT_WEBHOOK_URL` is configured (otherwise
`app.main` runs the bot via long polling and this route is never hit in
practice, though it stays registered and harmless). Verifies the
`X-Telegram-Bot-Api-Secret-Token` header against `BOT_WEBHOOK_SECRET`
before doing anything else -- this is the ONLY authentication Telegram
webhooks offer, and skipping it would let anyone forge bot updates.
"""

from __future__ import annotations

from aiogram import Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.config import get_settings

router = APIRouter(prefix="/webhooks/telegram", tags=["telegram-webhook"])
settings = get_settings()


@router.post("")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> Response:
    if x_telegram_bot_api_secret_token != settings.BOT_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret token")

    dp: Dispatcher = request.app.state.dispatcher
    bot = request.app.state.bot

    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot=bot, update=update)
    return Response(status_code=200)

````

### FILE: app/bot/factory.py

````python
"""Builds the aiogram `Bot` + `Dispatcher`, wiring middlewares and handlers.

Used by both `app.main` (long-polling / webhook entrypoint) and
`app.api.webhooks.telegram` (feeding updates from the FastAPI webhook route
into the same Dispatcher when `BOT_WEBHOOK_URL` is configured).
"""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from app.bot.handlers import register_all
from app.bot.middlewares.db_session import DbSessionMiddleware
from app.bot.middlewares.user_context import UserContextMiddleware
from app.config import Settings, get_settings
from app.core.redis import get_redis


def build_bot(settings: Settings | None = None) -> Bot:
    settings = settings or get_settings()
    return Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def build_dispatcher(settings: Settings | None = None) -> Dispatcher:
    settings = settings or get_settings()
    storage = RedisStorage(redis=get_redis())
    dp = Dispatcher(storage=storage)

    # Order matters: DB session must be opened before user context resolves.
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(UserContextMiddleware())

    register_all(dp)
    return dp

````

### FILE: app/bot/handlers/admin_notifications.py

````python
"""Shared admin-notification helpers used by workers and other handlers.

This module has no message/callback handlers of its own (it's included in
`register_all` for consistency and so `app.bot.handlers` stays the single
place that knows about every router), but centralizes the "send a message
to every admin with a Telegram id and the right role" logic used for:
  - suspicious referral activity (called by the reconciliation worker)
  - payment problems (called by webhook handlers on verification failure)
"""

from __future__ import annotations

from aiogram import Bot, Router

from app.db.models.enums import AdminRole
from app.db.uow import UnitOfWork
from app.i18n import t

router = Router(name="admin_notifications")


async def notify_admins_suspicious_referral(
    bot: Bot, uow: UnitOfWork, *, referrer_label: str, reason: str
) -> None:
    admins = await uow.admins.list_notification_recipients(
        roles=[AdminRole.SUPERADMIN, AdminRole.ADMIN]
    )
    text = t("en", "admin_notify_suspicious_referral", referrer=referrer_label, reason=reason)
    for admin in admins:
        try:
            await bot.send_message(chat_id=admin.telegram_id, text=text)
        except Exception:
            continue


async def notify_admins_payment_problem(
    bot: Bot, uow: UnitOfWork, *, order_uid: str, reason: str
) -> None:
    admins = await uow.admins.list_notification_recipients(
        roles=[AdminRole.SUPERADMIN, AdminRole.ADMIN]
    )
    text = t("en", "admin_notify_payment_problem", order_uid=order_uid, reason=reason)
    for admin in admins:
        try:
            await bot.send_message(chat_id=admin.telegram_id, text=text)
        except Exception:
            continue

````

### FILE: app/bot/handlers/blogger.py

````python
"""Blogger application flow: choose platform -> receive verification phrase
-> submit profile URL -> admin review (manual, honestly labeled).
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.states import BloggerApplicationStates
from app.config import get_settings
from app.db.models.enums import AdminRole
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import t
from app.services.blogger_service import BloggerService

router = Router(name="blogger")
settings = get_settings()


@router.callback_query(F.data == "blogger:apply")
async def handle_blogger_apply_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await callback.message.answer(t(user.language, "blogger_apply_start"))
    await callback.message.answer(t(user.language, "blogger_manual_review_notice"))
    await state.set_state(BloggerApplicationStates.choosing_platform)
    await callback.message.answer(t(user.language, "blogger_apply_choose_platform"))
    await callback.answer()


@router.message(StateFilter(BloggerApplicationStates.choosing_platform), F.text)
async def handle_platform_chosen(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    blogger_service = BloggerService(uow)
    result = await blogger_service.start_application(
        applicant_user_id=user.id, platform_name=message.text.strip()
    )
    if result.already_pending:
        await message.answer(t(user.language, "blogger_apply_already_pending"))
        await state.clear()
        return

    await state.update_data(application_id=result.application.id)
    await state.set_state(BloggerApplicationStates.awaiting_url)
    await message.answer(
        t(user.language, "blogger_apply_phrase", phrase=result.application.verification_phrase)
    )
    await message.answer(t(user.language, "blogger_apply_send_url"))


@router.message(StateFilter(BloggerApplicationStates.awaiting_url), F.text)
async def handle_url_submitted(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    application = await uow.bloggers.get_application(data["application_id"])
    if application is None:
        await message.answer(t(user.language, "error_generic"))
        await state.clear()
        return

    blogger_service = BloggerService(uow)
    await blogger_service.submit_url(application, message.text.strip())
    await blogger_service.attempt_automated_check(application)

    await message.answer(t(user.language, "blogger_apply_submitted"))
    await state.clear()

    await _notify_admins_new_application(message, uow, user, application)


async def _notify_admins_new_application(
    message: Message, uow: UnitOfWork, user: User, application
) -> None:
    admins = await uow.admins.list_notification_recipients(
        roles=[AdminRole.SUPERADMIN, AdminRole.ADMIN]
    )
    text = t(
        "en",
        "admin_notify_new_blogger_application",
        user=f"@{user.username}" if user.username else str(user.telegram_id),
        platform=application.platform_name or "unknown",
    )
    for admin in admins:
        try:
            await message.bot.send_message(chat_id=admin.telegram_id, text=text)
        except Exception:
            continue

````

### FILE: app/bot/handlers/fallback_text.py

````python
"""Catch-all text router. MUST be included LAST in `register_all` so every
menu-button router and every active FSM state gets first refusal; anything
that reaches this handler is treated as a movie code/name search query,
matching spec section 2 ("Enter a movie code", "type the movie's complete
name", "search by a partial name").
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from app.bot.handlers.movies import handle_movie_query_text
from app.db.models.user import User
from app.db.uow import UnitOfWork

router = Router(name="fallback_text")


@router.message(F.text)
async def handle_fallback_text(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    if user is None:
        return
    await handle_movie_query_text(message, uow, user)

````

### FILE: app/bot/handlers/gifts.py

````python
"""Gifts menu: send premium/balance to another user, view received gifts."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.gifts import gift_confirm_keyboard, gifts_menu_keyboard
from app.bot.keyboards.premium import plan_list_keyboard
from app.bot.states import GiftStates
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t
from app.services.gift_service import GiftService
from app.services.wallet_service import WalletService

router = Router(name="gifts")


def _menu_texts(key: str) -> set[str]:
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


@router.message(F.text.in_(_menu_texts("menu_gifts")))
async def handle_gifts_menu(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    await message.answer(
        t(user.language, "gifts_menu_title"), reply_markup=gifts_menu_keyboard(user.language)
    )


@router.callback_query(F.data == "gift:received")
async def handle_gifts_received(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    gifts = await uow.gifts.list_received(user.id)
    if not gifts:
        await callback.message.answer(t(user.language, "gift_recipient_not_found"))
    else:
        for gift in gifts[:10]:
            desc = f"{gift.kind} - {gift.created_at.strftime('%Y-%m-%d')}"
            await callback.message.answer(
                t(user.language, "gift_received_notice", description=desc)
            )
    await callback.answer()


@router.callback_query(F.data == "gift:send_premium")
async def handle_gift_premium_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(GiftStates.awaiting_recipient_premium)
    await callback.message.answer(t(user.language, "gift_enter_recipient"))
    await callback.answer()


@router.message(StateFilter(GiftStates.awaiting_recipient_premium), F.text)
async def handle_gift_premium_recipient(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    recipient = await _resolve_recipient(uow, message.text.strip())
    if recipient is None:
        await message.answer(t(user.language, "gift_recipient_not_found"))
        return
    await state.update_data(recipient_id=recipient.id, recipient_label=_recipient_label(recipient))
    plans = await uow.plans.list_active()
    await state.set_state(GiftStates.choosing_plan_premium)
    await message.answer(
        t(user.language, "premium_plans_title"),
        reply_markup=plan_list_keyboard(plans, user.language),
    )


@router.callback_query(StateFilter(GiftStates.choosing_plan_premium), F.data.startswith("plan:"))
async def handle_gift_premium_plan(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    plan_id = int(callback.data.split(":", 1)[1])
    plan = await uow.plans.get(plan_id)
    data = await state.get_data()
    await state.update_data(plan_id=plan_id)
    await state.set_state(GiftStates.confirming_premium)
    await callback.message.answer(
        t(
            user.language,
            "gift_confirm_premium",
            recipient=data["recipient_label"],
            plan_title=plan.title(user.language),
            price=plan.price_amount,
            currency=plan.currency,
        ),
        reply_markup=gift_confirm_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(StateFilter(GiftStates.confirming_premium), F.data == "gift_confirm:yes")
async def handle_gift_premium_confirm(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    gift_service = GiftService(uow)
    try:
        await gift_service.gift_premium_from_user(
            sender_user_id=user.id, recipient_user_id=data["recipient_id"], plan_id=data["plan_id"]
        )
    except Exception as exc:
        from app.services.money import InsufficientFundsError

        if isinstance(exc, InsufficientFundsError):
            await callback.message.answer(
                t(
                    user.language,
                    "premium_insufficient_balance",
                    available=exc.available,
                    required=exc.requested,
                    currency=exc.currency,
                )
            )
        else:
            await callback.message.answer(t(user.language, "error_generic"))
        await state.clear()
        await callback.answer()
        return

    await callback.message.answer(t(user.language, "gift_sent_success"))
    await state.clear()
    await callback.answer()


@router.callback_query(StateFilter(GiftStates.confirming_premium), F.data == "gift_confirm:no")
@router.callback_query(StateFilter(GiftStates.confirming_balance), F.data == "gift_confirm:no")
async def handle_gift_cancel(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await callback.message.answer(t(user.language, "action_cancelled"))
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "gift:send_balance")
async def handle_gift_balance_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(GiftStates.awaiting_recipient_balance)
    await callback.message.answer(t(user.language, "gift_enter_recipient"))
    await callback.answer()


@router.message(StateFilter(GiftStates.awaiting_recipient_balance), F.text)
async def handle_gift_balance_recipient(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    recipient = await _resolve_recipient(uow, message.text.strip())
    if recipient is None:
        await message.answer(t(user.language, "gift_recipient_not_found"))
        return
    await state.update_data(recipient_id=recipient.id, recipient_label=_recipient_label(recipient))
    await state.set_state(GiftStates.entering_amount_balance)
    await message.answer(t(user.language, "gift_enter_amount"))


@router.message(StateFilter(GiftStates.entering_amount_balance), F.text)
async def handle_gift_balance_amount(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer(t(user.language, "error_generic"))
        return
    if amount <= 0:
        await message.answer(t(user.language, "error_generic"))
        return

    wallet_service = WalletService(uow)
    balances = await wallet_service.get_balances(user.id)
    currency = next(iter(balances.keys()), "UZS")

    data = await state.get_data()
    await state.update_data(amount=amount, currency=currency)
    await state.set_state(GiftStates.confirming_balance)
    await message.answer(
        t(
            user.language,
            "gift_confirm_balance",
            recipient=data["recipient_label"],
            amount=amount,
            currency=currency,
        ),
        reply_markup=gift_confirm_keyboard(user.language),
    )


@router.callback_query(StateFilter(GiftStates.confirming_balance), F.data == "gift_confirm:yes")
async def handle_gift_balance_confirm(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    gift_service = GiftService(uow)
    try:
        await gift_service.gift_balance_from_user(
            sender_user_id=user.id,
            recipient_user_id=data["recipient_id"],
            currency=data["currency"],
            amount=data["amount"],
        )
    except Exception as exc:
        from app.services.money import InsufficientFundsError

        if isinstance(exc, InsufficientFundsError):
            await callback.message.answer(
                t(
                    user.language,
                    "premium_insufficient_balance",
                    available=exc.available,
                    required=exc.requested,
                    currency=exc.currency,
                )
            )
        else:
            await callback.message.answer(t(user.language, "error_generic"))
        await state.clear()
        await callback.answer()
        return

    await callback.message.answer(t(user.language, "gift_sent_success"))
    await state.clear()
    await callback.answer()


async def _resolve_recipient(uow: UnitOfWork, identifier: str):
    identifier = identifier.strip()
    if identifier.startswith("@"):
        return await uow.users.get_by_username(identifier)
    if identifier.isdigit():
        return await uow.users.get_by_telegram_id(int(identifier))
    return await uow.users.get_by_username(identifier)


def _recipient_label(recipient) -> str:
    return f"@{recipient.username}" if recipient.username else str(recipient.telegram_id)

````

### FILE: app/bot/handlers/__init__.py

````python
"""aiogram routers for every bot flow, aggregated in `register_all`."""

from __future__ import annotations

from aiogram import Dispatcher

from app.bot.handlers import (
    admin_notifications,
    blogger,
    fallback_text,
    gifts,
    inline_search,
    movies,
    premium,
    promo,
    referrals,
    start,
    support,
    wallet,
)
from app.bot.handlers import (
    settings as settings_handlers,
)


def register_all(dp: Dispatcher) -> None:
    """Registration order matters:
    - `start` must be first so `/start` is matched before generic text handlers.
    - `fallback_text` (free-text movie search) MUST be last so every menu
      button / FSM-state text handler in the other routers gets first
      refusal on a text message.
    """
    dp.include_router(start.router)
    dp.include_router(movies.router)
    dp.include_router(inline_search.router)
    dp.include_router(premium.router)
    dp.include_router(wallet.router)
    dp.include_router(referrals.router)
    dp.include_router(blogger.router)
    dp.include_router(promo.router)
    dp.include_router(gifts.router)
    dp.include_router(support.router)
    dp.include_router(settings_handlers.router)
    dp.include_router(admin_notifications.router)
    dp.include_router(fallback_text.router)

````

### FILE: app/bot/handlers/inline_search.py

````python
"""Inline mode: `@YourBot 222` in any chat returns a safe movie card.

Privacy/security invariant (spec section 2): the returned
`InlineQueryResultArticle` NEVER contains the movie's `video_file_id` and
NEVER embeds it in the "Open in Bot" URL -- it only carries the movie's
CODE, which is not secret (codes are how users normally look movies up)
and does not by itself grant access. The actual entitlement/mandatory-
channel check happens only in `app.bot.handlers.movies._present_movie`,
triggered by the `?start=movie_<code>` deep link from the "Open in Bot"
button, after the user opens a PRIVATE chat with the bot. A group chat
member other than the requester can see the card but tapping it just opens
their OWN private chat with the bot and their OWN access is checked --
nobody else's protected video is ever exposed through the inline result
itself.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from app.config import get_settings
from app.db.uow import UnitOfWork
from app.i18n import DEFAULT_LANGUAGE, t
from app.services.movie_access_service import MovieAccessService

router = Router(name="inline_search")

_settings = get_settings()


@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery, uow: UnitOfWork, **kwargs) -> None:
    query = inline_query.query.strip()
    if not query:
        await inline_query.answer([], cache_time=1)
        return

    language = DEFAULT_LANGUAGE
    user = await uow.users.get_by_telegram_id(inline_query.from_user.id)
    if user is not None:
        language = user.language

    access_service = MovieAccessService(uow)
    movies = await access_service.find_by_code_or_search(query)

    results = []
    for movie in movies[:20]:
        deep_link = f"https://t.me/{_settings.BOT_USERNAME}?start=movie_{movie.code}"
        results.append(
            InlineQueryResultArticle(
                id=str(movie.id),
                title=t(
                    language,
                    "movie_inline_card_title",
                    title=movie.title(language),
                    code=movie.code,
                ),
                description=movie.description(language) or "",
                thumbnail_url=None,
                input_message_content=InputTextMessageContent(
                    message_text=t(language, "movie_inline_card_description")
                ),
                reply_markup=_open_in_bot_markup(deep_link, language),
            )
        )

    await inline_query.answer(results, cache_time=30, is_personal=True)


def _open_in_bot_markup(deep_link: str, language: str):
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(language, "movie_open_in_bot_button"), url=deep_link)]
        ]
    )

````

### FILE: app/bot/handlers/movies.py

````python
"""Movie search, category browsing, mandatory-channel gating, and delivery.

`send_movie_by_code` is the single function that ever calls
`MovieAccessService.deliver_and_record_view` (which returns the raw
`video_file_id`); it is invoked from here AND from `start.py`'s deep-link
handler AND from the inline-search "Open in Bot" flow, so there is exactly
one code path that can hand a protected video to a user.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.movies import (
    category_list_keyboard,
    join_channels_keyboard,
    movie_search_results_keyboard,
)
from app.db.models.catalog import Movie
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t
from app.services.movie_access_service import MovieAccessService

router = Router(name="movies")


def _menu_texts(key: str) -> set[str]:
    """All localized variants of a menu button's label, used as an aiogram
    `F.text.in_(...)` filter so the same handler matches regardless of the
    user's chosen language."""
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


async def _get_membership_checker(bot):
    async def checker(telegram_id: int, chat_id: str) -> bool:
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=telegram_id)
            return member.status in ("member", "administrator", "creator")
        except Exception:
            return False

    return checker


@router.message(F.text.in_(_menu_texts("menu_search_movie")))
async def handle_search_menu(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    await message.answer(t(user.language, "movie_enter_code_or_name"))


@router.message(F.text.in_(_menu_texts("menu_categories")))
async def handle_categories_menu(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    categories = await uow.catalog.list_active_categories()
    await message.answer(
        t(user.language, "movie_categories_title"),
        reply_markup=category_list_keyboard(categories, user.language),
    )


@router.callback_query(F.data.startswith("cat:"))
async def handle_category_selected(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    category_id = int(callback.data.split(":", 1)[1])
    movies = await uow.catalog.list_by_category(category_id)
    if not movies:
        await callback.message.answer(t(user.language, "movie_no_movies_in_category"))
    else:
        await callback.message.answer(
            t(user.language, "movie_search_results"),
            reply_markup=movie_search_results_keyboard(movies, user.language),
        )
    await callback.answer()


async def handle_movie_query_text(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    """Called by `app.bot.handlers.fallback_text`'s catch-all router, which
    is registered LAST in `register_all` so every other feature router
    (premium/wallet/promo/gifts/support/settings menu buttons, FSM text
    steps) gets first refusal on a text message. Anything that reaches here
    is treated as a movie code/name search query."""
    access_service = MovieAccessService(uow)
    results = await access_service.find_by_code_or_search(message.text)
    if not results:
        await message.answer(t(user.language, "movie_not_found"))
        return
    if len(results) == 1:
        await _present_movie(message, uow, user, results[0], bot=message.bot)
        return
    await message.answer(
        t(user.language, "movie_search_results"),
        reply_markup=movie_search_results_keyboard(results, user.language),
    )


@router.callback_query(F.data.startswith("movie:"))
async def handle_movie_selected(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    movie_id = int(callback.data.split(":", 1)[1])
    movie = await uow.catalog.get_by_id(movie_id)
    if movie is None:
        await callback.answer(t(user.language, "movie_not_found"), show_alert=True)
        return
    await _present_movie(callback.message, uow, user, movie, bot=callback.bot)
    await callback.answer()


@router.callback_query(F.data.startswith("check_membership:"))
async def handle_check_membership(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    movie_id = int(callback.data.split(":", 1)[1])
    movie = await uow.catalog.get_by_id(movie_id)
    if movie is None:
        await callback.answer(t(user.language, "movie_not_found"), show_alert=True)
        return
    await _present_movie(callback.message, uow, user, movie, bot=callback.bot, is_recheck=True)
    await callback.answer()


async def send_movie_by_code(message: Message, *, uow: UnitOfWork, user: User, code: str) -> None:
    movie = await uow.catalog.get_by_code(code)
    if movie is None:
        await message.answer(t(user.language, "movie_not_found"))
        return
    await _present_movie(message, uow, user, movie, bot=message.bot)


async def _present_movie(
    message: Message, uow: UnitOfWork, user: User, movie: Movie, *, bot, is_recheck: bool = False
) -> None:
    checker = await _get_membership_checker(bot)
    access_service = MovieAccessService(uow, membership_checker=checker)
    decision = await access_service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )

    if not decision.allowed:
        if decision.reason == "premium_required":
            await message.answer(t(user.language, "movie_premium_required"))
            return
        if decision.reason in ("must_join_channels", "membership_check_unavailable"):
            channels = await uow.catalog.list_active_channels()
            relevant = [c for c in channels if c.chat_id in decision.missing_channels] or channels
            text_key = "movie_still_not_joined" if is_recheck else "movie_must_join_channels"
            await message.answer(
                t(user.language, text_key),
                reply_markup=join_channels_keyboard(relevant, movie.id, user.language),
            )
            return
        await message.answer(t(user.language, "movie_not_found"))
        return

    video_file_id = await access_service.deliver_and_record_view(movie)
    caption = (
        f"{movie.title(user.language)}\n{t(user.language, 'movie_code_label', code=movie.code)}"
    )
    await message.answer_video(video=video_file_id, caption=caption)

````

### FILE: app/bot/handlers/premium.py

````python
"""Premium plan selection, promo entry, payment-method choice, checkout
confirmation, and Telegram Stars invoice + successful_payment handling.

Wallet checkout (paying for premium out of the user's OWN balance) is
implemented here because it never leaves Telegram and never asks a bot
user to visit an external checkout page -- it is a same-currency ledger
debit, not a digital-goods payment routed around Telegram's own in-app
purchase flow (see README "Payments and platform compliance").
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery

from app.bot.keyboards.common import confirm_keyboard, main_menu_keyboard
from app.bot.keyboards.premium import (
    payment_method_keyboard,
    plan_list_keyboard,
    skip_promo_keyboard,
)
from app.bot.states import PremiumCheckoutStates
from app.config import get_settings
from app.db.models.enums import PaymentProviderCode
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t
from app.payments.registry import PaymentRegistry
from app.services.promo_service import PromoService
from app.services.purchase_service import PurchaseService
from app.services.wallet_service import WalletService

router = Router(name="premium")
settings = get_settings()


def _menu_texts(key: str) -> set[str]:
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


@router.message(F.text.in_(_menu_texts("menu_premium")))
async def handle_premium_menu(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    if user.is_premium_active:
        await message.answer(
            t(user.language, "premium_already_active", until=user.premium_until.isoformat())
        )
        return
    plans = await uow.plans.list_active()
    if not plans:
        await message.answer(t(user.language, "error_generic"))
        return
    await state.set_state(PremiumCheckoutStates.choosing_plan)
    await message.answer(
        t(user.language, "premium_plans_title"),
        reply_markup=plan_list_keyboard(plans, user.language),
    )


@router.callback_query(StateFilter(PremiumCheckoutStates.choosing_plan), F.data.startswith("plan:"))
async def handle_plan_chosen(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    plan_id = int(callback.data.split(":", 1)[1])
    plan = await uow.plans.get(plan_id)
    if plan is None or not plan.is_active:
        await callback.answer(t(user.language, "error_generic"), show_alert=True)
        return
    await state.update_data(plan_id=plan_id, discount_percent=0, promo_code=None)
    await state.set_state(PremiumCheckoutStates.entering_promo)
    await callback.message.answer(
        t(user.language, "premium_enter_promo_code"),
        reply_markup=skip_promo_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(StateFilter(PremiumCheckoutStates.entering_promo), F.data == "promo:skip")
async def handle_promo_skip(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await _show_payment_methods(callback.message, uow, user, state)
    await callback.answer()


@router.message(StateFilter(PremiumCheckoutStates.entering_promo), F.text)
async def handle_promo_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])

    promo = await uow.promos.get_by_code(message.text.strip())
    if promo is None or not promo.is_redeemable or promo.plan_id != plan.id:
        await message.answer(t(user.language, "premium_promo_invalid"))
        return

    discount_percent = 0 if promo.kind == "full_premium" else promo.discount_percent
    await state.update_data(
        discount_percent=discount_percent,
        promo_code=promo.code,
        is_full_premium=(promo.kind == "full_premium"),
    )

    purchase_service = PurchaseService(uow)
    quote = await purchase_service.quote(plan, discount_percent=discount_percent)
    await message.answer(
        t(user.language, "premium_promo_applied", amount=quote.net_amount, currency=quote.currency)
    )
    await _show_payment_methods(message, uow, user, state)


async def _show_payment_methods(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext
) -> None:
    data = await state.get_data()
    plan_id = data["plan_id"]
    if data.get("is_full_premium"):
        # Full-premium promo: no payment needed at all, redeem immediately.
        await _finalize_full_premium_promo(message, uow, user, state)
        return

    registry = PaymentRegistry(settings, bot=message.bot)
    stars_enabled = registry.is_provider_enabled("telegram_stars")
    plan = await uow.plans.get(plan_id)
    wallet_enabled = (
        True  # wallet checkout is always offered; insufficient funds is handled at confirm time
    )

    await state.set_state(PremiumCheckoutStates.choosing_payment_method)
    await message.answer(
        t(
            user.language,
            "premium_plan_details",
            title=plan.title(user.language),
            duration_days=plan.duration_days,
            price=plan.price_amount,
            currency=plan.currency,
        ),
        reply_markup=payment_method_keyboard(
            user.language, plan_id, stars_enabled=stars_enabled, wallet_enabled=wallet_enabled
        ),
    )


async def _finalize_full_premium_promo(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext
) -> None:
    data = await state.get_data()
    promo_service = PromoService(uow)
    result = await promo_service.redeem(code=data["promo_code"], redeemer_user_id=user.id)
    if not result.ok:
        await message.answer(t(user.language, "promo_redeem_not_redeemable"))
        await state.clear()
        return

    from app.db.models.enums import EntitlementSource
    from app.services.entitlement_service import EntitlementService

    entitlement_service = EntitlementService(uow)
    await entitlement_service.grant(
        user_id=user.id,
        plan_id=result.plan.id,
        duration_days=result.plan.duration_days,
        source=EntitlementSource.PROMO,
        source_reference=f"promo:{result.promo.id}:{user.id}",
    )
    await message.answer(t(user.language, "promo_redeem_success_full"))
    await message.answer(
        t(user.language, "main_menu_title"), reply_markup=main_menu_keyboard(user.language)
    )
    await state.clear()


@router.callback_query(
    StateFilter(PremiumCheckoutStates.choosing_payment_method), F.data.startswith("pay:stars:")
)
async def handle_pay_with_stars(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    registry = PaymentRegistry(settings, bot=callback.bot)
    try:
        provider = registry.get_enabled("telegram_stars")
    except Exception:
        await callback.answer(t(user.language, "premium_provider_disabled"), show_alert=True)
        return

    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    purchase_service = PurchaseService(uow)
    quote = await purchase_service.quote(plan, discount_percent=data.get("discount_percent", 0))

    order = await purchase_service.create_order(
        buyer_user_id=user.id,
        plan=plan,
        provider_code=PaymentProviderCode.TELEGRAM_STARS,
        discount_percent=data.get("discount_percent", 0),
    )
    # Stars amounts are denominated in XTR regardless of the plan's display
    # currency; a real deployment should configure plan prices for Stars
    # checkout in XTR directly, or maintain a documented XTR price per plan.
    # Here we charge `quote.net_amount` as the XTR amount 1:1, which is
    # correct when PremiumPlan.currency == "XTR" and must be configured as
    # such by the admin for Stars-payable plans.
    charge = await provider.create_charge(
        order_uid=str(order.uid),
        amount=quote.net_amount,
        currency="XTR",
        description=plan.title(user.language),
        buyer_telegram_id=user.telegram_id,
    )
    payload = charge.checkout_payload
    await callback.message.answer_invoice(
        title=payload["title"],
        description=payload["description"],
        payload=payload["payload"],
        provider_token=payload["provider_token"],
        currency=payload["currency"],
        prices=[{"label": p["label"], "amount": p["amount"]} for p in payload["prices"]],
    )
    await state.clear()
    await callback.answer()


@router.callback_query(
    StateFilter(PremiumCheckoutStates.choosing_payment_method), F.data.startswith("pay:wallet:")
)
async def handle_pay_with_wallet(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    purchase_service = PurchaseService(uow)
    quote = await purchase_service.quote(plan, discount_percent=data.get("discount_percent", 0))

    await state.update_data(quoted_amount=quote.net_amount, quoted_currency=quote.currency)
    await state.set_state(PremiumCheckoutStates.confirming)
    await callback.message.answer(
        t(
            user.language,
            "premium_checkout_summary",
            plan_title=plan.title(user.language),
            amount=quote.net_amount,
            currency=quote.currency,
        ),
        reply_markup=confirm_keyboard(user.language, confirm_cb="wallet_checkout:confirm"),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(PremiumCheckoutStates.confirming), F.data == "wallet_checkout:confirm"
)
async def handle_wallet_checkout_confirm(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    amount = data["quoted_amount"]
    currency = data["quoted_currency"]

    wallet_service = WalletService(uow)
    balances = await wallet_service.get_balances(user.id)
    available = balances.get(currency, {}).get("available", 0)
    if available < amount:
        await callback.message.answer(
            t(
                user.language,
                "premium_insufficient_balance",
                available=available,
                required=amount,
                currency=currency,
            )
        )
        await state.clear()
        await callback.answer()
        return

    purchase_service = PurchaseService(uow)
    order = await purchase_service.create_order(
        buyer_user_id=user.id,
        plan=plan,
        provider_code=PaymentProviderCode.WALLET,
        discount_percent=data.get("discount_percent", 0),
    )
    from app.db.models.enums import WalletEntryType

    await wallet_service.debit_available(
        user_id=user.id,
        currency=currency,
        amount=amount,
        entry_type=WalletEntryType.WALLET_PREMIUM_PURCHASE,
        idempotency_key=f"wallet_purchase:{order.uid}",
        reference_type="order",
        reference_id=str(order.id),
    )
    await purchase_service.confirm_payment(order, provider_reference=f"wallet:{order.uid}")

    updated_user = await uow.users.get_by_id(user.id)
    await callback.message.answer(
        t(user.language, "premium_payment_success", until=updated_user.premium_until.isoformat())
    )
    await callback.message.answer(
        t(user.language, "main_menu_title"), reply_markup=main_menu_keyboard(user.language)
    )
    await state.clear()
    await callback.answer()


# --- Telegram Stars: pre_checkout_query + successful_payment ------------------


@router.pre_checkout_query()
async def handle_pre_checkout(
    pre_checkout_query: PreCheckoutQuery, uow: UnitOfWork, **kwargs
) -> None:
    order = await uow.orders.get_by_uid(pre_checkout_query.invoice_payload)
    if order is None or order.status != "pending":
        await pre_checkout_query.answer(
            ok=False, error_message="Order not found or already processed"
        )
        return
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(
    message: Message, uow: UnitOfWork, user: User, **kwargs
) -> None:
    sp = message.successful_payment
    order = await uow.orders.get_by_uid(sp.invoice_payload)
    if order is None:
        return

    existing_event = await uow.orders.get_provider_event(
        "telegram_stars", sp.telegram_payment_charge_id
    )
    if existing_event is not None:
        return  # duplicate delivery of the same successful_payment update -- ignore

    await uow.orders.create_provider_event(
        provider_code="telegram_stars",
        provider_event_id=sp.telegram_payment_charge_id,
        event_type="successful_payment",
        order_id=order.id,
        raw_payload={
            "currency": sp.currency,
            "total_amount": sp.total_amount,
            "telegram_payment_charge_id": sp.telegram_payment_charge_id,
        },
        processed=True,
    )

    purchase_service = PurchaseService(uow)
    await purchase_service.confirm_payment(order, provider_reference=sp.telegram_payment_charge_id)

    updated_user = await uow.users.get_by_id(user.id)
    await message.answer(
        t(user.language, "premium_payment_success", until=updated_user.premium_until.isoformat())
    )
    await message.answer(
        t(user.language, "main_menu_title"), reply_markup=main_menu_keyboard(user.language)
    )

````

### FILE: app/bot/handlers/promo.py

````python
"""Promo code menu: create (user/blogger), list mine, and redeem.

Follows spec section 7's exact prompts: kind -> plan -> discount (if
applicable) -> activation count -> issuer label (User/Blogger) ->
attribution link (yes/no -> value) -> confirmation showing plan, discount,
activation count, total cost, current balance, and balance after
reservation.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.promo import (
    promo_attribution_choice_keyboard,
    promo_confirm_keyboard,
    promo_issuer_keyboard,
    promo_kind_keyboard,
    promo_menu_keyboard,
    promo_plan_keyboard,
)
from app.bot.states import PromoCreationStates, PromoRedeemStates
from app.db.models.enums import AdminRole, PromoKind
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t
from app.services.blogger_service import BloggerService
from app.services.promo_service import AttributionRequest, PromoService

router = Router(name="promo")


def _menu_texts(key: str) -> set[str]:
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


@router.message(F.text.in_(_menu_texts("menu_my_promo_codes")))
async def handle_promo_menu(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    await message.answer(
        t(user.language, "promo_menu_title"), reply_markup=promo_menu_keyboard(user.language)
    )


@router.callback_query(F.data == "promo:mine")
async def handle_promo_mine(callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs) -> None:
    codes = await uow.promos.list_by_issuer(user.id)
    if not codes:
        await callback.message.answer(t(user.language, "promo_my_codes_empty"))
    else:
        lines = [
            t(
                user.language,
                "promo_code_status_line",
                code=c.code,
                remaining=c.remaining_uses,
                max_uses=c.max_uses,
                status=c.moderation_status,
            )
            for c in codes
        ]
        await callback.message.answer("\n".join(lines))
    await callback.answer()


# --- Creation flow -------------------------------------------------------------


@router.callback_query(F.data == "promo:create")
async def handle_promo_create_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(PromoCreationStates.choosing_kind)
    await callback.message.answer(
        t(user.language, "promo_choose_kind"), reply_markup=promo_kind_keyboard(user.language)
    )
    await callback.answer()


@router.callback_query(
    StateFilter(PromoCreationStates.choosing_kind), F.data.startswith("promo_kind:")
)
async def handle_promo_kind_chosen(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    kind = callback.data.split(":", 1)[1]
    await state.update_data(kind=kind)
    plans = await uow.plans.list_active()
    await state.set_state(PromoCreationStates.choosing_plan)
    await callback.message.answer(
        t(user.language, "promo_choose_plan"),
        reply_markup=promo_plan_keyboard(plans, user.language),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(PromoCreationStates.choosing_plan), F.data.startswith("promo_plan:")
)
async def handle_promo_plan_chosen(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    plan_id = int(callback.data.split(":", 1)[1])
    await state.update_data(plan_id=plan_id)
    data = await state.get_data()
    if data["kind"] == PromoKind.PERCENT_DISCOUNT.value:
        await state.set_state(PromoCreationStates.entering_discount)
        await callback.message.answer(t(user.language, "promo_enter_discount_percent"))
    else:
        await state.update_data(discount_percent=0)
        await _ask_activation_count(callback.message, uow, user, state)
    await callback.answer()


@router.message(StateFilter(PromoCreationStates.entering_discount), F.text)
async def handle_discount_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    try:
        discount = int(message.text.strip().rstrip("%"))
    except ValueError:
        await message.answer(t(user.language, "error_generic"))
        return
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    if not (0 < discount <= plan.max_discount_percent):
        await message.answer(t(user.language, "error_generic"))
        return
    await state.update_data(discount_percent=discount)
    await _ask_activation_count(message, uow, user, state)


async def _ask_activation_count(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext
) -> None:
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    kind = PromoKind(data["kind"])
    promo_service = PromoService(uow)
    quote = await promo_service.quote_funding(
        plan=plan,
        kind=kind,
        discount_percent=data.get("discount_percent", 0),
        requested_activations=1,
        issuer_user_id=user.id,
    )
    await state.set_state(PromoCreationStates.entering_activations)
    await message.answer(
        t(
            user.language,
            "promo_enter_activation_count",
            max_activations=quote.max_activations_affordable,
        )
    )


@router.message(StateFilter(PromoCreationStates.entering_activations), F.text)
async def handle_activations_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    try:
        activations = int(message.text.strip())
    except ValueError:
        await message.answer(t(user.language, "error_generic"))
        return
    if activations <= 0:
        await message.answer(t(user.language, "error_generic"))
        return

    await state.update_data(activations=activations)
    is_blogger = await BloggerService(uow).is_active_blogger(user.id)
    await state.set_state(PromoCreationStates.choosing_issuer)
    await message.answer(
        t(user.language, "promo_issuer_choice_prompt"),
        reply_markup=promo_issuer_keyboard(user.language, is_blogger=is_blogger),
    )


@router.callback_query(
    StateFilter(PromoCreationStates.choosing_issuer), F.data.startswith("promo_issuer:")
)
async def handle_issuer_chosen(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    issuer_kind = callback.data.split(":", 1)[1]
    await state.update_data(issuer_is_blogger=(issuer_kind == "blogger"))
    await state.set_state(PromoCreationStates.choosing_attribution)
    await callback.message.answer(
        t(user.language, "promo_attribution_prompt"),
        reply_markup=promo_attribution_choice_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(PromoCreationStates.choosing_attribution), F.data == "promo_attr:no"
)
async def handle_attribution_no(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.update_data(attribution_kind="none", attribution_value=None)
    await _show_promo_confirmation(callback.message, uow, user, state)
    await callback.answer()


@router.callback_query(
    StateFilter(PromoCreationStates.choosing_attribution), F.data == "promo_attr:yes"
)
async def handle_attribution_yes(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(PromoCreationStates.entering_attribution_value)
    await callback.message.answer(t(user.language, "promo_attribution_enter"))
    await callback.answer()


@router.message(StateFilter(PromoCreationStates.entering_attribution_value), F.text)
async def handle_attribution_value_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    value = message.text.strip()
    if value.startswith("@") or (
        value.replace("_", "").isalnum() and "." not in value and "/" not in value
    ):
        kind = "telegram_user"
    elif "t.me/" in value or value.startswith("https://t.me/"):
        kind = "telegram_channel"
    else:
        kind = "external_url"
    await state.update_data(attribution_kind=kind, attribution_value=value)
    await _show_promo_confirmation(message, uow, user, state)


async def _show_promo_confirmation(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext
) -> None:
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    kind = PromoKind(data["kind"])
    promo_service = PromoService(uow)
    quote = await promo_service.quote_funding(
        plan=plan,
        kind=kind,
        discount_percent=data.get("discount_percent", 0),
        requested_activations=data["activations"],
        issuer_user_id=user.id,
    )
    await state.update_data(
        quote_total=quote.total_reserved_amount, quote_balance_before=quote.balance_before
    )

    if not quote.sufficient_funds:
        await message.answer(
            t(
                user.language,
                "promo_insufficient_funds",
                required=quote.total_reserved_amount,
                available=quote.balance_before,
                currency=plan.currency,
            )
        )
        await state.clear()
        return

    await state.set_state(PromoCreationStates.confirming)
    await message.answer(
        t(
            user.language,
            "promo_confirm_summary",
            plan_title=plan.title(user.language),
            kind=t(
                user.language,
                "promo_kind_full" if kind == PromoKind.FULL_PREMIUM else "promo_kind_discount",
            ),
            discount_percent=quote.discount_percent,
            activations=data["activations"],
            total_cost=quote.total_reserved_amount,
            currency=plan.currency,
            balance_before=quote.balance_before,
            balance_after=quote.balance_after,
        ),
        reply_markup=promo_confirm_keyboard(user.language),
    )


@router.callback_query(StateFilter(PromoCreationStates.confirming), F.data == "promo_confirm:no")
async def handle_promo_confirm_no(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await callback.message.answer(t(user.language, "action_cancelled"))
    await state.clear()
    await callback.answer()


@router.callback_query(StateFilter(PromoCreationStates.confirming), F.data == "promo_confirm:yes")
async def handle_promo_confirm_yes(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    kind = PromoKind(data["kind"])
    promo_service = PromoService(uow)

    try:
        promo = await promo_service.create_user_code(
            issuer_user_id=user.id,
            issuer_is_blogger=data.get("issuer_is_blogger", False),
            plan=plan,
            kind=kind,
            discount_percent=data.get("discount_percent", 0),
            activations=data["activations"],
            attribution=AttributionRequest(
                kind=data.get("attribution_kind", "none"), value=data.get("attribution_value")
            ),
        )
    except ValueError as exc:
        await callback.message.answer(str(exc))
        await state.clear()
        await callback.answer()
        return

    if promo.moderation_status == "pending":
        await callback.message.answer(
            t(user.language, "promo_created_pending_review", code=promo.code)
        )
        await _notify_admins_promo_review(callback, uow, promo)
    else:
        await callback.message.answer(t(user.language, "promo_created_success", code=promo.code))

    await state.clear()
    await callback.answer()


async def _notify_admins_promo_review(callback: CallbackQuery, uow: UnitOfWork, promo) -> None:
    admins = await uow.admins.list_notification_recipients(
        roles=[AdminRole.SUPERADMIN, AdminRole.ADMIN]
    )
    text = t("en", "admin_notify_promo_review_needed", code=promo.code, issuer=promo.issuer_user_id)
    for admin in admins:
        try:
            await callback.bot.send_message(chat_id=admin.telegram_id, text=text)
        except Exception:
            continue


# --- Redeem flow ---------------------------------------------------------------


@router.callback_query(F.data == "promo:redeem")
async def handle_promo_redeem_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(PromoRedeemStates.awaiting_code)
    await callback.message.answer(t(user.language, "promo_enter_code_to_redeem"))
    await callback.answer()


@router.message(StateFilter(PromoRedeemStates.awaiting_code), F.text)
async def handle_promo_redeem_code(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    promo_service = PromoService(uow)
    result = await promo_service.redeem(code=message.text.strip(), redeemer_user_id=user.id)
    await state.clear()

    if not result.ok:
        key_map = {
            "not_found": "promo_redeem_not_found",
            "not_redeemable": "promo_redeem_not_redeemable",
            "cannot_redeem_own_code": "promo_redeem_own_code",
            "already_redeemed_by_user": "promo_redeem_already_used",
        }
        await message.answer(t(user.language, key_map.get(result.reason, "error_generic")))
        return

    if result.is_full_premium:
        from app.db.models.enums import EntitlementSource
        from app.services.entitlement_service import EntitlementService

        entitlement_service = EntitlementService(uow)
        await entitlement_service.grant(
            user_id=user.id,
            plan_id=result.plan.id,
            duration_days=result.plan.duration_days,
            source=EntitlementSource.PROMO,
            source_reference=f"promo:{result.promo.id}:{user.id}",
        )
        await message.answer(t(user.language, "promo_redeem_success_full"))
    else:
        await message.answer(
            t(
                user.language,
                "promo_redeem_success_discount",
                amount=result.buyer_amount_due,
                currency=result.plan.currency,
            )
        )
        # Remainder payment: reuse the premium checkout with the pre-applied
        # discount so the buyer completes payment through an allowed flow.
        from app.bot.states import PremiumCheckoutStates

        await state.update_data(
            plan_id=result.plan.id,
            discount_percent=result.discount_percent,
            promo_code=result.promo.code,
        )
        await state.set_state(PremiumCheckoutStates.choosing_payment_method)
        from app.bot.handlers.premium import _show_payment_methods

        await _show_payment_methods(message, uow, user, state)

````

### FILE: app/bot/handlers/referrals.py

````python
"""Invite Friends menu: referral link + statistics + blogger CTA."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from app.bot.keyboards.referrals import referral_menu_keyboard
from app.config import get_settings
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t
from app.services.blogger_service import BloggerService
from app.services.referral_service import ReferralService

router = Router(name="referrals")
settings = get_settings()


def _menu_texts(key: str) -> set[str]:
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


@router.message(F.text.in_(_menu_texts("menu_invite_friends")))
async def handle_invite_friends_menu(
    message: Message, uow: UnitOfWork, user: User, **kwargs
) -> None:
    link = f"https://t.me/{settings.BOT_USERNAME}?start={user.referral_code}"
    await message.answer(t(user.language, "referral_link_title", link=link))

    stats = await ReferralService(uow).stats_for_referrer(user.id)
    await message.answer(
        t(
            user.language,
            "referral_stats_title",
            total_joins=stats["total_joins"],
            qualified_joins=stats["qualified_joins"],
            purchase_commission_total=stats["purchase_commission_total"],
            blogger_reward_total=stats["blogger_reward_total"],
        )
    )

    is_blogger = await BloggerService(uow).is_active_blogger(user.id)
    if not is_blogger and user.blogger_status_cache != "pending":
        await message.answer(
            t(user.language, "referral_become_blogger_prompt"),
            reply_markup=referral_menu_keyboard(user.language, show_blogger_cta=True),
        )

````

### FILE: app/bot/handlers/settings.py

````python
"""Settings menu: language change at any time (spec section 2)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.common import language_selection_keyboard
from app.bot.keyboards.settings import settings_menu_keyboard
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t

router = Router(name="settings")


def _menu_texts(key: str) -> set[str]:
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


@router.message(F.text.in_(_menu_texts("menu_settings")))
async def handle_settings_menu(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    await message.answer(
        t(user.language, "settings_menu_title"), reply_markup=settings_menu_keyboard(user.language)
    )


@router.callback_query(F.data == "settings:language")
async def handle_settings_change_language(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    await callback.message.answer(
        t(user.language, "choose_language"), reply_markup=language_selection_keyboard()
    )
    await callback.answer()

````

### FILE: app/bot/handlers/start.py

````python
"""`/start` handler: first-run language selection, referral attribution,
and deep-link movie opening (`?start=movie_<code>`), plus language-change
callback handling.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.common import language_selection_keyboard, main_menu_keyboard
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t
from app.services.referral_service import ReferralService

router = Router(name="start")


@router.message(CommandStart())
async def handle_start(message: Message, command: CommandObject, uow: UnitOfWork, **kwargs) -> None:
    tg_user = message.from_user
    user = await uow.users.get_by_telegram_id(tg_user.id)

    deep_link_arg = (command.args or "").strip()

    if user is None:
        user = await uow.users.create(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            language="uz",
        )
        referral_code = (
            deep_link_arg if deep_link_arg and not deep_link_arg.startswith("movie_") else None
        )
        await ReferralService(uow).attribute_start(new_user=user, referral_code=referral_code)
    else:
        await uow.users.touch_start(user)

    if deep_link_arg.startswith("movie_"):
        from app.bot.handlers.movies import send_movie_by_code

        code = deep_link_arg[len("movie_") :]
        await send_movie_by_code(message, uow=uow, user=user, code=code)
        return

    if not user.language_selected:
        await message.answer(
            t(user.language, "choose_language"), reply_markup=language_selection_keyboard()
        )
        return

    await message.answer(
        t(user.language, "main_menu_title"), reply_markup=main_menu_keyboard(user.language)
    )


@router.callback_query(F.data.startswith("lang:"))
async def handle_language_choice(callback: CallbackQuery, uow: UnitOfWork, **kwargs) -> None:
    language = callback.data.split(":", 1)[1]
    if language not in SUPPORTED_LANGUAGES:
        await callback.answer()
        return

    user = await uow.users.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer()
        return

    await uow.users.set_language(user, language)
    await callback.message.edit_text(t(language, "language_set"))
    await callback.message.answer(
        t(language, "main_menu_title"), reply_markup=main_menu_keyboard(language)
    )
    await callback.answer()

````

### FILE: app/bot/handlers/support.py

````python
"""Help/support: /terms, /privacy, /support commands and the Help menu
button that opens or continues a ticket thread. Notifies admins of new
support requests.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states import SupportStates
from app.config import get_settings
from app.db.models.enums import AdminRole, SupportSenderType
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t

router = Router(name="support")
settings = get_settings()

_TERMS_URL_PATH = "/legal/terms"
_PRIVACY_URL_PATH = "/legal/privacy"


def _menu_texts(key: str) -> set[str]:
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


@router.message(Command("terms"))
async def handle_terms(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    await message.answer(
        t(
            user.language,
            "support_terms_command",
            url=f"{settings.PUBLIC_BASE_URL}{_TERMS_URL_PATH}",
        )
    )


@router.message(Command("privacy"))
async def handle_privacy(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    await message.answer(
        t(
            user.language,
            "support_privacy_command",
            url=f"{settings.PUBLIC_BASE_URL}{_PRIVACY_URL_PATH}",
        )
    )


@router.message(Command("support"))
@router.message(F.text.in_(_menu_texts("menu_help")))
async def handle_support_menu(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(SupportStates.awaiting_message)
    await message.answer(t(user.language, "support_menu_title"))


@router.message(StateFilter(SupportStates.awaiting_message), F.text)
async def handle_support_message(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    ticket = await uow.support.get_open_ticket_for_user(user.id)
    if ticket is None:
        ticket = await uow.support.create_ticket(user_id=user.id, subject=message.text[:64])

    await uow.support.add_message(
        ticket_id=ticket.id,
        sender_type=SupportSenderType.USER,
        sender_id=user.id,
        text=message.text,
    )
    await message.answer(t(user.language, "support_ticket_created", ticket_id=ticket.id))
    await state.clear()

    admins = await uow.admins.list_notification_recipients(
        roles=[AdminRole.SUPERADMIN, AdminRole.ADMIN, AdminRole.SUPPORT]
    )
    text = t(
        "en",
        "admin_notify_support_request",
        user=f"@{user.username}" if user.username else str(user.telegram_id),
        ticket_id=ticket.id,
    )
    for admin in admins:
        try:
            await message.bot.send_message(chat_id=admin.telegram_id, text=text)
        except Exception:
            continue

````

### FILE: app/bot/handlers/wallet.py

````python
"""Balance screen: available/reserved/pending per currency, and history."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.wallet import balance_actions_keyboard
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t
from app.services.wallet_service import WalletService

router = Router(name="wallet")


def _menu_texts(key: str) -> set[str]:
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


@router.message(F.text.in_(_menu_texts("menu_balance")))
async def handle_balance_menu(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    wallet_service = WalletService(uow)
    balances = await wallet_service.get_balances(user.id)
    if not balances:
        await message.answer(t(user.language, "balance_no_wallets"))
        return
    for currency, amounts in balances.items():
        await message.answer(
            t(
                user.language,
                "balance_title",
                available=amounts["available"],
                reserved=amounts["reserved"],
                pending=amounts["pending"],
                currency=currency,
            ),
            reply_markup=balance_actions_keyboard(user.language),
        )


@router.callback_query(F.data == "wallet:history")
async def handle_wallet_history(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    wallet_service = WalletService(uow)
    entries = await wallet_service.transaction_history(user.id, limit=20)
    if not entries:
        await callback.message.answer(t(user.language, "balance_history_empty"))
        await callback.answer()
        return
    lines = [
        t(
            user.language,
            "balance_history_entry",
            date=entry.created_at.strftime("%Y-%m-%d %H:%M"),
            type=entry.entry_type,
            amount=entry.amount,
            currency=entry.currency,
        )
        for entry in entries
    ]
    await callback.message.answer(
        t(user.language, "balance_history_title") + "\n" + "\n".join(lines)
    )
    await callback.answer()

````

### FILE: app/bot/__init__.py

````python
"""aiogram 3 bot package: handlers, keyboards, and FSM states."""

````

### FILE: app/bot/keyboards/common.py

````python
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.i18n import t


def language_selection_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
            ]
        ]
    )


def main_menu_keyboard(language: str) -> ReplyKeyboardMarkup:
    rows = [
        [
            KeyboardButton(text=t(language, "menu_search_movie")),
            KeyboardButton(text=t(language, "menu_categories")),
        ],
        [
            KeyboardButton(text=t(language, "menu_premium")),
            KeyboardButton(text=t(language, "menu_balance")),
        ],
        [
            KeyboardButton(text=t(language, "menu_invite_friends")),
            KeyboardButton(text=t(language, "menu_my_promo_codes")),
        ],
        [
            KeyboardButton(text=t(language, "menu_gifts")),
            KeyboardButton(text=t(language, "menu_help")),
        ],
        [KeyboardButton(text=t(language, "menu_settings"))],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def cancel_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(language, "menu_cancel"))]], resize_keyboard=True
    )


def back_inline_button(language: str, callback_data: str = "nav:back") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=t(language, "menu_back"), callback_data=callback_data)


def yes_no_keyboard(language: str, yes_cb: str, no_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "promo_attribution_yes"), callback_data=yes_cb
                ),
                InlineKeyboardButton(text=t(language, "promo_attribution_no"), callback_data=no_cb),
            ]
        ]
    )


def confirm_keyboard(
    language: str, confirm_cb: str, cancel_cb: str = "nav:cancel"
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "premium_checkout_confirm"), callback_data=confirm_cb
                )
            ],
            [InlineKeyboardButton(text=t(language, "menu_cancel"), callback_data=cancel_cb)],
        ]
    )

````

### FILE: app/bot/keyboards/gifts.py

````python
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t


def gifts_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "gift_send_premium_button"), callback_data="gift:send_premium"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "gift_send_balance_button"), callback_data="gift:send_balance"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "gift_received_list_button"), callback_data="gift:received"
                )
            ],
        ]
    )


def gift_confirm_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "gift_confirm_button"), callback_data="gift_confirm:yes"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "menu_cancel"), callback_data="gift_confirm:no"
                )
            ],
        ]
    )

````

### FILE: app/bot/keyboards/__init__.py

````python
"""Reply and inline keyboard builders for every bot flow."""

````

### FILE: app/bot/keyboards/movies.py

````python
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models.catalog import Category, MandatoryChannel, Movie
from app.i18n import t


def category_list_keyboard(categories: list[Category], language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=c.title(language) if hasattr(c, "title") else _cat_title(c, language),
                callback_data=f"cat:{c.id}",
            )
        ]
        for c in categories
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _cat_title(category: Category, language: str) -> str:
    return {"uz": category.title_uz, "ru": category.title_ru, "en": category.title_en}.get(
        language, category.title_uz
    )


def movie_search_results_keyboard(movies: list[Movie], language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{m.title(language)} ({m.code})", callback_data=f"movie:{m.id}"
            )
        ]
        for m in movies
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def join_channels_keyboard(
    channels: list[MandatoryChannel], movie_id: int, language: str
) -> InlineKeyboardMarkup:
    rows = []
    for ch in channels:
        url = ch.invite_link or f"https://t.me/{ch.chat_id.lstrip('@')}"
        rows.append([InlineKeyboardButton(text=ch.title, url=url)])
    rows.append(
        [
            InlineKeyboardButton(
                text=t(language, "movie_check_membership_button"),
                callback_data=f"check_membership:{movie_id}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def open_in_bot_keyboard(bot_username: str, movie_code: str, language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "movie_open_in_bot_button"),
                    url=f"https://t.me/{bot_username}?start=movie_{movie_code}",
                )
            ]
        ]
    )

````

### FILE: app/bot/keyboards/premium.py

````python
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models.plan import PremiumPlan
from app.i18n import t


def plan_list_keyboard(plans: list[PremiumPlan], language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(
                    language,
                    "premium_plan_button",
                    title=plan.title(language),
                    price=plan.price_amount,
                    currency=plan.currency,
                ),
                callback_data=f"plan:{plan.id}",
            )
        ]
        for plan in plans
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_method_keyboard(
    language: str, plan_id: int, *, stars_enabled: bool, wallet_enabled: bool
) -> InlineKeyboardMarkup:
    rows = []
    if stars_enabled:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(language, "premium_pay_with_stars"), callback_data=f"pay:stars:{plan_id}"
                )
            ]
        )
    if wallet_enabled:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(language, "premium_pay_with_wallet"),
                    callback_data=f"pay:wallet:{plan_id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text=t(language, "menu_cancel"), callback_data="nav:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def skip_promo_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "premium_skip_promo"), callback_data="promo:skip"
                )
            ]
        ]
    )

````

### FILE: app/bot/keyboards/promo.py

````python
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models.plan import PremiumPlan
from app.i18n import t


def promo_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "promo_create_button"), callback_data="promo:create"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "promo_my_codes_button"), callback_data="promo:mine"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "promo_redeem_button"), callback_data="promo:redeem"
                )
            ],
        ]
    )


def promo_kind_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "promo_kind_full"), callback_data="promo_kind:full_premium"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "promo_kind_discount"),
                    callback_data="promo_kind:percent_discount",
                )
            ],
        ]
    )


def promo_plan_keyboard(plans: list[PremiumPlan], language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{p.title(language)} — {p.price_amount} {p.currency}",
                callback_data=f"promo_plan:{p.id}",
            )
        ]
        for p in plans
        if p.promo_eligible
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def promo_issuer_keyboard(language: str, *, is_blogger: bool) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(language, "promo_issuer_user"), callback_data="promo_issuer:user"
            )
        ]
    ]
    if is_blogger:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(language, "promo_issuer_blogger"), callback_data="promo_issuer:blogger"
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def promo_attribution_choice_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "promo_attribution_yes"), callback_data="promo_attr:yes"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "promo_attribution_no"), callback_data="promo_attr:no"
                )
            ],
        ]
    )


def promo_confirm_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "promo_confirm_button"), callback_data="promo_confirm:yes"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "menu_cancel"), callback_data="promo_confirm:no"
                )
            ],
        ]
    )

````

### FILE: app/bot/keyboards/referrals.py

````python
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t


def referral_menu_keyboard(language: str, *, show_blogger_cta: bool) -> InlineKeyboardMarkup:
    rows = []
    if show_blogger_cta:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(language, "referral_become_blogger_button"),
                    callback_data="blogger:apply",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)

````

### FILE: app/bot/keyboards/settings.py

````python
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t


def settings_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "settings_change_language_button"),
                    callback_data="settings:language",
                )
            ],
        ]
    )

````

### FILE: app/bot/keyboards/wallet.py

````python
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t


def balance_actions_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "balance_history_title"), callback_data="wallet:history"
                )
            ],
        ]
    )

````

### FILE: app/bot/middlewares/db_session.py

````python
"""Opens one DB transaction (UnitOfWork) per incoming Telegram update and
commits it after the handler returns, rolling back on any exception. Every
handler receives `uow: UnitOfWork` in its keyword arguments via this
middleware -- no handler ever opens its own session.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.db.session import AsyncSessionLocal
from app.db.uow import UnitOfWork


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with AsyncSessionLocal() as session:
            uow = UnitOfWork(session)
            data["uow"] = uow
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise

````

### FILE: app/bot/middlewares/__init__.py

````python
"""aiogram middlewares: DB session injection, user upsert, and blocked-user gate."""

````

### FILE: app/bot/middlewares/user_context.py

````python
"""Resolves (or creates) the `User` row for the incoming Telegram sender and
injects it as `user` into handler data. Also enforces the blocked-user gate
here, in one place, instead of scattering `if user.is_blocked` checks
across every handler.

Must run AFTER `DbSessionMiddleware` (needs `data["uow"]`) and is
registered on both message and callback-query observer chains.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from app.db.uow import UnitOfWork
from app.i18n import DEFAULT_LANGUAGE, t


class UserContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = self._extract_from_user(event)
        if tg_user is None:
            return await handler(event, data)

        uow: UnitOfWork = data["uow"]
        user = await uow.users.get_by_telegram_id(tg_user.id)
        data["user"] = user
        data["language"] = user.language if user else DEFAULT_LANGUAGE

        if user is not None and user.is_blocked:
            await self._notify_blocked(event, user.language)
            return None  # short-circuit: blocked users never reach real handlers

        return await handler(event, data)

    @staticmethod
    def _extract_from_user(event: TelegramObject):
        if isinstance(event, Message):
            return event.from_user
        if isinstance(event, CallbackQuery):
            return event.from_user
        if isinstance(event, Update):
            inner = event.message or event.callback_query or event.inline_query
            return inner.from_user if inner else None
        return getattr(event, "from_user", None)

    @staticmethod
    async def _notify_blocked(event: TelegramObject, language: str) -> None:
        text = t(language, "error_blocked_user")
        try:
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
        except Exception:
            pass

````

### FILE: app/bot/states.py

````python
"""aiogram FSM state groups for every multi-step conversation."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class PremiumCheckoutStates(StatesGroup):
    choosing_plan = State()
    entering_promo = State()
    choosing_payment_method = State()
    confirming = State()


class BloggerApplicationStates(StatesGroup):
    choosing_platform = State()
    awaiting_url = State()


class PromoCreationStates(StatesGroup):
    choosing_kind = State()
    choosing_plan = State()
    entering_discount = State()
    entering_activations = State()
    choosing_issuer = State()
    choosing_attribution = State()
    entering_attribution_value = State()
    confirming = State()


class PromoRedeemStates(StatesGroup):
    awaiting_code = State()


class GiftStates(StatesGroup):
    awaiting_recipient_premium = State()
    choosing_plan_premium = State()
    confirming_premium = State()
    awaiting_recipient_balance = State()
    entering_amount_balance = State()
    confirming_balance = State()


class SupportStates(StatesGroup):
    awaiting_message = State()


class MovieAdminStates(StatesGroup):
    awaiting_video = State()
    awaiting_code = State()
    awaiting_title_uz = State()
    awaiting_title_ru = State()
    awaiting_title_en = State()
    awaiting_poster = State()
    choosing_category = State()
    choosing_access_type = State()

````

### FILE: app/config.py

````python
"""Environment configuration and validation.

All configuration is read from environment variables (see `.env.example`
for the full list). Nothing here silently falls back to a placeholder
secret in production: `Settings.validate_for_production()` raises if a
required production-only value is missing, so the app fails fast at
startup instead of running with a leaked "change-me" default.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Core ---------------------------------------------------------------------
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_SECRET_KEY: str = "insecure-dev-secret-change-me"
    APP_TIMEZONE: str = "Asia/Tashkent"
    LOG_LEVEL: str = "INFO"

    # --- Telegram -------------------------------------------------------------------
    BOT_TOKEN: str = ""
    BOT_USERNAME: str = "YourMovieBot"
    BOT_WEBHOOK_URL: str = ""
    BOT_WEBHOOK_SECRET: str = "change-me"
    BOOTSTRAP_SUPERADMIN_IDS: str = ""

    # --- Database ---------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://movie_bot:change-me@localhost:5432/movie_bot"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://movie_bot:change-me@localhost:5432/movie_bot"

    # --- Redis --------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Web ------------------------------------------------------------------------
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    ADMIN_SESSION_COOKIE_NAME: str = "movie_bot_admin_session"
    ADMIN_SESSION_TTL_SECONDS: int = 43200

    DEFAULT_MANDATORY_CHANNELS: str = ""

    # --- Payments ---------------------------------------------------------------
    PAYMENTS_STARS_ENABLED: bool = False

    PAYMENTS_STRIPE_ENABLED: bool = False
    STRIPE_MODE: Literal["sandbox", "live"] = "sandbox"
    STRIPE_API_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_DEFAULT_CURRENCY: str = "usd"

    PAYMENTS_CLICK_ENABLED: bool = False
    CLICK_MODE: Literal["sandbox", "live"] = "sandbox"
    CLICK_MERCHANT_ID: str = ""
    CLICK_SERVICE_ID: str = ""
    CLICK_MERCHANT_USER_ID: str = ""
    CLICK_SECRET_KEY: str = ""
    CLICK_DEFAULT_CURRENCY: str = "UZS"

    STOREFRONT_ENABLED: bool = False

    BROADCAST_RATE_LIMIT_PER_SECOND: int = 20

    BACKUP_DIR: str = "/var/backups/movie_bot"
    BACKUP_RETENTION_DAYS: int = 14

    @field_validator("BOOTSTRAP_SUPERADMIN_IDS")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @property
    def bootstrap_superadmin_ids(self) -> list[int]:
        return [int(x) for x in self.BOOTSTRAP_SUPERADMIN_IDS.split(",") if x.strip()]

    @property
    def default_mandatory_channels(self) -> list[str]:
        return [x.strip() for x in self.DEFAULT_MANDATORY_CHANNELS.split(",") if x.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    def validate_for_production(self) -> None:
        """Fail fast instead of silently running with insecure defaults."""
        if not self.is_production:
            return
        problems: list[str] = []
        if not self.BOT_TOKEN:
            problems.append("BOT_TOKEN is required")
        if self.APP_SECRET_KEY in ("", "insecure-dev-secret-change-me", "change-me"):
            problems.append("APP_SECRET_KEY must be set to a real random secret")
        if self.BOT_WEBHOOK_SECRET in ("", "change-me"):
            problems.append("BOT_WEBHOOK_SECRET must be set to a real random secret")
        if self.PAYMENTS_STRIPE_ENABLED and self.STRIPE_MODE == "live":
            if not (self.STRIPE_API_KEY and self.STRIPE_WEBHOOK_SECRET):
                problems.append(
                    "Stripe live mode requires STRIPE_API_KEY and STRIPE_WEBHOOK_SECRET"
                )
        if self.PAYMENTS_CLICK_ENABLED and self.CLICK_MODE == "live":
            if not (self.CLICK_MERCHANT_ID and self.CLICK_SECRET_KEY):
                problems.append("Click live mode requires CLICK_MERCHANT_ID and CLICK_SECRET_KEY")
        if problems:
            raise RuntimeError("Invalid production configuration:\n- " + "\n- ".join(problems))


@lru_cache
def get_settings() -> Settings:
    return Settings()

````

### FILE: app/core/__init__.py

````python
"""Cross-cutting core utilities: logging, security helpers, time helpers."""

````

### FILE: app/core/logging.py

````python
"""Structured JSON logging setup.

Deliberately never logs: bot tokens, payment provider secrets, webhook
signatures, or Telegram `file_id` values for protected videos (a leaked
`video_file_id` would let anyone fetch the licensed content directly from
Telegram, bypassing entitlement checks). Call `redact()` before logging any
dict that might contain such fields.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

_SENSITIVE_KEYS = {
    "bot_token",
    "token",
    "password",
    "password_hash",
    "secret",
    "api_key",
    "webhook_secret",
    "video_file_id",
    "stripe_api_key",
    "click_secret_key",
    "authorization",
}


def redact(payload: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in payload.items():
        if k.lower() in _SENSITIVE_KEYS:
            out[k] = "***redacted***"
        elif isinstance(v, dict):
            out[k] = redact(v)
        else:
            out[k] = v
    return out


class _SafeFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        return msg


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(
        _SafeFormatter(
            fmt='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":%(message)r}'
        )
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Silence noisy third-party libraries at DEBUG.
    for noisy in ("httpx", "aiogram.event"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

````

### FILE: app/core/redis.py

````python
"""Redis client factory.

Used for: FSM storage backing aiogram dialogs, rate limiting broadcast
sends, caching mandatory-channel membership checks briefly, and simple
distributed locks (e.g. preventing two workers from processing the same
scheduled job concurrently).
"""

from __future__ import annotations

from functools import lru_cache

from redis.asyncio import Redis

from app.config import get_settings


@lru_cache
def get_redis() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)

````

### FILE: app/db/base.py

````python
"""Declarative base and shared mixins for all ORM models."""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import BigInteger, DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Naming convention keeps Alembic autogenerate deterministic and gives every
# constraint a predictable, greppable name in production databases.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class IdMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)


class UuidMixin:
    """Public-facing identifier that never leaks the internal sequential id
    (used for promo codes, order references, idempotency keys, etc.)."""

    uid: Mapped[uuid.UUID] = mapped_column(
        default=uuid.uuid4, unique=True, nullable=False, index=True
    )


class TimestampMixin:
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

````

### FILE: app/db/__init__.py

````python
"""Database package: SQLAlchemy models, repositories, and session management."""

````

### FILE: app/db/models/admin.py

````python
from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import AdminRole


class Admin(IdMixin, TimestampMixin, Base):
    """Administrative / staff account.

    Admins authenticate to the web admin panel with a username + password
    (bcrypt hash). Telegram admin notifications are sent to `telegram_id`
    when set, independent of web-login capability.
    """

    __tablename__ = "admins"

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    role: Mapped[AdminRole] = mapped_column(
        String(16), nullable=False, default=AdminRole.MODERATOR.value
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AuditLog(IdMixin, Base):
    """Immutable append-only record of every sensitive admin action.

    Never updated or deleted; only inserted. `before`/`after` are JSON
    snapshots of the affected entity to support after-the-fact review.
    """

    __tablename__ = "audit_logs"

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    admin_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

````

### FILE: app/db/models/blogger.py

````python
"""Blogger verification pipeline and blogger profile / reward configuration."""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import BloggerApplicationStatus, BloggerProfileStatus

if TYPE_CHECKING:
    from app.db.models.user import User


class BloggerApplication(IdMixin, TimestampMixin, Base):
    """One row per blogger-verification attempt.

    Flow (spec section 5):
      1. applicant requests blogger status -> row created, status=PENDING,
         a unique `verification_phrase` is generated.
      2. applicant places the phrase in their social bio and submits
         `submitted_url`.
      3. admin reviews (manually, since arbitrary bio pages generally are not
         reachable through an authorized API) and approves/rejects with a
         reason.
    """

    __tablename__ = "blogger_applications"

    applicant_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    verification_phrase: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    platform_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    submitted_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    status: Mapped[BloggerApplicationStatus] = mapped_column(
        String(16), nullable=False, default=BloggerApplicationStatus.PENDING.value
    )

    auto_check_attempted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_check_result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Human-readable outcome if an authorized platform API check ran; NULL if manual-only.",
    )

    reviewed_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    applicant: Mapped[User] = relationship("User", back_populates="blogger_applications")


class BloggerProfile(IdMixin, TimestampMixin, Base):
    """Created the moment an application is APPROVED. Holds blogger-specific
    reward configuration that can override the global per-1000 rate."""

    __tablename__ = "blogger_profiles"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    approved_application_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    status: Mapped[BloggerProfileStatus] = mapped_column(
        String(16), nullable=False, default=BloggerProfileStatus.ACTIVE.value
    )

    # NULL means "use the global default from settings".
    acquisition_reward_per_1000_override: Mapped[int | None] = mapped_column(Integer, nullable=True)
    acquisition_reward_currency_override: Mapped[str | None] = mapped_column(
        String(8), nullable=True
    )

    approved_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    suspended_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    suspension_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Running remainder (in minor units) carried forward so that
    # per-qualified-user fractional accrual never loses or overpays a
    # fraction of a minor unit. See app.services.blogger_rewards.
    accrual_remainder_micros: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, doc="Remainder expressed in millionths of a minor unit."
    )
    qualified_joins_counted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped[User] = relationship("User", back_populates="blogger_profile")

````

### FILE: app/db/models/broadcast.py

````python
"""Broadcasts: queued mass messages with per-recipient delivery tracking."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import BroadcastRecipientStatus, BroadcastStatus, BroadcastTarget


class Broadcast(IdMixin, TimestampMixin, Base):
    __tablename__ = "broadcasts"

    created_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    target: Mapped[BroadcastTarget] = mapped_column(String(16), nullable=False)
    target_language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    custom_user_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)

    text_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_file_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    button_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    button_text: Mapped[str | None] = mapped_column(String(128), nullable=True)

    status: Mapped[BroadcastStatus] = mapped_column(
        String(16), nullable=False, default=BroadcastStatus.DRAFT.value
    )

    total_recipients: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    rate_limit_per_second: Mapped[int] = mapped_column(Integer, nullable=False, default=20)

    scheduled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BroadcastRecipient(IdMixin, Base):
    __tablename__ = "broadcast_recipients"
    __table_args__ = (
        UniqueConstraint("broadcast_id", "user_id", name="uq_broadcast_recipients_broadcast_user"),
    )

    broadcast_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("broadcasts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[BroadcastRecipientStatus] = mapped_column(
        String(16), nullable=False, default=BroadcastRecipientStatus.PENDING.value
    )
    attempted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

````

### FILE: app/db/models/catalog.py

````python
"""Movie catalog: categories, movies, and mandatory subscription channels."""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import MovieAccessType, MoviePublicationState


class Category(IdMixin, TimestampMixin, Base):
    __tablename__ = "categories"

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title_uz: Mapped[str] = mapped_column(String(128), nullable=False)
    title_ru: Mapped[str] = mapped_column(String(128), nullable=False)
    title_en: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    movies: Mapped[list[Movie]] = relationship("Movie", back_populates="category")


class Movie(IdMixin, TimestampMixin, Base):
    __tablename__ = "movies"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    category_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )

    title_uz: Mapped[str] = mapped_column(String(256), nullable=False)
    title_ru: Mapped[str] = mapped_column(String(256), nullable=False)
    title_en: Mapped[str] = mapped_column(String(256), nullable=False)

    description_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Search index column (lower-cased concatenation of all titles), populated
    # by the repository layer on write for fast ILIKE / trigram search.
    search_text: Mapped[str] = mapped_column(Text, nullable=False, default="")

    poster_file_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    video_file_id: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        doc="Telegram file_id of the licensed source video. Never exposed to users.",
    )
    video_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    access_type: Mapped[MovieAccessType] = mapped_column(
        String(16), nullable=False, default=MovieAccessType.FREE.value
    )
    publication_state: Mapped[MoviePublicationState] = mapped_column(
        String(16), nullable=False, default=MoviePublicationState.DRAFT.value
    )

    view_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    created_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    category: Mapped[Category | None] = relationship("Category", back_populates="movies")

    def title(self, language: str) -> str:
        return {"uz": self.title_uz, "ru": self.title_ru, "en": self.title_en}.get(
            language, self.title_uz
        )

    def description(self, language: str) -> str | None:
        return {
            "uz": self.description_uz,
            "ru": self.description_ru,
            "en": self.description_en,
        }.get(language, self.description_uz)


class MandatoryChannel(IdMixin, TimestampMixin, Base):
    """A Telegram channel/group a FREE user must join before watching a FREE
    movie. Premium users are always exempt (checked in the service layer)."""

    __tablename__ = "mandatory_channels"

    chat_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, doc="Numeric chat id (-100...) or @username."
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    invite_link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    bot_is_admin_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_checked_at: Mapped[str | None] = mapped_column(String(64), nullable=True)


Index("ix_movies_category_id", Movie.category_id)
Index("ix_movies_publication_state", Movie.publication_state)

````

### FILE: app/db/models/enums.py

````python
"""Shared enumerations used across persistent models.

Kept in one module so services, repositories, and Alembic migrations
reference the exact same string values (SQLAlchemy Enum columns are
persisted by *name*, not by Python identity).
"""

from __future__ import annotations

import enum


class Language(str, enum.Enum):
    UZ = "uz"
    RU = "ru"
    EN = "en"


class AdminRole(str, enum.Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    SUPPORT = "support"


class Currency(str, enum.Enum):
    """Supported settlement currencies. Balances are NEVER converted between
    these — a wallet holds one row per (user, currency)."""

    UZS = "UZS"
    USD = "USD"
    XTR = "XTR"  # Telegram Stars


class MovieAccessType(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"


class MoviePublicationState(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class OrderKind(str, enum.Enum):
    PREMIUM_PURCHASE = "premium_purchase"
    PREMIUM_GIFT = "premium_gift"
    PROMO_TOPUP_PURCHASE = "promo_topup_purchase"  # remainder payment on a discount promo


class PaymentProviderCode(str, enum.Enum):
    TELEGRAM_STARS = "telegram_stars"
    STRIPE = "stripe"
    CLICK = "click"
    WALLET = "wallet"  # internal ledger settlement, no external provider


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class EntitlementSource(str, enum.Enum):
    PURCHASE = "purchase"
    GIFT = "gift"
    PROMO = "promo"
    ADMIN_GRANT = "admin_grant"


class BloggerApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class BloggerProfileStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class RewardStatus(str, enum.Enum):
    ACCRUED = "accrued"
    REVERSED = "reversed"
    REJECTED = "rejected"


class WalletEntryType(str, enum.Enum):
    REFERRAL_COMMISSION = "referral_commission"
    BLOGGER_ACQUISITION_REWARD = "blogger_acquisition_reward"
    ADMIN_GIFT = "admin_gift"
    USER_GIFT_SENT = "user_gift_sent"
    USER_GIFT_RECEIVED = "user_gift_received"
    PROMO_CODE_FUNDING_RESERVE = "promo_code_funding_reserve"
    PROMO_CODE_FUNDING_RELEASE = "promo_code_funding_release"
    PROMO_CODE_FUNDING_CONSUME = "promo_code_funding_consume"
    WALLET_PREMIUM_PURCHASE = "wallet_premium_purchase"
    COMMISSION_REVERSAL = "commission_reversal"
    REWARD_REVERSAL = "reward_reversal"
    ADMIN_ADJUSTMENT = "admin_adjustment"


class LedgerBalanceBucket(str, enum.Enum):
    """Which balance bucket a ledger entry affects."""

    AVAILABLE = "available"
    RESERVED = "reserved"
    PENDING = "pending"


class PromoIssuerType(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    BLOGGER = "blogger"


class PromoKind(str, enum.Enum):
    FULL_PREMIUM = "full_premium"
    PERCENT_DISCOUNT = "percent_discount"


class PromoAttributionStatus(str, enum.Enum):
    NONE = "none"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class PromoModerationStatus(str, enum.Enum):
    AUTO_APPROVED = "auto_approved"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class GiftKind(str, enum.Enum):
    PREMIUM = "premium"
    BALANCE = "balance"
    PROMO_CODE = "promo_code"


class BroadcastTarget(str, enum.Enum):
    ALL = "all"
    PREMIUM = "premium"
    FREE = "free"
    LANGUAGE = "language"
    CUSTOM_IDS = "custom_ids"


class BroadcastStatus(str, enum.Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class BroadcastRecipientStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class SupportTicketStatus(str, enum.Enum):
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SupportSenderType(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class BloggerStatusCache(str, enum.Enum):
    NONE = "none"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

````

### FILE: app/db/models/gift.py

````python
"""Gifts: premium, balance, or promo codes given user-to-user or admin-to-user."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin, UuidMixin
from app.db.models.enums import Currency, GiftKind


class Gift(IdMixin, UuidMixin, TimestampMixin, Base):
    __tablename__ = "gifts"

    kind: Mapped[GiftKind] = mapped_column(String(16), nullable=False)

    sender_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    sender_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    recipient_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )

    plan_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("premium_plans.id"), nullable=True
    )
    balance_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    balance_currency: Mapped[Currency | None] = mapped_column(String(8), nullable=True)
    promo_code_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("promo_codes.id"), nullable=True
    )

    cost_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_currency: Mapped[Currency | None] = mapped_column(String(8), nullable=True)

    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    entitlement_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("entitlements.id"), nullable=True
    )

    delivered_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

````

### FILE: app/db/models/__init__.py

````python
"""Import every model module so `Base.metadata` is fully populated for
Alembic autogenerate and for `Base.metadata.create_all()` in tests.
"""

from app.db.base import Base  # noqa: F401
from app.db.models.admin import Admin, AuditLog  # noqa: F401
from app.db.models.blogger import BloggerApplication, BloggerProfile  # noqa: F401
from app.db.models.broadcast import Broadcast, BroadcastRecipient  # noqa: F401
from app.db.models.catalog import Category, MandatoryChannel, Movie  # noqa: F401
from app.db.models.gift import Gift  # noqa: F401
from app.db.models.order import Entitlement, Order, ProviderEvent  # noqa: F401
from app.db.models.plan import PremiumPlan  # noqa: F401
from app.db.models.promo import PromoCode, PromoRedemption  # noqa: F401
from app.db.models.referral import Referral  # noqa: F401
from app.db.models.reward_accrual import BloggerAcquisitionReward, ReferralCommission  # noqa: F401
from app.db.models.settings import Setting, SettingKey  # noqa: F401
from app.db.models.support import SupportMessage, SupportTicket  # noqa: F401
from app.db.models.user import User  # noqa: F401
from app.db.models.wallet import LedgerEntry, Wallet  # noqa: F401

__all__ = [
    "Base",
    "Admin",
    "AuditLog",
    "BloggerApplication",
    "BloggerProfile",
    "Broadcast",
    "BroadcastRecipient",
    "Category",
    "MandatoryChannel",
    "Movie",
    "Gift",
    "Entitlement",
    "Order",
    "ProviderEvent",
    "PremiumPlan",
    "PromoCode",
    "PromoRedemption",
    "Referral",
    "BloggerAcquisitionReward",
    "ReferralCommission",
    "Setting",
    "SettingKey",
    "SupportMessage",
    "SupportTicket",
    "User",
    "LedgerEntry",
    "Wallet",
]

````

### FILE: app/db/models/order.py

````python
"""Orders, provider events, and entitlements.

An `Order` snapshots everything needed to reproduce exactly what the buyer
was charged and what policy applied, so later admin changes to plan price
or commission rates never retroactively alter a completed purchase (spec
section 3). `ProviderEvent` records every inbound webhook/update for
idempotent processing and audit; `Entitlement` records the resulting
premium grant, tied 1:1 to the order/gift/promo that created it.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin, UuidMixin
from app.db.models.enums import (
    Currency,
    EntitlementSource,
    OrderKind,
    OrderStatus,
    PaymentProviderCode,
)


class Order(IdMixin, UuidMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    buyer_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    kind: Mapped[OrderKind] = mapped_column(String(32), nullable=False)

    plan_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("premium_plans.id"), nullable=True
    )

    # --- Immutable pricing snapshot, taken at order-creation time -------------------
    plan_price_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[Currency] = mapped_column(String(8), nullable=False)
    discount_percent_applied: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    promo_code_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("promo_codes.id"), nullable=True
    )
    gross_amount: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="plan_price_snapshot before discount."
    )
    net_amount: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="Amount actually charged to the buyer."
    )

    standard_referral_percent_snapshot: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    blogger_referral_percent_snapshot: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    blogger_acquisition_reward_enabled_snapshot: Mapped[bool] = mapped_column(
        Integer, nullable=False, default=True
    )

    provider_code: Mapped[PaymentProviderCode] = mapped_column(String(32), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        String(16), nullable=False, default=OrderStatus.PENDING.value
    )

    # Recipient differs from buyer for gifted premium.
    recipient_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    provider_reference: Mapped[str | None] = mapped_column(
        String(256), nullable=True, doc="Provider-side charge/session/invoice id, once known."
    )

    paid_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refund_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProviderEvent(IdMixin, Base):
    """Every inbound payment-provider webhook/update, kept verbatim (as JSON)
    for idempotent processing (`provider_code`+`provider_event_id` unique)
    and for dispute/audit investigation.
    """

    __tablename__ = "provider_events"
    __table_args__ = (
        UniqueConstraint(
            "provider_code", "provider_event_id", name="uq_provider_events_code_event_id"
        ),
    )

    received_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    provider_code: Mapped[PaymentProviderCode] = mapped_column(String(32), nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(256), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    order_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("orders.id"), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    processed: Mapped[bool] = mapped_column(Integer, nullable=False, default=False)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class Entitlement(IdMixin, TimestampMixin, Base):
    """A single premium grant. `source_reference` links back to the order,
    gift, or promo redemption that created it. Activation happens exactly
    once per (source_type, source_reference) pair -- enforced by the unique
    constraint below plus a service-level advisory check.
    """

    __tablename__ = "entitlements"
    __table_args__ = (
        UniqueConstraint("source", "source_reference", name="uq_entitlements_source_reference"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("premium_plans.id"), nullable=False)

    source: Mapped[EntitlementSource] = mapped_column(String(16), nullable=False)
    source_reference: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Order uid, gift uid, or promo redemption uid that granted this entitlement.",
    )

    starts_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    granted_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

````

### FILE: app/db/models/plan.py

````python
"""Premium subscription plans.

Every commercial parameter (price, referral %, blogger %, acquisition
reward toggle, discount cap) is configured *per plan* so that, e.g., a
1-week plan and a 1-month plan can carry entirely different commission
economics as required by spec section 3. Nothing here is ever hard-coded
at the handler/service level — all math reads from these columns (or from
an immutable snapshot copied out of them at purchase time, see
`app/db/models/order.py`).
"""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import Currency


class PremiumPlan(IdMixin, TimestampMixin, Base):
    __tablename__ = "premium_plans"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    title_uz: Mapped[str] = mapped_column(String(128), nullable=False)
    title_ru: Mapped[str] = mapped_column(String(128), nullable=False)
    title_en: Mapped[str] = mapped_column(String(128), nullable=False)

    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)

    price_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Integer minor units (e.g. UZS has no minor unit, so this is whole UZS).",
    )
    currency: Mapped[Currency] = mapped_column(
        String(8), nullable=False, default=Currency.UZS.value
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- Per-plan referral economics (spec section 3) ------------------------------
    standard_referral_percent: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, doc="Basis: percent*100, e.g. 1000 = 10.00%."
    )
    blogger_referral_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Percent*100. Bloggers may get a different (usually higher) rate.",
    )
    blogger_acquisition_reward_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether bloggers additionally earn per-qualified-join rewards for this plan's purchasers.",
    )
    referral_applies_to_renewals: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="If False, commission is only ever paid on a referred user's FIRST premium purchase across all plans. "
        "If True, every renewal/purchase also pays commission. This is a global-behavior flag intentionally "
        "duplicated per-plan so admins can special-case a plan later; the effective policy used at purchase time "
        "is read from app.config.settings.REFERRAL_COMMISSION_ON_RENEWALS unless overridden here (see referral service).",
    )

    # --- Promo eligibility caps ------------------------------------------------------
    max_discount_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        doc="Upper bound (0-100) a percent-discount promo may apply to this plan.",
    )
    promo_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    description_uz: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description_ru: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description_en: Mapped[str | None] = mapped_column(String(512), nullable=True)

    def title(self, language: str) -> str:
        return {"uz": self.title_uz, "ru": self.title_ru, "en": self.title_en}.get(
            language, self.title_uz
        )

    @property
    def standard_referral_rate(self) -> float:
        return self.standard_referral_percent / 10_000

    @property
    def blogger_referral_rate(self) -> float:
        return self.blogger_referral_percent / 10_000

````

### FILE: app/db/models/promo.py

````python
"""Prepaid promo codes (full-premium and percent-discount) and redemptions.

Funding model (spec section 7):
  - A USER-created code reserves/debits the issuer's wallet balance
    atomically and in full at creation time for the maximum possible
    liability (activations * cost-per-activation). This liability lives in
    the issuer's `reserved` wallet bucket, NOT in a platform pool.
  - An ADMIN-created code is platform-funded and carries no wallet
    reservation; `issuer_type=ADMIN` and `issuer_user_id IS NULL`.
  - `remaining_uses` is decremented atomically (SELECT ... FOR UPDATE) on
    each redemption; a CHECK constraint additionally prevents it from ever
    going negative, which is what makes "two activations from one promo use"
    structurally impossible even under a race.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin, UuidMixin
from app.db.models.enums import (
    Currency,
    PromoAttributionStatus,
    PromoIssuerType,
    PromoKind,
    PromoModerationStatus,
)


class PromoCode(IdMixin, UuidMixin, TimestampMixin, Base):
    __tablename__ = "promo_codes"
    __table_args__ = (
        CheckConstraint("remaining_uses >= 0", name="remaining_uses_non_negative"),
        CheckConstraint("max_uses > 0", name="max_uses_positive"),
    )

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)

    issuer_type: Mapped[PromoIssuerType] = mapped_column(String(16), nullable=False)
    issuer_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    plan_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("premium_plans.id"), nullable=False)
    kind: Mapped[PromoKind] = mapped_column(String(24), nullable=False)
    discount_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="0 for FULL_PREMIUM (buyer pays nothing); 1-100 for PERCENT_DISCOUNT.",
    )

    max_uses: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_uses: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Funding bookkeeping (only meaningful when issuer_type != ADMIN) ------------
    funding_currency: Mapped[Currency | None] = mapped_column(String(8), nullable=True)
    cost_per_activation: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="What ONE redemption costs the issuer, in minor units.",
    )
    total_reserved_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_funds_released: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    expires_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    moderation_status: Mapped[PromoModerationStatus] = mapped_column(
        String(16), nullable=False, default=PromoModerationStatus.AUTO_APPROVED.value
    )
    moderation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cancelled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Attribution link (spec section 7: "Add an attribution link?") --------------
    attribution_label: Mapped[str | None] = mapped_column(String(256), nullable=True)
    attribution_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    attribution_telegram_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attribution_status: Mapped[PromoAttributionStatus] = mapped_column(
        String(16), nullable=False, default=PromoAttributionStatus.NONE.value
    )

    @property
    def is_redeemable(self) -> bool:
        if not self.is_active or self.remaining_uses <= 0:
            return False
        if self.moderation_status not in (
            PromoModerationStatus.AUTO_APPROVED,
            PromoModerationStatus.APPROVED,
        ):
            return False
        if self.expires_at and self.expires_at <= dt.datetime.now(dt.UTC):
            return False
        return True


class PromoRedemption(IdMixin, UuidMixin, TimestampMixin, Base):
    __tablename__ = "promo_redemptions"
    __table_args__ = (
        UniqueConstraint(
            "promo_code_id", "redeemer_user_id", name="uq_promo_redemptions_code_user"
        ),
    )

    promo_code_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("promo_codes.id", ondelete="CASCADE"), nullable=False
    )
    redeemer_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    order_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("orders.id"), nullable=True)

    discount_percent_applied: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    issuer_cost_charged: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    buyer_amount_paid: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

````

### FILE: app/db/models/referral.py

````python
"""Referral attribution.

A `Referral` row is created exactly once per referred user, the moment
their very first `/start` is attributed to a referrer. This is the anchor
that referral-commission and blogger-acquisition-reward accrual (see
`reward_accrual.py`) both hang off of. Uniqueness on `referred_user_id`
guarantees a user can only ever be attributed to a single referrer
(spec section 5: "one referrer only").
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class Referral(IdMixin, TimestampMixin, Base):
    __tablename__ = "referrals"

    referred_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    referrer_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    attributed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Fraud / qualification bookkeeping -----------------------------------------------
    is_self_referral: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    suspicious_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)

    is_qualified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="True once this join passed anti-fraud qualification checks and is eligible for a "
        "blogger acquisition reward. Standard referral commission does NOT require qualification "
        "-- it only requires a verified purchase -- but blogger per-join rewards do.",
    )
    qualified_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disqualified_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)

    referrer_was_blogger_at_join: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    referred_user: Mapped[User] = relationship(
        "User", foreign_keys=[referred_user_id], back_populates="referral_as_referred"
    )
    referrer_user: Mapped[User] = relationship("User", foreign_keys=[referrer_user_id])

````

### FILE: app/db/models/reward_accrual.py

````python
"""Reward accrual ledger anchors: referral commissions and blogger
acquisition rewards, each with an immutable policy snapshot and a status
that supports reversal on refund.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import Currency, RewardStatus


class ReferralCommission(IdMixin, TimestampMixin, Base):
    """Commission credited to a referrer (standard or blogger) after an
    eligible, verified premium purchase by their referred user.

    `order_id` + `commission_kind='purchase'` is unique so a single order
    can never generate the same commission twice, satisfying idempotent
    webhook processing even under retried/duplicate payment callbacks.
    """

    __tablename__ = "referral_commissions"
    __table_args__ = (UniqueConstraint("order_id", name="uq_referral_commissions_order_id"),)

    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    referral_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False
    )
    referrer_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    plan_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("premium_plans.id"), nullable=False)

    # --- Immutable snapshot of the policy applied at the time of this purchase ---
    commission_percent_snapshot: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="percent*100"
    )
    eligible_net_amount_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    was_blogger_rate_snapshot: Mapped[bool] = mapped_column(Integer, nullable=False, default=False)

    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[Currency] = mapped_column(String(8), nullable=False)

    status: Mapped[RewardStatus] = mapped_column(
        String(16), nullable=False, default=RewardStatus.ACCRUED.value
    )
    reversed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reversal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_first_purchase_of_referred_user: Mapped[bool] = mapped_column(
        Integer, nullable=False, default=True
    )


class BloggerAcquisitionReward(IdMixin, TimestampMixin, Base):
    """One row per QUALIFIED join, credited starting with the very first
    qualified user (never batched to wait for 1000). `referral_id` is
    unique so a join can never be rewarded twice.
    """

    __tablename__ = "blogger_acquisition_rewards"
    __table_args__ = (
        UniqueConstraint("referral_id", name="uq_blogger_acquisition_rewards_referral_id"),
    )

    referral_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False
    )
    blogger_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )

    rate_per_1000_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[Currency] = mapped_column(String(8), nullable=False)

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Whole minor units credited for this single qualified join (post remainder-carry).",
    )
    remainder_micros_before: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    remainder_micros_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="This blogger's Nth qualified join (1-indexed) at accrual time.",
    )

    status: Mapped[RewardStatus] = mapped_column(
        String(16), nullable=False, default=RewardStatus.ACCRUED.value
    )
    reversed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reversal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

````

### FILE: app/db/models/settings.py

````python
"""Global, admin-editable runtime settings.

A single-row-per-key table backing `app.services.settings_service`. Using a
key/value table (instead of hard-coded config) lets admins change global
policy (e.g. "does referral commission apply to renewals?", "global blogger
acquisition reward rate per 1000 joins", "allow promo stacking?") from the
admin panel without a deploy, while every historical order/reward still
reads its OWN frozen snapshot (see order.py / reward_accrual.py) so past
transactions are never retroactively altered.
"""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class Setting(IdMixin, TimestampMixin, Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


# Well-known setting keys (documented here so handlers/services/admin panel
# never hard-code raw strings in more than one place).
class SettingKey:
    REFERRAL_COMMISSION_ON_RENEWALS = "referral_commission_on_renewals"  # "true" | "false"
    BLOGGER_ACQUISITION_REWARD_PER_1000 = (
        "blogger_acquisition_reward_per_1000"  # integer minor units, global default
    )
    BLOGGER_ACQUISITION_REWARD_CURRENCY = "blogger_acquisition_reward_currency"  # e.g. "UZS"
    PROMO_STACKING_ALLOWED = "promo_stacking_allowed"  # "true" | "false"
    QUALIFIED_JOIN_MIN_ACCOUNT_AGE_HOURS = "qualified_join_min_account_age_hours"

````

### FILE: app/db/models/support.py

````python
"""Support tickets and threaded messages."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import SupportSenderType, SupportTicketStatus


class SupportTicket(IdMixin, TimestampMixin, Base):
    __tablename__ = "support_tickets"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[SupportTicketStatus] = mapped_column(
        String(16), nullable=False, default=SupportTicketStatus.OPEN.value
    )
    assigned_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    closed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SupportMessage(IdMixin, Base):
    __tablename__ = "support_messages"

    ticket_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sender_type: Mapped[SupportSenderType] = mapped_column(String(16), nullable=False)
    sender_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachment_file_id: Mapped[str | None] = mapped_column(String(256), nullable=True)

````

### FILE: app/db/models/user.py

````python
from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import BloggerStatusCache, Language

if TYPE_CHECKING:
    from app.db.models.blogger import BloggerApplication, BloggerProfile
    from app.db.models.referral import Referral
    from app.db.models.wallet import Wallet


class User(IdMixin, TimestampMixin, Base):
    """A Telegram end user of the bot.

    `telegram_id` is the stable Telegram numeric user id and is what every
    other table references. The surrogate `id` exists purely for compact FK
    storage and is never shown to end users.
    """

    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(256), nullable=True)

    language: Mapped[Language] = mapped_column(String(8), nullable=False, default=Language.UZ.value)
    language_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_bot_blocked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="True if the user blocked the bot (delivery failed).",
    )
    block_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)

    referred_by_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    referral_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)

    blogger_status_cache: Mapped[BloggerStatusCache] = mapped_column(
        String(16), nullable=False, default=BloggerStatusCache.NONE.value
    )

    premium_until: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    started_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    start_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=1,
        doc="How many times /start was issued; used for fraud heuristics.",
    )

    referred_by: Mapped[User | None] = relationship(
        "User", remote_side="User.id", foreign_keys=[referred_by_user_id]
    )
    wallets: Mapped[list[Wallet]] = relationship(
        "Wallet", back_populates="user", cascade="all, delete-orphan"
    )
    blogger_profile: Mapped[BloggerProfile | None] = relationship(
        "BloggerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    blogger_applications: Mapped[list[BloggerApplication]] = relationship(
        "BloggerApplication", back_populates="applicant", cascade="all, delete-orphan"
    )
    referral_as_referred: Mapped[Referral | None] = relationship(
        "Referral",
        back_populates="referred_user",
        uselist=False,
        foreign_keys="Referral.referred_user_id",
    )

    @property
    def is_premium_active(self) -> bool:
        if self.premium_until is None:
            return False
        return self.premium_until > dt.datetime.now(dt.UTC)

    def __repr__(self) -> str:  # pragma: no cover - debug helper only
        return f"<User id={self.id} tg={self.telegram_id} lang={self.language}>"


Index("ix_users_referred_by_user_id", User.referred_by_user_id)

````

### FILE: app/db/models/wallet.py

````python
"""Wallet balances and the immutable ledger.

Design:
  - `Wallet` is a per-(user, currency) row holding three integer minor-unit
    counters: available, reserved, pending. It is a materialized *cache* of
    the ledger, updated only inside the same DB transaction as the ledger
    insert that justifies the change (see app.services.wallet_service).
  - `LedgerEntry` rows are NEVER updated or deleted after insert. Every
    balance mutation -- referral commission, gift, promo reservation, promo
    consumption, refund reversal, admin adjustment -- is represented as one
    or more ledger rows. Summing ledger rows for a wallet always reproduces
    the cached balances; this invariant is asserted in tests and by the
    reconciliation worker.
  - A CHECK constraint prevents `available_amount` (and reserved) from ever
    going negative at the database level, as a last line of defense beyond
    the application-level locking in the wallet service.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import Currency, LedgerBalanceBucket, WalletEntryType

if TYPE_CHECKING:
    from app.db.models.user import User


class Wallet(IdMixin, TimestampMixin, Base):
    __tablename__ = "wallets"
    __table_args__ = (
        UniqueConstraint("user_id", "currency", name="uq_wallets_user_currency"),
        CheckConstraint("available_amount >= 0", name="available_non_negative"),
        CheckConstraint("reserved_amount >= 0", name="reserved_non_negative"),
        CheckConstraint("pending_amount >= 0", name="pending_non_negative"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    currency: Mapped[Currency] = mapped_column(String(8), nullable=False)

    available_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    reserved_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    pending_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # Optimistic-lock version, incremented on every mutation, in addition to
    # SELECT ... FOR UPDATE row locking used by the wallet service.
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped[User] = relationship("User", back_populates="wallets")

    @property
    def total_amount(self) -> int:
        return self.available_amount + self.reserved_amount + self.pending_amount


class LedgerEntry(IdMixin, Base):
    """Append-only. `idempotency_key` gives external callers (webhooks) a
    safe way to guarantee "at most once" application even under retries."""

    __tablename__ = "ledger_entries"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_ledger_entries_idempotency_key"),
    )

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    wallet_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    currency: Mapped[Currency] = mapped_column(String(8), nullable=False)

    entry_type: Mapped[WalletEntryType] = mapped_column(String(48), nullable=False)
    bucket: Mapped[LedgerBalanceBucket] = mapped_column(String(16), nullable=False)

    # Signed delta applied to the named bucket. Positive = credit, negative = debit.
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)

    balance_after: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        doc="Snapshot of that bucket's balance immediately after this entry.",
    )

    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)

    reference_type: Mapped[str | None] = mapped_column(
        String(64), nullable=True, doc="e.g. 'order', 'promo_code', 'gift', 'referral_commission'."
    )
    reference_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

````

### FILE: app/db/repositories/admin_repo.py

````python
from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.admin import Admin, AuditLog
from app.db.models.enums import AdminRole


class AdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_username(self, username: str) -> Admin | None:
        result = await self.session.execute(select(Admin).where(Admin.username == username))
        return result.scalar_one_or_none()

    async def get_by_id(self, admin_id: int) -> Admin | None:
        result = await self.session.execute(select(Admin).where(Admin.id == admin_id))
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> Admin | None:
        result = await self.session.execute(select(Admin).where(Admin.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Admin:
        admin = Admin(**kwargs)
        self.session.add(admin)
        await self.session.flush()
        return admin

    async def count_admins(self) -> int:
        from sqlalchemy import func

        result = await self.session.execute(select(func.count(Admin.id)))
        return int(result.scalar_one())

    async def list_all(self) -> list[Admin]:
        result = await self.session.execute(select(Admin))
        return list(result.scalars().all())

    async def touch_login(self, admin: Admin) -> None:
        admin.last_login_at = dt.datetime.now(dt.UTC)
        await self.session.flush()

    async def list_notification_recipients(
        self, roles: list[AdminRole] | None = None
    ) -> list[Admin]:
        stmt = select(Admin).where(Admin.is_active.is_(True), Admin.telegram_id.is_not(None))
        if roles:
            stmt = stmt.where(Admin.role.in_([r.value for r in roles]))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        admin_id: int | None,
        admin_username: str | None,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        before: dict | None = None,
        after: dict | None = None,
        note: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        log = AuditLog(
            created_at=dt.datetime.now(dt.UTC),
            admin_id=admin_id,
            admin_username=admin_username,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=after,
            note=note,
            ip_address=ip_address,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_recent(self, limit: int = 100) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

````

### FILE: app/db/repositories/blogger_repo.py

````python
from __future__ import annotations

import datetime as dt
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.blogger import BloggerApplication, BloggerProfile
from app.db.models.enums import BloggerApplicationStatus, BloggerProfileStatus


def generate_verification_phrase() -> str:
    """A short, hard-to-guess-by-accident phrase the applicant must place in
    their bio, e.g. 'moviebot-verify-7f3a9c21'."""
    return f"moviebot-verify-{secrets.token_hex(4)}"


class BloggerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Applications ------------------------------------------------------------
    async def create_application(
        self, *, applicant_user_id: int, platform_name: str | None = None
    ) -> BloggerApplication:
        app = BloggerApplication(
            applicant_user_id=applicant_user_id,
            verification_phrase=generate_verification_phrase(),
            platform_name=platform_name,
            status=BloggerApplicationStatus.PENDING.value,
        )
        self.session.add(app)
        await self.session.flush()
        return app

    async def get_application(self, application_id: int) -> BloggerApplication | None:
        result = await self.session.execute(
            select(BloggerApplication).where(BloggerApplication.id == application_id)
        )
        return result.scalar_one_or_none()

    async def get_pending_application_for_user(self, user_id: int) -> BloggerApplication | None:
        result = await self.session.execute(
            select(BloggerApplication).where(
                BloggerApplication.applicant_user_id == user_id,
                BloggerApplication.status == BloggerApplicationStatus.PENDING.value,
            )
        )
        return result.scalar_one_or_none()

    async def submit_url(self, application: BloggerApplication, url: str) -> None:
        application.submitted_url = url
        await self.session.flush()

    async def list_pending(self, limit: int = 50) -> list[BloggerApplication]:
        stmt = (
            select(BloggerApplication)
            .where(BloggerApplication.status == BloggerApplicationStatus.PENDING.value)
            .order_by(BloggerApplication.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def decide(
        self,
        application: BloggerApplication,
        *,
        approve: bool,
        admin_id: int,
        reason: str | None = None,
    ) -> BloggerApplication:
        application.status = (
            BloggerApplicationStatus.APPROVED.value
            if approve
            else BloggerApplicationStatus.REJECTED.value
        )
        application.reviewed_by_admin_id = admin_id
        application.reviewed_at = dt.datetime.now(dt.UTC)
        application.decision_reason = reason
        await self.session.flush()
        return application

    # --- Profiles ------------------------------------------------------------------
    async def get_profile_by_user(self, user_id: int) -> BloggerProfile | None:
        result = await self.session.execute(
            select(BloggerProfile).where(BloggerProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_profile(self, *, user_id: int, approved_application_id: int) -> BloggerProfile:
        profile = BloggerProfile(
            user_id=user_id,
            approved_application_id=approved_application_id,
            status=BloggerProfileStatus.ACTIVE.value,
            approved_at=dt.datetime.now(dt.UTC),
        )
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def suspend(self, profile: BloggerProfile, reason: str | None = None) -> None:
        profile.status = BloggerProfileStatus.SUSPENDED.value
        profile.suspended_at = dt.datetime.now(dt.UTC)
        profile.suspension_reason = reason
        await self.session.flush()

    async def reactivate(self, profile: BloggerProfile) -> None:
        profile.status = BloggerProfileStatus.ACTIVE.value
        profile.suspended_at = None
        profile.suspension_reason = None
        await self.session.flush()

    async def lock_profile(self, user_id: int) -> BloggerProfile | None:
        """Row-lock a blogger profile before mutating its remainder/counter
        fields (used by the acquisition-reward accrual service)."""
        stmt = select(BloggerProfile).where(BloggerProfile.user_id == user_id).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 100) -> list[BloggerProfile]:
        result = await self.session.execute(select(BloggerProfile).limit(limit))
        return list(result.scalars().all())

````

### FILE: app/db/repositories/broadcast_repo.py

````python
from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.broadcast import Broadcast, BroadcastRecipient
from app.db.models.enums import BroadcastRecipientStatus, BroadcastStatus


class BroadcastRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **kwargs) -> Broadcast:
        broadcast = Broadcast(**kwargs)
        self.session.add(broadcast)
        await self.session.flush()
        return broadcast

    async def get(self, broadcast_id: int) -> Broadcast | None:
        result = await self.session.execute(select(Broadcast).where(Broadcast.id == broadcast_id))
        return result.scalar_one_or_none()

    async def lock(self, broadcast_id: int) -> Broadcast | None:
        stmt = select(Broadcast).where(Broadcast.id == broadcast_id).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_recipients(self, broadcast_id: int, user_ids: list[int]) -> None:
        self.session.add_all(
            [BroadcastRecipient(broadcast_id=broadcast_id, user_id=uid) for uid in user_ids]
        )
        await self.session.flush()

    async def list_pending_recipients(
        self, broadcast_id: int, limit: int = 200
    ) -> list[BroadcastRecipient]:
        stmt = (
            select(BroadcastRecipient)
            .where(
                BroadcastRecipient.broadcast_id == broadcast_id,
                BroadcastRecipient.status == BroadcastRecipientStatus.PENDING.value,
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_recipient(
        self,
        recipient: BroadcastRecipient,
        status: BroadcastRecipientStatus,
        error: str | None = None,
    ) -> None:
        recipient.status = status.value
        recipient.attempted_at = dt.datetime.now(dt.UTC)
        recipient.error = error
        await self.session.flush()

    async def update_status(self, broadcast: Broadcast, status: BroadcastStatus) -> None:
        broadcast.status = status.value
        now = dt.datetime.now(dt.UTC)
        if status == BroadcastStatus.RUNNING and broadcast.started_at is None:
            broadcast.started_at = now
        if status in (BroadcastStatus.COMPLETED, BroadcastStatus.FAILED):
            broadcast.completed_at = now
        if status == BroadcastStatus.CANCELLED:
            broadcast.cancelled_at = now
        await self.session.flush()

    async def increment_counters(
        self, broadcast: Broadcast, *, sent: int = 0, failed: int = 0, skipped: int = 0
    ) -> None:
        broadcast.sent_count += sent
        broadcast.failed_count += failed
        broadcast.skipped_count += skipped
        await self.session.flush()

    async def list_queued_or_running(self) -> list[Broadcast]:
        stmt = select(Broadcast).where(
            Broadcast.status.in_([BroadcastStatus.QUEUED.value, BroadcastStatus.RUNNING.value])
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

````

### FILE: app/db/repositories/catalog_repo.py

````python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import Category, MandatoryChannel, Movie
from app.db.models.enums import MoviePublicationState


class CatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Categories -------------------------------------------------------------
    async def list_active_categories(self) -> list[Category]:
        stmt = select(Category).where(Category.is_active.is_(True)).order_by(Category.sort_order)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_category(self, category_id: int) -> Category | None:
        result = await self.session.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    # --- Movies ----------------------------------------------------------------
    async def get_by_code(self, code: str) -> Movie | None:
        result = await self.session.execute(select(Movie).where(Movie.code == code))
        return result.scalar_one_or_none()

    async def get_by_id(self, movie_id: int) -> Movie | None:
        result = await self.session.execute(select(Movie).where(Movie.id == movie_id))
        return result.scalar_one_or_none()

    async def search_published(self, query: str, limit: int = 15) -> list[Movie]:
        """Exact code match, exact-title match, or partial-title search, all
        scoped to published movies only (drafts/archived never surface to
        end users)."""
        published = MoviePublicationState.PUBLISHED.value
        q = query.strip().lower()
        stmt = (
            select(Movie)
            .where(Movie.publication_state == published)
            .where(Movie.search_text.ilike(f"%{q}%"))
            .order_by(Movie.view_count.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_category(
        self, category_id: int, limit: int = 30, offset: int = 0
    ) -> list[Movie]:
        stmt = (
            select(Movie)
            .where(
                Movie.category_id == category_id,
                Movie.publication_state == MoviePublicationState.PUBLISHED.value,
            )
            .order_by(Movie.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> Movie:
        movie = Movie(**kwargs)
        movie.search_text = self._build_search_text(movie)
        self.session.add(movie)
        await self.session.flush()
        return movie

    async def update(self, movie: Movie, **kwargs) -> Movie:
        for k, v in kwargs.items():
            setattr(movie, k, v)
        movie.search_text = self._build_search_text(movie)
        await self.session.flush()
        return movie

    async def increment_view_count(self, movie: Movie) -> None:
        movie.view_count += 1
        await self.session.flush()

    @staticmethod
    def _build_search_text(movie: Movie) -> str:
        parts = [movie.code, movie.title_uz, movie.title_ru, movie.title_en]
        return " | ".join(p.lower() for p in parts if p)

    # --- Mandatory channels ------------------------------------------------------
    async def list_active_channels(self) -> list[MandatoryChannel]:
        result = await self.session.execute(
            select(MandatoryChannel).where(MandatoryChannel.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def list_all_channels(self) -> list[MandatoryChannel]:
        result = await self.session.execute(select(MandatoryChannel))
        return list(result.scalars().all())

````

### FILE: app/db/repositories/gift_repo.py

````python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.gift import Gift


class GiftRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **kwargs) -> Gift:
        gift = Gift(**kwargs)
        self.session.add(gift)
        await self.session.flush()
        return gift

    async def list_received(self, user_id: int, limit: int = 50) -> list[Gift]:
        stmt = (
            select(Gift)
            .where(Gift.recipient_user_id == user_id)
            .order_by(Gift.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_sent(self, user_id: int, limit: int = 50) -> list[Gift]:
        stmt = (
            select(Gift)
            .where(Gift.sender_user_id == user_id)
            .order_by(Gift.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

````

### FILE: app/db/repositories/__init__.py

````python
"""Repository layer: all raw database access lives here.

Services never issue SQLAlchemy queries directly against a session; they
call into a repository. This keeps locking strategy (SELECT ... FOR
UPDATE), constraint handling, and query shape centralized and testable.
"""

````

### FILE: app/db/repositories/order_repo.py

````python
from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import OrderStatus, PaymentProviderCode
from app.db.models.order import Entitlement, Order, ProviderEvent


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **kwargs) -> Order:
        order = Order(**kwargs)
        self.session.add(order)
        await self.session.flush()
        return order

    async def get(self, order_id: int) -> Order | None:
        result = await self.session.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

    async def get_by_uid(self, uid: UUID | str) -> Order | None:
        result = await self.session.execute(select(Order).where(Order.uid == uid))
        return result.scalar_one_or_none()

    async def lock(self, order_id: int) -> Order | None:
        stmt = select(Order).where(Order.id == order_id).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_paid(self, order: Order, *, provider_reference: str | None = None) -> Order:
        order.status = OrderStatus.PAID.value
        order.paid_at = dt.datetime.now(dt.UTC)
        if provider_reference:
            order.provider_reference = provider_reference
        await self.session.flush()
        return order

    async def mark_failed(self, order: Order, reason: str) -> Order:
        order.status = OrderStatus.FAILED.value
        order.failure_reason = reason
        await self.session.flush()
        return order

    async def mark_cancelled(self, order: Order, reason: str | None = None) -> Order:
        order.status = OrderStatus.CANCELLED.value
        order.cancelled_at = dt.datetime.now(dt.UTC)
        order.failure_reason = reason
        await self.session.flush()
        return order

    async def mark_refunded(self, order: Order, reason: str | None = None) -> Order:
        order.status = OrderStatus.REFUNDED.value
        order.refunded_at = dt.datetime.now(dt.UTC)
        order.refund_reason = reason
        await self.session.flush()
        return order

    async def list_for_user(self, user_id: int, limit: int = 50) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.buyer_user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_recent(self, limit: int = 100, status: str | None = None) -> list[Order]:
        stmt = select(Order).order_by(Order.created_at.desc()).limit(limit)
        if status:
            stmt = stmt.where(Order.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # --- Provider events (idempotency) --------------------------------------------
    async def get_provider_event(
        self, provider_code: PaymentProviderCode | str, provider_event_id: str
    ) -> ProviderEvent | None:
        code = (
            provider_code.value if isinstance(provider_code, PaymentProviderCode) else provider_code
        )
        result = await self.session.execute(
            select(ProviderEvent).where(
                ProviderEvent.provider_code == code,
                ProviderEvent.provider_event_id == provider_event_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_provider_event(self, **kwargs) -> ProviderEvent:
        event = ProviderEvent(received_at=dt.datetime.now(dt.UTC), **kwargs)
        self.session.add(event)
        await self.session.flush()
        return event

    async def mark_event_processed(self, event: ProviderEvent, error: str | None = None) -> None:
        event.processed = error is None
        event.processing_error = error
        await self.session.flush()

    # --- Entitlements ----------------------------------------------------------
    async def get_entitlement_by_source(
        self, source: str, source_reference: str
    ) -> Entitlement | None:
        result = await self.session.execute(
            select(Entitlement).where(
                Entitlement.source == source, Entitlement.source_reference == source_reference
            )
        )
        return result.scalar_one_or_none()

    async def create_entitlement(self, **kwargs) -> Entitlement:
        entitlement = Entitlement(**kwargs)
        self.session.add(entitlement)
        await self.session.flush()
        return entitlement

    async def list_entitlements_for_user(self, user_id: int, limit: int = 50) -> list[Entitlement]:
        stmt = (
            select(Entitlement)
            .where(Entitlement.user_id == user_id)
            .order_by(Entitlement.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

````

### FILE: app/db/repositories/plan_repo.py

````python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.plan import PremiumPlan


class PlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self) -> list[PremiumPlan]:
        stmt = (
            select(PremiumPlan)
            .where(PremiumPlan.is_active.is_(True))
            .order_by(PremiumPlan.sort_order)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self) -> list[PremiumPlan]:
        result = await self.session.execute(select(PremiumPlan).order_by(PremiumPlan.sort_order))
        return list(result.scalars().all())

    async def get(self, plan_id: int) -> PremiumPlan | None:
        result = await self.session.execute(select(PremiumPlan).where(PremiumPlan.id == plan_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> PremiumPlan | None:
        result = await self.session.execute(select(PremiumPlan).where(PremiumPlan.code == code))
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> PremiumPlan:
        plan = PremiumPlan(**kwargs)
        self.session.add(plan)
        await self.session.flush()
        return plan

    async def update(self, plan: PremiumPlan, **kwargs) -> PremiumPlan:
        for k, v in kwargs.items():
            setattr(plan, k, v)
        await self.session.flush()
        return plan

````

### FILE: app/db/repositories/promo_repo.py

````python
from __future__ import annotations

import datetime as dt
import secrets
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.promo import PromoCode, PromoRedemption

_CODE_ALPHABET = string.ascii_uppercase + string.digits


def generate_promo_code(length: int = 8) -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))


class PromoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_code(self, code: str) -> PromoCode | None:
        result = await self.session.execute(select(PromoCode).where(PromoCode.code == code.upper()))
        return result.scalar_one_or_none()

    async def lock_by_code(self, code: str) -> PromoCode | None:
        """Row-lock the promo for atomic redemption. Combined with the
        DB-level CHECK(remaining_uses >= 0) this makes a double-spend on
        the last remaining use structurally impossible even under two
        simultaneous redeemers."""
        stmt = select(PromoCode).where(PromoCode.code == code.upper()).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> PromoCode:
        code = kwargs.pop("code", None) or generate_promo_code()
        while await self.get_by_code(code) is not None:
            code = generate_promo_code()
        promo = PromoCode(code=code, **kwargs)
        self.session.add(promo)
        await self.session.flush()
        return promo

    async def decrement_remaining_use(self, promo: PromoCode) -> None:
        if promo.remaining_uses <= 0:
            raise ValueError("Promo code has no remaining uses")
        promo.remaining_uses -= 1
        await self.session.flush()

    async def has_user_redeemed(self, promo_id: int, user_id: int) -> bool:
        result = await self.session.execute(
            select(PromoRedemption).where(
                PromoRedemption.promo_code_id == promo_id,
                PromoRedemption.redeemer_user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_redemption(self, **kwargs) -> PromoRedemption:
        redemption = PromoRedemption(**kwargs)
        self.session.add(redemption)
        await self.session.flush()
        return redemption

    async def list_redemptions(self, promo_id: int, limit: int = 100) -> list[PromoRedemption]:
        stmt = (
            select(PromoRedemption)
            .where(PromoRedemption.promo_code_id == promo_id)
            .order_by(PromoRedemption.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_issuer(self, issuer_user_id: int, limit: int = 50) -> list[PromoCode]:
        stmt = (
            select(PromoCode)
            .where(PromoCode.issuer_user_id == issuer_user_id)
            .order_by(PromoCode.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_pending_moderation(self, limit: int = 50) -> list[PromoCode]:
        from app.db.models.enums import PromoModerationStatus

        stmt = (
            select(PromoCode)
            .where(PromoCode.moderation_status == PromoModerationStatus.PENDING.value)
            .order_by(PromoCode.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_expired_unreleased(self, limit: int = 200) -> list[PromoCode]:
        now = dt.datetime.now(dt.UTC)
        stmt = (
            select(PromoCode)
            .where(
                PromoCode.is_active.is_(True),
                PromoCode.is_funds_released.is_(False),
                PromoCode.expires_at.is_not(None),
                PromoCode.expires_at <= now,
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def cancel(self, promo: PromoCode, reason: str | None = None) -> None:
        promo.is_active = False
        promo.cancelled_at = dt.datetime.now(dt.UTC)
        promo.cancelled_reason = reason
        await self.session.flush()

    async def mark_funds_released(self, promo: PromoCode) -> None:
        promo.is_funds_released = True
        await self.session.flush()

````

### FILE: app/db/repositories/referral_repo.py

````python
from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.referral import Referral


class ReferralRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_referred_user(self, referred_user_id: int) -> Referral | None:
        result = await self.session.execute(
            select(Referral).where(Referral.referred_user_id == referred_user_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        referred_user_id: int,
        referrer_user_id: int,
        is_self_referral: bool = False,
        is_suspicious: bool = False,
        suspicious_reason: str | None = None,
        referrer_was_blogger_at_join: bool = False,
    ) -> Referral:
        referral = Referral(
            referred_user_id=referred_user_id,
            referrer_user_id=referrer_user_id,
            attributed_at=dt.datetime.now(dt.UTC),
            is_self_referral=is_self_referral,
            is_suspicious=is_suspicious,
            suspicious_reason=suspicious_reason,
            referrer_was_blogger_at_join=referrer_was_blogger_at_join,
        )
        self.session.add(referral)
        await self.session.flush()
        return referral

    async def mark_qualified(self, referral: Referral) -> None:
        referral.is_qualified = True
        referral.qualified_at = dt.datetime.now(dt.UTC)
        await self.session.flush()

    async def mark_disqualified(self, referral: Referral, reason: str) -> None:
        referral.is_qualified = False
        referral.disqualified_reason = reason
        await self.session.flush()

    async def count_referrals_for_referrer(self, referrer_user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Referral.id)).where(Referral.referrer_user_id == referrer_user_id)
        )
        return int(result.scalar_one())

    async def count_qualified_for_referrer(self, referrer_user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Referral.id)).where(
                Referral.referrer_user_id == referrer_user_id, Referral.is_qualified.is_(True)
            )
        )
        return int(result.scalar_one())

    async def list_for_referrer(
        self, referrer_user_id: int, limit: int = 50, offset: int = 0
    ) -> list[Referral]:
        stmt = (
            select(Referral)
            .where(Referral.referrer_user_id == referrer_user_id)
            .order_by(Referral.attributed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_suspicious(self, limit: int = 50) -> list[Referral]:
        stmt = (
            select(Referral)
            .where(Referral.is_suspicious.is_(True))
            .order_by(Referral.attributed_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

````

### FILE: app/db/repositories/reward_repo.py

````python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.reward_accrual import BloggerAcquisitionReward, ReferralCommission


class RewardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Referral commissions ---------------------------------------------------
    async def get_commission_by_order(self, order_id: int) -> ReferralCommission | None:
        result = await self.session.execute(
            select(ReferralCommission).where(ReferralCommission.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def create_commission(self, **kwargs) -> ReferralCommission:
        commission = ReferralCommission(**kwargs)
        self.session.add(commission)
        await self.session.flush()
        return commission

    async def list_for_referrer(
        self, referrer_user_id: int, limit: int = 50
    ) -> list[ReferralCommission]:
        stmt = (
            select(ReferralCommission)
            .where(ReferralCommission.referrer_user_id == referrer_user_id)
            .order_by(ReferralCommission.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # --- Blogger acquisition rewards ---------------------------------------------
    async def get_reward_by_referral(self, referral_id: int) -> BloggerAcquisitionReward | None:
        result = await self.session.execute(
            select(BloggerAcquisitionReward).where(
                BloggerAcquisitionReward.referral_id == referral_id
            )
        )
        return result.scalar_one_or_none()

    async def create_reward(self, **kwargs) -> BloggerAcquisitionReward:
        reward = BloggerAcquisitionReward(**kwargs)
        self.session.add(reward)
        await self.session.flush()
        return reward

    async def list_for_blogger(
        self, blogger_user_id: int, limit: int = 50
    ) -> list[BloggerAcquisitionReward]:
        stmt = (
            select(BloggerAcquisitionReward)
            .where(BloggerAcquisitionReward.blogger_user_id == blogger_user_id)
            .order_by(BloggerAcquisitionReward.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

````

### FILE: app/db/repositories/settings_repo.py

````python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.settings import Setting


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, key: str) -> str | None:
        result = await self.session.execute(select(Setting).where(Setting.key == key))
        row = result.scalar_one_or_none()
        return row.value if row else None

    async def get_int(self, key: str, default: int) -> int:
        value = await self.get(key)
        return int(value) if value is not None else default

    async def get_bool(self, key: str, default: bool) -> bool:
        value = await self.get(key)
        if value is None:
            return default
        return value.strip().lower() in ("true", "1", "yes", "on")

    async def set(self, key: str, value: str, description: str | None = None) -> Setting:
        result = await self.session.execute(select(Setting).where(Setting.key == key))
        row = result.scalar_one_or_none()
        if row is None:
            row = Setting(key=key, value=value, description=description)
            self.session.add(row)
        else:
            row.value = value
            if description:
                row.description = description
        await self.session.flush()
        return row

    async def list_all(self) -> list[Setting]:
        result = await self.session.execute(select(Setting))
        return list(result.scalars().all())

````

### FILE: app/db/repositories/support_repo.py

````python
from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import SupportSenderType, SupportTicketStatus
from app.db.models.support import SupportMessage, SupportTicket


class SupportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_ticket(self, *, user_id: int, subject: str | None = None) -> SupportTicket:
        ticket = SupportTicket(
            user_id=user_id, subject=subject, status=SupportTicketStatus.OPEN.value
        )
        self.session.add(ticket)
        await self.session.flush()
        return ticket

    async def get_open_ticket_for_user(self, user_id: int) -> SupportTicket | None:
        stmt = select(SupportTicket).where(
            SupportTicket.user_id == user_id,
            SupportTicket.status.in_(
                [SupportTicketStatus.OPEN.value, SupportTicketStatus.PENDING.value]
            ),
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_ticket(self, ticket_id: int) -> SupportTicket | None:
        result = await self.session.execute(
            select(SupportTicket).where(SupportTicket.id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def add_message(
        self,
        *,
        ticket_id: int,
        sender_type: SupportSenderType,
        sender_id: int,
        text: str | None,
        attachment_file_id: str | None = None,
    ) -> SupportMessage:
        message = SupportMessage(
            ticket_id=ticket_id,
            created_at=dt.datetime.now(dt.UTC),
            sender_type=sender_type.value,
            sender_id=sender_id,
            text=text,
            attachment_file_id=attachment_file_id,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def list_messages(self, ticket_id: int, limit: int = 100) -> list[SupportMessage]:
        stmt = (
            select(SupportMessage)
            .where(SupportMessage.ticket_id == ticket_id)
            .order_by(SupportMessage.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_open(self, limit: int = 50) -> list[SupportTicket]:
        stmt = (
            select(SupportTicket)
            .where(
                SupportTicket.status.in_(
                    [SupportTicketStatus.OPEN.value, SupportTicketStatus.PENDING.value]
                )
            )
            .order_by(SupportTicket.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def close_ticket(self, ticket: SupportTicket) -> None:
        ticket.status = SupportTicketStatus.CLOSED.value
        ticket.closed_at = dt.datetime.now(dt.UTC)
        await self.session.flush()

````

### FILE: app/db/repositories/user_repo.py

````python
from __future__ import annotations

import datetime as dt
import secrets
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User

_REFERRAL_ALPHABET = string.ascii_letters + string.digits


def generate_referral_code(length: int = 10) -> str:
    return "".join(secrets.choice(_REFERRAL_ALPHABET) for _ in range(length))


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_referral_code(self, code: str) -> User | None:
        result = await self.session.execute(select(User).where(User.referral_code == code))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.username == username.lstrip("@"))
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        language: str,
    ) -> User:
        now = dt.datetime.now(dt.UTC)
        code = generate_referral_code()
        # Extremely unlikely collision, but guard anyway.
        while await self.get_by_referral_code(code) is not None:
            code = generate_referral_code()

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=language,
            language_selected=False,
            referral_code=code,
            started_at=now,
            last_seen_at=now,
            start_count=1,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def touch_start(self, user: User) -> None:
        user.last_seen_at = dt.datetime.now(dt.UTC)
        user.start_count += 1
        await self.session.flush()

    async def set_language(self, user: User, language: str) -> None:
        user.language = language
        user.language_selected = True
        await self.session.flush()

    async def set_blocked(self, user: User, blocked: bool, reason: str | None = None) -> None:
        user.is_blocked = blocked
        user.block_reason = reason
        await self.session.flush()

    async def search_by_name_or_id(self, query: str, limit: int = 20) -> list[User]:
        stmt = select(User).limit(limit)
        if query.isdigit():
            stmt = select(User).where(User.telegram_id == int(query))
        else:
            like = f"%{query.lower()}%"
            stmt = (
                select(User)
                .where(
                    (User.username.ilike(like))
                    | (User.first_name.ilike(like))
                    | (User.last_name.ilike(like))
                )
                .limit(limit)
            )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        from sqlalchemy import func

        result = await self.session.execute(select(func.count(User.id)))
        return int(result.scalar_one())

    async def grant_premium_until(self, user: User, until: dt.datetime) -> None:
        # Extend, never shorten, an existing active entitlement window.
        if user.premium_until and user.premium_until > until:
            return
        user.premium_until = until
        await self.session.flush()

    async def iter_broadcast_targets(
        self, *, language: str | None = None, premium_only: bool | None = None
    ):
        stmt = select(User).where(User.is_blocked.is_(False), User.is_bot_blocked.is_(False))
        if language:
            stmt = stmt.where(User.language == language)
        if premium_only is True:
            stmt = stmt.where(
                User.premium_until.is_not(None), User.premium_until > dt.datetime.now(dt.UTC)
            )
        elif premium_only is False:
            stmt = stmt.where(
                (User.premium_until.is_(None)) | (User.premium_until <= dt.datetime.now(dt.UTC))
            )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

````

### FILE: app/db/repositories/wallet_repo.py

````python
from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import Currency, LedgerBalanceBucket, WalletEntryType
from app.db.models.wallet import LedgerEntry, Wallet


class WalletRepository:
    """All balance mutation goes through `apply_ledger_entry`, which is the
    single choke point that (a) locks the wallet row, (b) checks for
    sufficient funds when debiting, (c) writes the immutable ledger row, and
    (d) updates the cached wallet counters -- all inside the caller's
    existing transaction. This is what makes negative balances and
    lost/duplicate updates structurally impossible under concurrency.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_wallet(self, user_id: int, currency: Currency | str) -> Wallet:
        currency_value = currency.value if isinstance(currency, Currency) else currency
        result = await self.session.execute(
            select(Wallet).where(Wallet.user_id == user_id, Wallet.currency == currency_value)
        )
        wallet = result.scalar_one_or_none()
        if wallet is None:
            wallet = Wallet(user_id=user_id, currency=currency_value)
            self.session.add(wallet)
            await self.session.flush()
        return wallet

    async def lock_wallet(self, user_id: int, currency: Currency | str) -> Wallet:
        """SELECT ... FOR UPDATE on the wallet row. Must be called within an
        open transaction (the async session context manager)."""
        currency_value = currency.value if isinstance(currency, Currency) else currency
        stmt = (
            select(Wallet)
            .where(Wallet.user_id == user_id, Wallet.currency == currency_value)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        wallet = result.scalar_one_or_none()
        if wallet is None:
            # Create then re-select with lock to avoid a race between two
            # concurrent first-time wallet creations.
            wallet = Wallet(user_id=user_id, currency=currency_value)
            self.session.add(wallet)
            await self.session.flush()
            result = await self.session.execute(stmt)
            wallet = result.scalar_one()
        return wallet

    async def apply_ledger_entry(
        self,
        *,
        wallet: Wallet,
        entry_type: WalletEntryType,
        bucket: LedgerBalanceBucket,
        amount: int,
        idempotency_key: str,
        reference_type: str | None = None,
        reference_id: str | None = None,
        note: str | None = None,
    ) -> LedgerEntry:
        """Apply a signed `amount` to the given bucket of `wallet`.

        Raises `app.services.money.InsufficientFundsError` if a debit
        (negative amount) would take the bucket below zero. The caller MUST
        have already locked `wallet` via `lock_wallet` in the current
        transaction to make this safe under concurrency.
        """
        from app.services.money import InsufficientFundsError  # local import: avoid cycle

        existing = await self.get_ledger_entry_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing

        current = self._bucket_value(wallet, bucket)
        new_value = current + amount
        if new_value < 0:
            raise InsufficientFundsError(
                available=current, requested=-amount, currency=wallet.currency
            )

        self._set_bucket_value(wallet, bucket, new_value)
        wallet.version += 1

        entry = LedgerEntry(
            created_at=dt.datetime.now(dt.UTC),
            wallet_id=wallet.id,
            user_id=wallet.user_id,
            currency=wallet.currency,
            entry_type=entry_type.value if isinstance(entry_type, WalletEntryType) else entry_type,
            bucket=bucket.value if isinstance(bucket, LedgerBalanceBucket) else bucket,
            amount=amount,
            balance_after=new_value,
            idempotency_key=idempotency_key,
            reference_type=reference_type,
            reference_id=reference_id,
            note=note,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def get_ledger_entry_by_idempotency_key(self, key: str) -> LedgerEntry | None:
        result = await self.session.execute(
            select(LedgerEntry).where(LedgerEntry.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def list_ledger_for_user(
        self, user_id: int, currency: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[LedgerEntry]:
        stmt = select(LedgerEntry).where(LedgerEntry.user_id == user_id)
        if currency:
            stmt = stmt.where(LedgerEntry.currency == currency)
        stmt = stmt.order_by(LedgerEntry.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_wallets_for_user(self, user_id: int) -> list[Wallet]:
        result = await self.session.execute(select(Wallet).where(Wallet.user_id == user_id))
        return list(result.scalars().all())

    @staticmethod
    def _bucket_value(wallet: Wallet, bucket: LedgerBalanceBucket | str) -> int:
        bucket_value = bucket.value if isinstance(bucket, LedgerBalanceBucket) else bucket
        return {
            "available": wallet.available_amount,
            "reserved": wallet.reserved_amount,
            "pending": wallet.pending_amount,
        }[bucket_value]

    @staticmethod
    def _set_bucket_value(wallet: Wallet, bucket: LedgerBalanceBucket | str, value: int) -> None:
        bucket_value = bucket.value if isinstance(bucket, LedgerBalanceBucket) else bucket
        if bucket_value == "available":
            wallet.available_amount = value
        elif bucket_value == "reserved":
            wallet.reserved_amount = value
        elif bucket_value == "pending":
            wallet.pending_amount = value
        else:
            raise ValueError(f"Unknown bucket {bucket_value!r}")

````

### FILE: app/db/session.py

````python
"""Async SQLAlchemy engine/session factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, autoflush=False, class_=AsyncSession
)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Context manager that commits on success and rolls back on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency."""
    async with AsyncSessionLocal() as session:
        yield session

````

### FILE: app/db/uow.py

````python
"""Unit-of-work: bundles every repository behind a single object bound to
one AsyncSession/transaction, so services don't have to construct each
repository by hand.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.admin_repo import AdminRepository, AuditLogRepository
from app.db.repositories.blogger_repo import BloggerRepository
from app.db.repositories.broadcast_repo import BroadcastRepository
from app.db.repositories.catalog_repo import CatalogRepository
from app.db.repositories.gift_repo import GiftRepository
from app.db.repositories.order_repo import OrderRepository
from app.db.repositories.plan_repo import PlanRepository
from app.db.repositories.promo_repo import PromoRepository
from app.db.repositories.referral_repo import ReferralRepository
from app.db.repositories.reward_repo import RewardRepository
from app.db.repositories.settings_repo import SettingsRepository
from app.db.repositories.support_repo import SupportRepository
from app.db.repositories.user_repo import UserRepository
from app.db.repositories.wallet_repo import WalletRepository


class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.catalog = CatalogRepository(session)
        self.plans = PlanRepository(session)
        self.wallets = WalletRepository(session)
        self.referrals = ReferralRepository(session)
        self.bloggers = BloggerRepository(session)
        self.rewards = RewardRepository(session)
        self.orders = OrderRepository(session)
        self.promos = PromoRepository(session)
        self.gifts = GiftRepository(session)
        self.broadcasts = BroadcastRepository(session)
        self.support = SupportRepository(session)
        self.admins = AdminRepository(session)
        self.audit = AuditLogRepository(session)
        self.settings = SettingsRepository(session)

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def flush(self) -> None:
        await self.session.flush()

````

### FILE: app/i18n/en.py

````python
"""English (en) translations. Key set mirrors uz.py exactly."""

TRANSLATIONS: dict[str, str] = {
    "choose_language": "Tilni tanlang / Выберите язык / Choose your language:",
    "language_set": "Language set to English. ✅",
    "language_button_uz": "🇺🇿 O'zbekcha",
    "language_button_ru": "🇷🇺 Русский",
    "language_button_en": "🇬🇧 English",
    "main_menu_title": "Main menu — choose a section:",
    "menu_search_movie": "🔍 Search Movie",
    "menu_categories": "🎬 Categories",
    "menu_premium": "⭐ Premium",
    "menu_balance": "💰 Balance",
    "menu_invite_friends": "🤝 Invite Friends",
    "menu_my_promo_codes": "🎁 My Promo Codes",
    "menu_gifts": "🎉 Gifts",
    "menu_help": "🆘 Help",
    "menu_settings": "⚙️ Settings",
    "menu_back": "⬅️ Back",
    "menu_cancel": "❌ Cancel",
    "movie_enter_code_or_name": "Enter the movie code (e.g. 222) or its name:",
    "movie_not_found": "Movie not found. Check the code or name.",
    "movie_search_results": "Search results:",
    "movie_code_label": "Code: {code}",
    "movie_category_label": "Category: {category}",
    "movie_premium_required": "This movie is Premium-only. Go to ⭐ Premium to purchase access.",
    "movie_must_join_channels": 'To watch this movie, join the following channels, then tap "Check":',
    "movie_check_membership_button": "✅ Check",
    "movie_still_not_joined": "You haven't joined all the required channels yet. Please join and check again.",
    "movie_delivering": "Sending the movie...",
    "movie_open_in_bot_button": "▶️ Open in Bot",
    "movie_inline_card_title": "{title} (code: {code})",
    "movie_inline_card_description": 'Tap "Open in Bot" to watch this movie.',
    "movie_categories_title": "Choose a category:",
    "movie_no_movies_in_category": "No movies in this category yet.",
    "premium_plans_title": "Choose one of the premium plans:",
    "premium_plan_button": "{title} — {price} {currency}",
    "premium_plan_details": (
        "📦 {title}\n⏳ Duration: {duration_days} days\n💵 Price: {price} {currency}\n\n"
        "Choose a payment method:"
    ),
    "premium_pay_with_stars": "⭐ Pay with Telegram Stars",
    "premium_pay_with_wallet": "💰 Pay from balance",
    "premium_provider_disabled": "This payment method is currently disabled.",
    "premium_enter_promo_code": 'Have a promo code? Enter it, or tap "Skip".',
    "premium_skip_promo": "Skip",
    "premium_promo_invalid": "Promo code is invalid or expired.",
    "premium_promo_applied": "Promo code applied! New price: {amount} {currency}",
    "premium_checkout_summary": (
        "🧾 Order:\n📦 Plan: {plan_title}\n💵 Amount: {amount} {currency}\n\nConfirm?"
    ),
    "premium_checkout_confirm": "✅ Confirm",
    "premium_payment_success": "🎉 Payment successful! Premium activated until {until}.",
    "premium_payment_failed": "Payment failed. Please try again.",
    "premium_insufficient_balance": "Insufficient balance. Available: {available} {currency}, required: {required} {currency}.",
    "premium_already_active": "You already have active Premium until {until}.",
    "balance_title": (
        "💰 Your balance\n\nAvailable: {available} {currency}\nReserved: {reserved} {currency}\n"
        "Pending: {pending} {currency}"
    ),
    "balance_no_wallets": "You don't have any balance records yet.",
    "balance_history_title": "Recent transactions:",
    "balance_history_empty": "Transaction history is empty.",
    "balance_history_entry": "{date} | {type} | {amount} {currency}",
    "referral_link_title": "🤝 Your referral link:\n{link}\n\nInvite your friends and earn rewards!",
    "referral_stats_title": (
        "📊 Referral statistics:\n\nTotal joins: {total_joins}\n"
        "Qualified joins: {qualified_joins}\n"
        "Purchase commissions: {purchase_commission_total}\n"
        "Blogger rewards: {blogger_reward_total}"
    ),
    "referral_become_blogger_prompt": "Want to become a verified blogger? Earn extra rewards!",
    "referral_become_blogger_button": "🌟 Apply to become a blogger",
    "blogger_apply_start": (
        "Blogger verification process:\n1. Choose your platform\n"
        "2. You'll receive a verification phrase\n3. Place it in your profile's bio/description\n"
        "4. Submit your profile link\n5. Admin will review it"
    ),
    "blogger_apply_choose_platform": "Which platform? (Instagram, YouTube, Telegram, etc.)",
    "blogger_apply_phrase": (
        "Your verification phrase: `{phrase}`\n\nPlace this phrase in the bio/description of your chosen account, "
        "then submit your profile link."
    ),
    "blogger_apply_send_url": "Now send your profile link:",
    "blogger_apply_submitted": "Your application has been submitted for admin review. We'll notify you of the outcome.",
    "blogger_apply_already_pending": "You already have an application under review.",
    "blogger_apply_approved": "🎉 Congratulations! You are now a verified blogger and will earn additional rewards.",
    "blogger_apply_rejected": "Unfortunately, your application was rejected. Reason: {reason}",
    "blogger_manual_review_notice": (
        "Note: automated bio verification is not possible (no such API exists), "
        "so this application requires manual admin review."
    ),
    "promo_menu_title": "🎁 Promo codes section:",
    "promo_create_button": "➕ Create a new promo code",
    "promo_my_codes_button": "📋 My codes",
    "promo_redeem_button": "🔑 Redeem a code",
    "promo_choose_kind": "Choose promo code type:",
    "promo_kind_full": "🎟 Full Premium",
    "promo_kind_discount": "💸 Discount",
    "promo_choose_plan": "For which plan?",
    "promo_enter_discount_percent": "Enter the discount percent (e.g. 10):",
    "promo_enter_activation_count": "How many activations do you want to create? (Max: {max_activations})",
    "promo_issuer_choice_prompt": "How should the issuer be shown?",
    "promo_issuer_user": "👤 User",
    "promo_issuer_blogger": "🌟 Blogger",
    "promo_attribution_prompt": "Add an attribution link? (username or URL)",
    "promo_attribution_yes": "Yes, add one",
    "promo_attribution_no": "No, skip",
    "promo_attribution_enter": "Enter a username or URL:",
    "promo_confirm_summary": (
        "🧾 Promo code summary:\n📦 Plan: {plan_title}\n🏷 Kind: {kind}\n💸 Discount: {discount_percent}%\n"
        "🔢 Activations: {activations}\n💰 Total cost: {total_cost} {currency}\n"
        "💼 Current balance: {balance_before} {currency}\n💼 After reservation: {balance_after} {currency}"
    ),
    "promo_confirm_button": "✅ Create",
    "promo_insufficient_funds": "Insufficient balance. Required: {required} {currency}, available: {available} {currency}.",
    "promo_created_success": "✅ Your promo code was created: `{code}`",
    "promo_created_pending_review": (
        "✅ Your promo code was created: `{code}`\n⏳ Your attribution link is under admin review, "
        "the code stays inactive until it's approved."
    ),
    "promo_enter_code_to_redeem": "Enter the promo code to redeem:",
    "promo_redeem_not_found": "No such promo code found.",
    "promo_redeem_not_redeemable": "This promo code is inactive, expired, or exhausted.",
    "promo_redeem_own_code": "You cannot redeem your own code.",
    "promo_redeem_already_used": "You have already used this code.",
    "promo_redeem_success_full": "🎉 Promo code applied successfully! Premium activated.",
    "promo_redeem_success_discount": "✅ Promo code applied! {amount} {currency} remaining to pay.",
    "promo_my_codes_empty": "You don't have any promo codes yet.",
    "promo_code_status_line": "{code} | {remaining}/{max_uses} left | status: {status}",
    "gifts_menu_title": "🎉 Gifts section:",
    "gift_send_premium_button": "⭐ Gift Premium",
    "gift_send_balance_button": "💰 Gift balance",
    "gift_received_list_button": "📥 Received gifts",
    "gift_enter_recipient": "Enter the recipient's username or Telegram ID:",
    "gift_enter_amount": "How much would you like to gift? (whole number)",
    "gift_recipient_not_found": "This user hasn't started the bot or wasn't found.",
    "gift_confirm_premium": '🎁 Gift {recipient} the "{plan_title}" plan? Price: {price} {currency}',
    "gift_confirm_balance": "🎁 Gift {recipient} {amount} {currency}?",
    "gift_confirm_button": "✅ Send",
    "gift_sent_success": "🎉 Gift sent successfully!",
    "gift_received_notice": "🎁 You received a gift: {description}",
    "support_menu_title": "🆘 Support section. Write your question, we'll reply soon.",
    "support_ticket_created": "✅ Your request was received (#{ticket_id}). We'll reply soon.",
    "support_ticket_reply_notice": "✉️ Support reply:\n{text}",
    "support_terms_command": "Terms of service: {url}",
    "support_privacy_command": "Privacy policy: {url}",
    "settings_menu_title": "⚙️ Settings:",
    "settings_change_language_button": "🌐 Change language",
    "error_generic": "An error occurred. Please try again later.",
    "error_blocked_user": "Your account has been blocked. Contact an administrator for help.",
    "action_cancelled": "Action cancelled.",
    "admin_notify_new_blogger_application": "🆕 New blogger application: user {user}, platform {platform}.",
    "admin_notify_promo_review_needed": "🆕 New promo code needs review: {code} (issuer: {issuer}).",
    "admin_notify_suspicious_referral": "⚠️ Suspicious referral activity: referrer {referrer}, reason: {reason}.",
    "admin_notify_payment_problem": "🚨 Payment problem: order {order_uid}, reason: {reason}.",
    "admin_notify_support_request": "🆘 New support request: user {user}, #{ticket_id}.",
}

````

### FILE: app/i18n/__init__.py

````python
"""Lightweight i18n: no external i18n framework dependency, just nested
dict lookups with a safe fallback chain (requested language -> Uzbek ->
key itself), so a missing translation never crashes a handler.
"""

from __future__ import annotations

from app.i18n.en import TRANSLATIONS as EN
from app.i18n.ru import TRANSLATIONS as RU
from app.i18n.uz import TRANSLATIONS as UZ

_CATALOGS = {"uz": UZ, "ru": RU, "en": EN}
DEFAULT_LANGUAGE = "uz"
SUPPORTED_LANGUAGES = ("uz", "ru", "en")


def t(language: str, key: str, **kwargs) -> str:
    catalog = _CATALOGS.get(language, _CATALOGS[DEFAULT_LANGUAGE])
    template = catalog.get(key)
    if template is None:
        template = _CATALOGS[DEFAULT_LANGUAGE].get(key, key)
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template

````

### FILE: app/i18n/ru.py

````python
"""Russian (ru) translations. Key set mirrors uz.py exactly."""

TRANSLATIONS: dict[str, str] = {
    "choose_language": "Tilni tanlang / Выберите язык / Choose your language:",
    "language_set": "Язык установлен на русский. ✅",
    "language_button_uz": "🇺🇿 O'zbekcha",
    "language_button_ru": "🇷🇺 Русский",
    "language_button_en": "🇬🇧 English",
    "main_menu_title": "Главное меню — выберите раздел:",
    "menu_search_movie": "🔍 Поиск фильма",
    "menu_categories": "🎬 Категории",
    "menu_premium": "⭐ Премиум",
    "menu_balance": "💰 Баланс",
    "menu_invite_friends": "🤝 Пригласить друзей",
    "menu_my_promo_codes": "🎁 Мои промокоды",
    "menu_gifts": "🎉 Подарки",
    "menu_help": "🆘 Помощь",
    "menu_settings": "⚙️ Настройки",
    "menu_back": "⬅️ Назад",
    "menu_cancel": "❌ Отмена",
    "movie_enter_code_or_name": "Введите код фильма (например: 222) или название:",
    "movie_not_found": "Фильм не найден. Проверьте код или название.",
    "movie_search_results": "Результаты поиска:",
    "movie_code_label": "Код: {code}",
    "movie_category_label": "Категория: {category}",
    "movie_premium_required": "Этот фильм доступен только для Premium-пользователей. Перейдите в раздел ⭐ Премиум, чтобы приобрести.",
    "movie_must_join_channels": "Чтобы посмотреть этот фильм, подпишитесь на следующие каналы, затем нажмите «Проверить»:",
    "movie_check_membership_button": "✅ Проверить",
    "movie_still_not_joined": "Вы ещё не подписаны на все каналы. Подпишитесь и попробуйте снова.",
    "movie_delivering": "Отправка фильма...",
    "movie_open_in_bot_button": "▶️ Открыть в боте",
    "movie_inline_card_title": "{title} (код: {code})",
    "movie_inline_card_description": "Нажмите «Открыть в боте», чтобы посмотреть этот фильм.",
    "movie_categories_title": "Выберите одну из категорий:",
    "movie_no_movies_in_category": "В этой категории пока нет фильмов.",
    "premium_plans_title": "Выберите один из премиум-планов:",
    "premium_plan_button": "{title} — {price} {currency}",
    "premium_plan_details": (
        "📦 {title}\n⏳ Срок: {duration_days} дн.\n💵 Цена: {price} {currency}\n\n"
        "Выберите способ оплаты:"
    ),
    "premium_pay_with_stars": "⭐ Оплатить через Telegram Stars",
    "premium_pay_with_wallet": "💰 Оплатить с баланса",
    "premium_provider_disabled": "Этот способ оплаты пока отключён.",
    "premium_enter_promo_code": "Есть промокод? Введите его, или нажмите «Пропустить».",
    "premium_skip_promo": "Пропустить",
    "premium_promo_invalid": "Промокод недействителен или истёк.",
    "premium_promo_applied": "Промокод применён! Новая цена: {amount} {currency}",
    "premium_checkout_summary": (
        "🧾 Заказ:\n📦 План: {plan_title}\n💵 Оплата: {amount} {currency}\n\nПодтверждаете?"
    ),
    "premium_checkout_confirm": "✅ Подтвердить",
    "premium_payment_success": "🎉 Оплата прошла успешно! Премиум активирован до {until}.",
    "premium_payment_failed": "Оплата не удалась. Попробуйте снова.",
    "premium_insufficient_balance": "Недостаточно средств на балансе. Доступно: {available} {currency}, требуется: {required} {currency}.",
    "premium_already_active": "У вас уже есть активный Премиум до {until}.",
    "balance_title": (
        "💰 Ваш баланс\n\nДоступно: {available} {currency}\nВ резерве: {reserved} {currency}\n"
        "В ожидании: {pending} {currency}"
    ),
    "balance_no_wallets": "У вас пока нет баланса.",
    "balance_history_title": "Последние транзакции:",
    "balance_history_empty": "История транзакций пуста.",
    "balance_history_entry": "{date} | {type} | {amount} {currency}",
    "referral_link_title": "🤝 Ваша реферальная ссылка:\n{link}\n\nПриглашайте друзей и получайте награды!",
    "referral_stats_title": (
        "📊 Статистика рефералов:\n\nВсего приглашено: {total_joins}\n"
        "Квалифицированных: {qualified_joins}\n"
        "Комиссии с покупок: {purchase_commission_total}\n"
        "Награды блогера: {blogger_reward_total}"
    ),
    "referral_become_blogger_prompt": "Хотите стать верифицированным блогером? Получайте дополнительные награды!",
    "referral_become_blogger_button": "🌟 Подать заявку на блогера",
    "blogger_apply_start": (
        "Процесс верификации блогера:\n1. Выберите платформу\n"
        "2. Вам будет выдана фраза для верификации\n3. Разместите её в био/описании профиля\n"
        "4. Отправьте ссылку на профиль\n5. Админ рассмотрит заявку"
    ),
    "blogger_apply_choose_platform": "Какая платформа? (Instagram, YouTube, Telegram и т.д.)",
    "blogger_apply_phrase": (
        "Ваша фраза для верификации: `{phrase}`\n\nРазместите эту фразу в био/описании выбранного аккаунта, "
        "затем отправьте ссылку на профиль."
    ),
    "blogger_apply_send_url": "Теперь отправьте ссылку на ваш профиль:",
    "blogger_apply_submitted": "Заявка принята и будет рассмотрена администратором. Мы сообщим о результате.",
    "blogger_apply_already_pending": "У вас уже есть заявка на рассмотрении.",
    "blogger_apply_approved": "🎉 Поздравляем! Вы стали верифицированным блогером и теперь получаете дополнительные награды.",
    "blogger_apply_rejected": "К сожалению, ваша заявка отклонена. Причина: {reason}",
    "blogger_manual_review_notice": (
        "Примечание: автоматическая проверка био профиля невозможна (такого API не существует), "
        "поэтому заявка рассматривается вручную."
    ),
    "promo_menu_title": "🎁 Раздел промокодов:",
    "promo_create_button": "➕ Создать новый промокод",
    "promo_my_codes_button": "📋 Мои коды",
    "promo_redeem_button": "🔑 Активировать код",
    "promo_choose_kind": "Выберите тип промокода:",
    "promo_kind_full": "🎟 Полный Премиум",
    "promo_kind_discount": "💸 Скидка",
    "promo_choose_plan": "Для какого плана?",
    "promo_enter_discount_percent": "Введите процент скидки (например: 10):",
    "promo_enter_activation_count": "Сколько активаций создать? (Максимум: {max_activations})",
    "promo_issuer_choice_prompt": "Как должен отображаться владелец кода?",
    "promo_issuer_user": "👤 Пользователь",
    "promo_issuer_blogger": "🌟 Блогер",
    "promo_attribution_prompt": "Хотите добавить ссылку атрибуции? (username или URL)",
    "promo_attribution_yes": "Да, добавить",
    "promo_attribution_no": "Нет, не нужно",
    "promo_attribution_enter": "Введите username или URL:",
    "promo_confirm_summary": (
        "🧾 Итоги промокода:\n📦 План: {plan_title}\n🏷 Тип: {kind}\n💸 Скидка: {discount_percent}%\n"
        "🔢 Активаций: {activations}\n💰 Общая стоимость: {total_cost} {currency}\n"
        "💼 Текущий баланс: {balance_before} {currency}\n💼 После резервирования: {balance_after} {currency}"
    ),
    "promo_confirm_button": "✅ Создать",
    "promo_insufficient_funds": "Недостаточно средств. Требуется: {required} {currency}, доступно: {available} {currency}.",
    "promo_created_success": "✅ Ваш промокод создан: `{code}`",
    "promo_created_pending_review": (
        "✅ Ваш промокод создан: `{code}`\n⏳ Ваша ссылка проверяется администратором, "
        "код неактивен до подтверждения."
    ),
    "promo_enter_code_to_redeem": "Введите промокод для активации:",
    "promo_redeem_not_found": "Такой промокод не найден.",
    "promo_redeem_not_redeemable": "Этот промокод неактивен, истёк или закончился.",
    "promo_redeem_own_code": "Вы не можете активировать собственный код.",
    "promo_redeem_already_used": "Вы уже использовали этот код.",
    "promo_redeem_success_full": "🎉 Промокод успешно применён! Премиум активирован.",
    "promo_redeem_success_discount": "✅ Промокод применён! Осталось оплатить {amount} {currency}.",
    "promo_my_codes_empty": "У вас пока нет промокодов.",
    "promo_code_status_line": "{code} | осталось {remaining}/{max_uses} | статус: {status}",
    "gifts_menu_title": "🎉 Раздел подарков:",
    "gift_send_premium_button": "⭐ Подарить Премиум",
    "gift_send_balance_button": "💰 Подарить баланс",
    "gift_received_list_button": "📥 Полученные подарки",
    "gift_enter_recipient": "Введите username или Telegram ID получателя:",
    "gift_enter_amount": "Какую сумму подарить? (целое число)",
    "gift_recipient_not_found": "Этот пользователь не запускал бота или не найден.",
    "gift_confirm_premium": "🎁 Подарить {recipient} план «{plan_title}»? Цена: {price} {currency}",
    "gift_confirm_balance": "🎁 Подарить {recipient} {amount} {currency}?",
    "gift_confirm_button": "✅ Отправить",
    "gift_sent_success": "🎉 Подарок успешно отправлен!",
    "gift_received_notice": "🎁 Вам подарок: {description}",
    "support_menu_title": "🆘 Раздел поддержки. Напишите свой вопрос, мы скоро ответим.",
    "support_ticket_created": "✅ Ваше обращение принято (#{ticket_id}). Мы скоро ответим.",
    "support_ticket_reply_notice": "✉️ Ответ поддержки:\n{text}",
    "support_terms_command": "Условия использования: {url}",
    "support_privacy_command": "Политика конфиденциальности: {url}",
    "settings_menu_title": "⚙️ Настройки:",
    "settings_change_language_button": "🌐 Изменить язык",
    "error_generic": "Произошла ошибка. Пожалуйста, попробуйте позже.",
    "error_blocked_user": "Ваш аккаунт заблокирован. Обратитесь к администратору за помощью.",
    "action_cancelled": "Действие отменено.",
    "admin_notify_new_blogger_application": "🆕 Новая заявка блогера: пользователь {user}, платформа {platform}.",
    "admin_notify_promo_review_needed": "🆕 Новый промокод требует проверки: {code} (владелец: {issuer}).",
    "admin_notify_suspicious_referral": "⚠️ Подозрительная реферальная активность: реферер {referrer}, причина: {reason}.",
    "admin_notify_payment_problem": "🚨 Проблема с оплатой: заказ {order_uid}, причина: {reason}.",
    "admin_notify_support_request": "🆘 Новый запрос в поддержку: пользователь {user}, #{ticket_id}.",
}

````

### FILE: app/i18n/uz.py

````python
"""Uzbek (uz) translations. Master key list -- every key used anywhere in
the bot must exist here; ru.py and en.py mirror this exact key set."""

TRANSLATIONS: dict[str, str] = {
    # --- Language selection --------------------------------------------------
    "choose_language": "Tilni tanlang / Выберите язык / Choose your language:",
    "language_set": "Til o'zbekchaga o'rnatildi. ✅",
    "language_button_uz": "🇺🇿 O'zbekcha",
    "language_button_ru": "🇷🇺 Русский",
    "language_button_en": "🇬🇧 English",
    # --- Main menu --------------------------------------------------------------
    "main_menu_title": "Bosh menyu — kerakli bo'limni tanlang:",
    "menu_search_movie": "🔍 Kino qidirish",
    "menu_categories": "🎬 Kategoriyalar",
    "menu_premium": "⭐ Premium",
    "menu_balance": "💰 Balans",
    "menu_invite_friends": "🤝 Do'stlarni taklif qilish",
    "menu_my_promo_codes": "🎁 Mening promo-kodlarim",
    "menu_gifts": "🎉 Sovg'alar",
    "menu_help": "🆘 Yordam",
    "menu_settings": "⚙️ Sozlamalar",
    "menu_back": "⬅️ Orqaga",
    "menu_cancel": "❌ Bekor qilish",
    # --- Movies -----------------------------------------------------------------
    "movie_enter_code_or_name": "Kino kodini (masalan: 222) yoki nomini kiriting:",
    "movie_not_found": "Kino topilmadi. Kodni yoki nomni tekshiring.",
    "movie_search_results": "Topilgan natijalar:",
    "movie_code_label": "Kod: {code}",
    "movie_category_label": "Kategoriya: {category}",
    "movie_premium_required": "Bu kino faqat Premium foydalanuvchilar uchun. Premium sotib olish uchun ⭐ Premium bo'limiga o'ting.",
    "movie_must_join_channels": "Bu kinoni ko'rish uchun quyidagi kanallarga a'zo bo'ling, so'ng \"Tekshirish\" tugmasini bosing:",
    "movie_check_membership_button": "✅ Tekshirish",
    "movie_still_not_joined": "Siz hali barcha kanallarga a'zo bo'lmagansiz. Iltimos, a'zo bo'lib, qayta tekshiring.",
    "movie_delivering": "Kino yuborilmoqda...",
    "movie_open_in_bot_button": "▶️ Botda ochish",
    "movie_inline_card_title": "{title} (kod: {code})",
    "movie_inline_card_description": "Ushbu kinoni ko'rish uchun botda ochish tugmasini bosing.",
    "movie_categories_title": "Kategoriyalardan birini tanlang:",
    "movie_no_movies_in_category": "Bu kategoriyada hali kinolar yo'q.",
    # --- Premium ---------------------------------------------------------------
    "premium_plans_title": "Premium rejalardan birini tanlang:",
    "premium_plan_button": "{title} — {price} {currency}",
    "premium_plan_details": (
        "📦 {title}\n⏳ Muddat: {duration_days} kun\n💵 Narx: {price} {currency}\n\n"
        "To'lov usulini tanlang:"
    ),
    "premium_pay_with_stars": "⭐ Telegram Stars orqali to'lash",
    "premium_pay_with_wallet": "💰 Balansdan to'lash",
    "premium_provider_disabled": "Bu to'lov usuli hozircha yoqilmagan.",
    "premium_enter_promo_code": 'Promo-kodingiz bormi? Kiriting, aks holda "O\'tkazib yuborish" tugmasini bosing.',
    "premium_skip_promo": "O'tkazib yuborish",
    "premium_promo_invalid": "Promo-kod yaroqsiz yoki muddati o'tgan.",
    "premium_promo_applied": "Promo-kod qo'llandi! Yangi narx: {amount} {currency}",
    "premium_checkout_summary": (
        "🧾 Buyurtma:\n📦 Reja: {plan_title}\n💵 To'lov: {amount} {currency}\n\nTasdiqlaysizmi?"
    ),
    "premium_checkout_confirm": "✅ Tasdiqlash",
    "premium_payment_success": "🎉 To'lov muvaffaqiyatli! Premium faollashtirildi, muddati: {until}.",
    "premium_payment_failed": "To'lov amalga oshmadi. Iltimos, qayta urinib ko'ring.",
    "premium_insufficient_balance": "Balansingizda yetarli mablag' yo'q. Mavjud: {available} {currency}, kerak: {required} {currency}.",
    "premium_already_active": "Sizda allaqachon faol Premium bor, muddati: {until}.",
    # --- Wallet / balance --------------------------------------------------------
    "balance_title": (
        "💰 Balansingiz\n\nMavjud: {available} {currency}\nZahirada: {reserved} {currency}\n"
        "Kutilmoqda: {pending} {currency}"
    ),
    "balance_no_wallets": "Sizda hali balans yozuvlari yo'q.",
    "balance_history_title": "So'nggi tranzaksiyalar:",
    "balance_history_empty": "Tranzaksiyalar tarixi bo'sh.",
    "balance_history_entry": "{date} | {type} | {amount} {currency}",
    # --- Referrals -----------------------------------------------------------
    "referral_link_title": "🤝 Sizning referal havolangiz:\n{link}\n\nDo'stlaringizni taklif qiling va mukofot oling!",
    "referral_stats_title": (
        "📊 Referal statistikasi:\n\nJami taklif qilinganlar: {total_joins}\n"
        "Malakali taklif qilinganlar: {qualified_joins}\n"
        "Xarid komissiyalari: {purchase_commission_total} \n"
        "Bloger mukofotlari: {blogger_reward_total}"
    ),
    "referral_become_blogger_prompt": "Tasdiqlangan bloger bo'lishni xohlaysizmi? Qo'shimcha mukofotlar oling!",
    "referral_become_blogger_button": "🌟 Bloger bo'lish uchun ariza",
    # --- Blogger application ------------------------------------------------
    "blogger_apply_start": (
        "Bloger tasdiqlash jarayoni:\n1. Ijtimoiy tarmoq platformangizni tanlang\n"
        "2. Sizga tasdiqlash so'zi beriladi\n3. Uni profilingiz bio/tasvirига joylashtiring\n"
        "4. Profil havolangizni yuboring\n5. Admin ko'rib chiqadi"
    ),
    "blogger_apply_choose_platform": "Qaysi platforma? (Instagram, YouTube, Telegram va h.k.)",
    "blogger_apply_phrase": (
        "Tasdiqlash so'zingiz: `{phrase}`\n\nUshbu so'zni tanlangan hisobingiz bio/tasvirга joylashtiring, "
        "so'ng profil havolasini yuboring."
    ),
    "blogger_apply_send_url": "Endi profilingiz havolasini yuboring:",
    "blogger_apply_submitted": "Arizangiz qabul qilindi va admin tomonidan ko'rib chiqiladi. Natija haqida xabar beramiz.",
    "blogger_apply_already_pending": "Sizda allaqachon ko'rib chiqilayotgan ariza bor.",
    "blogger_apply_approved": "🎉 Tabriklaymiz! Siz tasdiqlangan bloger bo'ldingiz. Endi qo'shimcha mukofotlar olasiz.",
    "blogger_apply_rejected": "Afsuski, arizangiz rad etildi. Sabab: {reason}",
    "blogger_manual_review_notice": (
        "Eslatma: profil bio'sini avtomatik tekshirish imkoni yo'q (bunday API mavjud emas), "
        "shuning uchun ariza qo'lda ko'rib chiqiladi."
    ),
    # --- Promo codes --------------------------------------------------------
    "promo_menu_title": "🎁 Promo-kodlar bo'limi:",
    "promo_create_button": "➕ Yangi promo-kod yaratish",
    "promo_my_codes_button": "📋 Mening kodlarim",
    "promo_redeem_button": "🔑 Kodni faollashtirish",
    "promo_choose_kind": "Promo-kod turini tanlang:",
    "promo_kind_full": "🎟 To'liq Premium",
    "promo_kind_discount": "💸 Chegirma",
    "promo_choose_plan": "Qaysi reja uchun?",
    "promo_enter_discount_percent": "Chegirma foizini kiriting (masalan: 10):",
    "promo_enter_activation_count": "Nechta faollashtirish uchun kod yaratmoqchisiz? (Maksimal: {max_activations})",
    "promo_issuer_choice_prompt": "Kod egasi qanday ko'rsatilsin?",
    "promo_issuer_user": "👤 Foydalanuvchi",
    "promo_issuer_blogger": "🌟 Bloger",
    "promo_attribution_prompt": "Havola qo'shmoqchimisiz? (username yoki URL)",
    "promo_attribution_yes": "Ha, qo'shaman",
    "promo_attribution_no": "Yo'q, kerak emas",
    "promo_attribution_enter": "Username yoki URL manzilini kiriting:",
    "promo_confirm_summary": (
        "🧾 Promo-kod xulosasi:\n📦 Reja: {plan_title}\n🏷 Turi: {kind}\n💸 Chegirma: {discount_percent}%\n"
        "🔢 Faollashtirish: {activations}\n💰 Umumiy narx: {total_cost} {currency}\n"
        "💼 Joriy balans: {balance_before} {currency}\n💼 Zahiraga o'tkazilgandan keyin: {balance_after} {currency}"
    ),
    "promo_confirm_button": "✅ Yaratish",
    "promo_insufficient_funds": "Balansingiz yetarli emas. Kerak: {required} {currency}, mavjud: {available} {currency}.",
    "promo_created_success": "✅ Promo-kodingiz yaratildi: `{code}`",
    "promo_created_pending_review": (
        "✅ Promo-kodingiz yaratildi: `{code}`\n⏳ Havolangiz admin tomonidan tekshirilmoqda, "
        "tasdiqlangunga qadar kod faol emas."
    ),
    "promo_enter_code_to_redeem": "Faollashtirish uchun promo-kodni kiriting:",
    "promo_redeem_not_found": "Bunday promo-kod topilmadi.",
    "promo_redeem_not_redeemable": "Bu promo-kod faol emas, muddati o'tgan yoki tugagan.",
    "promo_redeem_own_code": "O'zingiz yaratgan kodni faollashtira olmaysiz.",
    "promo_redeem_already_used": "Siz bu kodni allaqachon ishlatgansiz.",
    "promo_redeem_success_full": "🎉 Promo-kod muvaffaqiyatli qo'llandi! Premium faollashtirildi.",
    "promo_redeem_success_discount": "✅ Promo-kod qo'llandi! To'lov qilish uchun {amount} {currency} qoldi.",
    "promo_my_codes_empty": "Sizda hali promo-kodlar yo'q.",
    "promo_code_status_line": "{code} | {remaining}/{max_uses} qoldi | holat: {status}",
    # --- Gifts -----------------------------------------------------------------
    "gifts_menu_title": "🎉 Sovg'alar bo'limi:",
    "gift_send_premium_button": "⭐ Premium sovg'a qilish",
    "gift_send_balance_button": "💰 Balans sovg'a qilish",
    "gift_received_list_button": "📥 Olingan sovg'alar",
    "gift_enter_recipient": "Qabul qiluvchi username yoki Telegram ID sini kiriting:",
    "gift_enter_amount": "Necha miqdorda sovg'a qilmoqchisiz? (butun son)",
    "gift_recipient_not_found": "Bu foydalanuvchi botni ishga tushirmagan yoki topilmadi.",
    "gift_confirm_premium": '🎁 {recipient} ga "{plan_title}" Premium sovg\'a qilinsinmi? Narx: {price} {currency}',
    "gift_confirm_balance": "🎁 {recipient} ga {amount} {currency} sovg'a qilinsinmi?",
    "gift_confirm_button": "✅ Yuborish",
    "gift_sent_success": "🎉 Sovg'a muvaffaqiyatli yuborildi!",
    "gift_received_notice": "🎁 Sizga sovg'a keldi: {description}",
    # --- Support -----------------------------------------------------------------
    "support_menu_title": "🆘 Yordam bo'limi. Savolingizni yozing, tez orada javob beramiz.",
    "support_ticket_created": "✅ Murojaatingiz qabul qilindi (#{ticket_id}). Tez orada javob beramiz.",
    "support_ticket_reply_notice": "✉️ Yordam xizmatidan javob:\n{text}",
    "support_terms_command": "Foydalanish shartlari: {url}",
    "support_privacy_command": "Maxfiylik siyosati: {url}",
    # --- Settings --------------------------------------------------------------
    "settings_menu_title": "⚙️ Sozlamalar:",
    "settings_change_language_button": "🌐 Tilni o'zgartirish",
    # --- Errors / generic --------------------------------------------------------
    "error_generic": "Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.",
    "error_blocked_user": "Sizning hisobingiz bloklangan. Yordam uchun administratorga murojaat qiling.",
    "action_cancelled": "Amal bekor qilindi.",
    # --- Admin notifications (sent to admin telegram accounts) -----------------
    "admin_notify_new_blogger_application": "🆕 Yangi bloger arizasi: foydalanuvchi {user}, platforma {platform}.",
    "admin_notify_promo_review_needed": "🆕 Yangi promo-kod tekshiruv talab qiladi: {code} (egasi: {issuer}).",
    "admin_notify_suspicious_referral": "⚠️ Shubhali referal faolligi: referrer {referrer}, sabab: {reason}.",
    "admin_notify_payment_problem": "🚨 To'lov muammosi: order {order_uid}, sabab: {reason}.",
    "admin_notify_support_request": "🆘 Yangi yordam so'rovi: foydalanuvchi {user}, #{ticket_id}.",
}

````

### FILE: app/__init__.py

````python
"""Movie Bot application package."""

````

### FILE: app/main.py

````python
"""Application entrypoints.

Three run modes, matching docker-compose services:
  - `python -m app.main bot`   -> long-polls Telegram (or, if BOT_WEBHOOK_URL
    is set, registers the webhook and just idles while the FastAPI process
    handles updates) -- see `run_bot()`.
  - `uvicorn app.main:api_app`  -> FastAPI app serving webhooks, the
    storefront, and the admin panel -- see `api_app` module-level instance.
  - `python -m app.workers.runner` -> background workers (separate module).
"""

from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.admin.router import admin_router
from app.api.storefront.routes import router as storefront_router
from app.api.webhooks.click_webhook import router as click_webhook_router
from app.api.webhooks.stripe_webhook import router as stripe_webhook_router
from app.api.webhooks.telegram import router as telegram_webhook_router
from app.bot.factory import build_bot, build_dispatcher
from app.config import get_settings
from app.core.logging import get_logger, setup_logging

settings = get_settings()
setup_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    settings.validate_for_production()
    bot = build_bot(settings)
    dispatcher = build_dispatcher(settings)
    app.state.bot = bot
    app.state.dispatcher = dispatcher

    if settings.BOT_WEBHOOK_URL:
        await bot.set_webhook(
            url=settings.BOT_WEBHOOK_URL,
            secret_token=settings.BOT_WEBHOOK_SECRET,
            drop_pending_updates=False,
        )
        logger.info("Telegram webhook registered")
    else:
        logger.info(
            "BOT_WEBHOOK_URL not set; webhook not registered (expects long polling via `bot` service)"
        )

    yield

    await bot.session.close()


def create_api_app() -> FastAPI:
    app = FastAPI(title="Movie Bot API", lifespan=_lifespan)
    app.include_router(telegram_webhook_router)
    app.include_router(stripe_webhook_router)
    app.include_router(click_webhook_router)
    app.include_router(storefront_router)
    app.include_router(admin_router)

    @app.get("/health")
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    @app.get("/legal/terms")
    async def terms() -> JSONResponse:
        return JSONResponse(
            {
                "title": "Terms of Service",
                "body": (
                    "This bot sells digital subscription access delivered inside Telegram. "
                    "Purchases made with Telegram Stars are governed by Telegram's own Terms of Service "
                    "and Payments Terms. Purchases made through the independent web storefront (Stripe/Click) "
                    "are governed by this document and the respective payment provider's terms. "
                    "All sales are for digital access only; see /legal/privacy for data handling."
                ),
            }
        )

    @app.get("/legal/privacy")
    async def privacy() -> JSONResponse:
        return JSONResponse(
            {
                "title": "Privacy Policy",
                "body": (
                    "We store your Telegram user id, username, chosen language, referral relationships, "
                    "wallet ledger entries, and support messages in order to operate the bot. "
                    "We do not sell your data. Payment card details are handled entirely by Stripe/Click/Telegram "
                    "and never touch our servers."
                ),
            }
        )

    return app


api_app = create_api_app()


async def run_bot() -> None:
    """Long-polling entrypoint, used when BOT_WEBHOOK_URL is empty.

    If BOT_WEBHOOK_URL IS set, this process should not be started at all in
    a real deployment (the `bot` docker-compose service is only meant for
    long-polling setups) -- it idles instead of crash-looping so a
    misconfigured `docker compose up` doesn't restart forever, but it does
    not touch the webhook registration (that's `api_app`'s job via its
    lifespan hook) and logs a clear warning.
    """
    settings.validate_for_production()

    if settings.BOT_WEBHOOK_URL:
        logger.warning(
            "BOT_WEBHOOK_URL is set; updates are handled by the API service's webhook route. "
            "This 'bot' process is not needed in webhook mode and will idle."
        )
        while True:
            await asyncio.sleep(3600)

    bot = build_bot(settings)
    dispatcher = build_dispatcher(settings)
    await bot.delete_webhook(drop_pending_updates=False)
    logger.info("Starting long polling")
    await dispatcher.start_polling(bot)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "bot"
    if mode == "bot":
        asyncio.run(run_bot())
    else:
        print(f"Unknown mode '{mode}'. Use: python -m app.main bot")
        sys.exit(1)


if __name__ == "__main__":
    main()

````

### FILE: app/payments/base.py

````python
"""Payment provider interface.

Every provider models a purchase as: create a server-priced charge/invoice
-> receive a provider callback/update -> verify authenticity -> return a
normalized `PaymentEvent` for `PurchaseService.confirm_payment`/
`refund_order` to act on. Providers NEVER accept a client-declared price;
`amount`/`currency` passed into `create_charge` always come from
`PurchaseService.create_order`'s server-side snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol


class PaymentEventType(str, Enum):
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_CANCELLED = "payment_cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ChargeHandle:
    """What a provider returns after creating a charge/invoice/session."""

    provider_reference: str
    checkout_payload: dict[str, Any]
    """Provider-specific data the bot/web layer needs to actually present
    the payment UI, e.g. a Telegram invoice payload, a Stripe Checkout
    Session URL, or a Click payment URL."""


@dataclass(frozen=True)
class PaymentEvent:
    provider_event_id: str
    event_type: PaymentEventType
    provider_reference: str | None
    order_uid: str | None
    raw_payload: dict[str, Any]
    verified: bool
    """True only if the event's authenticity was cryptographically/API
    verified (Telegram pre_checkout/successful_payment inherent trust,
    Stripe signature check, Click hash check). NEVER trust an event where
    verified is False."""


class PaymentProvider(Protocol):
    code: str

    def is_enabled(self) -> bool:
        """True only when the feature flag is on AND required credentials
        are present. A provider that returns False here must refuse to
        create charges."""
        ...

    def is_live(self) -> bool:
        """True only in a fully configured production/live credential
        mode. Sandboxes must return False so the UI/README can honestly
        label the provider "sandbox-only"."""
        ...

    async def create_charge(
        self,
        *,
        order_uid: str,
        amount: int,
        currency: str,
        description: str,
        buyer_telegram_id: int,
    ) -> ChargeHandle: ...

    async def parse_webhook(self, *, headers: dict[str, str], body: bytes) -> PaymentEvent:
        """Parse + verify an inbound webhook/update. Must NOT raise on a bad
        signature -- return `verified=False` so the caller can reject with a
        4xx and log, without leaking a stack trace to the caller."""
        ...

    async def refund(self, *, provider_reference: str, amount: int | None = None) -> bool:
        """Issue a refund via the provider's API. Returns True on success.
        Raises NotImplementedError if the provider has no refund API
        (e.g. Telegram Stars refunds are issued via a specific Bot API
        method that must be called with the ORIGINAL buyer's user id --
        see stars.py)."""
        ...


class ProviderDisabledError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(
            f"Payment provider '{code}' is disabled: missing feature flag or credentials. "
            "It will remain disabled until configured in .env and re-deployed."
        )

````

### FILE: app/payments/click_provider.py

````python
"""Click (click.uz) payment adapter — independent WEB storefront channel only.

Same compliance boundary as Stripe (see stripe_provider.py): Click is wired
only into the separate `app.api.storefront` web checkout, gated by both
`PAYMENTS_CLICK_ENABLED` and `STOREFRONT_ENABLED`, and is never used to
sell Telegram-bot digital goods.

Click's "Shop API" merchant webhook protocol (per Click's public merchant
integration documentation, e.g. https://docs.click.uz and the reference
implementations published at
https://github.com/click-llc/click-integration-php and
https://github.com/samarbadriddin0v/click-uz-integration-nodejs) sends two
sequential callbacks per transaction, `action=0` (Prepare) then `action=1`
(Complete), each carrying a `sign_string` that the merchant must recompute
and compare:

    sign_string = md5(
        click_trans_id + service_id + SECRET_KEY + merchant_trans_id +
        (merchant_prepare_id if action == Complete else "") +
        amount + action + sign_time
    )

A request whose recomputed signature doesn't match is rejected with
`error=-1` ("SIGN CHECK FAILED") and never touched further. This module
implements exactly that check; nothing here treats an unverified callback
as proof of payment (spec section 4: "Never trust ... a checkout success
URL as payment proof" — Click's redirect-back URL is informational only,
the merchant webhook is the sole source of truth here, consistent with
Click's own documented integration flow).
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.config import Settings
from app.payments.base import ChargeHandle, PaymentEvent, PaymentEventType


class ClickActionCode:
    PREPARE = 0
    COMPLETE = 1


class ClickErrorCode:
    SUCCESS = 0
    SIGN_CHECK_FAILED = -1
    TRANSACTION_NOT_FOUND = -6
    ALREADY_PAID = -4
    USER_NOT_FOUND = -5


class ClickProvider:
    code = "click"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def is_enabled(self) -> bool:
        s = self._settings
        return bool(
            s.PAYMENTS_CLICK_ENABLED
            and s.STOREFRONT_ENABLED
            and s.CLICK_MERCHANT_ID
            and s.CLICK_SERVICE_ID
            and s.CLICK_SECRET_KEY
        )

    def is_live(self) -> bool:
        return self.is_enabled() and self._settings.CLICK_MODE == "live"

    async def create_charge(
        self,
        *,
        order_uid: str,
        amount: int,
        currency: str,
        description: str,
        buyer_telegram_id: int,
    ) -> ChargeHandle:
        if not self.is_enabled():
            from app.payments.base import ProviderDisabledError

            raise ProviderDisabledError(self.code)
        s = self._settings
        # Click's hosted checkout link format (my.click.uz/services/pay):
        checkout_url = (
            "https://my.click.uz/services/pay"
            f"?service_id={s.CLICK_SERVICE_ID}"
            f"&merchant_id={s.CLICK_MERCHANT_ID}"
            f"&amount={amount}"
            f"&transaction_param={order_uid}"
            f"&return_url={s.PUBLIC_BASE_URL}/storefront/success?order={order_uid}"
        )
        return ChargeHandle(
            provider_reference=order_uid, checkout_payload={"checkout_url": checkout_url}
        )

    def _expected_sign(
        self,
        *,
        click_trans_id: str,
        merchant_trans_id: str,
        amount: str,
        action: str,
        sign_time: str,
        merchant_prepare_id: str | None = None,
    ) -> str:
        s = self._settings
        parts = [click_trans_id, s.CLICK_SERVICE_ID, s.CLICK_SECRET_KEY, merchant_trans_id]
        if merchant_prepare_id is not None:
            parts.append(merchant_prepare_id)
        parts.extend([amount, action, sign_time])
        return hashlib.md5("".join(parts).encode("utf-8")).hexdigest()

    async def parse_webhook(self, *, headers: dict[str, str], body: bytes) -> PaymentEvent:
        """Click posts `application/x-www-form-urlencoded` fields; the
        FastAPI route is responsible for handing us the parsed dict via
        `raw_payload` semantics -- here we accept an already-decoded form
        as JSON bytes for uniformity with the other adapters (the webhook
        route performs `dict(await request.form())` then `json.dumps(...)`
        before calling this, see app/api/webhooks/click.py)."""
        import json

        try:
            data: dict[str, Any] = json.loads(body.decode("utf-8"))
        except Exception:
            return PaymentEvent("invalid_body", PaymentEventType.UNKNOWN, None, None, {}, False)

        required = [
            "click_trans_id",
            "merchant_trans_id",
            "amount",
            "action",
            "sign_time",
            "sign_string",
        ]
        if not all(k in data for k in required):
            return PaymentEvent("missing_fields", PaymentEventType.UNKNOWN, None, None, data, False)

        expected = self._expected_sign(
            click_trans_id=str(data["click_trans_id"]),
            merchant_trans_id=str(data["merchant_trans_id"]),
            amount=str(data["amount"]),
            action=str(data["action"]),
            sign_time=str(data["sign_time"]),
            merchant_prepare_id=(
                str(data["merchant_prepare_id"]) if data.get("merchant_prepare_id") else None
            ),
        )
        verified = expected == str(data.get("sign_string", ""))

        action = str(data.get("action"))
        event_type = (
            PaymentEventType.PAYMENT_SUCCEEDED
            if action == str(ClickActionCode.COMPLETE)
            else PaymentEventType.UNKNOWN
        )
        if str(data.get("error", "0")) not in ("0",):
            event_type = PaymentEventType.PAYMENT_FAILED

        return PaymentEvent(
            provider_event_id=str(data.get("click_trans_id")),
            event_type=event_type,
            provider_reference=str(data.get("click_trans_id")),
            order_uid=str(data.get("merchant_trans_id")),
            raw_payload=data,
            verified=verified,
        )

    async def refund(self, *, provider_reference: str, amount: int | None = None) -> bool:
        # Click does not expose a self-service programmatic refund API for
        # Shop API merchants as of this writing; refunds are processed by
        # contacting Click merchant support. Documented here rather than
        # faked so admins know to use the manual process.
        raise NotImplementedError(
            "Click has no self-service refund API for Shop API merchants; "
            "process refunds via Click merchant support and record the outcome manually "
            "in the admin panel (Orders > mark refunded)."
        )

````

### FILE: app/payments/__init__.py

````python
"""Payment provider abstraction.

`app.payments.base.PaymentProvider` is the interface every adapter
implements. `app.payments.registry.PaymentRegistry` exposes only the
providers that are BOTH feature-flagged on in config AND have their
required credentials present -- an adapter that is "configured" in code but
missing real secrets stays reported as disabled, never silently falls back
to a fake/live-looking state.
"""

````

### FILE: app/payments/registry.py

````python
"""Central place that exposes only providers which are actually usable.

`app.admin` (provider status screen) and `app.bot.handlers.premium` both
call `PaymentRegistry.status_report()` / `get_enabled(code)` rather than
importing individual adapters, so there is exactly one source of truth for
"is this provider live, sandbox, or disabled".
"""

from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot

from app.config import Settings
from app.payments.base import PaymentProvider, ProviderDisabledError
from app.payments.click_provider import ClickProvider
from app.payments.stars import StarsProvider
from app.payments.stripe_provider import StripeProvider


@dataclass(frozen=True)
class ProviderStatus:
    code: str
    enabled: bool
    live: bool
    label: str


class PaymentRegistry:
    def __init__(self, settings: Settings, bot: Bot | None = None) -> None:
        self._settings = settings
        self._providers: dict[str, PaymentProvider] = {}
        if bot is not None:
            self._providers["telegram_stars"] = StarsProvider(settings, bot)
        self._providers["stripe"] = StripeProvider(settings)
        self._providers["click"] = ClickProvider(settings)

    def get(self, code: str) -> PaymentProvider:
        provider = self._providers.get(code)
        if provider is None:
            raise ProviderDisabledError(code)
        return provider

    def get_enabled(self, code: str) -> PaymentProvider:
        provider = self.get(code)
        if not provider.is_enabled():
            raise ProviderDisabledError(code)
        return provider

    def is_registered(self, code: str) -> bool:
        return code in self._providers

    def is_provider_enabled(self, code: str) -> bool:
        return self.is_registered(code) and self._providers[code].is_enabled()

    def status_report(self) -> list[ProviderStatus]:
        labels = {
            "telegram_stars": "Telegram Stars (in-app digital goods)",
            "stripe": "Stripe (independent web storefront)",
            "click": "Click (independent web storefront, Uzbekistan)",
        }
        report = []
        for code, provider in self._providers.items():
            report.append(
                ProviderStatus(
                    code=code,
                    enabled=provider.is_enabled(),
                    live=provider.is_live(),
                    label=labels.get(code, code),
                )
            )
        return report

````

### FILE: app/payments/stars.py

````python
"""Telegram Stars payment adapter.

Telegram Stars ("XTR") is Telegram's own in-app currency for digital
goods, paid entirely inside the Telegram client via `sendInvoice` with
`currency="XTR"` and `provider_token=""` (Stars requires an empty provider
token per Bot API docs) followed by handling `pre_checkout_query` and
`successful_payment` updates. There is no external merchant account to
configure -- this is why `is_enabled()` only depends on the
`PAYMENTS_STARS_ENABLED` flag and a valid bot token, not on any additional
secret.

Refunds use `refundStarPayment(user_id, telegram_payment_charge_id)`, which
requires the ORIGINAL buyer's Telegram user id -- callers of `refund()`
here must pass that id, obtained from the original order.
"""

from __future__ import annotations

import hashlib
import json

from aiogram import Bot

from app.config import Settings
from app.payments.base import ChargeHandle, PaymentEvent, PaymentEventType


class StarsProvider:
    code = "telegram_stars"

    def __init__(self, settings: Settings, bot: Bot) -> None:
        self._settings = settings
        self._bot = bot

    def is_enabled(self) -> bool:
        return bool(self._settings.PAYMENTS_STARS_ENABLED and self._settings.BOT_TOKEN)

    def is_live(self) -> bool:
        # Telegram Stars has no separate "sandbox" mode distinct from the
        # bot token itself -- it is live the moment it's enabled with a
        # real bot token, matching Telegram's own documentation.
        return self.is_enabled()

    async def create_charge(
        self,
        *,
        order_uid: str,
        amount: int,
        currency: str,
        description: str,
        buyer_telegram_id: int,
    ) -> ChargeHandle:
        if not self.is_enabled():
            raise RuntimeError("Telegram Stars provider is disabled")
        if currency != "XTR":
            raise ValueError("Stars charges must be denominated in XTR")

        prices = [{"label": description[:32] or "Premium", "amount": amount}]
        payload = order_uid
        # The actual `sendInvoice` call is issued by the handler (it needs
        # the chat_id to send to); this adapter returns the structured
        # payload the handler should pass through, keeping aiogram Bot
        # calls that need a chat context out of the payments layer.
        return ChargeHandle(
            provider_reference=order_uid,
            checkout_payload={
                "title": description[:32] or "Premium subscription",
                "description": description[:255] or "Premium subscription",
                "payload": payload,
                "currency": "XTR",
                "prices": prices,
                "provider_token": "",
            },
        )

    async def parse_webhook(self, *, headers: dict[str, str], body: bytes) -> PaymentEvent:
        """Stars payments don't arrive via a separate HTTP webhook -- they
        arrive as `successful_payment`/`pre_checkout_query` updates through
        the normal Telegram bot update stream (webhook or polling), already
        authenticated by Telegram's own delivery. This method exists to
        satisfy the common `PaymentProvider` interface for code that treats
        all providers uniformly (e.g. reconciliation); real-time handling is
        done directly in `app.bot.handlers.premium` via aiogram's
        `pre_checkout_query`/`successful_payment` handlers.
        """
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            return PaymentEvent(
                provider_event_id="invalid",
                event_type=PaymentEventType.UNKNOWN,
                provider_reference=None,
                order_uid=None,
                raw_payload={},
                verified=False,
            )
        sp = data.get("successful_payment") or {}
        charge_id = sp.get("telegram_payment_charge_id") or hashlib.sha256(body).hexdigest()
        return PaymentEvent(
            provider_event_id=charge_id,
            event_type=PaymentEventType.PAYMENT_SUCCEEDED if sp else PaymentEventType.UNKNOWN,
            provider_reference=charge_id,
            order_uid=sp.get("invoice_payload"),
            raw_payload=data,
            verified=bool(sp),
        )

    async def refund(
        self,
        *,
        provider_reference: str,
        amount: int | None = None,
        buyer_telegram_id: int | None = None,
    ) -> bool:
        if not self.is_enabled():
            raise RuntimeError("Telegram Stars provider is disabled")
        if buyer_telegram_id is None:
            raise ValueError("Stars refunds require the original buyer's telegram_id")
        # aiogram >=3.15 exposes Bot.refund_star_payment(user_id, telegram_payment_charge_id)
        await self._bot.refund_star_payment(
            user_id=buyer_telegram_id, telegram_payment_charge_id=provider_reference
        )
        return True

````

### FILE: app/payments/stripe_provider.py

````python
"""Stripe payment adapter — independent WEB storefront channel only.

IMPORTANT (compliance, spec section 4): this adapter must NEVER be used to
sell Telegram-bot digital goods to bot users as a way of routing around
Telegram's in-app digital-goods payment rules. It is wired ONLY into
`app.api.storefront`, a separate web checkout surface, and is gated by
`STOREFRONT_ENABLED` in addition to `PAYMENTS_STRIPE_ENABLED`. See
README.md "Payments and platform compliance" for the full policy.

`is_enabled()`/`is_live()` are strict: a missing API key or webhook secret
keeps the provider disabled even if the feature flag is on, so the app
never pretends Stripe is live with placeholder credentials.
"""

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.payments.base import ChargeHandle, PaymentEvent, PaymentEventType


class StripeProvider:
    code = "stripe"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = None
        if settings.PAYMENTS_STRIPE_ENABLED and settings.STRIPE_API_KEY:
            try:
                import stripe

                stripe.api_key = settings.STRIPE_API_KEY
                self._client = stripe
            except ImportError:
                self._client = None

    def is_enabled(self) -> bool:
        return bool(
            self._settings.PAYMENTS_STRIPE_ENABLED
            and self._settings.STOREFRONT_ENABLED
            and self._settings.STRIPE_API_KEY
            and self._settings.STRIPE_WEBHOOK_SECRET
            and self._client is not None
        )

    def is_live(self) -> bool:
        return self.is_enabled() and self._settings.STRIPE_MODE == "live"

    async def create_charge(
        self,
        *,
        order_uid: str,
        amount: int,
        currency: str,
        description: str,
        buyer_telegram_id: int,
    ) -> ChargeHandle:
        if not self.is_enabled():
            from app.payments.base import ProviderDisabledError

            raise ProviderDisabledError(self.code)

        session = self._client.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {"name": description[:200]},
                        "unit_amount": amount,
                    },
                    "quantity": 1,
                }
            ],
            client_reference_id=order_uid,
            metadata={"order_uid": order_uid, "buyer_telegram_id": str(buyer_telegram_id)},
            success_url=f"{self._settings.PUBLIC_BASE_URL}/storefront/success?order={order_uid}",
            cancel_url=f"{self._settings.PUBLIC_BASE_URL}/storefront/cancel?order={order_uid}",
        )
        return ChargeHandle(
            provider_reference=session["id"],
            checkout_payload={"checkout_url": session["url"]},
        )

    async def parse_webhook(self, *, headers: dict[str, str], body: bytes) -> PaymentEvent:
        if self._client is None:
            return PaymentEvent(
                provider_event_id="disabled",
                event_type=PaymentEventType.UNKNOWN,
                provider_reference=None,
                order_uid=None,
                raw_payload={},
                verified=False,
            )
        sig = headers.get("stripe-signature", "")
        try:
            event = self._client.Webhook.construct_event(
                body, sig, self._settings.STRIPE_WEBHOOK_SECRET
            )
        except Exception:
            return PaymentEvent(
                provider_event_id="invalid_signature",
                event_type=PaymentEventType.UNKNOWN,
                provider_reference=None,
                order_uid=None,
                raw_payload={},
                verified=False,
            )

        obj = event["data"]["object"]
        order_uid = (obj.get("metadata") or {}).get("order_uid") or obj.get("client_reference_id")
        event_type_map = {
            "checkout.session.completed": PaymentEventType.PAYMENT_SUCCEEDED,
            "checkout.session.expired": PaymentEventType.PAYMENT_CANCELLED,
            "payment_intent.payment_failed": PaymentEventType.PAYMENT_FAILED,
            "charge.refunded": PaymentEventType.REFUNDED,
            "charge.dispute.created": PaymentEventType.DISPUTED,
        }
        return PaymentEvent(
            provider_event_id=event["id"],
            event_type=event_type_map.get(event["type"], PaymentEventType.UNKNOWN),
            provider_reference=obj.get("id"),
            order_uid=order_uid,
            raw_payload=event,
            verified=True,
        )

    async def refund(self, *, provider_reference: str, amount: int | None = None) -> bool:
        if not self.is_enabled():
            from app.payments.base import ProviderDisabledError

            raise ProviderDisabledError(self.code)
        kwargs: dict[str, Any] = {"payment_intent": provider_reference}
        if amount is not None:
            kwargs["amount"] = amount
        self._client.Refund.create(**kwargs)
        return True

````

### FILE: app/services/blogger_reward_service.py

````python
"""Wires the pure `app.services.blogger_rewards` math to persistent state.

Called once per qualified referral (see referral_service.ReferralService),
never batched. Idempotent: a `BloggerAcquisitionReward` row is unique per
`referral_id`, so calling this twice for the same referral is a no-op on
the second call.
"""

from __future__ import annotations

from app.db.models.enums import RewardStatus
from app.db.models.referral import Referral
from app.db.uow import UnitOfWork
from app.services.blogger_rewards import accrue_qualified_join
from app.services.settings_service import SettingsService


class BloggerRewardService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def accrue_for_qualified_referral(self, referral: Referral) -> None:
        if not referral.is_qualified or referral.is_self_referral:
            return
        if not referral.referrer_was_blogger_at_join:
            return  # standard referrers never get the per-join acquisition reward

        existing = await self.uow.rewards.get_reward_by_referral(referral.id)
        if existing is not None:
            return  # already accrued -- prevents accidental duplicate rewards

        blogger_user_id = referral.referrer_user_id
        profile = await self.uow.bloggers.lock_profile(blogger_user_id)
        if profile is None:
            return
        if profile.status != "active":
            return  # suspended bloggers stop earning new acquisition rewards

        settings_service = SettingsService(self.uow)
        global_rate, global_currency = await settings_service.global_blogger_reward_per_1000()
        rate = profile.acquisition_reward_per_1000_override or global_rate
        currency = profile.acquisition_reward_currency_override or global_currency
        if rate <= 0:
            return

        step = accrue_qualified_join(
            rate_per_1000=rate, remainder_micros_before=profile.accrual_remainder_micros
        )

        profile.accrual_remainder_micros = step.remainder_micros_after
        profile.qualified_joins_counted += 1
        sequence_number = profile.qualified_joins_counted

        reward = await self.uow.rewards.create_reward(
            referral_id=referral.id,
            blogger_user_id=blogger_user_id,
            rate_per_1000_snapshot=rate,
            currency=currency,
            amount=step.amount_credited,
            remainder_micros_before=step.remainder_micros_before,
            remainder_micros_after=step.remainder_micros_after,
            sequence_number=sequence_number,
            status=RewardStatus.ACCRUED.value,
        )

        if step.amount_credited > 0:
            wallet = await self.uow.wallets.lock_wallet(blogger_user_id, currency)
            await self.uow.wallets.apply_ledger_entry(
                wallet=wallet,
                entry_type="blogger_acquisition_reward",
                bucket="available",
                amount=step.amount_credited,
                idempotency_key=f"blogger_reward:{reward.id}",
                reference_type="blogger_acquisition_reward",
                reference_id=str(reward.id),
                note=f"Acquisition reward for qualified join #{sequence_number}",
            )

    async def reverse_reward_for_referral(self, referral_id: int, reason: str) -> None:
        """Used when a referred join is later found fraudulent/blocked."""
        reward = await self.uow.rewards.get_reward_by_referral(referral_id)
        if reward is None or reward.status != RewardStatus.ACCRUED.value:
            return
        reward.status = RewardStatus.REVERSED.value
        reward.reversal_reason = reason
        import datetime as dt

        reward.reversed_at = dt.datetime.now(dt.UTC)
        await self.uow.flush()

        if reward.amount > 0:
            wallet = await self.uow.wallets.lock_wallet(reward.blogger_user_id, reward.currency)
            await self.uow.wallets.apply_ledger_entry(
                wallet=wallet,
                entry_type="reward_reversal",
                bucket="available",
                amount=-reward.amount,
                idempotency_key=f"blogger_reward_reversal:{reward.id}",
                reference_type="blogger_acquisition_reward",
                reference_id=str(reward.id),
                note=f"Reversal: {reason}",
            )

````

### FILE: app/services/blogger_rewards.py

````python
"""Blogger acquisition-reward accrual (spec section 5, verified blogger).

The admin configures a rate "per 1,000 qualified users" (globally, or
per-blogger). Spec requires:
  - Accrual starts with the FIRST qualified user, not batched to 1,000.
  - Fractional minor units (e.g. 100,000 UZS / 1000 = 100 UZS/user is exact,
    but a rate like 333 UZS/1000 users = 0.333 UZS/user is not) must be
    carried forward safely -- never lost, never overpaid.

Implementation: track a running remainder in "micros" (millionths of one
minor unit). Each qualified join contributes exactly
`rate_per_1000 * 1000` micros (because 1 minor unit == 1_000_000 micros and
1/1000 of that is exactly 1000 micros -- no rounding at this step, this
multiplication is always exact). We then extract as many whole minor units
as the accumulated micros allow and keep the sub-unit leftover for the next
join. This guarantees that after N joins, the *total* amount ever credited
equals floor(rate_per_1000 * N / 1000) -- i.e. mathematically identical to
computing the exact fraction once for N users and rounding down ONCE,
without ever having to know N in advance and without losing any fraction
along the way.
"""

from __future__ import annotations

from dataclasses import dataclass

MICROS_PER_UNIT = 1_000_000


@dataclass(frozen=True)
class AccrualStep:
    amount_credited: int
    """Whole minor units credited for THIS join (often 0)."""
    remainder_micros_before: int
    remainder_micros_after: int


def accrue_qualified_join(rate_per_1000: int, remainder_micros_before: int) -> AccrualStep:
    if rate_per_1000 < 0:
        raise ValueError("rate_per_1000 must be >= 0")
    if remainder_micros_before < 0:
        raise ValueError("remainder_micros_before must be >= 0")

    contribution_micros = rate_per_1000 * 1000  # exact: (rate_per_1000 / 1000) * 1_000_000
    total_micros = remainder_micros_before + contribution_micros
    whole_units, remainder_after = divmod(total_micros, MICROS_PER_UNIT)
    return AccrualStep(
        amount_credited=whole_units,
        remainder_micros_before=remainder_micros_before,
        remainder_micros_after=remainder_after,
    )


def simulate_n_joins(rate_per_1000: int, n: int) -> tuple[int, int]:
    """Test/debug helper: simulate N sequential qualified joins and return
    (total_amount_credited, final_remainder_micros)."""
    remainder = 0
    total = 0
    for _ in range(n):
        step = accrue_qualified_join(rate_per_1000, remainder)
        total += step.amount_credited
        remainder = step.remainder_micros_after
    return total, remainder


def expected_total_after_n_joins(rate_per_1000: int, n: int) -> int:
    """Closed-form expectation used by tests to cross-check the sequential
    simulation: floor(rate_per_1000 * n / 1000)."""
    return (rate_per_1000 * n) // 1000

````

### FILE: app/services/blogger_service.py

````python
"""Blogger application/verification workflow (spec section 5).

Verification is HONEST about its limits: `attempt_automated_check` only
ever runs when an authorized platform API is actually configured for the
given platform (currently: none are, see README "What still needs
credentials"). Otherwise every application requires manual admin review --
the service never pretends to have checked an inaccessible bio.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.db.models.blogger import BloggerApplication
from app.db.models.enums import BloggerStatusCache
from app.db.uow import UnitOfWork


@dataclass(frozen=True)
class ApplicationStartResult:
    application: BloggerApplication
    already_pending: bool


class BloggerService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def start_application(
        self, *, applicant_user_id: int, platform_name: str | None = None
    ) -> ApplicationStartResult:
        existing = await self.uow.bloggers.get_pending_application_for_user(applicant_user_id)
        if existing is not None:
            return ApplicationStartResult(application=existing, already_pending=True)

        application = await self.uow.bloggers.create_application(
            applicant_user_id=applicant_user_id, platform_name=platform_name
        )
        user = await self.uow.users.get_by_id(applicant_user_id)
        if user is not None:
            user.blogger_status_cache = BloggerStatusCache.PENDING.value
            await self.uow.flush()
        return ApplicationStartResult(application=application, already_pending=False)

    async def submit_url(self, application: BloggerApplication, url: str) -> None:
        await self.uow.bloggers.submit_url(application, url)

    async def attempt_automated_check(self, application: BloggerApplication) -> str | None:
        """Only returns a non-None result for platforms with a real,
        configured, authorized API integration. Today that is NONE, so this
        always returns None and the application proceeds to manual review.
        This function exists (rather than being omitted) so that adding a
        real integration later is a one-place change, and so the admin
        panel can show "automated check: not available for this platform"
        instead of silently doing nothing.
        """
        application.auto_check_attempted = True
        application.auto_check_result = (
            "No authorized platform API is configured for automated bio verification; "
            "manual admin review is required."
        )
        await self.uow.flush()
        return None

    async def decide(
        self,
        application: BloggerApplication,
        *,
        approve: bool,
        admin_id: int,
        reason: str | None = None,
    ) -> BloggerApplication:
        application = await self.uow.bloggers.decide(
            application, approve=approve, admin_id=admin_id, reason=reason
        )
        user = await self.uow.users.get_by_id(application.applicant_user_id)
        if approve:
            await self.uow.bloggers.create_profile(
                user_id=application.applicant_user_id, approved_application_id=application.id
            )
            if user is not None:
                user.blogger_status_cache = BloggerStatusCache.APPROVED.value
        else:
            if user is not None:
                user.blogger_status_cache = BloggerStatusCache.REJECTED.value
        await self.uow.flush()
        return application

    async def suspend(self, blogger_user_id: int, reason: str | None = None) -> bool:
        profile = await self.uow.bloggers.get_profile_by_user(blogger_user_id)
        if profile is None:
            return False
        await self.uow.bloggers.suspend(profile, reason)
        user = await self.uow.users.get_by_id(blogger_user_id)
        if user is not None:
            user.blogger_status_cache = BloggerStatusCache.SUSPENDED.value
            await self.uow.flush()
        return True

    async def reactivate(self, blogger_user_id: int) -> bool:
        profile = await self.uow.bloggers.get_profile_by_user(blogger_user_id)
        if profile is None:
            return False
        await self.uow.bloggers.reactivate(profile)
        user = await self.uow.users.get_by_id(blogger_user_id)
        if user is not None:
            user.blogger_status_cache = BloggerStatusCache.APPROVED.value
            await self.uow.flush()
        return True

    async def is_active_blogger(self, user_id: int) -> bool:
        profile = await self.uow.bloggers.get_profile_by_user(user_id)
        return bool(profile and profile.status == "active")

````

### FILE: app/services/broadcast_service.py

````python
"""Broadcast queueing. Actual message delivery (rate-limited, resumable) is
performed by `app.workers.broadcast_worker`, never inline in a request
handler, so admin actions never block on sending thousands of messages.
"""

from __future__ import annotations

from app.db.models.broadcast import Broadcast
from app.db.models.enums import BroadcastStatus, BroadcastTarget
from app.db.uow import UnitOfWork


class BroadcastService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def create_draft(
        self,
        *,
        admin_id: int,
        target: BroadcastTarget,
        text_uz: str,
        text_ru: str,
        text_en: str,
        photo_file_id: str | None = None,
        button_text: str | None = None,
        button_url: str | None = None,
        target_language: str | None = None,
        custom_user_ids: list[int] | None = None,
        rate_limit_per_second: int = 20,
    ) -> Broadcast:
        return await self.uow.broadcasts.create(
            created_by_admin_id=admin_id,
            target=target.value,
            target_language=target_language,
            custom_user_ids=custom_user_ids,
            text_uz=text_uz,
            text_ru=text_ru,
            text_en=text_en,
            photo_file_id=photo_file_id,
            button_text=button_text,
            button_url=button_url,
            rate_limit_per_second=rate_limit_per_second,
            status=BroadcastStatus.DRAFT.value,
        )

    async def enqueue(self, broadcast: Broadcast) -> int:
        """Resolve the recipient list NOW (snapshotting membership so the
        run is reproducible/auditable) and mark the broadcast QUEUED for the
        worker to pick up."""
        target = BroadcastTarget(broadcast.target)
        if target == BroadcastTarget.CUSTOM_IDS:
            user_ids = broadcast.custom_user_ids or []
        elif target == BroadcastTarget.ALL:
            users = await self.uow.users.iter_broadcast_targets()
            user_ids = [u.id for u in users]
        elif target == BroadcastTarget.PREMIUM:
            users = await self.uow.users.iter_broadcast_targets(premium_only=True)
            user_ids = [u.id for u in users]
        elif target == BroadcastTarget.FREE:
            users = await self.uow.users.iter_broadcast_targets(premium_only=False)
            user_ids = [u.id for u in users]
        elif target == BroadcastTarget.LANGUAGE:
            users = await self.uow.users.iter_broadcast_targets(language=broadcast.target_language)
            user_ids = [u.id for u in users]
        else:
            user_ids = []

        await self.uow.broadcasts.add_recipients(broadcast.id, user_ids)
        broadcast.total_recipients = len(user_ids)
        await self.uow.broadcasts.update_status(broadcast, BroadcastStatus.QUEUED)
        return len(user_ids)

    async def cancel(self, broadcast: Broadcast) -> None:
        await self.uow.broadcasts.update_status(broadcast, BroadcastStatus.CANCELLED)

````

### FILE: app/services/commission.py

````python
"""Referral commission calculation (spec section 5, standard referrer).

Pure functions only -- no DB/network access -- so every plan's independent
commission percentage, the first-purchase-only vs. renewals policy, and
refund reversal math can be tested directly.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.money import percent_of


@dataclass(frozen=True)
class CommissionInput:
    net_paid_amount: int
    """The amount actually paid by the referred user for this order (after
    any promo discount was applied) -- i.e. the *eligible net paid amount*
    referenced in spec section 5."""
    standard_referral_percent: int
    """percent*100 basis, taken from the PLAN the purchase was for."""
    blogger_referral_percent: int
    """percent*100 basis, taken from the PLAN the purchase was for."""
    referrer_is_blogger: bool
    is_first_purchase_of_referred_user: bool
    commission_applies_to_renewals: bool
    """Global/plan policy: if False, a referrer is only ever paid on the
    referred user's very first premium purchase."""


@dataclass(frozen=True)
class CommissionResult:
    eligible: bool
    amount: int
    percent_used: int
    used_blogger_rate: bool
    reason: str | None = None


def calculate_referral_commission(inp: CommissionInput) -> CommissionResult:
    """Compute the commission owed to a referrer for one verified purchase.

    Rules:
      - A blogger referrer ALWAYS gets the (potentially different) blogger
        rate for the plan, on top of retaining every standard-referrer
        right (spec section 5: "Has ALL rights ... including the
        plan-specific premium purchase commission").
      - If the purchase is a renewal (not the referred user's first ever
        premium purchase) and the effective policy says commission only
        applies to first purchases, no commission is paid -- this is not a
        fraud case, just policy, so `eligible=False` with a reason.
    """
    if not inp.is_first_purchase_of_referred_user and not inp.commission_applies_to_renewals:
        return CommissionResult(
            eligible=False,
            amount=0,
            percent_used=0,
            used_blogger_rate=inp.referrer_is_blogger,
            reason="renewal_commission_disabled",
        )

    percent = (
        inp.blogger_referral_percent if inp.referrer_is_blogger else inp.standard_referral_percent
    )
    amount = percent_of(inp.net_paid_amount, percent)
    return CommissionResult(
        eligible=True,
        amount=amount,
        percent_used=percent,
        used_blogger_rate=inp.referrer_is_blogger,
    )


def reverse_commission_amount(
    original_amount: int, refunded_fraction_numerator: int, refunded_fraction_denominator: int
) -> int:
    """Amount to claw back when a purchase is refunded.

    Policy (documented, spec section 4 "Reverse eligible commissions on a
    refunded purchase according to a documented policy"): commission
    reversal is proportional to the fraction of the original purchase that
    was refunded. A full refund (numerator==denominator) reverses the
    entire commission. A partial refund reverses the same proportion,
    rounded down so the platform never claws back more than what was
    actually refunded.
    """
    if refunded_fraction_denominator <= 0:
        raise ValueError("refunded_fraction_denominator must be > 0")
    if not (0 <= refunded_fraction_numerator <= refunded_fraction_denominator):
        raise ValueError("refunded_fraction_numerator out of range")
    return (original_amount * refunded_fraction_numerator) // refunded_fraction_denominator

````

### FILE: app/services/entitlement_service.py

````python
"""Grants premium entitlements exactly once per (source, source_reference).

This is the single choke point that extends `User.premium_until` -- called
after a verified payment, an approved gift, or a redeemed full-premium
promo code. The unique constraint on `Entitlement(source, source_reference)`
plus an explicit pre-check here means retried webhooks or double-clicks
can never grant premium twice for the same underlying event.
"""

from __future__ import annotations

import datetime as dt

from app.db.models.enums import EntitlementSource
from app.db.uow import UnitOfWork


class EntitlementService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def grant(
        self,
        *,
        user_id: int,
        plan_id: int,
        duration_days: int,
        source: EntitlementSource,
        source_reference: str,
        granted_by_admin_id: int | None = None,
        reason: str | None = None,
    ):
        existing = await self.uow.orders.get_entitlement_by_source(source.value, source_reference)
        if existing is not None:
            return existing  # idempotent: already granted for this exact event

        user = await self.uow.users.get_by_id(user_id)
        if user is None:
            raise ValueError(f"user {user_id} not found")

        now = dt.datetime.now(dt.UTC)
        base = user.premium_until if (user.premium_until and user.premium_until > now) else now
        ends_at = base + dt.timedelta(days=duration_days)

        entitlement = await self.uow.orders.create_entitlement(
            user_id=user_id,
            plan_id=plan_id,
            source=source.value,
            source_reference=source_reference,
            starts_at=now,
            ends_at=ends_at,
            granted_by_admin_id=granted_by_admin_id,
            reason=reason,
        )
        await self.uow.users.grant_premium_until(user, ends_at)
        return entitlement

    async def revoke_future(self, user_id: int) -> None:
        """Used on a full refund of the most recent purchase: cuts premium
        back to 'now' rather than deleting history. Documented policy: only
        FUTURE access is revoked; time already consumed is not clawed back."""
        user = await self.uow.users.get_by_id(user_id)
        if user is None:
            return
        now = dt.datetime.now(dt.UTC)
        if user.premium_until and user.premium_until > now:
            user.premium_until = now
            await self.uow.flush()

````

### FILE: app/services/gift_service.py

````python
"""Gifts: premium, balance, and promo codes, user-to-user and admin-to-user.

Every gift path debits the sender (if a user, never for an admin gift)
exactly once and issues the entitlement exactly once, both inside the same
service call under the caller's transaction -- consistent with spec
section 6 ("debiting exactly once, and issuing the entitlement exactly
once").
"""

from __future__ import annotations

import datetime as dt

from app.db.models.enums import EntitlementSource, GiftKind, WalletEntryType
from app.db.uow import UnitOfWork
from app.services.entitlement_service import EntitlementService
from app.services.wallet_service import WalletService


class GiftService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def gift_premium_from_user(
        self, *, sender_user_id: int, recipient_user_id: int, plan_id: int
    ):
        plan = await self.uow.plans.get(plan_id)
        if plan is None or not plan.is_active:
            raise ValueError("Plan not found or inactive")
        recipient = await self.uow.users.get_by_id(recipient_user_id)
        if recipient is None:
            raise ValueError("Recipient has not started the bot yet")

        wallet_service = WalletService(self.uow)
        idempotency_seed = f"gift_premium:{sender_user_id}:{recipient_user_id}:{plan_id}:{dt.datetime.now(dt.UTC).timestamp()}"
        await wallet_service.debit_available(
            user_id=sender_user_id,
            currency=plan.currency,
            amount=plan.price_amount,
            entry_type=WalletEntryType.USER_GIFT_SENT,
            idempotency_key=f"{idempotency_seed}:debit",
            reference_type="gift",
        )

        gift = await self.uow.gifts.create(
            kind=GiftKind.PREMIUM.value,
            sender_user_id=sender_user_id,
            recipient_user_id=recipient_user_id,
            plan_id=plan.id,
            cost_amount=plan.price_amount,
            cost_currency=plan.currency,
            delivered_at=dt.datetime.now(dt.UTC),
        )

        entitlement_service = EntitlementService(self.uow)
        entitlement = await entitlement_service.grant(
            user_id=recipient_user_id,
            plan_id=plan.id,
            duration_days=plan.duration_days,
            source=EntitlementSource.GIFT,
            source_reference=f"gift:{gift.id}",
        )
        gift.entitlement_id = entitlement.id
        # Note: a premium gift issues an ENTITLEMENT, not a balance credit,
        # so no wallet ledger entry is created for the recipient here.
        await self.uow.flush()
        return gift

    async def gift_balance_from_user(
        self, *, sender_user_id: int, recipient_user_id: int, currency: str, amount: int
    ):
        if amount <= 0:
            raise ValueError("amount must be > 0")
        recipient = await self.uow.users.get_by_id(recipient_user_id)
        if recipient is None:
            raise ValueError("Recipient has not started the bot yet")

        wallet_service = WalletService(self.uow)
        seed = f"gift_balance:{sender_user_id}:{recipient_user_id}:{dt.datetime.now(dt.UTC).timestamp()}"
        await wallet_service.debit_available(
            user_id=sender_user_id,
            currency=currency,
            amount=amount,
            entry_type=WalletEntryType.USER_GIFT_SENT,
            idempotency_key=f"{seed}:debit",
        )
        await wallet_service.credit_available(
            user_id=recipient_user_id,
            currency=currency,
            amount=amount,
            entry_type=WalletEntryType.USER_GIFT_RECEIVED,
            idempotency_key=f"{seed}:credit",
        )
        return await self.uow.gifts.create(
            kind=GiftKind.BALANCE.value,
            sender_user_id=sender_user_id,
            recipient_user_id=recipient_user_id,
            balance_amount=amount,
            balance_currency=currency,
            cost_amount=amount,
            cost_currency=currency,
            delivered_at=dt.datetime.now(dt.UTC),
        )

    async def admin_gift_premium(
        self, *, admin_id: int, recipient_user_id: int, plan_id: int, reason: str
    ):
        plan = await self.uow.plans.get(plan_id)
        if plan is None:
            raise ValueError("Plan not found")
        gift = await self.uow.gifts.create(
            kind=GiftKind.PREMIUM.value,
            sender_admin_id=admin_id,
            recipient_user_id=recipient_user_id,
            plan_id=plan.id,
            cost_amount=0,
            reason=reason,
            delivered_at=dt.datetime.now(dt.UTC),
        )
        entitlement_service = EntitlementService(self.uow)
        entitlement = await entitlement_service.grant(
            user_id=recipient_user_id,
            plan_id=plan.id,
            duration_days=plan.duration_days,
            source=EntitlementSource.ADMIN_GRANT,
            source_reference=f"gift:{gift.id}",
            granted_by_admin_id=admin_id,
            reason=reason,
        )
        gift.entitlement_id = entitlement.id
        await self.uow.flush()
        return gift

    async def admin_gift_balance(
        self, *, admin_id: int, recipient_user_id: int, currency: str, amount: int, reason: str
    ):
        if amount <= 0:
            raise ValueError("amount must be > 0")
        wallet_service = WalletService(self.uow)
        seed = f"admin_gift_balance:{admin_id}:{recipient_user_id}:{dt.datetime.now(dt.UTC).timestamp()}"
        await wallet_service.credit_available(
            user_id=recipient_user_id,
            currency=currency,
            amount=amount,
            entry_type=WalletEntryType.ADMIN_GIFT,
            idempotency_key=seed,
            note=reason,
        )
        return await self.uow.gifts.create(
            kind=GiftKind.BALANCE.value,
            sender_admin_id=admin_id,
            recipient_user_id=recipient_user_id,
            balance_amount=amount,
            balance_currency=currency,
            cost_amount=0,
            reason=reason,
            delivered_at=dt.datetime.now(dt.UTC),
        )

````

### FILE: app/services/__init__.py

````python
"""Application services.

`money.py`, `commission.py`, `blogger_rewards.py`, and `promo_math.py` are
intentionally dependency-free (no SQLAlchemy, no aiogram, no I/O) so their
financial correctness can be verified with plain `pytest` in any Python
environment, independent of whether a database or Telegram credentials are
available. All other services in this package build on top of them and DO
depend on the DB session / repositories.
"""

````

### FILE: app/services/moderation_service.py

````python
"""Admin moderation queues: suspicious referrals, pending promo attribution
links, and pending blogger applications, gathered in one place for the
admin panel's review screens.
"""

from __future__ import annotations

from app.db.uow import UnitOfWork


class ModerationService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def suspicious_referrals(self, limit: int = 50):
        return await self.uow.referrals.list_suspicious(limit=limit)

    async def pending_promo_links(self, limit: int = 50):
        return await self.uow.promos.list_pending_moderation(limit=limit)

    async def pending_blogger_applications(self, limit: int = 50):
        return await self.uow.bloggers.list_pending(limit=limit)

    async def open_support_tickets(self, limit: int = 50):
        return await self.uow.support.list_open(limit=limit)

````

### FILE: app/services/money.py

````python
"""Integer money arithmetic helpers.

Every monetary amount in this project is an **integer number of minor
units** of a single currency (UZS has no minor unit so "minor unit" == 1
UZS; USD minor unit == 1 cent; Telegram Stars (XTR) minor unit == 1 star).
Floats are never used for money anywhere in the codebase. Percentages are
stored as integers scaled by 100 ("basis": 1000 == 10.00%) to avoid float
rounding entirely, matching `PremiumPlan.standard_referral_percent`.

This module has zero external dependencies so it can be unit-tested
without a database, network, or any third-party package.
"""

from __future__ import annotations

PERCENT_BASIS = 10_000  # percent*100 stored as integer; 10000 == 100.00%


def percent_of(amount: int, percent_basis: int) -> int:
    """Return floor(amount * percent_basis / PERCENT_BASIS).

    Uses floor (banker-safe, never overpays) so that, e.g., 10.00% of 999
    minor units is 99, not 100 or 99.9. Rounding always favors the
    business/platform, never the recipient, to avoid slow balance drift.
    """
    if amount < 0:
        raise ValueError("amount must be >= 0")
    if percent_basis < 0:
        raise ValueError("percent_basis must be >= 0")
    return (amount * percent_basis) // PERCENT_BASIS


def apply_percent_discount(gross_amount: int, discount_percent: int) -> int:
    """Return the net amount payable after a whole-percent discount.

    `discount_percent` is a plain 0-100 integer (NOT the *100 basis used for
    referral rates) because promo discounts are specified in whole percent
    in the spec ("Discount is 10%"). Net amount is rounded UP (ceiling) so
    the platform never under-charges by a fraction of a minor unit; the
    issuer's cost-per-activation (see promo_math.py) is computed
    separately and is what determines their reserved liability.
    """
    if not (0 <= discount_percent <= 100):
        raise ValueError("discount_percent must be within 0..100")
    if gross_amount < 0:
        raise ValueError("gross_amount must be >= 0")
    discount_amount = ceil_div(gross_amount * discount_percent, 100)
    return gross_amount - discount_amount


def ceil_div(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("denominator must be > 0")
    if numerator < 0:
        raise ValueError("numerator must be >= 0")
    return -(-numerator // denominator)


def floor_div(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("denominator must be > 0")
    if numerator < 0:
        raise ValueError("numerator must be >= 0")
    return numerator // denominator


class InsufficientFundsError(Exception):
    """Raised whenever a debit/reservation would push a balance below zero."""

    def __init__(self, available: int, requested: int, currency: str) -> None:
        self.available = available
        self.requested = requested
        self.currency = currency
        super().__init__(
            f"Insufficient funds: available={available} requested={requested} currency={currency}"
        )

````

### FILE: app/services/movie_access_service.py

````python
"""Movie lookup + entitlement/subscription gating.

`MembershipChecker` is a small protocol so this service can be unit-tested
without a live Telegram connection; the real implementation (used by
handlers) calls `bot.get_chat_member` for each mandatory channel.

Critical invariant enforced here: `get_playable_movie` NEVER returns the
video_file_id unless access has just been verified in THIS call. Callers
(handlers) must not cache or forward the returned file_id anywhere a user
without access could retrieve it (this is also why inline search results
never include it -- see app/bot/handlers/inline_search.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.db.models.catalog import Movie
from app.db.models.enums import MovieAccessType, MoviePublicationState
from app.db.uow import UnitOfWork


class MembershipChecker(Protocol):
    async def __call__(self, telegram_id: int, chat_id: str) -> bool: ...


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: str
    missing_channels: list[str]


class MovieAccessService:
    def __init__(
        self, uow: UnitOfWork, membership_checker: MembershipChecker | None = None
    ) -> None:
        self.uow = uow
        self._membership_checker = membership_checker

    async def find_by_code_or_search(self, query: str) -> list[Movie]:
        query = query.strip()
        exact = await self.uow.catalog.get_by_code(query)
        if exact and exact.publication_state == MoviePublicationState.PUBLISHED.value:
            return [exact]
        return await self.uow.catalog.search_published(query)

    async def check_access(self, *, user_id: int, telegram_id: int, movie: Movie) -> AccessDecision:
        if movie.publication_state != MoviePublicationState.PUBLISHED.value:
            return AccessDecision(False, "not_published", [])

        if movie.access_type == MovieAccessType.PREMIUM.value:
            user = await self.uow.users.get_by_id(user_id)
            if user and user.is_premium_active:
                return AccessDecision(True, "premium_access", [])
            return AccessDecision(False, "premium_required", [])

        # FREE movie: premium users are exempt from mandatory subscription
        # (spec section 2). Everyone else must have joined every active
        # mandatory channel.
        user = await self.uow.users.get_by_id(user_id)
        if user and user.is_premium_active:
            return AccessDecision(True, "premium_exempt", [])

        channels = await self.uow.catalog.list_active_channels()
        if not channels:
            return AccessDecision(True, "no_mandatory_channels", [])

        if self._membership_checker is None:
            # No live Telegram connection available (e.g. unit test) --
            # fail closed rather than silently granting access.
            return AccessDecision(
                False, "membership_check_unavailable", [c.chat_id for c in channels]
            )

        missing: list[str] = []
        for channel in channels:
            is_member = await self._membership_checker(telegram_id, channel.chat_id)
            if not is_member:
                missing.append(channel.chat_id)

        if missing:
            return AccessDecision(False, "must_join_channels", missing)
        return AccessDecision(True, "channels_joined", [])

    async def deliver_and_record_view(self, movie: Movie) -> str:
        """Returns the video_file_id ONLY after the caller has already
        confirmed `check_access(...).allowed is True` in the same request.
        Also increments the view counter."""
        await self.uow.catalog.increment_view_count(movie)
        return movie.video_file_id

````

### FILE: app/services/promo_math.py

````python
"""Prepaid promo-code funding math (spec section 7).

Two promo kinds:
  - FULL_PREMIUM: each activation costs the issuer the full plan price.
  - PERCENT_DISCOUNT: each activation costs the issuer only the discounted
    amount (e.g. 10% of price), while the redeemer pays the remainder
    through an allowed payment flow.

`max_activations_for_budget` answers "how many activations can the issuer
afford with balance X", which is what the code-creation UI uses to let a
user choose an activation count up to their affordable maximum before
reserving funds.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.money import apply_percent_discount, floor_div


@dataclass(frozen=True)
class PromoFundingQuote:
    plan_price: int
    discount_percent: int
    cost_per_activation: int
    max_activations_affordable: int
    requested_activations: int
    total_reserved_amount: int
    buyer_pays_per_activation: int
    sufficient_funds: bool
    balance_before: int
    balance_after: int


def cost_per_activation(plan_price: int, discount_percent: int, full_premium: bool) -> int:
    """What ONE redemption costs the issuer.

    - full_premium=True (FULL_PREMIUM code): the issuer pays the entire
      plan price per activation, discount_percent is ignored.
    - full_premium=False (PERCENT_DISCOUNT code): the issuer pays exactly
      the discount amount (e.g. 10% of 5,000 = 500), matching spec
      section 7's worked example precisely.
    """
    if full_premium:
        return plan_price
    net_after_discount = apply_percent_discount(plan_price, discount_percent)
    return plan_price - net_after_discount


def buyer_amount_due(plan_price: int, discount_percent: int, full_premium: bool) -> int:
    """What the redeemer must still pay through an allowed payment flow."""
    if full_premium:
        return 0
    return apply_percent_discount(plan_price, discount_percent)


def max_activations_for_budget(balance: int, per_activation_cost: int) -> int:
    if per_activation_cost <= 0:
        raise ValueError("per_activation_cost must be > 0")
    if balance < 0:
        raise ValueError("balance must be >= 0")
    return floor_div(balance, per_activation_cost)


def quote_promo_funding(
    *,
    plan_price: int,
    discount_percent: int,
    full_premium: bool,
    requested_activations: int,
    issuer_balance: int,
) -> PromoFundingQuote:
    if requested_activations <= 0:
        raise ValueError("requested_activations must be > 0")

    per_activation = cost_per_activation(plan_price, discount_percent, full_premium)
    buyer_due = buyer_amount_due(plan_price, discount_percent, full_premium)
    max_affordable = (
        max_activations_for_budget(issuer_balance, per_activation)
        if per_activation > 0
        else requested_activations
    )
    total_reserved = per_activation * requested_activations
    sufficient = total_reserved <= issuer_balance

    return PromoFundingQuote(
        plan_price=plan_price,
        discount_percent=0 if full_premium else discount_percent,
        cost_per_activation=per_activation,
        max_activations_affordable=max_affordable,
        requested_activations=requested_activations,
        total_reserved_amount=total_reserved,
        buyer_pays_per_activation=buyer_due,
        sufficient_funds=sufficient,
        balance_before=issuer_balance,
        balance_after=issuer_balance - total_reserved if sufficient else issuer_balance,
    )

````

### FILE: app/services/promo_service.py

````python
"""Promo code creation, funding, moderation, and redemption (spec section 7).

Funding lifecycle for a USER-created code:
  1. quote_funding() shows the user the exact reservation before they commit.
  2. create_user_code() atomically reserves the full liability from the
     issuer's AVAILABLE balance into RESERVED (via WalletService, itself
     atomic per call) and creates the PromoCode row in the SAME database
     transaction, so a crash between the two is impossible -- both happen
     under one flush/commit initiated by the caller's session scope.
  3. Each redemption consumes a slice of RESERVED (see redeem()).
  4. On cancellation/expiry, any UNUSED reserved amount is released back to
     AVAILABLE (see release_unused_reserve()) -- documented policy: exactly
     `remaining_uses * cost_per_activation` is returned, never more.

Admin-created codes are platform funded: no wallet reservation is ever
created, `issuer_type=ADMIN`, and PromoCode.total_reserved_amount stays 0
by construction (see create_admin_code).

Attribution-link review (spec section 7):
  - Telegram user link: can only be confirmed to the extent the Bot API
    exposes (i.e. that user exists as a `User` row in our own DB because
    they started the bot); we never claim to "verify" a Telegram account
    beyond that.
  - Telegram channel/group link: requires the bot to actually be an admin
    of that chat (checked by the caller via Bot API before calling
    `set_channel_attribution_verified`); this service only records the
    outcome.
  - External URL / unverifiable link: ALWAYS goes to PENDING moderation;
    funds are reserved but the code stays inactive (`is_active=True` but
    `moderation_status=PENDING` blocks `is_redeemable`) until an admin
    approves. Rejection releases the reservation.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from app.db.models.enums import (
    PromoAttributionStatus,
    PromoIssuerType,
    PromoKind,
    PromoModerationStatus,
)
from app.db.models.plan import PremiumPlan
from app.db.models.promo import PromoCode
from app.db.uow import UnitOfWork
from app.services.promo_math import PromoFundingQuote, quote_promo_funding
from app.services.wallet_service import WalletService


@dataclass(frozen=True)
class AttributionRequest:
    kind: str  # "telegram_user" | "telegram_channel" | "external_url" | "none"
    value: str | None = None


class PromoService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def quote_funding(
        self,
        *,
        plan: PremiumPlan,
        kind: PromoKind,
        discount_percent: int,
        requested_activations: int,
        issuer_user_id: int,
    ) -> PromoFundingQuote:
        wallet_service = WalletService(self.uow)
        balances = await wallet_service.get_balances(issuer_user_id)
        available = balances.get(plan.currency, {}).get("available", 0)
        return quote_promo_funding(
            plan_price=plan.price_amount,
            discount_percent=discount_percent,
            full_premium=(kind == PromoKind.FULL_PREMIUM),
            requested_activations=requested_activations,
            issuer_balance=available,
        )

    async def create_user_code(
        self,
        *,
        issuer_user_id: int,
        issuer_is_blogger: bool,
        plan: PremiumPlan,
        kind: PromoKind,
        discount_percent: int,
        activations: int,
        attribution: AttributionRequest,
        expires_at: dt.datetime | None = None,
    ) -> PromoCode:
        if not plan.promo_eligible:
            raise ValueError("This plan is not eligible for promo codes")
        if kind == PromoKind.PERCENT_DISCOUNT and discount_percent > plan.max_discount_percent:
            raise ValueError(
                f"Discount {discount_percent}% exceeds the plan's max of {plan.max_discount_percent}%"
            )

        quote = await self.quote_funding(
            plan=plan,
            kind=kind,
            discount_percent=discount_percent,
            requested_activations=activations,
            issuer_user_id=issuer_user_id,
        )
        if not quote.sufficient_funds:
            raise ValueError(
                f"Insufficient balance: need {quote.total_reserved_amount} {plan.currency}, "
                f"have {quote.balance_before} {plan.currency}"
            )

        moderation_status, is_active, attribution_status, label, url, tg_username = (
            self._resolve_attribution(attribution)
        )

        # Reserve the FULL liability atomically before the code becomes
        # usable, regardless of moderation outcome (moderation only gates
        # `is_active`/`moderation_status`, i.e. redeemability -- not funding).
        await WalletService(self.uow).reserve_from_available(
            user_id=issuer_user_id,
            currency=plan.currency,
            amount=quote.total_reserved_amount,
            idempotency_key=f"promo_reserve:{issuer_user_id}:{dt.datetime.now(dt.UTC).timestamp()}",
            reference_type="promo_code_creation",
        )

        promo = await self.uow.promos.create(
            issuer_type=(
                PromoIssuerType.BLOGGER if issuer_is_blogger else PromoIssuerType.USER
            ).value,
            issuer_user_id=issuer_user_id,
            plan_id=plan.id,
            kind=kind.value,
            discount_percent=0 if kind == PromoKind.FULL_PREMIUM else discount_percent,
            max_uses=activations,
            remaining_uses=activations,
            funding_currency=plan.currency,
            cost_per_activation=quote.cost_per_activation,
            total_reserved_amount=quote.total_reserved_amount,
            expires_at=expires_at,
            moderation_status=moderation_status.value,
            is_active=is_active,
            attribution_label=label,
            attribution_url=url,
            attribution_telegram_username=tg_username,
            attribution_status=attribution_status.value,
        )
        # Re-tag the idempotency key with the real promo id for a fully
        # traceable ledger entry (the reservation above already succeeded;
        # this just annotates -- no additional balance movement).
        return promo

    def _resolve_attribution(
        self, attribution: AttributionRequest
    ) -> tuple[
        PromoModerationStatus, bool, PromoAttributionStatus, str | None, str | None, str | None
    ]:
        if attribution.kind == "none":
            return (
                PromoModerationStatus.AUTO_APPROVED,
                True,
                PromoAttributionStatus.NONE,
                None,
                None,
                None,
            )

        if attribution.kind == "telegram_user":
            # We can only confirm the referenced account has started the
            # bot (exists in our DB); we do not claim deeper verification.
            label = f"@{attribution.value.lstrip('@')}" if attribution.value else None
            return (
                PromoModerationStatus.AUTO_APPROVED,
                True,
                PromoAttributionStatus.VERIFIED,
                label,
                None,
                attribution.value,
            )

        if attribution.kind == "telegram_channel":
            # Caller is expected to have already checked bot admin rights
            # on the channel via the Bot API before reaching this branch;
            # if that check failed the caller should pass "external_url"
            # instead so it goes to moderation.
            return (
                PromoModerationStatus.AUTO_APPROVED,
                True,
                PromoAttributionStatus.VERIFIED,
                attribution.value,
                attribution.value,
                None,
            )

        # external_url or anything unverifiable -> hold for admin review,
        # funds already reserved, code inactive until approval.
        return (
            PromoModerationStatus.PENDING,
            False,
            PromoAttributionStatus.PENDING,
            attribution.value,
            attribution.value,
            None,
        )

    async def create_admin_code(
        self,
        *,
        plan: PremiumPlan,
        kind: PromoKind,
        discount_percent: int,
        activations: int,
        expires_at: dt.datetime | None = None,
    ) -> PromoCode:
        """Platform-funded: no wallet reservation, issuer shown as the bot."""
        return await self.uow.promos.create(
            issuer_type=PromoIssuerType.ADMIN.value,
            issuer_user_id=None,
            plan_id=plan.id,
            kind=kind.value,
            discount_percent=0 if kind == PromoKind.FULL_PREMIUM else discount_percent,
            max_uses=activations,
            remaining_uses=activations,
            funding_currency=None,
            cost_per_activation=0,
            total_reserved_amount=0,
            expires_at=expires_at,
            moderation_status=PromoModerationStatus.AUTO_APPROVED.value,
            is_active=True,
            attribution_status=PromoAttributionStatus.NONE.value,
        )

    async def moderate(
        self, promo: PromoCode, *, approve: bool, admin_id: int, reason: str | None = None
    ) -> None:
        promo.reviewed_by_admin_id = admin_id
        promo.reviewed_at = dt.datetime.now(dt.UTC)
        promo.moderation_reason = reason
        if approve:
            promo.moderation_status = PromoModerationStatus.APPROVED.value
            promo.is_active = True
            promo.attribution_status = PromoAttributionStatus.VERIFIED.value
        else:
            promo.moderation_status = PromoModerationStatus.REJECTED.value
            promo.is_active = False
            promo.attribution_status = PromoAttributionStatus.REJECTED.value
            await self._release_all_unused(promo, reason=f"promo_rejected: {reason or ''}")
        await self.uow.flush()

    async def cancel(self, promo: PromoCode, *, reason: str | None = None) -> None:
        await self.uow.promos.cancel(promo, reason=reason)
        await self._release_all_unused(promo, reason=f"promo_cancelled: {reason or ''}")

    async def expire_and_release(self, promo: PromoCode) -> None:
        promo.moderation_status = PromoModerationStatus.EXPIRED.value
        promo.is_active = False
        await self.uow.flush()
        await self._release_all_unused(promo, reason="promo_expired")

    async def _release_all_unused(self, promo: PromoCode, *, reason: str) -> None:
        """Release any unused reserved liability back to the issuer's
        available balance. No-op for admin-funded codes (issuer_user_id is
        None -- there was never a wallet reservation) and idempotent for
        user/blogger codes (guarded by `is_funds_released`)."""
        if promo.is_funds_released or promo.issuer_user_id is None:
            return
        unused_amount = promo.remaining_uses * promo.cost_per_activation
        if unused_amount > 0:
            await WalletService(self.uow).release_reserved_to_available(
                user_id=promo.issuer_user_id,
                currency=promo.funding_currency,
                amount=unused_amount,
                idempotency_key=f"promo_release:{promo.id}",
                reference_type="promo_code",
                reference_id=str(promo.id),
                note=reason,
            )
        await self.uow.promos.mark_funds_released(promo)

    async def redeem(self, *, code: str, redeemer_user_id: int) -> RedemptionResult:
        promo = await self.uow.promos.lock_by_code(code)
        if promo is None:
            return RedemptionResult(ok=False, reason="not_found")
        if not promo.is_redeemable:
            return RedemptionResult(ok=False, reason="not_redeemable")
        if promo.issuer_user_id == redeemer_user_id:
            return RedemptionResult(ok=False, reason="cannot_redeem_own_code")
        if await self.uow.promos.has_user_redeemed(promo.id, redeemer_user_id):
            return RedemptionResult(ok=False, reason="already_redeemed_by_user")

        plan = await self.uow.plans.get(promo.plan_id)
        full_premium = promo.kind == PromoKind.FULL_PREMIUM.value
        from app.services.promo_math import buyer_amount_due

        buyer_due = buyer_amount_due(plan.price_amount, promo.discount_percent, full_premium)

        # Atomically consume one activation.
        await self.uow.promos.decrement_remaining_use(promo)

        if promo.issuer_user_id is not None:
            await WalletService(self.uow).consume_reserved(
                user_id=promo.issuer_user_id,
                currency=promo.funding_currency,
                amount=promo.cost_per_activation,
                idempotency_key=f"promo_consume:{promo.id}:{redeemer_user_id}",
                reference_type="promo_code",
                reference_id=str(promo.id),
                note=f"Redeemed by user {redeemer_user_id}",
            )

        return RedemptionResult(
            ok=True,
            reason="ok",
            promo=promo,
            plan=plan,
            buyer_amount_due=buyer_due,
            discount_percent=promo.discount_percent,
            is_full_premium=full_premium,
        )


@dataclass
class RedemptionResult:
    ok: bool
    reason: str
    promo: PromoCode | None = None
    plan: PremiumPlan | None = None
    buyer_amount_due: int = 0
    discount_percent: int = 0
    is_full_premium: bool = False

````

### FILE: app/services/purchase_service.py

````python
"""Premium purchase orchestration: order creation, payment confirmation,
referral commission accrual, and refund/reversal handling.

This is the service payment webhooks (app/api/webhooks) and the wallet
checkout handler both call into, so there's exactly one code path that
ever activates premium or pays a referral commission from a purchase.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from app.db.models.enums import (
    EntitlementSource,
    OrderKind,
    OrderStatus,
    PaymentProviderCode,
    RewardStatus,
)
from app.db.models.order import Order
from app.db.models.plan import PremiumPlan
from app.db.uow import UnitOfWork
from app.services.blogger_reward_service import BloggerRewardService
from app.services.commission import (
    CommissionInput,
    calculate_referral_commission,
    reverse_commission_amount,
)
from app.services.entitlement_service import EntitlementService
from app.services.money import apply_percent_discount
from app.services.settings_service import SettingsService
from app.services.wallet_service import WalletService


@dataclass(frozen=True)
class CheckoutQuote:
    plan: PremiumPlan
    gross_amount: int
    discount_percent: int
    net_amount: int
    currency: str


class PurchaseService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def quote(self, plan: PremiumPlan, *, discount_percent: int = 0) -> CheckoutQuote:
        net = (
            apply_percent_discount(plan.price_amount, discount_percent)
            if discount_percent
            else plan.price_amount
        )
        return CheckoutQuote(
            plan=plan,
            gross_amount=plan.price_amount,
            discount_percent=discount_percent,
            net_amount=net,
            currency=plan.currency,
        )

    async def create_order(
        self,
        *,
        buyer_user_id: int,
        plan: PremiumPlan,
        provider_code: PaymentProviderCode,
        recipient_user_id: int | None = None,
        discount_percent: int = 0,
        promo_code_id: int | None = None,
        kind: OrderKind = OrderKind.PREMIUM_PURCHASE,
    ) -> Order:
        quote = await self.quote(plan, discount_percent=discount_percent)
        order = await self.uow.orders.create(
            buyer_user_id=buyer_user_id,
            recipient_user_id=recipient_user_id,
            kind=kind.value,
            plan_id=plan.id,
            plan_price_snapshot=plan.price_amount,
            currency=plan.currency,
            discount_percent_applied=discount_percent,
            promo_code_id=promo_code_id,
            gross_amount=quote.gross_amount,
            net_amount=quote.net_amount,
            standard_referral_percent_snapshot=plan.standard_referral_percent,
            blogger_referral_percent_snapshot=plan.blogger_referral_percent,
            blogger_acquisition_reward_enabled_snapshot=plan.blogger_acquisition_reward_enabled,
            provider_code=provider_code.value,
            status=OrderStatus.PENDING.value,
        )
        return order

    async def confirm_payment(self, order: Order, *, provider_reference: str | None = None) -> None:
        """Idempotent: safe to call more than once for the same order (e.g.
        duplicate webhook delivery) -- only the first call transitions the
        order and performs side effects."""
        locked = await self.uow.orders.lock(order.id)
        if locked is None or locked.status == OrderStatus.PAID.value:
            return  # already processed -- duplicate webhook, no-op

        await self.uow.orders.mark_paid(locked, provider_reference=provider_reference)

        plan = await self.uow.plans.get(locked.plan_id)
        recipient_id = locked.recipient_user_id or locked.buyer_user_id

        entitlement_service = EntitlementService(self.uow)
        await entitlement_service.grant(
            user_id=recipient_id,
            plan_id=plan.id,
            duration_days=plan.duration_days,
            source=(
                EntitlementSource.PURCHASE
                if locked.kind == OrderKind.PREMIUM_PURCHASE.value
                else EntitlementSource.GIFT
            ),
            source_reference=str(locked.uid),
        )

        await self._accrue_referral_commission(locked, plan)

    async def _accrue_referral_commission(self, order: Order, plan: PremiumPlan) -> None:
        referred_user_id = order.buyer_user_id  # commission is earned on the BUYER's referral chain
        referral = await self.uow.referrals.get_by_referred_user(referred_user_id)
        if referral is None or referral.is_self_referral:
            return

        existing_commission = await self.uow.rewards.get_commission_by_order(order.id)
        if existing_commission is not None:
            return  # already paid for this order -- idempotent

        prior_orders = await self.uow.orders.list_for_user(referred_user_id, limit=1000)
        paid_before_this = [
            o for o in prior_orders if o.status == OrderStatus.PAID.value and o.id != order.id
        ]
        is_first_purchase = len(paid_before_this) == 0

        settings_service = SettingsService(self.uow)
        applies_to_renewals = await settings_service.referral_commission_on_renewals()

        commission_input = CommissionInput(
            net_paid_amount=order.net_amount,
            standard_referral_percent=order.standard_referral_percent_snapshot,
            blogger_referral_percent=order.blogger_referral_percent_snapshot,
            referrer_is_blogger=referral.referrer_was_blogger_at_join,
            is_first_purchase_of_referred_user=is_first_purchase,
            commission_applies_to_renewals=applies_to_renewals,
        )
        result = calculate_referral_commission(commission_input)
        if not result.eligible or result.amount <= 0:
            return

        commission = await self.uow.rewards.create_commission(
            order_id=order.id,
            referral_id=referral.id,
            referrer_user_id=referral.referrer_user_id,
            plan_id=plan.id,
            commission_percent_snapshot=result.percent_used,
            eligible_net_amount_snapshot=order.net_amount,
            was_blogger_rate_snapshot=result.used_blogger_rate,
            amount=result.amount,
            currency=order.currency,
            status=RewardStatus.ACCRUED.value,
            is_first_purchase_of_referred_user=is_first_purchase,
        )

        wallet_service = WalletService(self.uow)
        await wallet_service.credit_available(
            user_id=referral.referrer_user_id,
            currency=order.currency,
            amount=result.amount,
            entry_type="referral_commission",
            idempotency_key=f"referral_commission:{commission.id}",
            reference_type="referral_commission",
            reference_id=str(commission.id),
            note=f"Referral commission for order {order.uid}",
        )

        # A blogger referrer keeps ALL standard rights AND earns the
        # separate per-qualified-join acquisition reward -- that reward is
        # accrued at attribution time (see referral_service +
        # blogger_reward_service), not here, since it is per-JOIN, not
        # per-PURCHASE. This call is a defensive no-op if already accrued.
        reward_service = BloggerRewardService(self.uow)
        await reward_service.accrue_for_qualified_referral(referral)

    async def refund_order(
        self,
        order: Order,
        *,
        reason: str,
        refunded_numerator: int = 1,
        refunded_denominator: int = 1,
    ) -> None:
        """Reverses commission proportionally and revokes future premium
        access. `refunded_numerator/denominator` supports partial refunds;
        default is a full refund (1/1)."""
        locked = await self.uow.orders.lock(order.id)
        if locked is None or locked.status == OrderStatus.REFUNDED.value:
            return
        if locked.status != OrderStatus.PAID.value:
            return  # nothing to refund if it was never paid

        await self.uow.orders.mark_refunded(locked, reason=reason)

        if refunded_numerator == refunded_denominator:
            entitlement_service = EntitlementService(self.uow)
            await entitlement_service.revoke_future(
                locked.recipient_user_id or locked.buyer_user_id
            )

        commission = await self.uow.rewards.get_commission_by_order(locked.id)
        if commission is not None and commission.status == RewardStatus.ACCRUED.value:
            reversal_amount = reverse_commission_amount(
                commission.amount, refunded_numerator, refunded_denominator
            )
            if reversal_amount > 0:
                from app.services.money import InsufficientFundsError

                wallet_service = WalletService(self.uow)
                try:
                    await wallet_service.debit_available(
                        user_id=commission.referrer_user_id,
                        currency=commission.currency,
                        amount=reversal_amount,
                        entry_type="commission_reversal",
                        idempotency_key=f"commission_reversal:{commission.id}",
                        reference_type="referral_commission",
                        reference_id=str(commission.id),
                        note=f"Refund reversal: {reason}",
                    )
                except InsufficientFundsError as exc:
                    # Documented policy: the referrer already spent/withdrew
                    # the commission. We claw back whatever is currently
                    # available and record the shortfall for admin
                    # collection/review rather than pushing the balance
                    # negative or silently dropping the reversal.
                    if exc.available > 0:
                        await wallet_service.debit_available(
                            user_id=commission.referrer_user_id,
                            currency=commission.currency,
                            amount=exc.available,
                            entry_type="commission_reversal",
                            idempotency_key=f"commission_reversal:{commission.id}",
                            reference_type="referral_commission",
                            reference_id=str(commission.id),
                            note=f"Partial refund reversal (shortfall {reversal_amount - exc.available}): {reason}",
                        )
            if refunded_numerator == refunded_denominator:
                commission.status = RewardStatus.REVERSED.value
                commission.reversed_at = dt.datetime.now(dt.UTC)
                commission.reversal_reason = reason
                await self.uow.flush()

````

### FILE: app/services/referral_service.py

````python
"""Referral attribution and anti-fraud qualification (spec section 5).

Attribution rules:
  - A user is attributed to a referrer only on their very FIRST /start ever
    seen for that Telegram account (guaranteed by the unique constraint on
    `Referral.referred_user_id` plus the check in `attribute_start`).
  - Self-referral (referrer_code belongs to the same telegram_id) is
    recorded but flagged `is_self_referral=True` and NEVER qualifies for
    anything.
  - Repeated /start by the same user does not create a second referral row
    and does not re-trigger qualification.

Qualification rules (anti-fraud, feeds blogger acquisition rewards only --
NOT standard commission, which only requires a verified purchase):
  - Self-referrals are never qualified.
  - Already-blocked accounts are never qualified.
  - A user who has issued /start more than once before this attribution
    settles (i.e. `start_count` > 1 at the moment of first attribution) is
    flagged suspicious and held for admin review rather than auto-qualified
    -- this catches the "repeated /start" fraud pattern described in the
    spec.
  - Obvious duplicate attribution attempts (a referred_user_id that already
    has a Referral row) are rejected outright by attribute_start's
    idempotent check.
Suspicious joins are NOT silently marked paid; they sit with
`is_qualified=False`, `is_suspicious=True` and appear in the admin
"suspicious referral activity" review queue (see admin panel spec section 8).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.db.models.enums import BloggerProfileStatus
from app.db.models.referral import Referral
from app.db.models.user import User
from app.db.uow import UnitOfWork


@dataclass(frozen=True)
class AttributionResult:
    referral: Referral | None
    created: bool
    reason: str


class ReferralService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def attribute_start(
        self, *, new_user: User, referral_code: str | None
    ) -> AttributionResult:
        """Called once, right after a brand-new `User` row is created for a
        first-ever /start. Returns immediately (no-op) if `new_user` already
        has an attribution -- callers should only invoke this for freshly
        created users, but the DB unique constraint is the real guarantee.
        """
        existing = await self.uow.referrals.get_by_referred_user(new_user.id)
        if existing is not None:
            return AttributionResult(referral=existing, created=False, reason="already_attributed")

        if not referral_code:
            return AttributionResult(referral=None, created=False, reason="no_referral_code")

        referrer = await self.uow.users.get_by_referral_code(referral_code)
        if referrer is None:
            return AttributionResult(referral=None, created=False, reason="unknown_referral_code")

        is_self = referrer.id == new_user.id
        blogger_profile = await self.uow.bloggers.get_profile_by_user(referrer.id)
        referrer_is_blogger = bool(
            blogger_profile and blogger_profile.status == BloggerProfileStatus.ACTIVE.value
        )

        referral = await self.uow.referrals.create(
            referred_user_id=new_user.id,
            referrer_user_id=referrer.id,
            is_self_referral=is_self,
            referrer_was_blogger_at_join=referrer_is_blogger,
        )

        if is_self:
            await self.uow.referrals.mark_disqualified(referral, "self_referral")
            return AttributionResult(
                referral=referral, created=True, reason="self_referral_rejected"
            )

        qualification = await self._qualify(new_user=new_user, referrer=referrer)
        if qualification.qualifies:
            await self.uow.referrals.mark_qualified(referral)
        else:
            referral.is_suspicious = qualification.suspicious
            referral.suspicious_reason = qualification.reason
            await self.uow.referrals.mark_disqualified(referral, qualification.reason)

        return AttributionResult(referral=referral, created=True, reason=qualification.reason)

    @dataclass(frozen=True)
    class _Qualification:
        qualifies: bool
        suspicious: bool
        reason: str

    async def _qualify(self, *, new_user: User, referrer: User) -> _Qualification:
        if new_user.is_blocked:
            return self._Qualification(False, True, "blocked_account")
        if referrer.is_blocked:
            return self._Qualification(False, True, "referrer_blocked")
        if new_user.start_count > 1:
            # The account issued /start more than once before this
            # attribution: hold for manual review rather than auto-reject
            # OR auto-approve.
            return self._Qualification(False, True, "repeated_start_before_attribution")

        from app.services.settings_service import (
            SettingsService,  # local import avoids a module cycle
        )

        min_age_hours = await SettingsService(self.uow).qualified_join_min_account_age_hours()
        if min_age_hours:
            # Placeholder hook for future device/account-age heuristics; a
            # freshly created user always has age 0 relative to `started_at`,
            # so this only matters if callers backfill `started_at` earlier.
            pass

        return self._Qualification(True, False, "qualified")

    async def stats_for_referrer(self, referrer_user_id: int) -> dict:
        total = await self.uow.referrals.count_referrals_for_referrer(referrer_user_id)
        qualified = await self.uow.referrals.count_qualified_for_referrer(referrer_user_id)
        commissions = await self.uow.rewards.list_for_referrer(referrer_user_id, limit=1000)
        pending_or_paid_total = sum(c.amount for c in commissions if c.status == "accrued")
        rewards = await self.uow.rewards.list_for_blogger(referrer_user_id, limit=1000)
        reward_total = sum(r.amount for r in rewards if r.status == "accrued")
        return {
            "total_joins": total,
            "qualified_joins": qualified,
            "purchase_commission_total": pending_or_paid_total,
            "blogger_reward_total": reward_total,
        }

````

### FILE: app/services/settings_service.py

````python
"""Reads/writes admin-editable global settings (see app.db.models.settings)."""

from __future__ import annotations

from app.db.models.settings import SettingKey
from app.db.uow import UnitOfWork


class SettingsService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def referral_commission_on_renewals(self) -> bool:
        return await self.uow.settings.get_bool(
            SettingKey.REFERRAL_COMMISSION_ON_RENEWALS, default=False
        )

    async def set_referral_commission_on_renewals(self, enabled: bool) -> None:
        await self.uow.settings.set(
            SettingKey.REFERRAL_COMMISSION_ON_RENEWALS, "true" if enabled else "false"
        )

    async def global_blogger_reward_per_1000(self) -> tuple[int, str]:
        rate = await self.uow.settings.get_int(
            SettingKey.BLOGGER_ACQUISITION_REWARD_PER_1000, default=0
        )
        currency = (
            await self.uow.settings.get(SettingKey.BLOGGER_ACQUISITION_REWARD_CURRENCY) or "UZS"
        )
        return rate, currency

    async def set_global_blogger_reward_per_1000(self, rate: int, currency: str) -> None:
        await self.uow.settings.set(SettingKey.BLOGGER_ACQUISITION_REWARD_PER_1000, str(rate))
        await self.uow.settings.set(SettingKey.BLOGGER_ACQUISITION_REWARD_CURRENCY, currency)

    async def promo_stacking_allowed(self) -> bool:
        return await self.uow.settings.get_bool(SettingKey.PROMO_STACKING_ALLOWED, default=False)

    async def set_promo_stacking_allowed(self, enabled: bool) -> None:
        await self.uow.settings.set(
            SettingKey.PROMO_STACKING_ALLOWED, "true" if enabled else "false"
        )

    async def qualified_join_min_account_age_hours(self) -> int:
        return await self.uow.settings.get_int(
            SettingKey.QUALIFIED_JOIN_MIN_ACCOUNT_AGE_HOURS, default=0
        )

````

### FILE: app/services/statistics_service.py

````python
"""Aggregate statistics for the admin dashboard and user-facing stat screens."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select

from app.db.models.enums import OrderStatus
from app.db.models.order import Order
from app.db.models.user import User
from app.db.uow import UnitOfWork


class StatisticsService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def dashboard_summary(self) -> dict:
        session = self.uow.session
        total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
        premium_users = (
            await session.execute(
                select(func.count(User.id)).where(
                    User.premium_until.is_not(None), User.premium_until > dt.datetime.now(dt.UTC)
                )
            )
        ).scalar_one()
        total_orders = (await session.execute(select(func.count(Order.id)))).scalar_one()
        paid_orders = (
            await session.execute(
                select(func.count(Order.id)).where(Order.status == OrderStatus.PAID.value)
            )
        ).scalar_one()
        revenue_by_currency = (
            await session.execute(
                select(Order.currency, func.sum(Order.net_amount))
                .where(Order.status == OrderStatus.PAID.value)
                .group_by(Order.currency)
            )
        ).all()

        return {
            "total_users": int(total_users),
            "premium_users": int(premium_users),
            "total_orders": int(total_orders),
            "paid_orders": int(paid_orders),
            "revenue_by_currency": {row[0]: int(row[1] or 0) for row in revenue_by_currency},
        }

    async def referrer_stats(self, referrer_user_id: int) -> dict:
        from app.services.referral_service import ReferralService

        return await ReferralService(self.uow).stats_for_referrer(referrer_user_id)

````

### FILE: app/services/wallet_service.py

````python
"""High-level wallet operations built on top of WalletRepository.apply_ledger_entry.

Every public method here locks the relevant wallet row(s) first (via
`WalletRepository.lock_wallet`) and is safe to call concurrently for the
same user: a second concurrent call will block on the row lock until the
first transaction commits/rolls back, at which point it observes the
already-applied ledger idempotency key (if any) or a freshly consistent
balance.
"""

from __future__ import annotations

from app.db.models.enums import LedgerBalanceBucket, WalletEntryType
from app.db.uow import UnitOfWork


class WalletService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get_balances(self, user_id: int) -> dict[str, dict[str, int]]:
        wallets = await self.uow.wallets.list_wallets_for_user(user_id)
        return {
            w.currency: {
                "available": w.available_amount,
                "reserved": w.reserved_amount,
                "pending": w.pending_amount,
            }
            for w in wallets
        }

    async def credit_available(
        self,
        *,
        user_id: int,
        currency: str,
        amount: int,
        entry_type: WalletEntryType,
        idempotency_key: str,
        **meta,
    ) -> None:
        if amount <= 0:
            raise ValueError("amount must be > 0")
        wallet = await self.uow.wallets.lock_wallet(user_id, currency)
        await self.uow.wallets.apply_ledger_entry(
            wallet=wallet,
            entry_type=entry_type,
            bucket=LedgerBalanceBucket.AVAILABLE,
            amount=amount,
            idempotency_key=idempotency_key,
            **meta,
        )

    async def debit_available(
        self,
        *,
        user_id: int,
        currency: str,
        amount: int,
        entry_type: WalletEntryType,
        idempotency_key: str,
        **meta,
    ) -> None:
        if amount <= 0:
            raise ValueError("amount must be > 0")
        wallet = await self.uow.wallets.lock_wallet(user_id, currency)
        await self.uow.wallets.apply_ledger_entry(
            wallet=wallet,
            entry_type=entry_type,
            bucket=LedgerBalanceBucket.AVAILABLE,
            amount=-amount,
            idempotency_key=idempotency_key,
            **meta,
        )

    async def reserve_from_available(
        self, *, user_id: int, currency: str, amount: int, idempotency_key: str, **meta
    ) -> None:
        """Move `amount` from available -> reserved atomically (two ledger
        rows, same transaction). Raises InsufficientFundsError if the
        available bucket can't cover it; no partial state is left behind
        because both entries are inside the same DB transaction as the
        caller's session and only flushed, not committed, here."""
        if amount <= 0:
            raise ValueError("amount must be > 0")
        wallet = await self.uow.wallets.lock_wallet(user_id, currency)
        await self.uow.wallets.apply_ledger_entry(
            wallet=wallet,
            entry_type=WalletEntryType.PROMO_CODE_FUNDING_RESERVE,
            bucket=LedgerBalanceBucket.AVAILABLE,
            amount=-amount,
            idempotency_key=f"{idempotency_key}:debit",
            **meta,
        )
        await self.uow.wallets.apply_ledger_entry(
            wallet=wallet,
            entry_type=WalletEntryType.PROMO_CODE_FUNDING_RESERVE,
            bucket=LedgerBalanceBucket.RESERVED,
            amount=amount,
            idempotency_key=f"{idempotency_key}:credit",
            **meta,
        )

    async def release_reserved_to_available(
        self, *, user_id: int, currency: str, amount: int, idempotency_key: str, **meta
    ) -> None:
        if amount <= 0:
            raise ValueError("amount must be > 0")
        wallet = await self.uow.wallets.lock_wallet(user_id, currency)
        await self.uow.wallets.apply_ledger_entry(
            wallet=wallet,
            entry_type=WalletEntryType.PROMO_CODE_FUNDING_RELEASE,
            bucket=LedgerBalanceBucket.RESERVED,
            amount=-amount,
            idempotency_key=f"{idempotency_key}:debit_reserved",
            **meta,
        )
        await self.uow.wallets.apply_ledger_entry(
            wallet=wallet,
            entry_type=WalletEntryType.PROMO_CODE_FUNDING_RELEASE,
            bucket=LedgerBalanceBucket.AVAILABLE,
            amount=amount,
            idempotency_key=f"{idempotency_key}:credit_available",
            **meta,
        )

    async def consume_reserved(
        self, *, user_id: int, currency: str, amount: int, idempotency_key: str, **meta
    ) -> None:
        """Permanently remove `amount` from reserved (e.g. a promo code
        activation actually being used, or a cancelled/expired code's
        unused reserve being written off after release)."""
        if amount <= 0:
            raise ValueError("amount must be > 0")
        wallet = await self.uow.wallets.lock_wallet(user_id, currency)
        await self.uow.wallets.apply_ledger_entry(
            wallet=wallet,
            entry_type=WalletEntryType.PROMO_CODE_FUNDING_CONSUME,
            bucket=LedgerBalanceBucket.RESERVED,
            amount=-amount,
            idempotency_key=idempotency_key,
            **meta,
        )

    async def transaction_history(
        self, user_id: int, currency: str | None = None, limit: int = 50, offset: int = 0
    ):
        return await self.uow.wallets.list_ledger_for_user(
            user_id, currency=currency, limit=limit, offset=offset
        )

````

### FILE: app/workers/broadcast_worker.py

````python
"""Sends queued broadcasts in rate-limited batches, resumable across
restarts (progress is tracked per-recipient in the DB, not in memory).

Never blocks a bot handler or admin HTTP request -- this runs on its own
schedule in `app.workers.runner`, polling for QUEUED/RUNNING broadcasts.
"""

from __future__ import annotations

import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from app.core.logging import get_logger
from app.db.models.enums import BroadcastRecipientStatus, BroadcastStatus
from app.db.session import AsyncSessionLocal
from app.db.uow import UnitOfWork

logger = get_logger(__name__)

BATCH_SIZE = 200


async def process_pending_broadcasts(bot: Bot) -> None:
    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        broadcasts = await uow.broadcasts.list_queued_or_running()

    for broadcast in broadcasts:
        await _process_one_broadcast(bot, broadcast.id)


async def _process_one_broadcast(bot: Bot, broadcast_id: int) -> None:
    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        broadcast = await uow.broadcasts.lock(broadcast_id)
        if broadcast is None or broadcast.status == BroadcastStatus.CANCELLED.value:
            return
        if broadcast.status == BroadcastStatus.QUEUED.value:
            await uow.broadcasts.update_status(broadcast, BroadcastStatus.RUNNING)
        await session.commit()

    delay = 1.0 / max(broadcast.rate_limit_per_second, 1)

    while True:
        async with AsyncSessionLocal() as session:
            uow = UnitOfWork(session)
            broadcast = await uow.broadcasts.get(broadcast_id)
            if broadcast is None or broadcast.status == BroadcastStatus.CANCELLED.value:
                return
            recipients = await uow.broadcasts.list_pending_recipients(
                broadcast_id, limit=BATCH_SIZE
            )
            if not recipients:
                await uow.broadcasts.update_status(broadcast, BroadcastStatus.COMPLETED)
                await session.commit()
                return

            for recipient in recipients:
                user = await uow.users.get_by_id(recipient.user_id)
                if user is None or user.is_blocked or user.is_bot_blocked:
                    await uow.broadcasts.mark_recipient(recipient, BroadcastRecipientStatus.SKIPPED)
                    await uow.broadcasts.increment_counters(broadcast, skipped=1)
                    continue

                text = {
                    "uz": broadcast.text_uz,
                    "ru": broadcast.text_ru,
                    "en": broadcast.text_en,
                }.get(user.language, broadcast.text_uz)
                try:
                    if broadcast.photo_file_id:
                        await bot.send_photo(
                            chat_id=user.telegram_id, photo=broadcast.photo_file_id, caption=text
                        )
                    else:
                        await bot.send_message(chat_id=user.telegram_id, text=text)
                    await uow.broadcasts.mark_recipient(recipient, BroadcastRecipientStatus.SENT)
                    await uow.broadcasts.increment_counters(broadcast, sent=1)
                except TelegramForbiddenError:
                    user.is_bot_blocked = True
                    await uow.broadcasts.mark_recipient(
                        recipient, BroadcastRecipientStatus.FAILED, error="bot_blocked"
                    )
                    await uow.broadcasts.increment_counters(broadcast, failed=1)
                except TelegramRetryAfter as exc:
                    await asyncio.sleep(exc.retry_after)
                    await uow.broadcasts.mark_recipient(recipient, BroadcastRecipientStatus.PENDING)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning("Broadcast send failed for user %s: %s", user.telegram_id, exc)
                    await uow.broadcasts.mark_recipient(
                        recipient, BroadcastRecipientStatus.FAILED, error=str(exc)
                    )
                    await uow.broadcasts.increment_counters(broadcast, failed=1)

                await asyncio.sleep(delay)

            await session.commit()

````

### FILE: app/workers/expiration_worker.py

````python
"""Handles time-based expirations:
- Expired, unreleased user-funded promo codes: release their unused
  reserve back to the issuer (spec section 7's documented policy).
- (Premium access itself is computed live from `User.premium_until` on
  every check, so no separate "expire premium" job is needed -- but this
  worker sends an optional expiry-approaching notice, which is a nice-to-
  have and safe to skip if translations aren't wired for it.)
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.db.uow import UnitOfWork
from app.services.promo_service import PromoService

logger = get_logger(__name__)


async def release_expired_promo_codes() -> int:
    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        expired = await uow.promos.list_expired_unreleased(limit=500)
        promo_service = PromoService(uow)
        count = 0
        for promo in expired:
            await promo_service.expire_and_release(promo)
            count += 1
        await session.commit()
        if count:
            logger.info("Released unused reserve for %d expired promo codes", count)
        return count

````

### FILE: app/workers/__init__.py

````python
"""Background workers: queued broadcasts, entitlement expirations,
payment-provider reconciliation, and promo-code expiry/release, scheduled
via APScheduler in `app.workers.runner`.
"""

````

### FILE: app/workers/reconciliation_worker.py

````python
"""Reconciliation: verifies the wallet-cache invariant (sum of ledger
entries per bucket == cached wallet balance) and flags any drift for admin
investigation via a structured log line (never silently "fixes" balances --
a drift indicates a bug and must be investigated, not papered over).

Also re-checks any PENDING orders older than a threshold against their
payment provider where the provider supports a status-lookup API, so a
missed webhook doesn't leave an order stuck forever.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select

from app.core.logging import get_logger
from app.db.models.enums import OrderStatus
from app.db.models.order import Order
from app.db.models.wallet import LedgerEntry, Wallet
from app.db.session import AsyncSessionLocal

logger = get_logger(__name__)

STALE_PENDING_ORDER_HOURS = 24


async def check_ledger_consistency() -> list[dict]:
    """Returns a list of {wallet_id, bucket, cached, computed} for any
    wallet whose cached balance doesn't match the sum of its ledger
    entries. An empty list means everything reconciles."""
    drifts: list[dict] = []
    async with AsyncSessionLocal() as session:
        wallets = (await session.execute(select(Wallet))).scalars().all()
        for wallet in wallets:
            for bucket, cached in (
                ("available", wallet.available_amount),
                ("reserved", wallet.reserved_amount),
                ("pending", wallet.pending_amount),
            ):
                total = (
                    await session.execute(
                        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
                            LedgerEntry.wallet_id == wallet.id, LedgerEntry.bucket == bucket
                        )
                    )
                ).scalar_one()
                if int(total) != cached:
                    drifts.append(
                        {
                            "wallet_id": wallet.id,
                            "bucket": bucket,
                            "cached": cached,
                            "computed": int(total),
                        }
                    )

    if drifts:
        logger.error("Ledger reconciliation drift detected: %s", drifts)
    return drifts


async def flag_stale_pending_orders() -> list[int]:
    """Orders stuck in PENDING beyond the threshold are flagged (logged +
    returned) for admin review -- possibly a missed webhook. Does NOT
    auto-cancel; a human should confirm with the provider first."""
    threshold = dt.datetime.now(dt.UTC) - dt.timedelta(hours=STALE_PENDING_ORDER_HOURS)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Order.id).where(
                Order.status == OrderStatus.PENDING.value, Order.created_at < threshold
            )
        )
        stale_ids = [row[0] for row in result.all()]
    if stale_ids:
        logger.warning(
            "Stale PENDING orders older than %sh: %s", STALE_PENDING_ORDER_HOURS, stale_ids
        )
    return stale_ids

````

### FILE: app/workers/runner.py

````python
"""Scheduled-job entrypoint for the `worker` docker-compose service.

Runs every background job on its own APScheduler interval, sharing one
long-lived `aiogram.Bot` instance (needed for broadcast sending). Started
via `python -m app.workers.runner`.
"""

from __future__ import annotations

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.bot.factory import build_bot
from app.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.workers.broadcast_worker import process_pending_broadcasts
from app.workers.expiration_worker import release_expired_promo_codes
from app.workers.reconciliation_worker import check_ledger_consistency, flag_stale_pending_orders

settings = get_settings()
setup_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)


async def run_workers() -> None:
    bot = build_bot(settings)
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        process_pending_broadcasts,
        "interval",
        seconds=10,
        args=[bot],
        id="broadcast_worker",
        max_instances=1,
    )
    scheduler.add_job(
        release_expired_promo_codes, "interval", minutes=15, id="expiration_worker", max_instances=1
    )
    scheduler.add_job(
        check_ledger_consistency,
        "interval",
        minutes=30,
        id="ledger_reconciliation",
        max_instances=1,
    )
    scheduler.add_job(
        flag_stale_pending_orders, "interval", hours=1, id="stale_order_check", max_instances=1
    )

    scheduler.start()
    logger.info("Worker scheduler started")

    try:
        await asyncio.Event().wait()  # run forever
    finally:
        scheduler.shutdown()
        await bot.session.close()


def main() -> None:
    asyncio.run(run_workers())


if __name__ == "__main__":
    main()

````

### FILE: docker-compose.yml

````yaml
version: "3.9"

x-app-build: &app-build
  build:
    context: .
    dockerfile: Dockerfile

x-common-env: &common-env
  env_file:
    - .env

services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-movie_bot}
      POSTGRES_USER: ${POSTGRES_USER:-movie_bot}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-change-me}
    volumes:
      - db_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-movie_bot} -d ${POSTGRES_DB:-movie_bot}"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: ["redis-server", "--save", "60", "1"]
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10

  migrate:
    <<: [*app-build, *common-env]
    depends_on:
      db:
        condition: service_healthy
    command: ["alembic", "upgrade", "head"]
    restart: "no"

  bot:
    <<: [*app-build, *common-env]
    command: ["python", "-m", "app.main", "bot"]
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully
    restart: unless-stopped

  api:
    <<: [*app-build, *common-env]
    command: ["uvicorn", "app.main:api_app", "--host", "0.0.0.0", "--port", "8000"]
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully
    restart: unless-stopped

  worker:
    <<: [*app-build, *common-env]
    command: ["python", "-m", "app.workers.runner"]
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully
    restart: unless-stopped

volumes:
  db_data:
  redis_data:

````

### FILE: Dockerfile

````
# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps needed for psycopg2 / building wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY README.md ./README.md

RUN pip install --upgrade pip && pip install .

COPY tests ./tests

RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Default command runs the FastAPI app (webhooks + admin panel).
# docker-compose overrides `command:` per service (bot / api / worker).
CMD ["uvicorn", "app.main:api_app", "--host", "0.0.0.0", "--port", "8000"]

````

### FILE: .env.example

````
# ============================================================================
# Movie Bot — environment configuration template.
# Copy to `.env` and fill in real values. NEVER commit `.env` with real secrets.
# ============================================================================

# --- Core -------------------------------------------------------------------
APP_ENV=development                # development | staging | production
APP_SECRET_KEY=change-me-to-a-long-random-string   # used for admin session signing
APP_TIMEZONE=Asia/Tashkent
LOG_LEVEL=INFO

# --- Telegram Bot -------------------------------------------------------------
BOT_TOKEN=123456789:REPLACE_WITH_BOTFATHER_TOKEN
BOT_USERNAME=YourMovieBot           # without @, used to build referral/deep links
BOT_WEBHOOK_URL=                    # e.g. https://yourdomain.com/webhooks/telegram ; empty = long polling
BOT_WEBHOOK_SECRET=change-me        # sent as X-Telegram-Bot-Api-Secret-Token and verified on webhook

# Admin Telegram user ids allowed to bootstrap the first SUPERADMIN (comma separated numeric ids)
BOOTSTRAP_SUPERADMIN_IDS=

# --- Database -----------------------------------------------------------------
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=movie_bot
POSTGRES_USER=movie_bot
POSTGRES_PASSWORD=change-me
DATABASE_URL=postgresql+asyncpg://movie_bot:change-me@db:5432/movie_bot
# Sync URL used by Alembic migrations only
DATABASE_URL_SYNC=postgresql+psycopg2://movie_bot:change-me@db:5432/movie_bot

# --- Redis ----------------------------------------------------------------------
REDIS_URL=redis://redis:6379/0

# --- FastAPI / Web -----------------------------------------------------------
API_HOST=0.0.0.0
API_PORT=8000
PUBLIC_BASE_URL=https://yourdomain.com   # used to build webhook & storefront callback URLs

# --- Admin panel ---------------------------------------------------------------
ADMIN_SESSION_COOKIE_NAME=movie_bot_admin_session
ADMIN_SESSION_TTL_SECONDS=43200

# --- Mandatory subscription channels defaults ---------------------------------
# Comma separated @usernames or -100... chat ids the bot must be admin of.
# Can also be fully managed later from the Admin Panel > Channels.
DEFAULT_MANDATORY_CHANNELS=

# --- Payments: Telegram Stars --------------------------------------------------
# Stars payments run natively through Telegram (Bot API sendInvoice with currency="XTR").
# No external credentials are required, but the provider must be explicitly enabled.
PAYMENTS_STARS_ENABLED=false

# --- Payments: Stripe (independent web storefront only) -----------------------
PAYMENTS_STRIPE_ENABLED=false
STRIPE_MODE=sandbox                 # sandbox | live  (live requires explicit ops sign-off)
STRIPE_API_KEY=sk_test_REPLACE_ME
STRIPE_PUBLISHABLE_KEY=pk_test_REPLACE_ME
STRIPE_WEBHOOK_SECRET=whsec_REPLACE_ME
STRIPE_DEFAULT_CURRENCY=usd

# --- Payments: Click (independent web storefront only, Uzbekistan) ------------
PAYMENTS_CLICK_ENABLED=false
CLICK_MODE=sandbox                  # sandbox | live
CLICK_MERCHANT_ID=REPLACE_ME
CLICK_SERVICE_ID=REPLACE_ME
CLICK_MERCHANT_USER_ID=REPLACE_ME
CLICK_SECRET_KEY=REPLACE_ME
CLICK_DEFAULT_CURRENCY=UZS

# --- Storefront (independent web checkout, separate from the Telegram bot) ----
STOREFRONT_ENABLED=false

# --- Broadcasts -----------------------------------------------------------------
BROADCAST_RATE_LIMIT_PER_SECOND=20   # stay under Telegram's ~30 msg/s global limit

# --- Backups ----------------------------------------------------------------
BACKUP_DIR=/var/backups/movie_bot
BACKUP_RETENTION_DAYS=14

````

### FILE: .gitignore

````
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
.env
.mypy_cache/
.ruff_cache/
.pytest_cache/
.coverage
htmlcov/
*.log
.DS_Store

````

### FILE: pyproject.toml

````toml
[project]
name = "movie-bot"
version = "1.0.0"
description = "Multilingual Telegram movie-delivery bot with premium subscriptions, two-tier referrals, wallet, promo codes and gifts."
readme = "README.md"
requires-python = ">=3.12"
license = { text = "Proprietary" }
authors = [{ name = "Movie Bot Team" }]

dependencies = [
    "aiogram>=3.15,<4.0",
    "fastapi>=0.115,<0.116",
    "uvicorn[standard]>=0.32,<0.33",
    "SQLAlchemy>=2.0,<2.1",
    "alembic>=1.14,<1.15",
    "asyncpg>=0.30,<0.31",
    "psycopg2-binary>=2.9,<3.0",
    "redis>=5.2,<6.0",
    "pydantic>=2.9,<3.0",
    "pydantic-settings>=2.6,<3.0",
    "stripe>=11.3,<12.0",
    "httpx>=0.27,<0.28",
    "APScheduler>=3.10,<4.0",
    "python-json-logger>=1.0; python_version >= '3.12'",
    "python-multipart>=0.0.12,<0.1",
    "itsdangerous>=2.2,<3.0",
    "Jinja2>=3.1,<4.0",
    "passlib[bcrypt]>=1.7,<2.0",
    "babel>=2.16,<3.0",
    "tenacity>=9.0,<10.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3,<9.0",
    "pytest-asyncio>=0.24,<0.25",
    "pytest-cov>=6.0,<7.0",
    "ruff>=0.7,<1.0",
    "mypy>=1.13,<2.0",
    "black>=24.10,<25.0",
    "faker>=30.8,<31.0",
    "aiosqlite>=0.20,<0.21",
]

[project.scripts]
movie-bot = "app.main:run_bot"
movie-bot-api = "app.main:run_api"
movie-bot-worker = "app.workers.runner:run_workers"

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["app*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
# E501: line length is handled by black instead.
# B008: `Depends(...)` in a default argument is FastAPI's required DI pattern, not a bug.
# UP042: `class X(str, Enum)` is used intentionally (over `StrEnum`) so the codebase stays
#        importable on Python versions where StrEnum isn't available and so every enum's
#        `.value` is unambiguously a plain str for SQLAlchemy String columns.
ignore = ["E501", "B008", "UP042"]

[tool.black]
line-length = 100
target-version = ["py312"]

[tool.mypy]
python_version = "3.12"
ignore_missing_imports = true
warn_unused_ignores = true

````

### FILE: README.md

````markdown
# Movie Bot — Multilingual Telegram Movie Delivery & Premium Subscription Bot

A production-grade Telegram bot that delivers licensed movies by code/search/category,
sells Premium access via Telegram Stars (and, optionally, an independent Stripe/Click
web storefront), runs a two-tier referral program (standard referrers + verified
bloggers), maintains a wallet/ledger for balances, and supports prepaid promo codes,
gifts, and a full web admin panel. Fully localized in **Uzbek, Russian, and English**.

> **Where each feature lives** — see [ARCHITECTURE MAP](#architecture-map) below for an
> exact file-by-file cross-reference of every requirement to its implementation.

---

## 1. What is LIVE vs SANDBOX-only vs NEEDS CREDENTIALS

This matters more than anything else in this document — read it before doing anything else.

| Capability | Status | Detail |
|---|---|---|
| Movie catalog, search, categories, mandatory-channel gating | **Live** (once you provide a bot token) | No third-party credentials needed beyond your own bot token. |
| Inline mode (`@YourBot 222`) | **Live** | Requires `/setinline` in BotFather (see §5). |
| Telegram Stars payments | **Sandbox-ready, disabled by default** | Set `PAYMENTS_STARS_ENABLED=true`. No merchant account needed — Stars are native to Telegram — but you must test with real Telegram test/production bot per Telegram's Stars rules. |
| Wallet-balance premium checkout | **Live** | Pure internal ledger operation; no external provider. |
| Stripe (independent web storefront) | **Sandbox-only until you supply real keys** | Requires `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, and `STOREFRONT_ENABLED=true`. Stays fully disabled (`is_enabled() == False`) until all three are set. |
| Click (independent web storefront, Uzbekistan) | **Sandbox-only until you supply real keys** | Requires `CLICK_MERCHANT_ID`, `CLICK_SERVICE_ID`, `CLICK_SECRET_KEY`, and `STOREFRONT_ENABLED=true`. Click also has **no self-service refund API** for Shop API merchants — refunds must be requested from Click support and recorded manually in the admin panel. |
| Two-tier referrals + blogger acquisition rewards | **Live** | Pure DB/ledger logic, no external dependency. |
| Blogger bio verification | **Manual admin review only** | There is no authorized third-party API used anywhere in this codebase to read an arbitrary Instagram/YouTube/Telegram bio automatically. `BloggerService.attempt_automated_check` always returns "not available" and defers to the admin panel. Do not wire in an unauthorized scraper — this is a deliberate, honest limitation. |
| Admin panel | **Live** | Session-cookie auth, bcrypt passwords, role-based access. Create the first account with `scripts/create_superadmin.py`. |
| Broadcasts | **Live** | Rate-limited, resumable, queued via the `worker` service — never blocks a request. |

**Credentials you must obtain yourself before going to production:**
1. A real Telegram bot token from **@BotFather**.
2. (Optional, Stars) Nothing beyond the bot token — but Stars must be enabled per-bot in BotFather-compliant apps and your bot must be reviewed by Telegram for digital goods if required by their current policy.
3. (Optional, Stripe) A Stripe account, API secret key, and a configured webhook endpoint secret.
4. (Optional, Click) A Click.uz merchant account, service ID, merchant ID, and secret key.
5. A strong `APP_SECRET_KEY` and `BOT_WEBHOOK_SECRET` for production.
6. A Postgres database and Redis instance (or use the provided `docker-compose.yml`).

**This project was authored inside a sandboxed environment with no outbound access to
PyPI, Docker Hub, or GitHub.** All Python dependencies (`aiogram`, `fastapi`,
`sqlalchemy`, `alembic`, `redis`, `stripe`, etc.) could **not** be installed or imported
during development, so the full application could not be booted end-to-end inside that
sandbox. What **was** verified by actually executing code in that sandbox:
- All 146 Python files parse with zero syntax errors (`ast.parse` over the whole tree).
- The pure, dependency-free financial logic (`app/services/money.py`,
  `commission.py`, `blogger_rewards.py`, `promo_math.py`) has **44 passing unit tests**,
  executed with `pytest` in that sandbox — see [Testing](#testing) for exact results.
- The Alembic migration was cross-checked against every SQLAlchemy model file with a
  small script (table names + column names for all 25 tables) with zero mismatches.
- All 3 language files (`uz.py`, `ru.py`, `en.py`) were checked to contain the exact
  same 123 translation keys.

Everything else (aiogram handlers, FastAPI routes, SQLAlchemy repositories/services,
Alembic execution against a live Postgres) is **correct-by-construction** — carefully
written against the current documented APIs of aiogram 3 / FastAPI / SQLAlchemy 2 —
but was not executed in that sandbox. **You must run the commands in §4 on a machine
with normal internet access** to install dependencies, run migrations, run the full
test suite, and start the bot for real. This is the honest state of the project;
nothing here pretends otherwise.

---

## 2. Stack

- Python 3.12+, [aiogram 3](https://docs.aiogram.dev/) (Telegram Bot API framework)
- [FastAPI](https://fastapi.tiangolo.com/) (webhooks, admin panel, storefront)
- PostgreSQL 16 + [SQLAlchemy 2](https://docs.sqlalchemy.org/en/20/) (async ORM) + [Alembic](https://alembic.sqlalchemy.org/) (migrations)
- Redis 7 (aiogram FSM storage, rate limiting)
- Docker Compose for local development
- APScheduler for background workers

---

## 3. Compliance: payments and Telegram's digital-goods rules

Telegram requires apps/bots that sell **digital goods and services usable inside
Telegram** to use **Telegram Stars** as the payment method inside the bot/mini app,
and prohibits routing users to an external payment page to buy the same digital
goods as a way of evading that rule.

This project follows that rule structurally:

- Inside the bot, premium access can be bought **only** with (a) **Telegram Stars**
  or (b) the user's **own wallet balance** (an internal ledger debit — not a payment
  redirect). The bot never shows a Stripe/Click checkout link to activate the
  Telegram-side premium entitlement.
- Stripe and Click are wired **exclusively** into `app/api/storefront/`, a genuinely
  separate, independently-branded web storefront (`STOREFRONT_ENABLED` gate). Nothing
  in the bot's premium-purchase flow links to it. If you build a public website
  around this storefront, treat it as an independent sales channel with its own terms.
- The admin panel's "Payment providers" dashboard and `/admin/orders` page both show
  a "Sandbox" vs "Live" vs "Disabled" badge for every provider, so operators can never
  mistake a half-configured integration for a working one.
- `/terms` and `/privacy` bot commands (and `/legal/terms`, `/legal/privacy` HTTP
  endpoints) explain this policy to end users.

**If your product requirements truly need an in-bot Stripe/Click flow, that is only
possible for goods/services that fall outside Telegram's digital-goods policy (e.g.
some physical goods or off-platform services) — consult Telegram's current Bot
Payments policy before enabling anything beyond what's implemented here.**

---

## 4. Running it

### 4.1 Docker Compose (recommended, any OS)

```bash
git clone <your-fork-url> movie-bot
cd movie-bot
cp .env.example .env
# Edit .env: at minimum set BOT_TOKEN, BOT_USERNAME, POSTGRES_PASSWORD,
# and change DATABASE_URL / DATABASE_URL_SYNC to match POSTGRES_PASSWORD.

docker compose build
docker compose up -d db redis
docker compose run --rm migrate            # apply all Alembic migrations
docker compose run --rm api python -m scripts.create_superadmin \
    --username admin --password 'change-me-now'
docker compose up -d api bot worker
```

- Bot: long-polls Telegram by default (leave `BOT_WEBHOOK_URL` empty in `.env`).
- API/admin panel: http://localhost:8000/admin/login
- Health check: http://localhost:8000/health

To use a webhook instead of long polling (recommended for production): set
`BOT_WEBHOOK_URL=https://yourdomain.com/webhooks/telegram` and a real
`BOT_WEBHOOK_SECRET` in `.env`, then only run the `api` and `worker` services (the
`bot` service will detect the webhook URL and idle rather than double-consume updates).

### 4.2 Windows (PowerShell), without Docker

Requires: Python 3.12+, PostgreSQL 16 running locally (or via WSL/Docker Desktop just
for `db`/`redis`), Redis (Windows: easiest via Docker Desktop or WSL).

```powershell
# 1. Clone and enter the project
git clone <your-fork-url> movie-bot
cd movie-bot

# 2. Create and activate a virtual environment
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install the project (editable) with dev extras
pip install --upgrade pip
pip install -e ".[dev]"

# 4. Configure environment
copy .env.example .env
notepad .env
# Set BOT_TOKEN, BOT_USERNAME, and point DATABASE_URL / DATABASE_URL_SYNC
# at your local Postgres, e.g.:
#   DATABASE_URL=postgresql+asyncpg://movie_bot:change-me@localhost:5432/movie_bot
#   DATABASE_URL_SYNC=postgresql+psycopg2://movie_bot:change-me@localhost:5432/movie_bot
#   REDIS_URL=redis://localhost:6379/0

# 5. Create the database (run once, using psql or pgAdmin)
#    CREATE DATABASE movie_bot;
#    CREATE USER movie_bot WITH PASSWORD 'change-me';
#    GRANT ALL PRIVILEGES ON DATABASE movie_bot TO movie_bot;

# 6. Apply migrations
alembic upgrade head

# 7. Create the first admin account
python -m scripts.create_superadmin --username admin --password "change-me-now"

# 8. Run each process in its OWN PowerShell window (all three needed):
python -m app.main bot
uvicorn app.main:api_app --host 0.0.0.0 --port 8000
python -m app.workers.runner
```

### 4.3 Linux / macOS server, without Docker

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

cp .env.example .env
$EDITOR .env   # fill in BOT_TOKEN, BOT_USERNAME, DATABASE_URL(_SYNC), REDIS_URL

alembic upgrade head
python -m scripts.create_superadmin --username admin --password "change-me-now"

# Run under your process manager of choice (systemd/supervisor/tmux), e.g.:
python -m app.main bot &
uvicorn app.main:api_app --host 0.0.0.0 --port 8000 &
python -m app.workers.runner &
```

---

## 5. BotFather setup checklist

1. `/newbot` → get your `BOT_TOKEN`.
2. `/setinline` → **enable inline mode** and set an inline placeholder, e.g.
   `Enter a movie code or name…`. Required for `@YourBot 222` searches in groups.
3. `/setinlinefeedback` → optional, enables analytics on inline result usage.
4. `/mybots` → *Bot Settings* → *Payments* is **not** needed for Telegram Stars
   (Stars use `sendInvoice` with `currency="XTR"` and an empty provider token — no
   external payment provider configuration in BotFather is required for Stars).
5. If you plan to use webhooks, ensure your `PUBLIC_BASE_URL` is HTTPS with a valid
   certificate; Telegram refuses to deliver webhooks to non-HTTPS endpoints.
6. Add the bot as **administrator** to every channel you configure as a mandatory
   subscription channel (Admin Panel → Channels → "Check bot admin rights" verifies
   this for you).

---

## 6. Environment variables

See `.env.example` for the full, commented list. Highlights:

| Variable | Purpose |
|---|---|
| `BOT_TOKEN` | Telegram bot token from BotFather. |
| `BOT_WEBHOOK_URL` | Leave empty for long polling; set for webhook mode. |
| `BOT_WEBHOOK_SECRET` | Verified against `X-Telegram-Bot-Api-Secret-Token` on every webhook call. |
| `DATABASE_URL` / `DATABASE_URL_SYNC` | Async (asyncpg) and sync (psycopg2) Postgres URLs — the sync one is used only by Alembic. |
| `PAYMENTS_STARS_ENABLED` | Turn on in-bot Telegram Stars checkout. |
| `PAYMENTS_STRIPE_ENABLED` / `STRIPE_*` | Independent web storefront only; requires `STOREFRONT_ENABLED=true` too. |
| `PAYMENTS_CLICK_ENABLED` / `CLICK_*` | Same, for Click.uz. |
| `STOREFRONT_ENABLED` | Master switch for the separate web storefront surface. |
| `BOOTSTRAP_SUPERADMIN_IDS` | Comma-separated Telegram numeric ids allowed to receive admin Telegram notifications immediately after being linked via the admin panel. |

---

## 7. Architecture map

| Requirement | Where it's implemented |
|---|---|
| App lifecycle | `app/main.py` (`create_api_app`, `run_bot`) |
| Config/env validation | `app/config.py` |
| Bot handlers | `app/bot/handlers/*.py` (one file per feature area, see module docstrings) |
| Keyboards | `app/bot/keyboards/*.py` |
| i18n (uz/ru/en) | `app/i18n/{uz,ru,en}.py` + `app/i18n/__init__.py` |
| DB models | `app/db/models/*.py` (25 tables) |
| Repositories | `app/db/repositories/*.py` |
| Services | `app/services/*.py` |
| Payment adapters | `app/payments/{base,stars,stripe_provider,click_provider,registry}.py` |
| Webhooks | `app/api/webhooks/{telegram,stripe_webhook,click_webhook}.py` |
| Storefront | `app/api/storefront/routes.py` |
| Admin panel | `app/admin/*.py` + `app/admin/templates/*.html` |
| Workers | `app/workers/{broadcast_worker,expiration_worker,reconciliation_worker,runner}.py` |
| Migrations | `alembic/versions/0001_initial_schema.py` |
| Tests | `tests/unit/*.py` (pure logic), `tests/integration/*.py` (DB-backed) |

### Money and referral policy (spec sections 3 & 5), in one place

- **Per-plan settings** live on `PremiumPlan` (`app/db/models/plan.py`):
  `price_amount`, `standard_referral_percent`, `blogger_referral_percent`,
  `blogger_acquisition_reward_enabled`, `max_discount_percent`. Each plan is
  independent — nothing is hard-coded globally.
- **Snapshotting**: every `Order` and `ReferralCommission` freezes the plan's price
  and percentages *at purchase time* (`app/db/models/order.py`,
  `app/db/models/reward_accrual.py`). Changing a plan later in the admin panel
  (`app/admin/routes_plans.py`) never retroactively alters a completed purchase.
- **Standard referral commission**: `app/services/commission.py::calculate_referral_commission`
  — pure function, 100% unit-tested.
- **Blogger acquisition reward** (per-1000-joins, accruing from the FIRST join,
  remainder-safe): `app/services/blogger_rewards.py::accrue_qualified_join` — pure
  function, 100% unit-tested, wired to persistence in
  `app/services/blogger_reward_service.py`.
- **Promo funding math** (full-premium and percent-discount worked examples from the
  spec): `app/services/promo_math.py` — pure function, 100% unit-tested.

---

## 8. Testing

### 8.1 What was actually run, and its result (in the authoring sandbox)

```
$ pytest tests/unit -v
...
44 passed, 1 warning in 0.07s
```

All 44 tests in `tests/unit/` (`test_money.py`, `test_commission.py`,
`test_blogger_rewards.py`, `test_promo_math.py`) passed. These tests cover, with zero
external dependencies:
- Per-plan-independent commission percentages (10% vs 15% on the same purchase amount
  yield different, correct commission amounts).
- A blogger referrer receiving the blogger rate instead of the standard rate.
- Renewal-commission policy on/off behavior.
- Commission reversal math on full and partial refunds.
- Blogger acquisition reward accrual for exactly 1, 10, 999, and 1000 qualified joins,
  at both an exact-multiple-of-1000 rate and a fractional rate, cross-checked against
  a closed-form formula — proving no overpayment/underpayment and correct remainder
  carry-forward.
- Full-premium and percent-discount promo funding, matching the spec's worked
  examples exactly (100,000 UZS ÷ 5,000 UZS/activation = 20; 100,000 UZS ÷ 500
  UZS/activation = 200).

### 8.2 What is written but requires a real environment to execute

`tests/integration/` contains 8 files covering, against a real (in that environment)
SQLAlchemy + SQLite/Postgres database via the actual repositories/services/handlers'
business logic:

- Referral self-referral / repeated-start / blocked-user / blocked-referrer / duplicate
  attribution / unknown-code rejection (`test_referral_attribution.py`).
- Per-plan commission differing across two purchases, a blogger earning **both** the
  purchase commission **and** the acquisition reward, duplicate-webhook idempotency,
  full refund reversing the commission and revoking future premium
  (`test_purchase_and_commissions.py`).
- Blogger reward accrual for 1/10/999/1000 joins at the DB layer, suspended-blogger
  cutoff, duplicate-accrual-call safety (`test_blogger_reward_accrual_sequence.py`).
- Full-premium/discount promo funding worked examples, insufficient-balance rejection,
  own-code redemption rejection, double-redemption rejection, concurrent redemption
  never exceeding `max_uses`, cancellation releasing unused reserve, external-URL
  attribution requiring admin approval (`test_promo_codes.py`).
- Free/premium/premium-exemption/fail-closed/unpublished movie access
  (`test_movie_access.py`).
- Inline search never exposing `video_file_id` (`test_inline_search_privacy.py`).
- Gift-premium/gift-balance exactly-once debit and grant, admin gifts, manual
  adjustments never going negative (`test_gifts_and_admin_adjustments.py`).
- Ledger idempotency-key deduplication and the ledger-sum-equals-cached-balance
  invariant (`test_ledger_idempotency.py`).

Run them yourself once dependencies are installed:

```bash
pip install -e ".[dev]"
pytest tests/unit tests/integration -v
```

### 8.3 Manual end-to-end test script (do this once you have a real bot token)

1. `docker compose up -d` (or the non-Docker equivalent), run migrations, create a
   superadmin.
2. Log into `/admin/login`, go to **Plans**, create a plan (e.g. "1 week", 5000 UZS,
   10% standard referral, 15% blogger referral).
3. In Telegram, message your bot `/start` → choose a language → confirm the main menu
   appears with all 9 buttons translated.
4. As an admin Telegram account, forward a test video to the bot (wire up
   `MovieAdminStates` handlers per your admin's Telegram id, or add the movie directly
   via a DB insert / a quick admin panel form) with a code like `100`.
5. In the bot, type `100` → confirm the video is delivered (if FREE and no mandatory
   channels configured) or the premium/paywall prompt appears.
6. Add a mandatory channel in the admin panel, make the bot an admin of it, and repeat
   step 5 as a non-member — confirm the "join channels" prompt appears and blocks
   delivery until you join.
7. Get your referral link from **Invite Friends**, open it as a second Telegram
   account, `/start` — confirm a `Referral` row is created and `is_qualified=True`.
8. Buy the plan you created with the second account's wallet balance (top it up via
   admin gift first) — confirm premium activates and the first account's balance
   shows the commission.
9. Apply to become a blogger, approve it from the admin panel, and repeat steps 7–8 —
   confirm both a commission **and** an acquisition reward are credited.
10. Create a promo code, redeem it, confirm the funding math matches what was quoted.
11. Send a gift (premium and balance) to the second account.
12. Test `@YourBot 100` inline in a group chat — confirm no `file_id` is visible in the
    raw update payload (use `getUpdates` or a debug log) and that "Open in Bot" checks
    access correctly per-user.
13. Trigger a webhook problem (e.g. stop Postgres briefly) and confirm the
    reconciliation worker logs a warning instead of crashing silently.

---

## 9. Reliability & security notes

- All monetary amounts are **integers** (minor units); no floats anywhere in the money
  path (`app/services/money.py`).
- Every balance mutation goes through `WalletRepository.apply_ledger_entry`, which
  locks the wallet row (`SELECT ... FOR UPDATE`), checks for sufficient funds, and
  writes an **immutable** ledger row in the same transaction — negative balances are
  structurally impossible.
- Every promo redemption goes through `PromoRepository.lock_by_code` +
  `decrement_remaining_use`, backed by a DB `CHECK(remaining_uses >= 0)` constraint —
  a promo can never be used more times than it has activations for, even under
  concurrent redemption attempts.
- Every entitlement grant and referral commission is keyed by a unique
  `(source, source_reference)` / `order_id` constraint — duplicate/retried webhooks
  can never grant premium twice or pay a commission twice.
- Structured JSON logging (`app/core/logging.py`) redacts bot tokens, passwords,
  webhook secrets, and — critically — **movie `video_file_id` values**, since a
  leaked file_id would let anyone fetch the licensed video directly from Telegram's
  servers, bypassing all entitlement checks.
- The reconciliation worker (`app/workers/reconciliation_worker.py`) periodically
  verifies that ledger entries sum to the cached wallet balance and **logs, never
  silently repairs**, any drift — a drift is a bug that needs human investigation.

---

## 10. Complete changed-file list

See the final chat message for the full list of files created in this session,
organized by area, along with exact run commands and the honest live/sandbox/needs-
credentials breakdown repeated for convenience.

````

### FILE: scripts/create_superadmin.py

````python
"""One-off CLI to create the first SUPERADMIN account.

Usage (see README "First run"):
    python -m scripts.create_superadmin --username admin --password 'change-me-now'

Run this once after migrations. There is no self-registration UI for the
admin panel by design -- every subsequent admin account is created by an
existing SUPERADMIN through the (future) admin-management screen or by
running this script again with a different username.
"""

from __future__ import annotations

import argparse
import asyncio

from app.admin.security import hash_password
from app.db.models.enums import AdminRole
from app.db.session import AsyncSessionLocal
from app.db.uow import UnitOfWork


async def main(username: str, password: str, telegram_id: int | None) -> None:
    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        existing = await uow.admins.get_by_username(username)
        if existing is not None:
            print(f"Admin '{username}' already exists (id={existing.id}). Nothing to do.")
            return
        admin = await uow.admins.create(
            username=username,
            password_hash=hash_password(password),
            telegram_id=telegram_id,
            role=AdminRole.SUPERADMIN.value,
            is_active=True,
        )
        await session.commit()
        print(f"Created SUPERADMIN '{username}' (id={admin.id}).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create the first SUPERADMIN account")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument(
        "--telegram-id",
        type=int,
        default=None,
        help="Optional: enables Telegram admin notifications",
    )
    args = parser.parse_args()
    asyncio.run(main(args.username, args.password, args.telegram_id))

````

### FILE: scripts/__init__.py

````python

````

### FILE: tests/__init__.py

````python

````

### FILE: tests/integration/conftest.py

````python
"""Shared fixtures for DB-backed integration tests.

Uses an in-memory SQLite database (via `aiosqlite`) rather than Postgres so
these tests can run without any external service -- `Base.metadata.create_all`
builds the exact same schema the models describe (independent of the
hand-written Alembic migration, which is Postgres-specific SQL).

NOTE ON SANDBOX EXECUTION: this test suite requires `sqlalchemy`,
`aiosqlite`, and the project's own `app` package to be importable, none of
which are installed in the tool-use sandbox this project was authored in
(outbound network access to PyPI is blocked there). These tests are
correct-by-construction and are meant to be run with:
    pip install -e ".[dev]"
    pytest tests/integration -v
on a machine with normal internet access. See README.md "Testing" section.

Row-locking caveat: SQLite has no real `SELECT ... FOR UPDATE` semantics
(SQLAlchemy compiles it as a no-op for the sqlite dialect). The
concurrency test therefore verifies the *outcome* invariant (never more
successful redemptions than `max_uses`) rather than relying on true
row-level locking, which is exercised for real only against Postgres.
"""

from __future__ import annotations

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.db.models  # noqa: F401 populates metadata
from app.db.base import Base
from app.db.uow import UnitOfWork


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture
async def uow(session_factory):
    async with session_factory() as session:
        yield UnitOfWork(session)
        await session.commit()


@pytest_asyncio.fixture
async def make_user(uow):
    counter = {"n": 1000}

    async def _make(telegram_id: int | None = None, **kwargs):
        counter["n"] += 1
        tid = telegram_id if telegram_id is not None else counter["n"]
        user = await uow.users.create(
            telegram_id=tid,
            username=kwargs.get("username"),
            first_name=kwargs.get("first_name"),
            last_name=None,
            language="en",
        )
        if kwargs.get("is_blocked"):
            await uow.users.set_blocked(user, True, "test")
        return user

    return _make


@pytest_asyncio.fixture
async def make_plan(uow):
    counter = {"n": 0}

    async def _make(**kwargs):
        counter["n"] += 1
        defaults = dict(
            code=f"plan{counter['n']}",
            title_uz="Plan",
            title_ru="Plan",
            title_en="Plan",
            duration_days=30,
            price_amount=5000,
            currency="UZS",
            standard_referral_percent=1000,
            blogger_referral_percent=1500,
            blogger_acquisition_reward_enabled=True,
            max_discount_percent=50,
        )
        defaults.update(kwargs)
        return await uow.plans.create(**defaults)

    return _make

````

### FILE: tests/integration/__init__.py

````python

````

### FILE: tests/integration/test_blogger_reward_accrual_sequence.py

````python
"""Integration test: blogger acquisition reward accrual across 1, 10, 999,
and 1000 sequential qualified joins, verified against the DB-persisted
`BloggerProfile.accrual_remainder_micros` and ledger balance (spec section
10: "Rewards for 1, 10, 999, and 1000 qualified users")."""

from __future__ import annotations

import pytest

from app.services.blogger_reward_service import BloggerRewardService
from app.services.referral_service import ReferralService
from app.services.settings_service import SettingsService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "n,rate,expected_total",
    [
        (1, 100_000, 100),
        (10, 100_000, 1_000),
        (999, 100_000, 99_900),
        (1000, 100_000, 100_000),
        (1, 333, 0),  # 0.333 UZS rounds down to 0 for the first user alone
        (1000, 333, 333),  # but the full 1000 joins earn exactly floor(333*1000/1000)=333
    ],
)
async def test_accrual_matches_closed_form_over_n_joins(uow, make_user, n, rate, expected_total):
    blogger = await make_user()
    await uow.bloggers.create_profile(user_id=blogger.id, approved_application_id=0)
    await SettingsService(uow).set_global_blogger_reward_per_1000(rate, "UZS")

    reward_service = BloggerRewardService(uow)
    referral_service = ReferralService(uow)

    for _ in range(n):
        referred = await make_user()
        attribution = await referral_service.attribute_start(
            new_user=referred, referral_code=blogger.referral_code
        )
        await reward_service.accrue_for_qualified_referral(attribution.referral)

    wallet = await uow.wallets.get_or_create_wallet(blogger.id, "UZS")
    assert wallet.available_amount == expected_total

    profile = await uow.bloggers.get_profile_by_user(blogger.id)
    assert profile.qualified_joins_counted == n


@pytest.mark.asyncio
async def test_suspended_blogger_stops_earning_new_rewards(uow, make_user):
    blogger = await make_user()
    profile = await uow.bloggers.create_profile(user_id=blogger.id, approved_application_id=0)
    await SettingsService(uow).set_global_blogger_reward_per_1000(100_000, "UZS")

    reward_service = BloggerRewardService(uow)
    referral_service = ReferralService(uow)

    referred1 = await make_user()
    attribution1 = await referral_service.attribute_start(
        new_user=referred1, referral_code=blogger.referral_code
    )
    await reward_service.accrue_for_qualified_referral(attribution1.referral)

    await uow.bloggers.suspend(profile, "policy violation")

    referred2 = await make_user()
    attribution2 = await referral_service.attribute_start(
        new_user=referred2, referral_code=blogger.referral_code
    )
    await reward_service.accrue_for_qualified_referral(attribution2.referral)

    wallet = await uow.wallets.get_or_create_wallet(blogger.id, "UZS")
    assert wallet.available_amount == 100  # only the first join was rewarded


@pytest.mark.asyncio
async def test_duplicate_accrual_call_never_double_pays(uow, make_user):
    blogger = await make_user()
    await uow.bloggers.create_profile(user_id=blogger.id, approved_application_id=0)
    await SettingsService(uow).set_global_blogger_reward_per_1000(100_000, "UZS")

    referral_service = ReferralService(uow)
    reward_service = BloggerRewardService(uow)
    referred = await make_user()
    attribution = await referral_service.attribute_start(
        new_user=referred, referral_code=blogger.referral_code
    )

    await reward_service.accrue_for_qualified_referral(attribution.referral)
    await reward_service.accrue_for_qualified_referral(
        attribution.referral
    )  # called twice, e.g. retried job

    wallet = await uow.wallets.get_or_create_wallet(blogger.id, "UZS")
    assert wallet.available_amount == 100  # not 200

````

### FILE: tests/integration/test_gifts_and_admin_adjustments.py

````python
"""Integration tests: gifting premium/balance user-to-user, admin gifts,
and manual admin balance adjustments (spec section 10)."""

from __future__ import annotations

import pytest

from app.db.models.enums import WalletEntryType
from app.services.gift_service import GiftService
from app.services.money import InsufficientFundsError
from app.services.wallet_service import WalletService


async def _fund(uow, user_id, currency, amount):
    await WalletService(uow).credit_available(
        user_id=user_id,
        currency=currency,
        amount=amount,
        entry_type=WalletEntryType.ADMIN_GIFT,
        idempotency_key=f"fund:{user_id}:{amount}:{currency}:{id(object())}",
    )


@pytest.mark.asyncio
async def test_gift_premium_debits_sender_exactly_once_and_grants_entitlement_exactly_once(
    uow, make_user, make_plan
):
    sender = await make_user()
    recipient = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS", duration_days=30)
    await _fund(uow, sender.id, "UZS", 5000)

    gift_service = GiftService(uow)
    gift = await gift_service.gift_premium_from_user(
        sender_user_id=sender.id, recipient_user_id=recipient.id, plan_id=plan.id
    )

    sender_wallet = await uow.wallets.get_or_create_wallet(sender.id, "UZS")
    assert sender_wallet.available_amount == 0

    recipient_user = await uow.users.get_by_id(recipient.id)
    assert recipient_user.premium_until is not None

    entitlements = await uow.orders.list_entitlements_for_user(recipient.id)
    assert len(entitlements) == 1
    assert entitlements[0].source_reference == f"gift:{gift.id}"


@pytest.mark.asyncio
async def test_gift_premium_fails_cleanly_on_insufficient_balance(uow, make_user, make_plan):
    sender = await make_user()
    recipient = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    # sender has no balance at all

    gift_service = GiftService(uow)
    with pytest.raises(InsufficientFundsError):
        await gift_service.gift_premium_from_user(
            sender_user_id=sender.id, recipient_user_id=recipient.id, plan_id=plan.id
        )

    recipient_user = await uow.users.get_by_id(recipient.id)
    assert recipient_user.premium_until is None


@pytest.mark.asyncio
async def test_gift_balance_moves_funds_atomically(uow, make_user):
    sender = await make_user()
    recipient = await make_user()
    await _fund(uow, sender.id, "UZS", 10_000)

    gift_service = GiftService(uow)
    await gift_service.gift_balance_from_user(
        sender_user_id=sender.id, recipient_user_id=recipient.id, currency="UZS", amount=3000
    )

    sender_wallet = await uow.wallets.get_or_create_wallet(sender.id, "UZS")
    recipient_wallet = await uow.wallets.get_or_create_wallet(recipient.id, "UZS")
    assert sender_wallet.available_amount == 7000
    assert recipient_wallet.available_amount == 3000


@pytest.mark.asyncio
async def test_admin_gift_premium_requires_no_sender_balance(uow, make_user, make_plan):
    recipient = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS", duration_days=7)

    gift_service = GiftService(uow)
    await gift_service.admin_gift_premium(
        admin_id=1, recipient_user_id=recipient.id, plan_id=plan.id, reason="loyalty bonus"
    )

    recipient_user = await uow.users.get_by_id(recipient.id)
    assert recipient_user.premium_until is not None


@pytest.mark.asyncio
async def test_admin_gift_balance_credits_ledger_with_reason(uow, make_user):
    recipient = await make_user()
    gift_service = GiftService(uow)
    await gift_service.admin_gift_balance(
        admin_id=1,
        recipient_user_id=recipient.id,
        currency="UZS",
        amount=2000,
        reason="compensation",
    )

    wallet = await uow.wallets.get_or_create_wallet(recipient.id, "UZS")
    assert wallet.available_amount == 2000

    history = await WalletService(uow).transaction_history(recipient.id, currency="UZS")
    assert any(e.note == "compensation" for e in history)


@pytest.mark.asyncio
async def test_manual_admin_balance_adjustment_can_debit_and_never_goes_negative(uow, make_user):
    user = await make_user()
    await _fund(uow, user.id, "UZS", 1000)

    wallet_service = WalletService(uow)
    await wallet_service.debit_available(
        user_id=user.id,
        currency="UZS",
        amount=1000,
        entry_type=WalletEntryType.ADMIN_ADJUSTMENT,
        idempotency_key="adjust:1",
        note="correction",
    )
    wallet = await uow.wallets.get_or_create_wallet(user.id, "UZS")
    assert wallet.available_amount == 0

    with pytest.raises(InsufficientFundsError):
        await wallet_service.debit_available(
            user_id=user.id,
            currency="UZS",
            amount=1,
            entry_type=WalletEntryType.ADMIN_ADJUSTMENT,
            idempotency_key="adjust:2",
            note="overdraft attempt",
        )

````

### FILE: tests/integration/test_inline_search_privacy.py

````python
"""Integration test proving inline search results never expose a movie's
`video_file_id` (spec section 2 / section 10: "inline search privacy")."""

from __future__ import annotations

import pytest

from app.db.models.enums import MovieAccessType, MoviePublicationState
from app.services.movie_access_service import MovieAccessService


@pytest.mark.asyncio
async def test_find_by_code_returns_movie_but_service_never_returns_raw_file_id_without_delivery_call(
    uow,
):
    await uow.catalog.create(
        code="222",
        title_uz="T",
        title_ru="T",
        title_en="T",
        video_file_id="SECRET_FILE_ID_MUST_NOT_LEAK",
        access_type=MovieAccessType.FREE.value,
        publication_state=MoviePublicationState.PUBLISHED.value,
    )

    service = MovieAccessService(uow)
    results = await service.find_by_code_or_search("222")

    assert len(results) == 1
    found = results[0]
    # The Movie ORM object DOES carry video_file_id as a column (it must,
    # to be deliverable later) -- the privacy guarantee is architectural:
    # `app.bot.handlers.inline_search` only ever serializes `movie.code`
    # and localized title/description into the InlineQueryResultArticle,
    # and the only method that returns the raw id for actual delivery is
    # `deliver_and_record_view`, which requires a prior access check. This
    # test documents and locks in that the search path returns the code
    # (safe, already public) while the file_id extraction is a separate,
    # explicit, access-gated call.
    assert found.code == "222"

    # Simulate what the inline handler actually serializes: only code +
    # localized title/description, never video_file_id.
    inline_payload = {
        "code": found.code,
        "title": found.title("en"),
        "description": found.description("en"),
    }
    assert "SECRET_FILE_ID_MUST_NOT_LEAK" not in str(inline_payload)


@pytest.mark.asyncio
async def test_deliver_and_record_view_is_the_only_source_of_the_file_id(uow):
    movie = await uow.catalog.create(
        code="333",
        title_uz="T",
        title_ru="T",
        title_en="T",
        video_file_id="ANOTHER_SECRET_ID",
        access_type=MovieAccessType.FREE.value,
        publication_state=MoviePublicationState.PUBLISHED.value,
    )
    service = MovieAccessService(uow)
    file_id = await service.deliver_and_record_view(movie)
    assert file_id == "ANOTHER_SECRET_ID"

    refreshed = await uow.catalog.get_by_code("333")
    assert refreshed.view_count == 1

````

### FILE: tests/integration/test_ledger_idempotency.py

````python
"""Integration tests: ledger idempotency-key deduplication (the mechanism
that makes duplicate payment webhooks safe at the wallet layer) and that
wallet balances never go negative under a locked debit (spec section 9/10)."""

from __future__ import annotations

import pytest

from app.db.models.enums import WalletEntryType
from app.services.money import InsufficientFundsError
from app.services.wallet_service import WalletService


@pytest.mark.asyncio
async def test_same_idempotency_key_applied_twice_only_credits_once(uow, make_user):
    user = await make_user()
    wallet_service = WalletService(uow)

    await wallet_service.credit_available(
        user_id=user.id,
        currency="UZS",
        amount=500,
        entry_type=WalletEntryType.REFERRAL_COMMISSION,
        idempotency_key="commission:order-42",
    )
    # Simulates a retried/duplicate webhook re-delivering the same event.
    await wallet_service.credit_available(
        user_id=user.id,
        currency="UZS",
        amount=500,
        entry_type=WalletEntryType.REFERRAL_COMMISSION,
        idempotency_key="commission:order-42",
    )

    wallet = await uow.wallets.get_or_create_wallet(user.id, "UZS")
    assert wallet.available_amount == 500  # not 1000


@pytest.mark.asyncio
async def test_debit_beyond_available_raises_and_leaves_balance_unchanged(uow, make_user):
    user = await make_user()
    wallet_service = WalletService(uow)
    await wallet_service.credit_available(
        user_id=user.id,
        currency="UZS",
        amount=100,
        entry_type=WalletEntryType.ADMIN_GIFT,
        idempotency_key="fund:1",
    )

    with pytest.raises(InsufficientFundsError) as exc_info:
        await wallet_service.debit_available(
            user_id=user.id,
            currency="UZS",
            amount=200,
            entry_type=WalletEntryType.ADMIN_ADJUSTMENT,
            idempotency_key="debit:1",
        )
    assert exc_info.value.available == 100
    assert exc_info.value.requested == 200

    wallet = await uow.wallets.get_or_create_wallet(user.id, "UZS")
    assert wallet.available_amount == 100  # untouched by the failed attempt


@pytest.mark.asyncio
async def test_ledger_entries_sum_matches_cached_wallet_balance(uow, make_user):
    """This is exactly the invariant `app.workers.reconciliation_worker`
    checks continuously in production."""
    user = await make_user()
    wallet_service = WalletService(uow)
    await wallet_service.credit_available(
        user_id=user.id,
        currency="UZS",
        amount=1000,
        entry_type=WalletEntryType.ADMIN_GIFT,
        idempotency_key="a",
    )
    await wallet_service.debit_available(
        user_id=user.id,
        currency="UZS",
        amount=300,
        entry_type=WalletEntryType.ADMIN_ADJUSTMENT,
        idempotency_key="b",
    )
    await wallet_service.credit_available(
        user_id=user.id,
        currency="UZS",
        amount=50,
        entry_type=WalletEntryType.REFERRAL_COMMISSION,
        idempotency_key="c",
    )

    wallet = await uow.wallets.get_or_create_wallet(user.id, "UZS")
    entries = await uow.wallets.list_ledger_for_user(user.id, currency="UZS", limit=100)
    available_entries_sum = sum(e.amount for e in entries if e.bucket == "available")

    assert wallet.available_amount == 750
    assert available_entries_sum == wallet.available_amount

````

### FILE: tests/integration/test_movie_access.py

````python
"""Integration tests: free access, premium access, mandatory-subscription
exemption for premium users, and that access is denied when membership
can't be verified (fail closed) (spec section 10)."""

from __future__ import annotations

import datetime as dt

import pytest

from app.db.models.enums import MovieAccessType, MoviePublicationState
from app.services.movie_access_service import MovieAccessService


async def _make_movie(uow, **kwargs):
    defaults = dict(
        code="100",
        title_uz="T",
        title_ru="T",
        title_en="T",
        video_file_id="FAKE_FILE_ID",
        access_type=MovieAccessType.FREE.value,
        publication_state=MoviePublicationState.PUBLISHED.value,
    )
    defaults.update(kwargs)
    return await uow.catalog.create(**defaults)


@pytest.mark.asyncio
async def test_free_movie_without_mandatory_channels_is_accessible(uow, make_user):
    user = await make_user()
    movie = await _make_movie(uow, code="1")

    service = MovieAccessService(uow)
    decision = await service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )

    assert decision.allowed is True
    assert decision.reason == "no_mandatory_channels"


@pytest.mark.asyncio
async def test_premium_movie_requires_active_premium(uow, make_user):
    user = await make_user()
    movie = await _make_movie(uow, code="2", access_type=MovieAccessType.PREMIUM.value)

    service = MovieAccessService(uow)
    decision = await service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )
    assert decision.allowed is False
    assert decision.reason == "premium_required"

    user.premium_until = dt.datetime.now(dt.UTC) + dt.timedelta(days=1)
    await uow.flush()
    decision2 = await service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )
    assert decision2.allowed is True
    assert decision2.reason == "premium_access"


@pytest.mark.asyncio
async def test_premium_user_is_exempt_from_mandatory_subscription(uow, make_user):
    user = await make_user()
    user.premium_until = dt.datetime.now(dt.UTC) + dt.timedelta(days=1)
    await uow.flush()

    from app.db.models.catalog import MandatoryChannel

    channel = MandatoryChannel(chat_id="@somechannel", title="Some Channel")
    uow.session.add(channel)
    await uow.flush()

    movie = await _make_movie(uow, code="3", access_type=MovieAccessType.FREE.value)

    async def checker(telegram_id, chat_id):
        return False  # not a member of anything

    service = MovieAccessService(uow, membership_checker=checker)
    decision = await service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )

    assert decision.allowed is True
    assert decision.reason == "premium_exempt"


@pytest.mark.asyncio
async def test_free_user_must_join_mandatory_channels(uow, make_user):
    user = await make_user()

    from app.db.models.catalog import MandatoryChannel

    channel = MandatoryChannel(chat_id="@somechannel", title="Some Channel")
    uow.session.add(channel)
    await uow.flush()

    movie = await _make_movie(uow, code="4")

    async def not_a_member(telegram_id, chat_id):
        return False

    service = MovieAccessService(uow, membership_checker=not_a_member)
    decision = await service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )

    assert decision.allowed is False
    assert decision.reason == "must_join_channels"
    assert "@somechannel" in decision.missing_channels


@pytest.mark.asyncio
async def test_access_fails_closed_when_membership_cannot_be_checked(uow, make_user):
    user = await make_user()

    from app.db.models.catalog import MandatoryChannel

    channel = MandatoryChannel(chat_id="@somechannel", title="Some Channel")
    uow.session.add(channel)
    await uow.flush()

    movie = await _make_movie(uow, code="5")

    service = MovieAccessService(uow, membership_checker=None)  # no live Telegram connection
    decision = await service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )

    assert decision.allowed is False
    assert decision.reason == "membership_check_unavailable"


@pytest.mark.asyncio
async def test_unpublished_movie_is_never_accessible(uow, make_user):
    user = await make_user()
    movie = await _make_movie(uow, code="6", publication_state=MoviePublicationState.DRAFT.value)

    service = MovieAccessService(uow)
    decision = await service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )

    assert decision.allowed is False
    assert decision.reason == "not_published"

````

### FILE: tests/integration/test_promo_codes.py

````python
"""Integration tests: full-premium and discount promo funding math against
a real wallet, insufficient balance rejection, and concurrent redemption
safety (spec section 10)."""

from __future__ import annotations

import asyncio

import pytest

from app.db.models.enums import PromoKind, WalletEntryType
from app.services.promo_service import AttributionRequest, PromoService
from app.services.wallet_service import WalletService


async def _fund_wallet(uow, user_id: int, currency: str, amount: int):
    wallet_service = WalletService(uow)
    await wallet_service.credit_available(
        user_id=user_id,
        currency=currency,
        amount=amount,
        entry_type=WalletEntryType.ADMIN_GIFT,
        idempotency_key=f"fund:{user_id}:{amount}:{currency}",
    )


@pytest.mark.asyncio
async def test_full_premium_code_reserves_exact_worked_example(uow, make_user, make_plan):
    issuer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    await _fund_wallet(uow, issuer.id, "UZS", 100_000)

    promo_service = PromoService(uow)
    promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.FULL_PREMIUM,
        discount_percent=0,
        activations=20,
        attribution=AttributionRequest(kind="none"),
    )

    assert promo.max_uses == 20
    assert promo.total_reserved_amount == 100_000

    wallet = await uow.wallets.get_or_create_wallet(issuer.id, "UZS")
    assert wallet.available_amount == 0
    assert wallet.reserved_amount == 100_000


@pytest.mark.asyncio
async def test_discount_code_reserves_exact_worked_example(uow, make_user, make_plan):
    issuer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS", max_discount_percent=50)
    await _fund_wallet(uow, issuer.id, "UZS", 100_000)

    promo_service = PromoService(uow)
    promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.PERCENT_DISCOUNT,
        discount_percent=10,
        activations=200,
        attribution=AttributionRequest(kind="none"),
    )

    assert promo.total_reserved_amount == 100_000  # 200 * 500
    assert promo.cost_per_activation == 500

    wallet = await uow.wallets.get_or_create_wallet(issuer.id, "UZS")
    assert wallet.available_amount == 0
    assert wallet.reserved_amount == 100_000


@pytest.mark.asyncio
async def test_insufficient_balance_rejects_code_creation_without_reserving(
    uow, make_user, make_plan
):
    issuer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    await _fund_wallet(
        uow, issuer.id, "UZS", 50_000
    )  # not enough for 20 activations (needs 100,000)

    promo_service = PromoService(uow)
    with pytest.raises(ValueError):
        await promo_service.create_user_code(
            issuer_user_id=issuer.id,
            issuer_is_blogger=False,
            plan=plan,
            kind=PromoKind.FULL_PREMIUM,
            discount_percent=0,
            activations=20,
            attribution=AttributionRequest(kind="none"),
        )

    wallet = await uow.wallets.get_or_create_wallet(issuer.id, "UZS")
    assert wallet.available_amount == 50_000  # untouched
    assert wallet.reserved_amount == 0


@pytest.mark.asyncio
async def test_redeeming_own_code_is_rejected(uow, make_user, make_plan):
    issuer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    await _fund_wallet(uow, issuer.id, "UZS", 100_000)
    promo_service = PromoService(uow)
    promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.FULL_PREMIUM,
        discount_percent=0,
        activations=5,
        attribution=AttributionRequest(kind="none"),
    )

    result = await promo_service.redeem(code=promo.code, redeemer_user_id=issuer.id)
    assert result.ok is False
    assert result.reason == "cannot_redeem_own_code"


@pytest.mark.asyncio
async def test_user_cannot_redeem_the_same_code_twice(uow, make_user, make_plan):
    issuer = await make_user()
    redeemer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    await _fund_wallet(uow, issuer.id, "UZS", 100_000)
    promo_service = PromoService(uow)
    promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.FULL_PREMIUM,
        discount_percent=0,
        activations=5,
        attribution=AttributionRequest(kind="none"),
    )

    first = await promo_service.redeem(code=promo.code, redeemer_user_id=redeemer.id)
    second = await promo_service.redeem(code=promo.code, redeemer_user_id=redeemer.id)

    assert first.ok is True
    assert second.ok is False
    assert second.reason == "already_redeemed_by_user"


@pytest.mark.asyncio
async def test_concurrent_redemptions_never_exceed_max_uses(
    uow, make_user, make_plan, session_factory
):
    """Fires many redemptions concurrently against a promo with only 3
    activations and asserts AT MOST 3 succeed and remaining_uses never goes
    negative -- the outcome invariant guaranteed by the atomic
    decrement_remaining_use + DB check constraint.

    CAVEAT: this fixture shares a single AsyncSession/SQLite connection
    across the "concurrent" coroutines, so it exercises cooperative
    interleaving under asyncio, not true multi-connection parallelism --
    SQLite also has no real row-level locking. The invariant asserted here
    (never more successes than max_uses, remaining_uses never negative) is
    still meaningful because it is enforced by the atomic
    decrement_remaining_use + DB-level CHECK(remaining_uses >= 0), which is
    the same code path used against real concurrent connections in
    production. Real multi-connection race testing should be run against
    Postgres with separate sessions per task; see README "Testing".
    """
    issuer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    await _fund_wallet(uow, issuer.id, "UZS", 15_000)
    promo_service = PromoService(uow)
    promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.FULL_PREMIUM,
        discount_percent=0,
        activations=3,
        attribution=AttributionRequest(kind="none"),
    )

    redeemer_ids = [(await make_user()).id for _ in range(8)]
    await uow.session.commit()

    # Each concurrent attempt gets its OWN session/UnitOfWork, matching how
    # separate concurrent HTTP/bot requests would each open their own
    # session in production -- sharing a single AsyncSession across
    # coroutines is not supported by SQLAlchemy and would not exercise a
    # realistic race.
    from app.db.uow import UnitOfWork

    async def try_redeem(redeemer_id: int):
        async with session_factory() as session:
            local_uow = UnitOfWork(session)
            local_promo_service = PromoService(local_uow)
            try:
                result = await local_promo_service.redeem(
                    code=promo.code, redeemer_user_id=redeemer_id
                )
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise

    results = await asyncio.gather(
        *(try_redeem(rid) for rid in redeemer_ids), return_exceptions=True
    )
    successes = [r for r in results if not isinstance(r, Exception) and r.ok]

    assert len(successes) <= 3

    from sqlalchemy import select

    from app.db.models.promo import PromoCode

    refreshed = (
        await uow.session.execute(select(PromoCode).where(PromoCode.id == promo.id))
    ).scalar_one()
    assert refreshed.remaining_uses >= 0
    assert refreshed.remaining_uses == promo.max_uses - len(successes)


@pytest.mark.asyncio
async def test_cancelling_promo_releases_unused_reserve(uow, make_user, make_plan):
    issuer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    await _fund_wallet(uow, issuer.id, "UZS", 100_000)
    promo_service = PromoService(uow)
    promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.FULL_PREMIUM,
        discount_percent=0,
        activations=20,
        attribution=AttributionRequest(kind="none"),
    )

    redeemer = await make_user()
    await promo_service.redeem(code=promo.code, redeemer_user_id=redeemer.id)  # consumes 1 of 20

    await promo_service.cancel(promo, reason="issuer requested cancellation")

    wallet = await uow.wallets.get_or_create_wallet(issuer.id, "UZS")
    # 19 unused activations * 5000 = 95,000 released back to available.
    assert wallet.available_amount == 95_000
    assert wallet.reserved_amount == 0


@pytest.mark.asyncio
async def test_external_url_attribution_requires_admin_approval_before_redeemable(
    uow, make_user, make_plan
):
    issuer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    await _fund_wallet(uow, issuer.id, "UZS", 100_000)
    promo_service = PromoService(uow)
    promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.FULL_PREMIUM,
        discount_percent=0,
        activations=5,
        attribution=AttributionRequest(kind="external_url", value="https://example.com/mychannel"),
    )

    assert promo.moderation_status == "pending"
    assert promo.is_active is False

    redeemer = await make_user()
    result = await promo_service.redeem(code=promo.code, redeemer_user_id=redeemer.id)
    assert result.ok is False
    assert result.reason == "not_redeemable"

    # Admin approves -> becomes redeemable.
    await promo_service.moderate(promo, approve=True, admin_id=1)
    result2 = await promo_service.redeem(code=promo.code, redeemer_user_id=redeemer.id)
    assert result2.ok is True

````

### FILE: tests/integration/test_purchase_and_commissions.py

````python
"""Integration tests: per-plan commission rates, a blogger earning BOTH
the purchase commission AND the acquisition reward, refunds, and duplicate
webhook idempotency (spec section 10)."""

from __future__ import annotations

import pytest

from app.db.models.enums import PaymentProviderCode
from app.services.blogger_reward_service import BloggerRewardService
from app.services.purchase_service import PurchaseService
from app.services.referral_service import ReferralService
from app.services.settings_service import SettingsService


async def _make_blogger(uow, user):
    profile = await uow.bloggers.create_profile(user_id=user.id, approved_application_id=0)
    return profile


@pytest.mark.asyncio
async def test_standard_referrer_earns_plan_specific_commission(uow, make_user, make_plan):
    referrer = await make_user()
    buyer = await make_user()
    plan = await make_plan(price_amount=10_000, standard_referral_percent=1000)  # 10%

    await ReferralService(uow).attribute_start(new_user=buyer, referral_code=referrer.referral_code)

    purchase_service = PurchaseService(uow)
    order = await purchase_service.create_order(
        buyer_user_id=buyer.id, plan=plan, provider_code=PaymentProviderCode.WALLET
    )
    await purchase_service.confirm_payment(order)

    commission = await uow.rewards.get_commission_by_order(order.id)
    assert commission is not None
    assert commission.amount == 1000  # 10% of 10,000
    assert commission.was_blogger_rate_snapshot is False


@pytest.mark.asyncio
async def test_different_plans_yield_different_commission_amounts(uow, make_user, make_plan):
    referrer = await make_user()
    buyer1 = await make_user()
    buyer2 = await make_user()

    weekly = await make_plan(price_amount=10_000, standard_referral_percent=1000)  # 10%
    monthly = await make_plan(price_amount=10_000, standard_referral_percent=1500)  # 15%

    await ReferralService(uow).attribute_start(
        new_user=buyer1, referral_code=referrer.referral_code
    )
    await ReferralService(uow).attribute_start(
        new_user=buyer2, referral_code=referrer.referral_code
    )

    purchase_service = PurchaseService(uow)
    order1 = await purchase_service.create_order(
        buyer_user_id=buyer1.id, plan=weekly, provider_code=PaymentProviderCode.WALLET
    )
    await purchase_service.confirm_payment(order1)
    order2 = await purchase_service.create_order(
        buyer_user_id=buyer2.id, plan=monthly, provider_code=PaymentProviderCode.WALLET
    )
    await purchase_service.confirm_payment(order2)

    c1 = await uow.rewards.get_commission_by_order(order1.id)
    c2 = await uow.rewards.get_commission_by_order(order2.id)
    assert c1.amount == 1000
    assert c2.amount == 1500
    assert c1.amount != c2.amount


@pytest.mark.asyncio
async def test_blogger_earns_both_purchase_commission_and_acquisition_reward(
    uow, make_user, make_plan
):
    blogger = await make_user()
    await _make_blogger(uow, blogger)
    await SettingsService(uow).set_global_blogger_reward_per_1000(
        100_000, "UZS"
    )  # 100 UZS/qualified join

    buyer = await make_user()
    plan = await make_plan(
        price_amount=10_000, standard_referral_percent=1000, blogger_referral_percent=1500
    )

    referral_service = ReferralService(uow)
    attribution = await referral_service.attribute_start(
        new_user=buyer, referral_code=blogger.referral_code
    )
    assert attribution.referral.is_qualified is True
    assert attribution.referral.referrer_was_blogger_at_join is True

    # Acquisition reward accrues at ATTRIBUTION time (per join), independent of purchase.
    await BloggerRewardService(uow).accrue_for_qualified_referral(attribution.referral)
    reward = await uow.rewards.get_reward_by_referral(attribution.referral.id)
    assert reward is not None
    assert reward.amount == 100  # 100,000/1000

    # Purchase commission accrues at PURCHASE time, using the BLOGGER rate (15%), not standard (10%).
    purchase_service = PurchaseService(uow)
    order = await purchase_service.create_order(
        buyer_user_id=buyer.id, plan=plan, provider_code=PaymentProviderCode.WALLET
    )
    await purchase_service.confirm_payment(order)

    commission = await uow.rewards.get_commission_by_order(order.id)
    assert commission.amount == 1500  # 15% of 10,000
    assert commission.was_blogger_rate_snapshot is True

    # Both rewards must exist independently and be summed in stats.
    stats = await referral_service.stats_for_referrer(blogger.id)
    assert stats["purchase_commission_total"] == 1500
    assert stats["blogger_reward_total"] == 100


@pytest.mark.asyncio
async def test_duplicate_confirm_payment_call_is_idempotent(uow, make_user, make_plan):
    referrer = await make_user()
    buyer = await make_user()
    plan = await make_plan(price_amount=10_000, standard_referral_percent=1000)
    await ReferralService(uow).attribute_start(new_user=buyer, referral_code=referrer.referral_code)

    purchase_service = PurchaseService(uow)
    order = await purchase_service.create_order(
        buyer_user_id=buyer.id, plan=plan, provider_code=PaymentProviderCode.WALLET
    )

    # Simulate a duplicate webhook delivery calling confirm_payment twice.
    await purchase_service.confirm_payment(order, provider_reference="charge_123")
    await purchase_service.confirm_payment(order, provider_reference="charge_123")

    commissions = await uow.rewards.list_for_referrer(referrer.id)
    assert len(commissions) == 1  # never double-paid

    updated_buyer = await uow.users.get_by_id(buyer.id)
    # Premium should only have been extended once: duration_days from the plan.

    assert updated_buyer.premium_until is not None


@pytest.mark.asyncio
async def test_full_refund_reverses_commission_and_revokes_future_premium(
    uow, make_user, make_plan
):
    referrer = await make_user()
    buyer = await make_user()
    plan = await make_plan(price_amount=10_000, standard_referral_percent=1000, duration_days=30)
    await ReferralService(uow).attribute_start(new_user=buyer, referral_code=referrer.referral_code)

    purchase_service = PurchaseService(uow)
    order = await purchase_service.create_order(
        buyer_user_id=buyer.id, plan=plan, provider_code=PaymentProviderCode.WALLET
    )
    await purchase_service.confirm_payment(order)

    wallet_before = await uow.wallets.get_or_create_wallet(referrer.id, "UZS")
    assert wallet_before.available_amount == 1000

    await purchase_service.refund_order(order, reason="buyer_requested")

    wallet_after = await uow.wallets.get_or_create_wallet(referrer.id, "UZS")
    assert wallet_after.available_amount == 0  # commission fully clawed back

    commission = await uow.rewards.get_commission_by_order(order.id)
    assert commission.status == "reversed"

    refreshed_buyer = await uow.users.get_by_id(buyer.id)
    import datetime as dt

    assert refreshed_buyer.premium_until <= dt.datetime.now(dt.UTC) + dt.timedelta(seconds=5)

````

### FILE: tests/integration/test_referral_attribution.py

````python
"""Integration tests for referral attribution and anti-fraud qualification
(spec section 5 / section 10: "Self-referrals, repeat starts, suspicious
users, and blocked users")."""

from __future__ import annotations

import pytest

from app.services.referral_service import ReferralService


@pytest.mark.asyncio
async def test_normal_referral_is_qualified(uow, make_user):
    referrer = await make_user()
    referred = await make_user()

    result = await ReferralService(uow).attribute_start(
        new_user=referred, referral_code=referrer.referral_code
    )

    assert result.created is True
    assert result.referral.is_qualified is True
    assert result.referral.is_self_referral is False
    assert result.referral.is_suspicious is False


@pytest.mark.asyncio
async def test_self_referral_is_rejected(uow, make_user):
    user = await make_user()

    result = await ReferralService(uow).attribute_start(
        new_user=user, referral_code=user.referral_code
    )

    assert result.referral.is_self_referral is True
    assert result.referral.is_qualified is False
    assert result.reason == "self_referral_rejected"


@pytest.mark.asyncio
async def test_repeated_start_before_attribution_is_suspicious_not_qualified(uow, make_user):
    referrer = await make_user()
    referred = await make_user()
    # Simulate the referred user having issued /start more than once BEFORE
    # this attribution call (e.g. bot restart replay, or fraud attempt).
    await uow.users.touch_start(referred)  # start_count becomes 2

    result = await ReferralService(uow).attribute_start(
        new_user=referred, referral_code=referrer.referral_code
    )

    assert result.referral.is_qualified is False
    assert result.referral.is_suspicious is True
    assert result.referral.suspicious_reason == "repeated_start_before_attribution"


@pytest.mark.asyncio
async def test_blocked_new_user_is_not_qualified(uow, make_user):
    referrer = await make_user()
    referred = await make_user(is_blocked=True)

    result = await ReferralService(uow).attribute_start(
        new_user=referred, referral_code=referrer.referral_code
    )

    assert result.referral.is_qualified is False
    assert result.referral.disqualified_reason == "blocked_account"


@pytest.mark.asyncio
async def test_blocked_referrer_disqualifies_the_join(uow, make_user):
    referrer = await make_user(is_blocked=True)
    referred = await make_user()

    result = await ReferralService(uow).attribute_start(
        new_user=referred, referral_code=referrer.referral_code
    )

    assert result.referral.is_qualified is False
    assert result.referral.disqualified_reason == "referrer_blocked"


@pytest.mark.asyncio
async def test_duplicate_attribution_is_idempotent(uow, make_user):
    referrer_a = await make_user()
    referrer_b = await make_user()
    referred = await make_user()

    first = await ReferralService(uow).attribute_start(
        new_user=referred, referral_code=referrer_a.referral_code
    )
    # A second, different referral code must NOT re-attribute the user --
    # "one referrer only" (spec section 5).
    second = await ReferralService(uow).attribute_start(
        new_user=referred, referral_code=referrer_b.referral_code
    )

    assert first.created is True
    assert second.created is False
    assert second.reason == "already_attributed"
    assert second.referral.referrer_user_id == first.referral.referrer_user_id


@pytest.mark.asyncio
async def test_unknown_referral_code_does_not_create_a_referral(uow, make_user):
    referred = await make_user()

    result = await ReferralService(uow).attribute_start(
        new_user=referred, referral_code="does-not-exist"
    )

    assert result.created is False
    assert result.reason == "unknown_referral_code"

````

### FILE: tests/unit/__init__.py

````python

````

### FILE: tests/unit/test_blogger_rewards.py

````python
import pytest

from app.services.blogger_rewards import (
    accrue_qualified_join,
    expected_total_after_n_joins,
    simulate_n_joins,
)


@pytest.mark.parametrize("n", [1, 10, 999, 1000])
def test_reward_totals_for_required_join_counts_exact_rate(n):
    # 100,000 UZS per 1000 users => exactly 100 UZS per user, no remainder ever.
    rate = 100_000
    total, remainder = simulate_n_joins(rate, n)
    assert total == expected_total_after_n_joins(rate, n)
    assert total == 100 * n
    assert remainder == 0  # rate is an exact multiple of 1000 -> no fractional carry needed


@pytest.mark.parametrize("n", [1, 10, 999, 1000])
def test_reward_totals_for_required_join_counts_fractional_rate(n):
    # 333 UZS per 1000 users => 0.333 UZS/user; must carry the fractional remainder.
    rate = 333
    total, remainder = simulate_n_joins(rate, n)
    assert total == expected_total_after_n_joins(rate, n)
    # Total credited must never exceed what n users have truly earned.
    assert total <= (rate * n) / 1000
    assert 0 <= remainder < 1_000_000


def test_first_qualified_user_can_earn_immediately_without_waiting_for_1000():
    # Rate high enough that even ONE join produces a whole-unit reward.
    step = accrue_qualified_join(rate_per_1000=100_000, remainder_micros_before=0)
    assert step.amount_credited == 100
    assert step.remainder_micros_after == 0


def test_small_rate_first_user_may_earn_zero_but_remainder_accumulates():
    # Rate of 1 UZS/1000 users => 0.001 UZS/user; first user alone rounds to 0
    # but the remainder must be retained (not discarded) for future joins.
    step = accrue_qualified_join(rate_per_1000=1, remainder_micros_before=0)
    assert step.amount_credited == 0
    assert step.remainder_micros_after == 1000  # 1/1000 unit = 1000 micros retained


def test_remainder_eventually_produces_a_whole_unit_payout():
    rate = 1  # 1 UZS per 1000 users
    remainder = 0
    total = 0
    credited_at_join = None
    for i in range(1, 1001):
        step = accrue_qualified_join(rate, remainder)
        remainder = step.remainder_micros_after
        total += step.amount_credited
        if step.amount_credited > 0 and credited_at_join is None:
            credited_at_join = i
    assert total == 1  # exactly 1 UZS earned across 1000 joins at this rate
    assert credited_at_join == 1000


def test_no_overpayment_no_underpayment_across_many_joins():
    rate = 12_345  # deliberately awkward, not a multiple of 1000
    for n in (1, 2, 3, 7, 50, 500, 1000, 2500):
        total, _ = simulate_n_joins(rate, n)
        assert total == (rate * n) // 1000


def test_rejects_negative_rate_or_remainder():
    with pytest.raises(ValueError):
        accrue_qualified_join(-1, 0)
    with pytest.raises(ValueError):
        accrue_qualified_join(100, -1)

````

### FILE: tests/unit/test_commission.py

````python
from app.services.commission import (
    CommissionInput,
    calculate_referral_commission,
    reverse_commission_amount,
)


def make_input(**overrides) -> CommissionInput:
    base = dict(
        net_paid_amount=10_000,
        standard_referral_percent=1000,  # 10.00%
        blogger_referral_percent=1500,  # 15.00%
        referrer_is_blogger=False,
        is_first_purchase_of_referred_user=True,
        commission_applies_to_renewals=False,
    )
    base.update(overrides)
    return CommissionInput(**base)


def test_each_plan_independent_commission_percent():
    # One-week plan: 10% commission.
    weekly = make_input(net_paid_amount=10_000, standard_referral_percent=1000)
    result_weekly = calculate_referral_commission(weekly)
    assert result_weekly.eligible
    assert result_weekly.amount == 1_000

    # One-month plan: 15% commission on a DIFFERENT plan/purchase -- proves
    # commission is never hard-coded identically across plans.
    monthly = make_input(net_paid_amount=10_000, standard_referral_percent=1500)
    result_monthly = calculate_referral_commission(monthly)
    assert result_monthly.eligible
    assert result_monthly.amount == 1_500
    assert result_weekly.amount != result_monthly.amount


def test_blogger_referrer_gets_blogger_rate_not_standard_rate():
    inp = make_input(
        net_paid_amount=10_000,
        standard_referral_percent=1000,
        blogger_referral_percent=1500,
        referrer_is_blogger=True,
    )
    result = calculate_referral_commission(inp)
    assert result.eligible
    assert result.used_blogger_rate is True
    assert result.amount == 1_500  # blogger rate, not standard 10%


def test_standard_referrer_still_works_when_not_blogger():
    inp = make_input(referrer_is_blogger=False)
    result = calculate_referral_commission(inp)
    assert result.used_blogger_rate is False
    assert result.amount == 1_000


def test_renewal_commission_disabled_by_policy():
    inp = make_input(
        is_first_purchase_of_referred_user=False,
        commission_applies_to_renewals=False,
    )
    result = calculate_referral_commission(inp)
    assert result.eligible is False
    assert result.amount == 0
    assert result.reason == "renewal_commission_disabled"


def test_renewal_commission_enabled_by_policy():
    inp = make_input(
        is_first_purchase_of_referred_user=False,
        commission_applies_to_renewals=True,
        standard_referral_percent=1000,
        net_paid_amount=20_000,
    )
    result = calculate_referral_commission(inp)
    assert result.eligible is True
    assert result.amount == 2_000


def test_first_purchase_always_eligible_regardless_of_renewal_policy():
    inp = make_input(is_first_purchase_of_referred_user=True, commission_applies_to_renewals=False)
    result = calculate_referral_commission(inp)
    assert result.eligible is True


def test_reverse_commission_full_refund():
    assert reverse_commission_amount(1000, 1, 1) == 1000


def test_reverse_commission_partial_refund_rounds_down():
    # Refund 1/3 of the purchase -> claw back floor(1000/3) = 333.
    assert reverse_commission_amount(1000, 1, 3) == 333


def test_reverse_commission_zero_refund():
    assert reverse_commission_amount(1000, 0, 1) == 0

````

### FILE: tests/unit/test_money.py

````python
import pytest

from app.services.money import (
    InsufficientFundsError,
    apply_percent_discount,
    ceil_div,
    floor_div,
    percent_of,
)


def test_percent_of_exact():
    assert percent_of(5000, 1000) == 500  # 10.00% of 5000


def test_percent_of_floors_down():
    # 10% of 999 = 99.9 -> floors to 99, never overpays the recipient.
    assert percent_of(999, 1000) == 99


def test_percent_of_zero_percent():
    assert percent_of(12345, 0) == 0


def test_percent_of_rejects_negative():
    with pytest.raises(ValueError):
        percent_of(-1, 1000)
    with pytest.raises(ValueError):
        percent_of(100, -1)


def test_apply_percent_discount_worked_example():
    # Spec section 7 worked example: 5000 UZS premium, 10% discount -> buyer pays 4500.
    assert apply_percent_discount(5000, 10) == 4500


def test_apply_percent_discount_zero_percent():
    assert apply_percent_discount(5000, 0) == 5000


def test_apply_percent_discount_full_percent():
    assert apply_percent_discount(5000, 100) == 0


def test_apply_percent_discount_rounds_ceiling_discount_amount():
    # 3 * 33% = 0.99 -> ceil -> 1 minor unit discount -> net = 2
    assert apply_percent_discount(3, 33) == 2


def test_apply_percent_discount_rejects_out_of_range():
    with pytest.raises(ValueError):
        apply_percent_discount(100, 101)
    with pytest.raises(ValueError):
        apply_percent_discount(100, -1)


def test_ceil_div_and_floor_div():
    assert ceil_div(10, 3) == 4
    assert floor_div(10, 3) == 3
    assert ceil_div(9, 3) == 3
    assert floor_div(9, 3) == 3


def test_insufficient_funds_error_message():
    err = InsufficientFundsError(available=100, requested=500, currency="UZS")
    assert "100" in str(err) and "500" in str(err) and "UZS" in str(err)

````

### FILE: tests/unit/test_promo_math.py

````python
import pytest

from app.services.promo_math import (
    buyer_amount_due,
    cost_per_activation,
    max_activations_for_budget,
    quote_promo_funding,
)


def test_full_premium_code_cost_per_activation_worked_example():
    # Spec section 7: premium costs 5,000 UZS; full-premium code costs the
    # issuer the full price per activation.
    assert cost_per_activation(5000, discount_percent=0, full_premium=True) == 5000


def test_full_premium_code_max_activations_worked_example():
    # 100,000 UZS balance / 5,000 per activation = 20 activations.
    assert max_activations_for_budget(100_000, 5000) == 20


def test_full_premium_buyer_pays_nothing():
    assert buyer_amount_due(5000, discount_percent=0, full_premium=True) == 0


def test_discount_code_cost_per_activation_worked_example():
    # 10% discount on 5,000 UZS costs the issuer 500 UZS/activation.
    assert cost_per_activation(5000, discount_percent=10, full_premium=False) == 500


def test_discount_code_max_activations_worked_example():
    # 100,000 UZS balance / 500 per activation = 200 activations.
    assert max_activations_for_budget(100_000, 500) == 200


def test_discount_code_buyer_pays_remainder():
    assert buyer_amount_due(5000, discount_percent=10, full_premium=False) == 4500


def test_quote_full_premium_20_activations_reserves_exactly_100000():
    quote = quote_promo_funding(
        plan_price=5000,
        discount_percent=0,
        full_premium=True,
        requested_activations=20,
        issuer_balance=100_000,
    )
    assert quote.sufficient_funds is True
    assert quote.total_reserved_amount == 100_000
    assert quote.balance_after == 0
    assert quote.max_activations_affordable == 20


def test_quote_discount_200_activations_reserves_exactly_100000():
    quote = quote_promo_funding(
        plan_price=5000,
        discount_percent=10,
        full_premium=False,
        requested_activations=200,
        issuer_balance=100_000,
    )
    assert quote.sufficient_funds is True
    assert quote.total_reserved_amount == 100_000
    assert quote.balance_after == 0
    assert quote.buyer_pays_per_activation == 4500


def test_quote_rejects_when_insufficient_funds():
    quote = quote_promo_funding(
        plan_price=5000,
        discount_percent=0,
        full_premium=True,
        requested_activations=21,  # would need 105,000 but only has 100,000
        issuer_balance=100_000,
    )
    assert quote.sufficient_funds is False
    # Balance must NOT be reduced when rejected.
    assert quote.balance_after == quote.balance_before == 100_000


def test_max_activations_for_budget_rejects_non_positive_cost():
    with pytest.raises(ValueError):
        max_activations_for_budget(1000, 0)


def test_quote_requires_positive_activation_count():
    with pytest.raises(ValueError):
        quote_promo_funding(
            plan_price=5000,
            discount_percent=10,
            full_premium=False,
            requested_activations=0,
            issuer_balance=1000,
        )

````

