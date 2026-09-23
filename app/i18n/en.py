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
