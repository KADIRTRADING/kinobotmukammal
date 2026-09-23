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
