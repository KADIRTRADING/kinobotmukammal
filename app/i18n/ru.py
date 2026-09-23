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
