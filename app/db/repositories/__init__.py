"""Repository layer: all raw database access lives here.

Services never issue SQLAlchemy queries directly against a session; they
call into a repository. This keeps locking strategy (SELECT ... FOR
UPDATE), constraint handling, and query shape centralized and testable.
"""
