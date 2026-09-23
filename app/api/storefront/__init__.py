"""Independent web storefront: a genuinely separate sales channel from the
Telegram bot, used ONLY for Stripe/Click checkout as permitted by spec
section 4. This surface is entirely gated behind `STOREFRONT_ENABLED` and
is never linked to from inside the bot's premium-purchase flow (the bot
only ever offers Telegram Stars or wallet payment -- see
app/bot/handlers/premium.py).
"""
