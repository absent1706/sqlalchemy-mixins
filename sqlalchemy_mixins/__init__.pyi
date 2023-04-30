from .serialize import SerializeMixin
from .repr import ReprMixin
from .smartquery import SmartQueryMixin
from .activerecord import ActiveRecordMixin
from .activerecordasync import ActiveRecordMixinAsync


class AllFeaturesMixin(ActiveRecordMixin, SmartQueryMixin, ReprMixin, SerializeMixin):
    __abstract__ = True
    __repr__ = ReprMixin.__repr__  # type: ignore

class AllFeaturesMixinAsync(ActiveRecordMixinAsync, SmartQueryMixin, ReprMixin, SerializeMixin):
    __abstract__ = True
    __repr__ = ReprMixin.__repr__  # type: ignore