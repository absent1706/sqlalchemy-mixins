# low-level, tiny mixins. you will rarely want to use them in real world
from .session import SessionMixin
from .inspection import InspectionMixin

# high-level mixins
from .activerecord import ActiveRecordMixin, ModelNotFoundError
from .smartquery import SmartQueryMixin
from .eagerload import EagerLoadMixin, JOINED, SUBQUERY
from .repr import ReprMixin


# all features combined to one mixin
class AllFeaturesMixin(ActiveRecordMixin, SmartQueryMixin, ReprMixin):
    __abstract__ = True
    __repr__ = ReprMixin.__repr__
