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
