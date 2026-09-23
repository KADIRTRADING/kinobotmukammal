"""Payment provider abstraction.

`app.payments.base.PaymentProvider` is the interface every adapter
implements. `app.payments.registry.PaymentRegistry` exposes only the
providers that are BOTH feature-flagged on in config AND have their
required credentials present -- an adapter that is "configured" in code but
missing real secrets stays reported as disabled, never silently falls back
to a fake/live-looking state.
"""
