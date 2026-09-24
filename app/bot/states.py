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
    awaiting_description_uz = State()
    awaiting_description_ru = State()
    awaiting_description_en = State()
    choosing_category = State()
    choosing_access_type = State()
    awaiting_poster = State()
    confirming_draft = State()
    awaiting_search_query = State()
    choosing_edit_field = State()
    awaiting_new_field_value = State()
    awaiting_new_video = State()
    awaiting_new_poster = State()


# =====================================================================
# ADMIN PANEL (in-Telegram) FSM state groups.
#
# Every admin-only handler that uses one of these states is registered on
# a Router gated by `app.bot.filters.admin_filter.AdminAccessFilter` (see
# app.bot.handlers.admin.__init__ -> register_admin_router), so an
# unauthorized sender can never advance or exploit these states -- the
# filter runs before aiogram even resolves which state handler to call.
# =====================================================================


class AdminCategoryStates(StatesGroup):
    awaiting_slug = State()
    awaiting_title_uz = State()
    awaiting_title_ru = State()
    awaiting_title_en = State()


class AdminChannelStates(StatesGroup):
    awaiting_chat_id = State()
    awaiting_title = State()
    awaiting_invite_link = State()


class AdminUserStates(StatesGroup):
    awaiting_search_query = State()
    awaiting_block_reason = State()
    awaiting_grant_premium_reason = State()
    awaiting_gift_amount = State()
    awaiting_gift_currency = State()
    awaiting_gift_reason = State()


class AdminPlanStates(StatesGroup):
    awaiting_code = State()
    awaiting_title_uz = State()
    awaiting_title_ru = State()
    awaiting_title_en = State()
    awaiting_duration = State()
    awaiting_price = State()
    awaiting_currency = State()
    awaiting_standard_referral = State()
    awaiting_blogger_referral = State()
    awaiting_max_discount = State()
    awaiting_new_price = State()
    awaiting_new_standard_referral = State()
    awaiting_new_blogger_referral = State()


class AdminPromoStates(StatesGroup):
    choosing_plan = State()
    choosing_kind = State()
    awaiting_discount = State()
    awaiting_activations = State()
    awaiting_reject_reason = State()
    awaiting_cancel_reason = State()


class AdminBloggerStates(StatesGroup):
    awaiting_reject_reason = State()
    awaiting_suspend_reason = State()
    awaiting_reward_rate = State()
    awaiting_reward_currency = State()


class AdminSupportStates(StatesGroup):
    awaiting_reply_text = State()


class AdminBroadcastStates(StatesGroup):
    choosing_target = State()
    awaiting_text_uz = State()
    awaiting_text_ru = State()
    awaiting_text_en = State()
    awaiting_photo = State()
    confirming = State()


class AdminOrderStates(StatesGroup):
    awaiting_refund_reason = State()


class AdminAdminsStates(StatesGroup):
    """FSM states for the "👑 Admins" section (grant/revoke runtime admin
    access). Every handler using these states is additionally gated to
    owners-only via `app.core.admin_access.is_owner_admin` inside the
    handler body -- see `app.bot.handlers.admin.admins` -- on top of the
    router-level `AdminAccessFilter` that already covers the whole admin
    subtree, so a granted (non-owner) admin can never reach these steps
    even though they pass the outer filter for every OTHER admin section.
    """

    awaiting_grant_telegram_id = State()
    awaiting_grant_label = State()
    awaiting_revoke_confirm_id = State()
