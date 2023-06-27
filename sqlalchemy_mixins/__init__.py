# low-level, tiny mixins. you will rarely want to use them in real world
from .session import SessionMixin
from .inspection import InspectionMixin

# high-level mixins
from .activerecord import ActiveRecordMixin, ModelNotFoundError
from .smartquery import SmartQueryMixin, smart_query
from .eagerload import EagerLoadMixin, JOINED, SUBQUERY
from .repr import ReprMixin
from .serialize import SerializeMixin
from .timestamp import TimestampsMixin


# all features combined to one mixin
class AllFeaturesMixin(ActiveRecordMixin, SmartQueryMixin, ReprMixin, SerializeMixin):
    __abstract__ = True
    __repr__ = ReprMixin.__repr__


__all__ = [
    "ActiveRecordMixin",
    "AllFeaturesMixin",
    "EagerLoadMixin",
    "InspectionMixin",
    "JOINED",
    "ModelNotFoundError",
    "ReprMixin",
    "SerializeMixin",
    "SessionMixin",
    "smart_query",
    "SmartQueryMixin",
    "SUBQUERY",
    "TimestampsMixin",
]
