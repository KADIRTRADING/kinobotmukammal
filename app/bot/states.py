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
