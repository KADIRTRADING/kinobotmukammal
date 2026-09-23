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
