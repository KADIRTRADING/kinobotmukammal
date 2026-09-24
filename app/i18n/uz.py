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
    # =====================================================================
    # ADMIN PANEL (in-Telegram, spec section: replaces the web admin panel)
    # =====================================================================
    # --- General ---------------------------------------------------------------
    "admin_menu_button": "🛠 Admin panel",
    "admin_panel_title": "🛠 Admin panel — bo'limni tanlang:",
    "admin_back_to_panel_button": "⬅️ Admin panelga qaytish",
    "admin_main_menu_button": "🏠 Bosh menyu",
    "admin_cancel_button": "❌ Bekor qilish",
    "admin_confirm_button": "✅ Tasdiqlash",
    "admin_action_cancelled": "Amal bekor qilindi.",
    "admin_invalid_input": "Noto'g'ri format. Qayta urinib ko'ring.",
    "admin_not_found": "Topilmadi.",
    "admin_page_nav": "{current}/{total} sahifa",
    "admin_no_items": "Hozircha yozuvlar yo'q.",
    "admin_prev_page": "⬅️",
    "admin_next_page": "➡️",
    "admin_reason_prompt": "Sababni kiriting:",
    "admin_saved": "✅ Saqlandi.",
    "admin_deleted": "🗑 O'chirildi.",
    # --- Dashboard ---------------------------------------------------------------
    "admin_dashboard_button": "📊 Boshqaruv paneli",
    "admin_dashboard_title": "📊 Boshqaruv paneli",
    "admin_dashboard_stats": (
        "👥 Jami foydalanuvchilar: {total_users}\n"
        "🟢 Faol foydalanuvchilar (7 kun): {active_users}\n"
        "⭐ Premium foydalanuvchilar: {premium_users}\n"
        "🎬 Kinolar: {movies_count}\n"
        "👁 Ko'rishlar: {views_count}\n"
        "🧾 Buyurtmalar: {orders_count}\n"
        "✅ Muvaffaqiyatli to'lovlar: {paid_orders_count}\n"
        "💰 Daromad:\n{revenue_lines}\n"
        "⏳ Ko'rib chiqilishi kutilayotgan: {pending_reviews}\n"
        "🚨 So'nggi xatolar: {recent_errors}"
    ),
    "admin_dashboard_revenue_line": "  {currency}: {amount}",
    "admin_dashboard_no_errors": "Yo'q",
    # --- Movies -------------------------------------------------------------------
    "admin_movies_button": "🎬 Kinolar",
    "admin_movies_menu_title": "🎬 Kinolar boshqaruvi:",
    "admin_movies_add_button": "➕ Yangi kino qo'shish",
    "admin_movies_list_button": "📋 Kinolar ro'yxati",
    "admin_movies_search_button": "🔍 Kod bo'yicha qidirish",
    "admin_movie_upload_video_prompt": "Kino videosini yuboring (video fayl sifatida):",
    "admin_movie_invalid_video": "Iltimos, video fayl yuboring.",
    "admin_movie_enter_code_prompt": "Kino kodini kiriting (masalan: 222):",
    "admin_movie_code_taken": "Bu kod band. Boshqa kod kiriting.",
    "admin_movie_enter_title_uz": "Kino nomini o'zbek tilida kiriting:",
    "admin_movie_enter_title_ru": "Kino nomini rus tilida kiriting:",
    "admin_movie_enter_title_en": "Kino nomini ingliz tilida kiriting:",
    "admin_movie_enter_description_uz": "Tavsifni o'zbek tilida kiriting (o'tkazib yuborish uchun '-' yuboring):",
    "admin_movie_enter_description_ru": "Tavsifni rus tilida kiriting (o'tkazib yuborish uchun '-' yuboring):",
    "admin_movie_enter_description_en": "Tavsifni ingliz tilida kiriting (o'tkazib yuborish uchun '-' yuboring):",
    "admin_movie_choose_category_prompt": "Kategoriyani tanlang:",
    "admin_movie_no_category_button": "Kategoriyasiz",
    "admin_movie_choose_access_prompt": "Kirish turini tanlang:",
    "admin_movie_access_free_button": "🆓 Bepul",
    "admin_movie_access_premium_button": "⭐ Premium",
    "admin_movie_upload_poster_prompt": "Poster rasmini yuboring (ixtiyoriy, o'tkazib yuborish uchun '-' yuboring):",
    "admin_movie_draft_summary": (
        "📦 Qoralama:\n🔢 Kod: {code}\n🇺🇿 {title_uz}\n🇷🇺 {title_ru}\n🇬🇧 {title_en}\n"
        "📁 Kategoriya: {category}\n🔐 Kirish: {access_type}\n\nSaqlansinmi (qoralama sifatida)?"
    ),
    "admin_movie_saved_draft": "✅ Kino qoralama sifatida saqlandi. Kodi: {code}",
    "admin_movie_list_empty": "Kinolar topilmadi.",
    "admin_movie_list_item": "{code} | {title} | {state} | 👁{views}",
    "admin_movie_detail_title": (
        "🎬 {title}\n🔢 Kod: {code}\n📁 Kategoriya: {category}\n🔐 Kirish: {access_type}\n"
        "📌 Holat: {state}\n👁 Ko'rishlar: {views}"
    ),
    "admin_movie_publish_button": "✅ Publikatsiya qilish",
    "admin_movie_archive_button": "📦 Arxivlash",
    "admin_movie_edit_button": "✏️ Tahrirlash",
    "admin_movie_replace_video_button": "🎞 Videoni almashtirish",
    "admin_movie_replace_poster_button": "🖼 Posterni almashtirish",
    "admin_movie_delete_button": "🗑 O'chirish",
    "admin_movie_delete_confirm": "⚠️ \"{title}\" ({code}) kinosini butunlay o'chirishni tasdiqlaysizmi? Bu amalni qaytarib bo'lmaydi.",
    "admin_movie_deleted": "🗑 Kino o'chirildi: {code}",
    "admin_movie_published": "✅ Kino publikatsiya qilindi: {code}",
    "admin_movie_archived": "📦 Kino arxivlandi: {code}",
    "admin_movie_search_prompt": "Qidirish uchun kino kodi yoki nomini kiriting:",
    "admin_movie_edit_field_prompt": "Qaysi maydonni tahrirlaysiz?",
    "admin_movie_edit_title_uz_button": "🇺🇿 Nomi (UZ)",
    "admin_movie_edit_title_ru_button": "🇷🇺 Nomi (RU)",
    "admin_movie_edit_title_en_button": "🇬🇧 Nomi (EN)",
    "admin_movie_edit_category_button": "📁 Kategoriya",
    "admin_movie_edit_access_button": "🔐 Kirish turi",
    "admin_movie_enter_new_value_prompt": "Yangi qiymatni kiriting:",
    "admin_movie_updated": "✅ Kino yangilandi.",
    "admin_movie_upload_new_video_prompt": "Yangi video faylni yuboring:",
    "admin_movie_video_replaced": "✅ Video almashtirildi.",
    "admin_movie_upload_new_poster_prompt": "Yangi poster rasmini yuboring:",
    "admin_movie_poster_replaced": "✅ Poster almashtirildi.",
    # --- Categories -----------------------------------------------------------
    "admin_categories_button": "📁 Kategoriyalar",
    "admin_categories_menu_title": "📁 Kategoriyalar boshqaruvi:",
    "admin_categories_list_empty": "Kategoriyalar yo'q.",
    "admin_category_list_item": "{title} | tartib: {sort_order} | {status}",
    "admin_category_add_button": "➕ Yangi kategoriya",
    "admin_category_enter_slug_prompt": "Kategoriya slug (lotincha, bo'sh joysiz, masalan: action):",
    "admin_category_slug_taken": "Bu slug band. Boshqasini kiriting.",
    "admin_category_enter_title_uz_prompt": "Nomi (o'zbekcha):",
    "admin_category_enter_title_ru_prompt": "Nomi (ruscha):",
    "admin_category_enter_title_en_prompt": "Nomi (inglizcha):",
    "admin_category_created": "✅ Kategoriya yaratildi: {title}",
    "admin_category_edit_button": "✏️ Tahrirlash",
    "admin_category_move_up_button": "⬆️",
    "admin_category_move_down_button": "⬇️",
    "admin_category_toggle_button": "🔁 Holatni almashtirish",
    "admin_category_enabled": "✅ Kategoriya yoqildi: {title}",
    "admin_category_disabled": "⛔ Kategoriya o'chirildi: {title}",
    "admin_category_reordered": "✅ Tartib yangilandi.",
    # --- Mandatory channels -----------------------------------------------------
    "admin_channels_button": "📢 Majburiy kanallar",
    "admin_channels_menu_title": "📢 Majburiy kanallar boshqaruvi:",
    "admin_channels_list_empty": "Kanallar yo'q.",
    "admin_channel_list_item": "{title} | {chat_id} | bot admin: {bot_admin} | {status}",
    "admin_channel_add_button": "➕ Kanal qo'shish",
    "admin_channel_enter_chat_id_prompt": "Kanal chat ID yoki @username kiriting:",
    "admin_channel_chat_id_taken": "Bu kanal allaqachon qo'shilgan.",
    "admin_channel_enter_title_prompt": "Kanal nomini kiriting:",
    "admin_channel_enter_invite_link_prompt": "Taklif havolasini kiriting (o'tkazib yuborish uchun '-' yuboring):",
    "admin_channel_created": "✅ Kanal qo'shildi: {title}",
    "admin_channel_verify_button": "🔍 Admin huquqini tekshirish",
    "admin_channel_verify_success": "✅ Bot bu kanalda admin ekan.",
    "admin_channel_verify_failed": "⚠️ Bot bu kanalda admin emas yoki kanal topilmadi: {error}",
    "admin_channel_toggle_button": "🔁 Holatni almashtirish",
    "admin_channel_enabled": "✅ Kanal yoqildi: {title}",
    "admin_channel_disabled": "⛔ Kanal o'chirildi: {title}",
    "admin_channel_remove_button": "🗑 O'chirish",
    "admin_channel_remove_confirm": '⚠️ "{title}" kanalini ro\'yxatdan olib tashlashni tasdiqlaysizmi?',
    "admin_channel_removed": "🗑 Kanal olib tashlandi: {title}",
    # --- Users -------------------------------------------------------------------
    "admin_users_button": "👥 Foydalanuvchilar",
    "admin_users_menu_title": "👥 Foydalanuvchilar boshqaruvi. Qidirish uchun Telegram ID yoki username kiriting:",
    "admin_users_search_prompt": "Telegram ID yoki username kiriting:",
    "admin_users_search_empty": "Foydalanuvchilar topilmadi.",
    "admin_user_list_item": "{label} | {status}",
    "admin_user_detail_title": (
        "👤 {label}\n🆔 {telegram_id}\n🌐 Til: {target_language}\n📌 Holat: {status}\n"
        "⭐ Premium: {premium_until}\n🤝 Referal kodi: {referral_code}\n"
        "🧾 Buyurtmalar: {orders_count}\n💰 Balans: {balances}"
    ),
    "admin_user_block_button": "🚫 Bloklash",
    "admin_user_unblock_button": "✅ Blokdan chiqarish",
    "admin_user_block_reason_prompt": "Bloklash sababini kiriting:",
    "admin_user_blocked": "🚫 Foydalanuvchi bloklandi.",
    "admin_user_unblocked": "✅ Foydalanuvchi blokdan chiqarildi.",
    "admin_user_grant_premium_button": "⭐ Premium berish",
    "admin_user_revoke_premium_button": "⛔ Premium bekor qilish",
    "admin_user_choose_plan_prompt": "Qaysi reja bo'yicha premium berilsin?",
    "admin_user_grant_premium_reason_prompt": "Sababni kiriting:",
    "admin_user_premium_granted": "✅ Premium berildi: {label}, muddati: {until}",
    "admin_user_premium_revoked": "⛔ Premium bekor qilindi: {label}",
    "admin_user_no_active_premium": "Bu foydalanuvchida faol premium yo'q.",
    "admin_user_gift_balance_button": "💰 Balans sovg'a qilish",
    "admin_user_enter_gift_amount_prompt": "Miqdorni kiriting (butun son):",
    "admin_user_enter_gift_currency_prompt": "Valyutani kiriting (masalan: UZS):",
    "admin_user_enter_gift_reason_prompt": "Sababni kiriting (majburiy):",
    "admin_user_gift_reason_required": "Sabab ko'rsatilishi shart.",
    "admin_user_gift_confirm": "🎁 {label} ga {amount} {currency} berilsinmi? Sabab: {reason}",
    "admin_user_gift_given": "✅ Balans berildi: {amount} {currency} -> {label}",
    "admin_user_orders_button": "🧾 Buyurtmalar tarixi",
    "admin_user_orders_empty": "Buyurtmalar yo'q.",
    "admin_user_order_line": "{uid} | {amount} {currency} | {status} | {date}",
    # --- Premium plans -----------------------------------------------------------
    "admin_plans_button": "⭐ Premium rejalar",
    "admin_plans_menu_title": "⭐ Premium rejalar boshqaruvi:",
    "admin_plans_list_empty": "Rejalar yo'q.",
    "admin_plan_list_item": "{code} | {price} {currency} | {duration_days} kun | {status}",
    "admin_plan_add_button": "➕ Yangi reja",
    "admin_plan_enter_code_prompt": "Reja kodini kiriting (lotincha, masalan: monthly):",
    "admin_plan_code_taken": "Bu kod band.",
    "admin_plan_enter_title_uz_prompt": "Nomi (o'zbekcha):",
    "admin_plan_enter_title_ru_prompt": "Nomi (ruscha):",
    "admin_plan_enter_title_en_prompt": "Nomi (inglizcha):",
    "admin_plan_enter_duration_prompt": "Muddatini kunlarda kiriting (masalan: 30):",
    "admin_plan_enter_price_prompt": "Narxini kiriting (butun son, masalan: 25000):",
    "admin_plan_enter_currency_prompt": "Valyutani kiriting (masalan: UZS):",
    "admin_plan_enter_standard_referral_prompt": "Standart referal komissiyasini foizda kiriting (masalan: 10):",
    "admin_plan_enter_blogger_referral_prompt": "Bloger referal komissiyasini foizda kiriting (masalan: 15):",
    "admin_plan_enter_max_discount_prompt": "Promo-kod uchun maksimal chegirma foizini kiriting (0-100):",
    "admin_plan_created": "✅ Reja yaratildi: {code}",
    "admin_plan_detail_title": (
        "⭐ {title}\n🔢 Kod: {code}\n💵 Narx: {price} {currency}\n⏳ Muddat: {duration_days} kun\n"
        "🤝 Standart referal: {standard_percent}%\n🌟 Bloger referal: {blogger_percent}%\n"
        "💸 Maks. chegirma: {max_discount}%\n📌 Holat: {status}"
    ),
    "admin_plan_edit_price_button": "💵 Narxni o'zgartirish",
    "admin_plan_edit_standard_referral_button": "🤝 Standart referal %",
    "admin_plan_edit_blogger_referral_button": "🌟 Bloger referal %",
    "admin_plan_toggle_button": "🔁 Holatni almashtirish",
    "admin_plan_activated": "✅ Reja faollashtirildi: {code}",
    "admin_plan_deactivated": "⛔ Reja o'chirildi: {code}",
    "admin_plan_updated": "✅ Reja yangilandi.",
    # --- Promo codes (admin) -----------------------------------------------------
    "admin_promos_button": "🎟 Promo-kodlar",
    "admin_promos_menu_title": "🎟 Promo-kodlar boshqaruvi:",
    "admin_promos_pending_button": "⏳ Ko'rib chiqilishi kerak",
    "admin_promos_all_button": "📋 Barcha kodlar",
    "admin_promos_create_button": "➕ Bot nomidan kod yaratish",
    "admin_promos_pending_empty": "Ko'rib chiqilishi kerak bo'lgan promo-kodlar yo'q.",
    "admin_promo_review_item": "🎟 {code}\n👤 Egasi: {issuer}\n🔗 Havola: {attribution}\n🔢 Faollashtirish: {max_uses}",
    "admin_promo_approve_button": "✅ Tasdiqlash",
    "admin_promo_reject_button": "❌ Rad etish",
    "admin_promo_reject_reason_prompt": "Rad etish sababini kiriting:",
    "admin_promo_approved": "✅ Promo-kod tasdiqlandi: {code}",
    "admin_promo_rejected": "❌ Promo-kod rad etildi: {code}",
    "admin_promo_cancel_button": "🛑 Bekor qilish",
    "admin_promo_cancel_reason_prompt": "Bekor qilish sababini kiriting:",
    "admin_promo_cancelled": "🛑 Promo-kod bekor qilindi: {code}, band qilingan mablag' qaytarildi.",
    "admin_promo_list_item": "{code} | {remaining}/{max_uses} | {status}",
    "admin_promo_detail_title": (
        "🎟 {code}\n👤 Egasi: {issuer}\n📦 Reja: {plan}\n🏷 Turi: {kind}\n"
        "💸 Chegirma: {discount_percent}%\n🔢 Qoldi: {remaining}/{max_uses}\n📌 Holat: {status}\n"
        "✅ Faollashtirishlar soni: {redemption_count}"
    ),
    "admin_promo_create_choose_plan_prompt": "Qaysi reja uchun kod yaratilsin?",
    "admin_promo_create_choose_kind_prompt": "Kod turini tanlang:",
    "admin_promo_create_enter_discount_prompt": "Chegirma foizini kiriting:",
    "admin_promo_create_enter_activations_prompt": "Nechta faollashtirish uchun (butun son):",
    "admin_promo_create_confirm": (
        "🎟 Bot nomidan promo-kod:\n📦 Reja: {plan_title}\n🏷 Turi: {kind}\n"
        "💸 Chegirma: {discount_percent}%\n🔢 Faollashtirish: {activations}\n\nYaratilsinmi?"
    ),
    "admin_promo_create_success": "✅ Bot nomidan promo-kod yaratildi: `{code}`",
    # --- Blogger applications & referrals ----------------------------------------
    "admin_bloggers_button": "🌟 Blogerlar",
    "admin_bloggers_menu_title": "🌟 Bloger arizalari va referallar:",
    "admin_bloggers_pending_button": "⏳ Kutilayotgan arizalar",
    "admin_bloggers_active_button": "✅ Faol blogerlar",
    "admin_bloggers_suspicious_button": "⚠️ Shubhali faollik",
    "admin_bloggers_pending_empty": "Kutilayotgan arizalar yo'q.",
    "admin_blogger_application_item": "👤 {applicant}\n📱 Platforma: {platform}\n🔗 Havola: {url}\n🔑 Fraza: {phrase}",
    "admin_blogger_approve_button": "✅ Tasdiqlash",
    "admin_blogger_reject_button": "❌ Rad etish",
    "admin_blogger_reject_reason_prompt": "Rad etish sababini kiriting:",
    "admin_blogger_approved": "✅ Ariza tasdiqlandi: {applicant}",
    "admin_blogger_rejected": "❌ Ariza rad etildi: {applicant}",
    "admin_bloggers_active_empty": "Faol blogerlar yo'q.",
    "admin_blogger_active_item": "{label} | qo'shilganlar: {joins}",
    "admin_blogger_suspend_button": "⛔ Muzlatish",
    "admin_blogger_suspend_reason_prompt": "Sababni kiriting:",
    "admin_blogger_suspended": "⛔ Bloger muzlatildi: {label}",
    "admin_blogger_reactivate_button": "✅ Qayta faollashtirish",
    "admin_blogger_reactivated": "✅ Bloger qayta faollashtirildi: {label}",
    "admin_bloggers_suspicious_empty": "Shubhali referal faolligi yo'q.",
    "admin_suspicious_referral_item": "👤 Referrer: {referrer} -> {referred} | sabab: {reason} | {date}",
    "admin_reward_rate_button": "⚙️ Mukofot stavkasi",
    "admin_reward_rate_prompt": "1000 ta malakali a'zo uchun mukofot miqdorini kiriting (masalan: 100000):",
    "admin_reward_rate_currency_prompt": "Valyutani kiriting (masalan: UZS):",
    "admin_reward_rate_updated": "✅ Mukofot stavkasi yangilandi: {rate} {currency} / 1000 ta a'zo.",
    # --- Support -------------------------------------------------------------------
    "admin_support_button": "🆘 Qo'llab-quvvatlash",
    "admin_support_menu_title": "🆘 Ochiq murojaatlar:",
    "admin_support_empty": "Ochiq murojaatlar yo'q.",
    "admin_support_ticket_item": "#{ticket_id} | {label} | {subject}",
    "admin_support_ticket_detail": "#{ticket_id} — {label}\n\n{messages}",
    "admin_support_message_line": "[{date}] {sender}: {text}",
    "admin_support_reply_button": "✉️ Javob yozish",
    "admin_support_close_button": "✅ Yopish",
    "admin_support_reply_prompt": "Javobingizni kiriting:",
    "admin_support_reply_sent": "✅ Javob yuborildi.",
    "admin_support_ticket_closed": "✅ Murojaat yopildi: #{ticket_id}",
    # --- Broadcasts ------------------------------------------------------------
    "admin_broadcasts_button": "📣 Xabar yuborish",
    "admin_broadcasts_menu_title": "📣 Xabar yuborish boshqaruvi:",
    "admin_broadcast_create_button": "➕ Yangi xabar",
    "admin_broadcast_active_button": "📊 Faol yuborishlar",
    "admin_broadcast_choose_target_prompt": "Kimga yuborilsin?",
    "admin_broadcast_target_all_button": "👥 Barcha foydalanuvchilar",
    "admin_broadcast_target_premium_button": "⭐ Faqat premium",
    "admin_broadcast_target_free_button": "🆓 Faqat bepul",
    "admin_broadcast_enter_text_uz_prompt": "Xabar matnini o'zbek tilida kiriting:",
    "admin_broadcast_enter_text_ru_prompt": "Xabar matnini rus tilida kiriting:",
    "admin_broadcast_enter_text_en_prompt": "Xabar matnini ingliz tilida kiriting:",
    "admin_broadcast_add_photo_prompt": "Rasm qo'shmoqchimisiz? Yuboring yoki o'tkazib yuborish uchun '-' yozing:",
    "admin_broadcast_preview_title": (
        "📣 Xabar oldindan ko'rish:\n👥 Qabul qiluvchilar: {target_label} (~{recipient_count} kishi)\n\n"
        "🇺🇿 {text_uz}\n\n🇷🇺 {text_ru}\n\n🇬🇧 {text_en}"
    ),
    "admin_broadcast_confirm_send_button": "✅ Yuborish",
    "admin_broadcast_queued": "✅ Xabar navbatga qo'yildi. Qabul qiluvchilar: {count}",
    "admin_broadcast_active_empty": "Faol yuborishlar yo'q.",
    "admin_broadcast_progress_item": "#{id} | {status} | Yuborildi: {sent}/{total} | Xato: {failed} | O'tkazib: {skipped}",
    "admin_broadcast_cancel_button": "🛑 Bekor qilish",
    "admin_broadcast_cancelled": "🛑 Yuborish bekor qilindi: #{id}",
    # --- Orders / Payments ------------------------------------------------------
    "admin_orders_button": "🧾 Buyurtmalar",
    "admin_orders_menu_title": "🧾 Buyurtmalar va to'lovlar:",
    "admin_orders_recent_button": "📋 So'nggi buyurtmalar",
    "admin_orders_filter_status_button": "🔍 Holat bo'yicha filtr",
    "admin_orders_choose_status_prompt": "Holatni tanlang:",
    "admin_orders_empty": "Buyurtmalar topilmadi.",
    "admin_order_list_item": "{uid} | {amount} {currency} | {provider} | {status}",
    "admin_order_detail_title": (
        "🧾 {uid}\n👤 Xaridor: {buyer}\n📦 Reja: {plan}\n💵 Summa: {amount} {currency}\n"
        "🏦 Provider: {provider}\n📌 Holat: {status}\n🕒 Yaratildi: {created_at}\n"
        "✅ To'landi: {paid_at}\n📄 Provider ma'lumoti: {provider_reference}"
    ),
    "admin_order_provider_status_button": "🔄 Provider holatini yangilash",
    "admin_order_provider_status_note": (
        "ℹ️ Bu tugma faqat provider tomonidan haqiqiy tasdiqlangan holatni qayta tekshiradi. "
        "Buyurtma hech qachon shunchaki tugma bosish orqali 'to'landi' deb belgilanmaydi."
    ),
    "admin_order_refund_button": "↩️ Qaytarish",
    "admin_order_refund_reason_prompt": "Qaytarish sababini kiriting:",
    "admin_order_refund_confirm": "⚠️ {uid} buyurtmasini qaytarishni tasdiqlaysizmi? Bog'liq komissiyalar ham bekor qilinadi.",
    "admin_order_refunded": "↩️ Buyurtma qaytarildi: {uid}",
    "admin_order_cannot_refund": "Bu buyurtmani qaytarib bo'lmaydi (to'lanmagan yoki allaqachon qaytarilgan).",
    "admin_order_provider_events_button": "📜 Provider hodisalari",
    "admin_order_provider_events_empty": "Provider hodisalari yo'q.",
    "admin_order_provider_event_line": "{date} | {event_type} | qayta ishlangan: {processed}",
    # --- Settings / Audit ----------------------------------------------------------
    "admin_settings_button": "⚙️ Sozlamalar",
    "admin_settings_menu_title": "⚙️ Bot sozlamalari:",
    "admin_settings_current_title": (
        "⚙️ Joriy sozlamalar:\n🔁 Referal komissiyasi yangilashda: {renewals}\n"
        "🌟 Bloger mukofoti (1000 ta uchun): {reward_rate} {reward_currency}\n"
        "🎟 Promo-kodlarni birlashtirish: {stacking}"
    ),
    "admin_settings_toggle_renewals_button": "🔁 Yangilashda komissiya",
    "admin_settings_toggle_stacking_button": "🎟 Promo birlashtirish",
    "admin_settings_renewals_enabled": "✅ Endi referal komissiyasi yangilashlarga ham qo'llanadi.",
    "admin_settings_renewals_disabled": "⛔ Endi referal komissiyasi faqat birinchi xariddan olinadi.",
    "admin_settings_stacking_enabled": "✅ Promo-kodlarni birlashtirish yoqildi.",
    "admin_settings_stacking_disabled": "⛔ Promo-kodlarni birlashtirish o'chirildi.",
    "admin_audit_button": "📜 Audit jurnali",
    "admin_audit_menu_title": "📜 So'nggi admin amallari:",
    "admin_audit_empty": "Amallar tarixi bo'sh.",
    "admin_audit_entry_line": "{date} | {admin} | {action} | {entity}",
    # --- Admins (runtime admin grant/revoke) --------------------------------------
    "admin_admins_button": "👑 Adminlar",
    "admin_admins_menu_title": "👑 Adminlarni boshqarish:",
    "admin_admins_list_button": "📋 Adminlar ro'yxati",
    "admin_admins_add_button": "➕ Admin qo'shish",
    "admin_admins_owners_header": "👑 Asosiy adminlar (.env orqali):",
    "admin_admins_granted_header": "➕ Qo'shilgan adminlar:",
    "admin_admins_none": "  (yo'q)",
    "admin_admins_owner_line": "  🆔 {telegram_id}",
    "admin_admins_granted_line": "  🆔 {telegram_id} — {label} (kim qo'shdi: {granted_by})",
    "admin_admins_revoke_row": "🗑 {label}",
    "admin_admins_owners_only": "⛔ Bu amalni faqat asosiy adminlar bajara oladi.",
    "admin_admins_enter_telegram_id_prompt": "Yangi admin uchun Telegram raqamli ID sini kiriting:",
    "admin_admins_enter_label_prompt": (
        "Ushbu admin haqida qisqa izoh kiriting (masalan, ism yoki @username), "
        'yoki izohsiz o\'tkazib yuborish uchun "-" yuboring:'
    ),
    "admin_admins_cannot_self_grant": "⛔ O'zingizga admin huquqini bera olmaysiz.",
    "admin_admins_already_owner": "Bu foydalanuvchi allaqachon asosiy admin (.env orqali).",
    "admin_admins_already_granted": "Bu foydalanuvchi allaqachon admin huquqiga ega.",
    "admin_admins_grant_confirm_prompt": (
        "Tasdiqlang: 🆔 {telegram_id} ({label}) ga admin huquqi berilsinmi?"
    ),
    "admin_admins_granted": "✅ 🆔 {telegram_id} ga admin huquqi berildi.",
    "admin_admins_revoke_confirm_prompt": "🆔 {telegram_id} uchun admin huquqini bekor qilishni tasdiqlaysizmi?",
    "admin_admins_revoked": "🗑 🆔 {telegram_id} uchun admin huquqi bekor qilindi.",
    "admin_admins_you_were_granted": "✅ Sizga bot boshqaruv paneliga kirish huquqi berildi. /start bosing.",
    "admin_admins_you_were_revoked": "⛔ Sizning admin boshqaruv paneliga kirish huquqingiz bekor qilindi.",
}
