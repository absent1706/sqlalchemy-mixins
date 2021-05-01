from .serialize import SerializeMixin
from .repr import ReprMixin
from .smartquery import SmartQueryMixin
from .activerecord import ActiveRecordMixin


class AllFeaturesMixin(ActiveRecordMixin, SmartQueryMixin, ReprMixin, SerializeMixin):
    __abstract__ = True
    __repr__ = ReprMixin.__repr__  # type: ignore