"""Application services.

`money.py`, `commission.py`, `blogger_rewards.py`, and `promo_math.py` are
intentionally dependency-free (no SQLAlchemy, no aiogram, no I/O) so their
financial correctness can be verified with plain `pytest` in any Python
environment, independent of whether a database or Telegram credentials are
available. All other services in this package build on top of them and DO
depend on the DB session / repositories.
"""
