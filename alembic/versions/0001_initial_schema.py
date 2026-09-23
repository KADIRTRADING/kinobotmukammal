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
