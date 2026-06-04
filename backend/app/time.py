from datetime import UTC, datetime


def utcnow() -> datetime:
    """Current UTC time as a naive datetime.

    The columns here are naive, so we strip tzinfo. This is the documented
    replacement for datetime.utcnow(), which is deprecated on 3.12+.
    """
    return datetime.now(UTC).replace(tzinfo=None)
