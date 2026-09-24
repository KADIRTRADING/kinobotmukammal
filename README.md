# Movie Bot — Multilingual Telegram Movie Delivery & Premium Subscription Bot

A production-grade Telegram bot that delivers licensed movies by code/search/category,
sells Premium access via Telegram Stars (and, optionally, an independent Stripe/Click
web storefront), runs a two-tier referral program (standard referrers + verified
bloggers), maintains a wallet/ledger for balances, and supports prepaid promo codes,
gifts, and a **full in-Telegram admin panel** (button-driven, no separate login,
gated purely by numeric Telegram IDs — see [§7](#7-in-telegram-admin-panel)).
Fully localized in **Uzbek, Russian, and English**.

> **Where each feature lives** — see [ARCHITECTURE MAP](#8-architecture-map) below for an
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
| **In-Telegram admin panel** | **Live** (once you set `TELEGRAM_SUPERADMIN_IDS`) | No login, no password, no `scripts/create_superadmin.py` step required — just add your numeric Telegram ID to `TELEGRAM_SUPERADMIN_IDS` and message the bot. See [§7](#7-in-telegram-admin-panel). |
| Legacy web admin panel | **Disabled by default** | Session-cookie auth, bcrypt passwords, role-based access. Set `WEB_ADMIN_ENABLED=true` to re-enable it; create the first account with `scripts/create_superadmin.py`. Kept only for anyone who still wants a browser-based view — every feature is also available from Telegram. |
| Broadcasts | **Live** | Rate-limited, resumable, queued via the `worker` service — never blocks a request. |

**Credentials you must obtain yourself before going to production:**
1. A real Telegram bot token from **@BotFather**.
2. (Optional, Stars) Nothing beyond the bot token — but Stars must be enabled per-bot in BotFather-compliant apps and your bot must be reviewed by Telegram for digital goods if required by their current policy.
3. (Optional, Stripe) A Stripe account, API secret key, and a configured webhook endpoint secret.
4. (Optional, Click) A Click.uz merchant account, service ID, merchant ID, and secret key.
5. A strong `APP_SECRET_KEY` and `BOT_WEBHOOK_SECRET` for production.
6. A Postgres database and Redis instance (or use the provided `docker-compose.yml`).
7. Your own numeric Telegram user ID (get it from **@userinfobot** or similar) to put
   in `TELEGRAM_SUPERADMIN_IDS` — this is what makes the in-Telegram admin panel
   appear for you and nobody else.

**This project was authored inside a sandboxed environment with no outbound access to
PyPI, Docker Hub, or GitHub.** All Python dependencies (`aiogram`, `fastapi`,
`sqlalchemy`, `alembic`, `redis`, `stripe`, `bcrypt`, etc.) could **not** be installed
or imported during development, so the full application could not be booted
end-to-end inside that sandbox. What **was** verified by actually executing code in
that sandbox:
- All 183 Python files under `app/` and `tests/` parse with zero syntax errors
  (`ast.parse` over the whole tree).
- The pure, dependency-free financial and authorization logic (`app/services/money.py`,
  `commission.py`, `blogger_rewards.py`, `promo_math.py`, `app/core/admin_access.py`)
  has **58 passing + 1 skipped unit tests**, executed with `pytest` in that sandbox —
  see [Testing](#9-testing) for exact results.
- The Alembic migration was cross-checked against every SQLAlchemy model file with a
  small script (table names + column names for all 25 tables) with zero mismatches.
- All 3 language files (`uz.py`, `ru.py`, `en.py`) contain the exact same 393
  translation keys with identical `{placeholder}` names (permanently enforced by
  `tests/unit/test_i18n_parity.py`).
- `ruff check` and `black --check` pass with zero issues on every file in the repo
  that this project's sessions touched.
- `mypy` was run against every new/changed file; the two real bugs it caught (both in
  the in-Telegram admin panel's code) were fixed — see §9.3.

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
- The legacy web admin panel's "Payment providers" dashboard and `/admin/orders` page
  (when `WEB_ADMIN_ENABLED=true`) show a "Sandbox" vs "Live" vs "Disabled" badge for
  every provider, so operators can never mistake a half-configured integration for a
  working one. The in-Telegram admin panel's Orders section (§7) shows the same
  underlying order/provider-event data.
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
# TELEGRAM_SUPERADMIN_IDS (your own numeric Telegram ID -- this is what makes the
# in-Telegram admin panel appear for you), and change DATABASE_URL / DATABASE_URL_SYNC
# to match POSTGRES_PASSWORD.

docker compose build
docker compose up -d db redis
docker compose run --rm migrate            # apply all Alembic migrations
docker compose up -d api bot worker
```

The in-Telegram admin panel needs **no** extra setup step beyond `TELEGRAM_SUPERADMIN_IDS`
in `.env` — message the bot from that account and the "🛠 Admin panel" button appears.
`scripts/create_superadmin.py` is only needed if you also set `WEB_ADMIN_ENABLED=true`
to use the legacy browser-based panel.

**Rebuilding after a code change** (e.g. after pulling the admin-panel update):

```bash
docker compose build
docker compose up -d --force-recreate api bot worker
```

Only `api`, `bot`, and `worker` need to be recreated — `db`, `redis`, and `migrate`
(a one-shot job) do not need to be re-run unless the schema or infrastructure config
changed. If a new Alembic migration was added, run `docker compose run --rm migrate`
again before recreating `api`/`bot`/`worker`.

- Bot: long-polls Telegram by default (leave `BOT_WEBHOOK_URL` empty in `.env`).
- Admin panel: just message the bot on Telegram from an ID listed in
  `TELEGRAM_SUPERADMIN_IDS` — no URL to visit.
- Legacy web admin panel (only if `WEB_ADMIN_ENABLED=true`): http://localhost:8000/admin/login
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

# 7. Set TELEGRAM_SUPERADMIN_IDS in .env to your own numeric Telegram ID -- this is
#    all that's needed to unlock the in-Telegram admin panel. The step below is only
#    needed if you ALSO want the legacy browser-based panel (WEB_ADMIN_ENABLED=true):
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
# Set TELEGRAM_SUPERADMIN_IDS in .env to unlock the in-Telegram admin panel -- no
# further step is required for it. Only run this next line if WEB_ADMIN_ENABLED=true:
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
   subscription channel (in-Telegram Admin panel → 📡 Channels → "Verify bot admin
   rights" checks this live via the Bot API for you — it never fakes success).

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
| `TELEGRAM_SUPERADMIN_IDS` | **Comma-separated numeric Telegram user IDs** (e.g. `123456789,987654321`) that are allowed to see and use the in-Telegram admin panel. This is the *entire* identity source for Telegram-native admin access — no DB row, no username/password. Malformed entries are silently skipped rather than crashing the whole allowlist; in production, at least one valid ID is required (`Settings.validate_for_production` will refuse to start otherwise). |
| `WEB_ADMIN_ENABLED` | `false` by default. Set to `true` only if you also want the legacy browser-based `/admin/*` panel mounted (requires running `scripts/create_superadmin.py` once to create a login). Telegram/Stripe/Click webhooks and the storefront are **never** gated by this flag — only the browser admin UI is. |

---

## 7. In-Telegram admin panel

The web admin panel described in earlier revisions of this project has been
**replaced** as the primary admin workflow by a full admin panel that lives entirely
inside Telegram — no browser, no separate login, no `scripts/create_superadmin.py`
step required to activate it.

### How access works

1. Add your numeric Telegram user ID to `TELEGRAM_SUPERADMIN_IDS` in `.env`
   (comma-separated for multiple admins, e.g. `TELEGRAM_SUPERADMIN_IDS=111111111,222222222`).
2. Restart the `bot` service.
3. Send `/start` to the bot from that Telegram account. A **"🛠 Admin panel"** button
   appears in the main menu — only for allow-listed IDs. Ordinary users never see it.
4. Tap the button to open the interactive admin menu (all buttons, no typing required
   except where a value must be entered, e.g. a movie code or a ban reason).

There is **no** DB-backed `Admin` account, username, or password involved in this
flow. Every admin action is authorized **server-side, on every single message and
button press** — never inferred from a button being visible, never trusted from a
client-supplied ID. The check (`app/core/admin_access.py::is_authorized_admin`)
rejects a request if:
- the Telegram user ID is missing, or not in `TELEGRAM_SUPERADMIN_IDS`;
- the chat is not a private 1:1 chat with the bot (i.e. a group/channel is always
  rejected, even if the sender's ID is allow-listed);
- the message was forwarded from elsewhere (checked via `forward_origin` on Bot API
  7.0+, and the legacy `forward_date`/`forward_from`/`forward_from_chat` fields for
  older aiogram/Bot API combinations) — this stops someone from forwarding an admin's
  message to trick a naive check.

This logic is applied as a single aiogram `Router`-level filter
(`app/bot/filters/admin_filter.py::AdminAccessFilter`) attached to the parent admin
router **before** any of its 12 sub-routers are included, so it gates the entire
admin subtree — the "🛠 Admin panel" button being shown is a UI convenience only,
never the actual security boundary.

### Admin panel sections

| Section | What it does | Key files |
|---|---|---|
| Dashboard | Total/active/premium users, movie/view counts, orders, revenue by currency, pending-review count, recent errors (real signal: failed orders + provider-event errors in the last 24h, never fabricated). | `app/bot/handlers/admin/dashboard.py`, `app/services/statistics_service.py` |
| Movies | Upload (video → code → titles/descriptions per language → category → access type → poster), preview, publish, archive, edit any field, replace video/poster, delete (**two-step confirmation**), search by code across every state including drafts. | `app/bot/handlers/admin/movies.py` |
| Categories | Create, edit, reorder (up/down), enable/disable. | `app/bot/handlers/admin/categories.py` |
| Mandatory channels | Add, **live** bot-admin-rights verification (`bot.get_chat_member`, never faked), enable/disable, remove. | `app/bot/handlers/admin/channels.py` |
| Users | Search by ID/username/name, view profile + balances + order history, block/unblock (reason required), grant/revoke premium, gift balance (reason required). | `app/bot/handlers/admin/users.py` |
| Premium plans | Create/edit price, duration, per-plan standard/blogger referral rates, max discount %, toggle active. | `app/bot/handlers/admin/plans.py` |
| Promo codes | Platform-funded admin-issued codes, pending-moderation queue for user/blogger codes with an external-link attribution, approve/reject (releases the issuer's reserved funds on reject), cancel, redemption counts. | `app/bot/handlers/admin/promos.py` |
| Bloggers & referrals | Approve/reject applications (reason required, applicant notified), suspend/reactivate active bloggers, list suspicious referrals for manual review, set the global acquisition reward rate. | `app/bot/handlers/admin/bloggers.py` |
| Support | List open tickets, read the thread, reply (user notified), close. | `app/bot/handlers/admin/support.py` |
| Broadcasts | Compose per-language text + optional photo, target all/premium/free users, preview the real recipient count, confirm, then **queue** for the `worker` service to send (never sent inline from the handler) — live progress and cancel. | `app/bot/handlers/admin/broadcasts.py`, `app/services/broadcast_service.py` |
| Orders & payments | List/filter by status, view raw provider events, **refund only** (never mark-as-paid — see below). | `app/bot/handlers/admin/orders.py` |
| Settings & audit | Toggle safe global flags (renewal commissions, promo stacking), set the blogger reward rate, view the recent audit log. | `app/bot/handlers/admin/settings.py` |

Every mutation reuses the **exact same service layer** the rest of the bot uses
(`GiftService`, `EntitlementService`, `WalletService`, `PromoService`,
`BloggerService`, `BroadcastService`, `PurchaseService`, `SettingsService`) — nothing
in the admin panel re-implements business logic that already exists elsewhere.

### Orders/payments safety guarantee

`app/bot/handlers/admin/orders.py` can **only** call `PurchaseService.refund_order`,
and only on an order whose status is already `PAID` (checked twice: once when the
refund is initiated, again right before the confirm button is honored, in case the
order's state changed in between). `PurchaseService.confirm_payment` — the *only*
method anywhere in the codebase that ever sets an order's status to `PAID` — is never
imported by the admin orders handler. `tests/integration/test_admin_orders_refund_safety.py`
enforces this with both a behavioral test (refunding a `PENDING` order is a no-op)
and a static AST check that `confirm_payment`/`mark_paid` are never called from that
file.

### Destructive/financial actions always require confirmation + an audit entry

Deleting a movie, removing a mandatory channel, blocking a user, granting/revoking
premium, gifting balance, refunding an order, and rejecting a promo/blogger
application all require an explicit confirm step (and, where the spec calls for it,
a mandatory reason) and are recorded via
`app/bot/handlers/admin/audit_helper.py::record_admin_action` into the existing
`AuditLog` table (`app/db/repositories/admin_repo.py::AuditLogRepository`). Since
there is no `Admin` DB row for a Telegram-native admin, `AuditLog.admin_id` is left
`NULL` and `AuditLog.admin_username` is set to `"tg:<telegram_id>"` — every action is
still traceable to a specific real Telegram account.

---

## 8. Architecture map

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
| **In-Telegram admin panel** | `app/bot/handlers/admin/*.py` (12 section handlers + `__init__.py`/`audit_helper.py`), `app/bot/keyboards/admin_*.py`, `app/core/admin_access.py`, `app/bot/filters/admin_filter.py` |
| Legacy web admin panel (disabled by default) | `app/admin/*.py` + `app/admin/templates/*.html`, mounted only when `WEB_ADMIN_ENABLED=true` |
| Workers | `app/workers/{broadcast_worker,expiration_worker,reconciliation_worker,runner}.py` |
| Migrations | `alembic/versions/0001_initial_schema.py` |
| Tests | `tests/unit/*.py` (pure logic + admin-access + i18n-parity), `tests/integration/*.py` (DB-backed, including 9 admin-panel-focused files) |

### Money and referral policy (spec sections 3 & 5), in one place

- **Per-plan settings** live on `PremiumPlan` (`app/db/models/plan.py`):
  `price_amount`, `standard_referral_percent`, `blogger_referral_percent`,
  `blogger_acquisition_reward_enabled`, `max_discount_percent`. Each plan is
  independent — nothing is hard-coded globally.
- **Snapshotting**: every `Order` and `ReferralCommission` freezes the plan's price
  and percentages *at purchase time* (`app/db/models/order.py`,
  `app/db/models/reward_accrual.py`). Changing a plan later — whether from the
  in-Telegram admin panel (`app/bot/handlers/admin/plans.py`) or the legacy web panel
  (`app/admin/routes_plans.py`) — never retroactively alters a completed purchase.
- **Standard referral commission**: `app/services/commission.py::calculate_referral_commission`
  — pure function, 100% unit-tested.
- **Blogger acquisition reward** (per-1000-joins, accruing from the FIRST join,
  remainder-safe): `app/services/blogger_rewards.py::accrue_qualified_join` — pure
  function, 100% unit-tested, wired to persistence in
  `app/services/blogger_reward_service.py`.
- **Promo funding math** (full-premium and percent-discount worked examples from the
  spec): `app/services/promo_math.py` — pure function, 100% unit-tested.

---

## 9. Testing

### 9.1 What was actually run, and its result (in the authoring sandbox)

The authoring sandbox has **no outbound network access** (PyPI/Docker Hub/GitHub are
all unreachable), so `aiogram`, `fastapi`, `sqlalchemy`, `pydantic`, `redis`,
`alembic`, `bcrypt`, etc. could never be installed there — only `pytest`, `ruff`,
`black`, and `mypy` (preinstalled) were available. Everything below marked "sandbox
result" was actually executed; everything marked "requires a real environment" was
written and statically verified (AST parsing + hand-written cross-reference scripts
matching every i18n key / FSM state / callback_data against its definition), but
**not run**, in that sandbox.

```
$ pytest tests/unit -v
...
58 passed, 1 skipped in 0.06s
```

`tests/unit/` (pure Python, zero third-party dependencies) covers:
- `test_money.py`, `test_commission.py`, `test_blogger_rewards.py`, `test_promo_math.py`
  — per-plan commission math, blogger vs. standard rates, refund reversal math,
  acquisition-reward accrual/remainder-carry-forward, promo funding worked examples.
- `test_admin_access.py` (12 tests, 11 pass + 1 skip) — the pure authorization logic
  behind the in-Telegram admin panel: ID allow-list membership, group/forwarded-message
  rejection, and the one skipped test (`test_real_settings_parses_allowlist_identically_to_fake`)
  which needs `pydantic` (unavailable in the sandbox) to construct a real `Settings`
  object — everything else about the same logic is covered by the pydantic-free fake.
- `test_i18n_parity.py` (3 tests) — asserts `uz.py`/`ru.py`/`en.py` have the exact
  same 393-key set and identical `{placeholder}` names per key, as a permanent
  regression guard.

### 9.2 What is written but requires a real environment to execute

`tests/integration/` (DB-backed, needs `sqlalchemy` + `aiosqlite`) has grown to 17
files. The 9 added for the in-Telegram admin panel:

- `test_admin_movie_lifecycle.py` — draft creation, publish/archive/delete lifecycle,
  admin any-state search finding drafts the public search can't see.
- `test_admin_categories_and_channels.py` — category CRUD + up/down reordering +
  enable/disable, mandatory-channel CRUD + verification-flag + hard delete.
- `test_admin_users_and_audit.py` — block/unblock, admin grant/revoke premium and
  gift balance (reusing `GiftService`/`EntitlementService`), each with an audit-log
  entry assertion (`admin_id IS NULL`, `admin_username == "tg:<id>"`).
- `test_admin_plans.py` — plan CRUD, independent field edits, active/inactive listing.
- `test_admin_promo_moderation.py` — admin-issued codes are platform-funded (no wallet
  reservation), the pending-moderation queue, and rejecting a pending code releasing
  the issuer's reserve.
- `test_admin_bloggers_and_referrals.py` — approve/reject applications (with reason),
  suspend/reactivate, pending-queue filtering, suspicious-referral listing.
- `test_admin_broadcasts.py` — draft → enqueue (real recipient snapshot, premium/free
  targeting, blocked-user exclusion) → cancel, and the unique-constraint dedupe
  guarantee the worker's resumability depends on.
- `test_admin_orders_refund_safety.py` — **the critical invariant**: refunding a
  `PENDING` order is a no-op, refund only succeeds after `confirm_payment`, refund is
  idempotent, and a static AST check that the admin orders handler never calls
  `confirm_payment`/`mark_paid`.
- `test_admin_settings_and_support.py` — settings toggles, audit-log recording,
  support ticket list/reply/close.

Plus the 8 pre-existing files (referral attribution, purchase/commission accrual,
blogger reward sequencing, promo code funding/redemption, movie access rules, inline
search privacy, gifts/admin adjustments, ledger idempotency).

Run them yourself once dependencies are installed:

```bash
pip install -e ".[dev]"
pytest tests/unit tests/integration -v
```

### 9.3 Static verification performed in place of execution

Since the admin-panel code (aiogram handlers/keyboards/FSM states) could not be
imported in the sandbox, the following were verified by parsing the source directly
instead of running it — each is re-runnable as a short Python script against the
repo:
- Every `t(user.language, "key", ...)` call across every admin (and modified)
  handler file resolves to a real key that exists in `app/i18n/uz.py` — 0 missing,
  checked against all 393 keys.
- `uz.py`/`ru.py`/`en.py` have byte-for-byte identical key sets (393 keys each).
- Every `AdminXxxStates.attr` / `MovieAdminStates.attr` reference matches a `State()`
  actually defined in `app/bot/states.py` — 0 mismatches.
- Every `callback_data` string produced by an `app/bot/keyboards/admin_*.py` keyboard
  has a matching `F.data == ...` / `F.data.startswith(...)` handler somewhere in
  `app/bot/handlers/admin/` — 0 orphaned callbacks across 107 distinct patterns.
- The longest realistic `callback_data` (worst case with a long numeric ID) is 54
  bytes — under Telegram's 64-byte limit.
- `ast.parse` succeeds on all 183 Python files under `app/` and `tests/`.
- `ruff check` and `black --check` pass with zero issues on every file touched this
  session.
- `mypy` was run against every new/changed file; the two real issues it caught in this
  session's code (a keyword-argument collision with `t()`'s own `language` parameter
  in `app/bot/handlers/admin/users.py`, and a missing `None`-guard on a possibly-
  deleted plan in `app/bot/handlers/admin/promos.py`) were fixed and re-verified.
  Every other `mypy` error reported anywhere in the tree belongs to files this session
  did not touch (e.g. `app/services/purchase_service.py`, `app/bot/handlers/promo.py`,
  `app/payments/stripe_provider.py`) and is pre-existing.

**What this does *not* prove**: that aiogram actually wires up the router filter the
way the code assumes, that a real Telegram update flows through
`AdminAccessFilter` correctly, or that the FSM state machine behaves as designed
under real Telegram network conditions. Those require running the bot against a
real Telegram bot token, which the sandbox this was authored in cannot do. Test with
ID `1234` (or whichever ID you configure) after deploying, per §9.4.

### 9.4 Manual verification checklist for the in-Telegram admin panel

Once deployed with `TELEGRAM_SUPERADMIN_IDS` set to your own ID:
1. `/start` from your admin account → confirm the "🛠 Admin panel" button appears.
2. `/start` from a **different** Telegram account (not in the allow-list) → confirm
   the button does **not** appear, and that manually sending the exact same
   `callback_data` (e.g. via a modified client / bot API call) as that second account
   is rejected — this is the real security boundary, not the missing button.
3. From your admin account, walk through: create a movie draft → publish it → find
   it via the "kod" search from the *user-facing* search too → archive it → delete it
   (confirm the two-step delete prompt).
4. Create a category, reorder it, disable/re-enable it.
5. Add a mandatory channel, run "verify bot admin rights" before and after actually
   promoting the bot in that channel — confirm the check reflects reality both times.
6. Search for a test user, grant them premium with a reason, confirm they receive it,
   then revoke it and confirm only *future* access is cut.
7. Create an admin promo code and redeem it as a test user.
8. Submit a blogger application from a test account, approve it as admin (with a
   reason), confirm the applicant is notified.
9. Open a support ticket as a test user, reply as admin, confirm the user receives
   the reply, then close it.
10. Compose a broadcast targeting "free users", preview the recipient count, confirm,
    and watch the live progress counters update (sent by the `worker` service, not
    inline).
11. Locate a real paid test order and refund it — confirm the refund button is only
    ever offered for `PAID` orders and that a `PENDING` order has no refund option at
    all.

### 9.5 Manual end-to-end test script for the rest of the bot (do this once you have a real bot token)

1. `docker compose up -d` (or the non-Docker equivalent), run migrations, and set
   `TELEGRAM_SUPERADMIN_IDS` to your own numeric Telegram ID.
2. From your admin Telegram account, open 🛠 Admin panel → ⭐ Plans, create a plan
   (e.g. "1 week", 5000 UZS, 10% standard referral, 15% blogger referral).
3. In Telegram, message your bot `/start` → choose a language → confirm the main menu
   appears with all buttons translated.
4. From the admin panel → 🎬 Movies → "Add movie", upload a test video and walk
   through the FSM (code, titles, category, access type, poster) with a code like
   `100`.
5. In the bot, type `100` → confirm the video is delivered (if FREE and no mandatory
   channels configured) or the premium/paywall prompt appears.
6. Add a mandatory channel from 🛠 Admin panel → 📡 Channels, make the bot an admin of
   it, run "verify bot admin rights", then repeat step 5 as a non-member — confirm the
   "join channels" prompt appears and blocks delivery until you join.
7. Get your referral link from **Invite Friends**, open it as a second Telegram
   account, `/start` — confirm a `Referral` row is created and `is_qualified=True`.
8. Buy the plan you created with the second account's wallet balance (top it up via
   admin gift first) — confirm premium activates and the first account's balance
   shows the commission.
9. Apply to become a blogger, approve it from 🛠 Admin panel → 🤝 Bloggers, and repeat
   steps 7–8 — confirm both a commission **and** an acquisition reward are credited.
10. Create a promo code, redeem it, confirm the funding math matches what was quoted.
11. Send a gift (premium and balance) to the second account.
12. Test `@YourBot 100` inline in a group chat — confirm no `file_id` is visible in the
    raw update payload (use `getUpdates` or a debug log) and that "Open in Bot" checks
    access correctly per-user.
13. Trigger a webhook problem (e.g. stop Postgres briefly) and confirm the
    reconciliation worker logs a warning instead of crashing silently.

---

## 10. Reliability & security notes

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
- Every destructive/financial in-Telegram admin action writes an `AuditLog` row
  (`app/bot/handlers/admin/audit_helper.py::record_admin_action`) with the actor's
  Telegram ID (`admin_username = "tg:<id>"`), the action, the entity, and — where
  meaningful — a before/after snapshot, viewable from Admin panel → ⚙️ Settings →
  audit log.
- Admin authorization is re-checked **server-side on every single message/callback**,
  never inferred from UI state (see [§7](#7-in-telegram-admin-panel) for the full
  threat model: group chats, forwarded messages, and non-allow-listed IDs are all
  rejected before any admin handler code runs).

---

## 11. Session change log: web admin panel → in-Telegram admin panel

This section documents the most recent body of work: replacing the web-based admin
workflow with a full in-Telegram admin panel, for anyone auditing what changed.

**New files:**
- `app/core/admin_access.py`, `app/bot/filters/admin_filter.py` — authorization core
  + aiogram adapter.
- `app/bot/handlers/admin/` (14 files: `__init__.py`, `audit_helper.py`, `root.py`,
  `dashboard.py`, and one file per section listed in [§7](#7-in-telegram-admin-panel)).
- `app/bot/keyboards/admin_common.py` + 11 per-section keyboard files.
- `tests/unit/test_admin_access.py`, `tests/unit/test_i18n_parity.py`.
- `tests/integration/test_admin_movie_lifecycle.py`,
  `test_admin_categories_and_channels.py`, `test_admin_users_and_audit.py`,
  `test_admin_plans.py`, `test_admin_promo_moderation.py`,
  `test_admin_bloggers_and_referrals.py`, `test_admin_broadcasts.py`,
  `test_admin_orders_refund_safety.py`, `test_admin_settings_and_support.py`.

**Modified files:** `app/config.py` (new `TELEGRAM_SUPERADMIN_IDS`/`WEB_ADMIN_ENABLED`,
removed the unused `BOOTSTRAP_SUPERADMIN_IDS`), `app/main.py` (web admin router
conditionally mounted), `app/bot/handlers/__init__.py` (wires the new admin router in),
`app/bot/handlers/start.py`/`premium.py` (admin-aware main menu), `app/bot/keyboards/common.py`
(`main_menu_keyboard(is_admin=...)` + `main_menu_keyboard_for_telegram_id`),
`app/bot/states.py` (9 new FSM state groups), `app/i18n/{uz,ru,en}.py` (270 new
`admin_*` keys, 393 total per language, exact parity verified),
`app/db/repositories/{catalog,user,order,promo,blogger,referral,support}_repo.py`
(admin-facing CRUD/pagination methods added, reusing the existing repository
pattern), `app/services/statistics_service.py` (dashboard metrics rewritten to use
real data), `Dockerfile` (now copies `scripts/` into the image), `pyproject.toml`
(pinned `bcrypt>=4.0.1,<4.1` alongside `passlib[bcrypt]` to avoid the
`bcrypt.__about__.__version__` `AttributeError` that bcrypt≥4.1 causes with
passlib 1.7.4).

**Docker rebuild/restart commands** (services per `docker-compose.yml`: `db`, `redis`,
`migrate`, `api`, `bot`, `worker`):

```bash
docker compose build
docker compose run --rm migrate                       # only if a migration was added
docker compose up -d --force-recreate api bot worker
```

**Honest state of this work**: every aiogram/FastAPI/SQLAlchemy file in this change
was authored and statically verified (AST parsing + custom cross-reference scripts for
i18n keys, FSM states, and `callback_data` wiring — see §9.3) in a sandbox with no
network access to install `aiogram`/`fastapi`/`sqlalchemy`/etc., so none of it could be
*executed* there. `pytest tests/unit` (58 passed, 1 skipped), `ruff check`, and
`black --check` **were** actually run and pass. `pytest tests/integration` was written
but requires a real environment (§9.2) — run it yourself with `pip install -e ".[dev]"`
before trusting this in production, and walk through §9.4's manual checklist against a
real bot token with a real `TELEGRAM_SUPERADMIN_IDS` value.
