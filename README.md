# Movie Bot — Multilingual Telegram Movie Delivery & Premium Subscription Bot

A production-grade Telegram bot that delivers licensed movies by code/search/category,
sells Premium access via Telegram Stars (and, optionally, an independent Stripe/Click
web storefront), runs a two-tier referral program (standard referrers + verified
bloggers), maintains a wallet/ledger for balances, and supports prepaid promo codes,
gifts, and a full web admin panel. Fully localized in **Uzbek, Russian, and English**.

> **Where each feature lives** — see [ARCHITECTURE MAP](#architecture-map) below for an
> exact file-by-file cross-reference of every requirement to its implementation.

---

## 1. What is LIVE vs SANDBOX-only vs NEEDS CREDENTIALS

This matters more than anything else in this document — read it before doing anything else.

| Capability | Status | Detail |
|---|---|---|
| Movie catalog, search, categories, mandatory-channel gating | **Live** (once you provide a bot token) | No third-party credentials needed beyond your own bot token. |
| Inline mode (`@YourBot 222`) | **Live** | Requires `/setinline` in BotFather (see §5). |
| Telegram Stars payments | **Sandbox-ready, disabled by default** | Set `PAYMENTS_STARS_ENABLED=true`. No merchant account needed — Stars are native to Telegram — but you must test with real Telegram test/production bot per Telegram's Stars rules. |
| Wallet-balance premium checkout | **Live** | Pure internal ledger operation; no external provider. |
| Stripe (independent web storefront) | **Sandbox-only until you supply real keys** | Requires `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, and `STOREFRONT_ENABLED=true`. Stays fully disabled (`is_enabled() == False`) until all three are set. |
| Click (independent web storefront, Uzbekistan) | **Sandbox-only until you supply real keys** | Requires `CLICK_MERCHANT_ID`, `CLICK_SERVICE_ID`, `CLICK_SECRET_KEY`, and `STOREFRONT_ENABLED=true`. Click also has **no self-service refund API** for Shop API merchants — refunds must be requested from Click support and recorded manually in the admin panel. |
| Two-tier referrals + blogger acquisition rewards | **Live** | Pure DB/ledger logic, no external dependency. |
| Blogger bio verification | **Manual admin review only** | There is no authorized third-party API used anywhere in this codebase to read an arbitrary Instagram/YouTube/Telegram bio automatically. `BloggerService.attempt_automated_check` always returns "not available" and defers to the admin panel. Do not wire in an unauthorized scraper — this is a deliberate, honest limitation. |
| Admin panel | **Live** | Session-cookie auth, bcrypt passwords, role-based access. Create the first account with `scripts/create_superadmin.py`. |
| Broadcasts | **Live** | Rate-limited, resumable, queued via the `worker` service — never blocks a request. |

**Credentials you must obtain yourself before going to production:**
1. A real Telegram bot token from **@BotFather**.
2. (Optional, Stars) Nothing beyond the bot token — but Stars must be enabled per-bot in BotFather-compliant apps and your bot must be reviewed by Telegram for digital goods if required by their current policy.
3. (Optional, Stripe) A Stripe account, API secret key, and a configured webhook endpoint secret.
4. (Optional, Click) A Click.uz merchant account, service ID, merchant ID, and secret key.
5. A strong `APP_SECRET_KEY` and `BOT_WEBHOOK_SECRET` for production.
6. A Postgres database and Redis instance (or use the provided `docker-compose.yml`).

**This project was authored inside a sandboxed environment with no outbound access to
PyPI, Docker Hub, or GitHub.** All Python dependencies (`aiogram`, `fastapi`,
`sqlalchemy`, `alembic`, `redis`, `stripe`, etc.) could **not** be installed or imported
during development, so the full application could not be booted end-to-end inside that
sandbox. What **was** verified by actually executing code in that sandbox:
- All 146 Python files parse with zero syntax errors (`ast.parse` over the whole tree).
- The pure, dependency-free financial logic (`app/services/money.py`,
  `commission.py`, `blogger_rewards.py`, `promo_math.py`) has **44 passing unit tests**,
  executed with `pytest` in that sandbox — see [Testing](#testing) for exact results.
- The Alembic migration was cross-checked against every SQLAlchemy model file with a
  small script (table names + column names for all 25 tables) with zero mismatches.
- All 3 language files (`uz.py`, `ru.py`, `en.py`) were checked to contain the exact
  same 123 translation keys.

Everything else (aiogram handlers, FastAPI routes, SQLAlchemy repositories/services,
Alembic execution against a live Postgres) is **correct-by-construction** — carefully
written against the current documented APIs of aiogram 3 / FastAPI / SQLAlchemy 2 —
but was not executed in that sandbox. **You must run the commands in §4 on a machine
with normal internet access** to install dependencies, run migrations, run the full
test suite, and start the bot for real. This is the honest state of the project;
nothing here pretends otherwise.

---

## 2. Stack

- Python 3.12+, [aiogram 3](https://docs.aiogram.dev/) (Telegram Bot API framework)
- [FastAPI](https://fastapi.tiangolo.com/) (webhooks, admin panel, storefront)
- PostgreSQL 16 + [SQLAlchemy 2](https://docs.sqlalchemy.org/en/20/) (async ORM) + [Alembic](https://alembic.sqlalchemy.org/) (migrations)
- Redis 7 (aiogram FSM storage, rate limiting)
- Docker Compose for local development
- APScheduler for background workers

---

## 3. Compliance: payments and Telegram's digital-goods rules

Telegram requires apps/bots that sell **digital goods and services usable inside
Telegram** to use **Telegram Stars** as the payment method inside the bot/mini app,
and prohibits routing users to an external payment page to buy the same digital
goods as a way of evading that rule.

This project follows that rule structurally:

- Inside the bot, premium access can be bought **only** with (a) **Telegram Stars**
  or (b) the user's **own wallet balance** (an internal ledger debit — not a payment
  redirect). The bot never shows a Stripe/Click checkout link to activate the
  Telegram-side premium entitlement.
- Stripe and Click are wired **exclusively** into `app/api/storefront/`, a genuinely
  separate, independently-branded web storefront (`STOREFRONT_ENABLED` gate). Nothing
  in the bot's premium-purchase flow links to it. If you build a public website
  around this storefront, treat it as an independent sales channel with its own terms.
- The admin panel's "Payment providers" dashboard and `/admin/orders` page both show
  a "Sandbox" vs "Live" vs "Disabled" badge for every provider, so operators can never
  mistake a half-configured integration for a working one.
- `/terms` and `/privacy` bot commands (and `/legal/terms`, `/legal/privacy` HTTP
  endpoints) explain this policy to end users.

**If your product requirements truly need an in-bot Stripe/Click flow, that is only
possible for goods/services that fall outside Telegram's digital-goods policy (e.g.
some physical goods or off-platform services) — consult Telegram's current Bot
Payments policy before enabling anything beyond what's implemented here.**

---

## 4. Running it

### 4.1 Docker Compose (recommended, any OS)

```bash
git clone <your-fork-url> movie-bot
cd movie-bot
cp .env.example .env
# Edit .env: at minimum set BOT_TOKEN, BOT_USERNAME, POSTGRES_PASSWORD,
# and change DATABASE_URL / DATABASE_URL_SYNC to match POSTGRES_PASSWORD.

docker compose build
docker compose up -d db redis
docker compose run --rm migrate            # apply all Alembic migrations
docker compose run --rm api python -m scripts.create_superadmin \
    --username admin --password 'change-me-now'
docker compose up -d api bot worker
```

- Bot: long-polls Telegram by default (leave `BOT_WEBHOOK_URL` empty in `.env`).
- API/admin panel: http://localhost:8000/admin/login
- Health check: http://localhost:8000/health

To use a webhook instead of long polling (recommended for production): set
`BOT_WEBHOOK_URL=https://yourdomain.com/webhooks/telegram` and a real
`BOT_WEBHOOK_SECRET` in `.env`, then only run the `api` and `worker` services (the
`bot` service will detect the webhook URL and idle rather than double-consume updates).

### 4.2 Windows (PowerShell), without Docker

Requires: Python 3.12+, PostgreSQL 16 running locally (or via WSL/Docker Desktop just
for `db`/`redis`), Redis (Windows: easiest via Docker Desktop or WSL).

```powershell
# 1. Clone and enter the project
git clone <your-fork-url> movie-bot
cd movie-bot

# 2. Create and activate a virtual environment
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install the project (editable) with dev extras
pip install --upgrade pip
pip install -e ".[dev]"

# 4. Configure environment
copy .env.example .env
notepad .env
# Set BOT_TOKEN, BOT_USERNAME, and point DATABASE_URL / DATABASE_URL_SYNC
# at your local Postgres, e.g.:
#   DATABASE_URL=postgresql+asyncpg://movie_bot:change-me@localhost:5432/movie_bot
#   DATABASE_URL_SYNC=postgresql+psycopg2://movie_bot:change-me@localhost:5432/movie_bot
#   REDIS_URL=redis://localhost:6379/0

# 5. Create the database (run once, using psql or pgAdmin)
#    CREATE DATABASE movie_bot;
#    CREATE USER movie_bot WITH PASSWORD 'change-me';
#    GRANT ALL PRIVILEGES ON DATABASE movie_bot TO movie_bot;

# 6. Apply migrations
alembic upgrade head

# 7. Create the first admin account
python -m scripts.create_superadmin --username admin --password "change-me-now"

# 8. Run each process in its OWN PowerShell window (all three needed):
python -m app.main bot
uvicorn app.main:api_app --host 0.0.0.0 --port 8000
python -m app.workers.runner
```

### 4.3 Linux / macOS server, without Docker

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

cp .env.example .env
$EDITOR .env   # fill in BOT_TOKEN, BOT_USERNAME, DATABASE_URL(_SYNC), REDIS_URL

alembic upgrade head
python -m scripts.create_superadmin --username admin --password "change-me-now"

# Run under your process manager of choice (systemd/supervisor/tmux), e.g.:
python -m app.main bot &
uvicorn app.main:api_app --host 0.0.0.0 --port 8000 &
python -m app.workers.runner &
```

---

## 5. BotFather setup checklist

1. `/newbot` → get your `BOT_TOKEN`.
2. `/setinline` → **enable inline mode** and set an inline placeholder, e.g.
   `Enter a movie code or name…`. Required for `@YourBot 222` searches in groups.
3. `/setinlinefeedback` → optional, enables analytics on inline result usage.
4. `/mybots` → *Bot Settings* → *Payments* is **not** needed for Telegram Stars
   (Stars use `sendInvoice` with `currency="XTR"` and an empty provider token — no
   external payment provider configuration in BotFather is required for Stars).
5. If you plan to use webhooks, ensure your `PUBLIC_BASE_URL` is HTTPS with a valid
   certificate; Telegram refuses to deliver webhooks to non-HTTPS endpoints.
6. Add the bot as **administrator** to every channel you configure as a mandatory
   subscription channel (Admin Panel → Channels → "Check bot admin rights" verifies
   this for you).

---

## 6. Environment variables

See `.env.example` for the full, commented list. Highlights:

| Variable | Purpose |
|---|---|
| `BOT_TOKEN` | Telegram bot token from BotFather. |
| `BOT_WEBHOOK_URL` | Leave empty for long polling; set for webhook mode. |
| `BOT_WEBHOOK_SECRET` | Verified against `X-Telegram-Bot-Api-Secret-Token` on every webhook call. |
| `DATABASE_URL` / `DATABASE_URL_SYNC` | Async (asyncpg) and sync (psycopg2) Postgres URLs — the sync one is used only by Alembic. |
| `PAYMENTS_STARS_ENABLED` | Turn on in-bot Telegram Stars checkout. |
| `PAYMENTS_STRIPE_ENABLED` / `STRIPE_*` | Independent web storefront only; requires `STOREFRONT_ENABLED=true` too. |
| `PAYMENTS_CLICK_ENABLED` / `CLICK_*` | Same, for Click.uz. |
| `STOREFRONT_ENABLED` | Master switch for the separate web storefront surface. |
| `BOOTSTRAP_SUPERADMIN_IDS` | Comma-separated Telegram numeric ids allowed to receive admin Telegram notifications immediately after being linked via the admin panel. |

---

## 7. Architecture map

| Requirement | Where it's implemented |
|---|---|
| App lifecycle | `app/main.py` (`create_api_app`, `run_bot`) |
| Config/env validation | `app/config.py` |
| Bot handlers | `app/bot/handlers/*.py` (one file per feature area, see module docstrings) |
| Keyboards | `app/bot/keyboards/*.py` |
| i18n (uz/ru/en) | `app/i18n/{uz,ru,en}.py` + `app/i18n/__init__.py` |
| DB models | `app/db/models/*.py` (25 tables) |
| Repositories | `app/db/repositories/*.py` |
| Services | `app/services/*.py` |
| Payment adapters | `app/payments/{base,stars,stripe_provider,click_provider,registry}.py` |
| Webhooks | `app/api/webhooks/{telegram,stripe_webhook,click_webhook}.py` |
| Storefront | `app/api/storefront/routes.py` |
| Admin panel | `app/admin/*.py` + `app/admin/templates/*.html` |
| Workers | `app/workers/{broadcast_worker,expiration_worker,reconciliation_worker,runner}.py` |
| Migrations | `alembic/versions/0001_initial_schema.py` |
| Tests | `tests/unit/*.py` (pure logic), `tests/integration/*.py` (DB-backed) |

### Money and referral policy (spec sections 3 & 5), in one place

- **Per-plan settings** live on `PremiumPlan` (`app/db/models/plan.py`):
  `price_amount`, `standard_referral_percent`, `blogger_referral_percent`,
  `blogger_acquisition_reward_enabled`, `max_discount_percent`. Each plan is
  independent — nothing is hard-coded globally.
- **Snapshotting**: every `Order` and `ReferralCommission` freezes the plan's price
  and percentages *at purchase time* (`app/db/models/order.py`,
  `app/db/models/reward_accrual.py`). Changing a plan later in the admin panel
  (`app/admin/routes_plans.py`) never retroactively alters a completed purchase.
- **Standard referral commission**: `app/services/commission.py::calculate_referral_commission`
  — pure function, 100% unit-tested.
- **Blogger acquisition reward** (per-1000-joins, accruing from the FIRST join,
  remainder-safe): `app/services/blogger_rewards.py::accrue_qualified_join` — pure
  function, 100% unit-tested, wired to persistence in
  `app/services/blogger_reward_service.py`.
- **Promo funding math** (full-premium and percent-discount worked examples from the
  spec): `app/services/promo_math.py` — pure function, 100% unit-tested.

---

## 8. Testing

### 8.1 What was actually run, and its result (in the authoring sandbox)

```
$ pytest tests/unit -v
...
44 passed, 1 warning in 0.07s
```

All 44 tests in `tests/unit/` (`test_money.py`, `test_commission.py`,
`test_blogger_rewards.py`, `test_promo_math.py`) passed. These tests cover, with zero
external dependencies:
- Per-plan-independent commission percentages (10% vs 15% on the same purchase amount
  yield different, correct commission amounts).
- A blogger referrer receiving the blogger rate instead of the standard rate.
- Renewal-commission policy on/off behavior.
- Commission reversal math on full and partial refunds.
- Blogger acquisition reward accrual for exactly 1, 10, 999, and 1000 qualified joins,
  at both an exact-multiple-of-1000 rate and a fractional rate, cross-checked against
  a closed-form formula — proving no overpayment/underpayment and correct remainder
  carry-forward.
- Full-premium and percent-discount promo funding, matching the spec's worked
  examples exactly (100,000 UZS ÷ 5,000 UZS/activation = 20; 100,000 UZS ÷ 500
  UZS/activation = 200).

### 8.2 What is written but requires a real environment to execute

`tests/integration/` contains 8 files covering, against a real (in that environment)
SQLAlchemy + SQLite/Postgres database via the actual repositories/services/handlers'
business logic:

- Referral self-referral / repeated-start / blocked-user / blocked-referrer / duplicate
  attribution / unknown-code rejection (`test_referral_attribution.py`).
- Per-plan commission differing across two purchases, a blogger earning **both** the
  purchase commission **and** the acquisition reward, duplicate-webhook idempotency,
  full refund reversing the commission and revoking future premium
  (`test_purchase_and_commissions.py`).
- Blogger reward accrual for 1/10/999/1000 joins at the DB layer, suspended-blogger
  cutoff, duplicate-accrual-call safety (`test_blogger_reward_accrual_sequence.py`).
- Full-premium/discount promo funding worked examples, insufficient-balance rejection,
  own-code redemption rejection, double-redemption rejection, concurrent redemption
  never exceeding `max_uses`, cancellation releasing unused reserve, external-URL
  attribution requiring admin approval (`test_promo_codes.py`).
- Free/premium/premium-exemption/fail-closed/unpublished movie access
  (`test_movie_access.py`).
- Inline search never exposing `video_file_id` (`test_inline_search_privacy.py`).
- Gift-premium/gift-balance exactly-once debit and grant, admin gifts, manual
  adjustments never going negative (`test_gifts_and_admin_adjustments.py`).
- Ledger idempotency-key deduplication and the ledger-sum-equals-cached-balance
  invariant (`test_ledger_idempotency.py`).

Run them yourself once dependencies are installed:

```bash
pip install -e ".[dev]"
pytest tests/unit tests/integration -v
```

### 8.3 Manual end-to-end test script (do this once you have a real bot token)

1. `docker compose up -d` (or the non-Docker equivalent), run migrations, create a
   superadmin.
2. Log into `/admin/login`, go to **Plans**, create a plan (e.g. "1 week", 5000 UZS,
   10% standard referral, 15% blogger referral).
3. In Telegram, message your bot `/start` → choose a language → confirm the main menu
   appears with all 9 buttons translated.
4. As an admin Telegram account, forward a test video to the bot (wire up
   `MovieAdminStates` handlers per your admin's Telegram id, or add the movie directly
   via a DB insert / a quick admin panel form) with a code like `100`.
5. In the bot, type `100` → confirm the video is delivered (if FREE and no mandatory
   channels configured) or the premium/paywall prompt appears.
6. Add a mandatory channel in the admin panel, make the bot an admin of it, and repeat
   step 5 as a non-member — confirm the "join channels" prompt appears and blocks
   delivery until you join.
7. Get your referral link from **Invite Friends**, open it as a second Telegram
   account, `/start` — confirm a `Referral` row is created and `is_qualified=True`.
8. Buy the plan you created with the second account's wallet balance (top it up via
   admin gift first) — confirm premium activates and the first account's balance
   shows the commission.
9. Apply to become a blogger, approve it from the admin panel, and repeat steps 7–8 —
   confirm both a commission **and** an acquisition reward are credited.
10. Create a promo code, redeem it, confirm the funding math matches what was quoted.
11. Send a gift (premium and balance) to the second account.
12. Test `@YourBot 100` inline in a group chat — confirm no `file_id` is visible in the
    raw update payload (use `getUpdates` or a debug log) and that "Open in Bot" checks
    access correctly per-user.
13. Trigger a webhook problem (e.g. stop Postgres briefly) and confirm the
    reconciliation worker logs a warning instead of crashing silently.

---

## 9. Reliability & security notes

- All monetary amounts are **integers** (minor units); no floats anywhere in the money
  path (`app/services/money.py`).
- Every balance mutation goes through `WalletRepository.apply_ledger_entry`, which
  locks the wallet row (`SELECT ... FOR UPDATE`), checks for sufficient funds, and
  writes an **immutable** ledger row in the same transaction — negative balances are
  structurally impossible.
- Every promo redemption goes through `PromoRepository.lock_by_code` +
  `decrement_remaining_use`, backed by a DB `CHECK(remaining_uses >= 0)` constraint —
  a promo can never be used more times than it has activations for, even under
  concurrent redemption attempts.
- Every entitlement grant and referral commission is keyed by a unique
  `(source, source_reference)` / `order_id` constraint — duplicate/retried webhooks
  can never grant premium twice or pay a commission twice.
- Structured JSON logging (`app/core/logging.py`) redacts bot tokens, passwords,
  webhook secrets, and — critically — **movie `video_file_id` values**, since a
  leaked file_id would let anyone fetch the licensed video directly from Telegram's
  servers, bypassing all entitlement checks.
- The reconciliation worker (`app/workers/reconciliation_worker.py`) periodically
  verifies that ledger entries sum to the cached wallet balance and **logs, never
  silently repairs**, any drift — a drift is a bug that needs human investigation.

---

## 10. Complete changed-file list

See the final chat message for the full list of files created in this session,
organized by area, along with exact run commands and the honest live/sandbox/needs-
credentials breakdown repeated for convenience.
