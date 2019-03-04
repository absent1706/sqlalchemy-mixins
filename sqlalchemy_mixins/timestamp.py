from datetime import datetime

import sqlalchemy as sa


class TimestampsMixin:
    """Mixin that define timestamp columns."""

    __abstract__ = True

    __created_at_name__ = 'created_at'
    __updated_at_name__ = 'updated_at'
    __datetime_callback__ = datetime.utcnow

    created_at = sa.Column(__created_at_name__,
                           sa.DateTime,
                           default=__datetime_callback__,
                           nullable=False)

    updated_at = sa.Column(__updated_at_name__,
                           sa.DateTime,
                           default=__datetime_callback__,
                           nullable=False)


@sa.event.listens_for(TimestampsMixin, 'before_update', propagate=True)
def _receive_before_update(mapper, connection, target):
    """Listen for updates and update `updated_at` column."""
    target.updated_at = target.__datetime_callback__()
