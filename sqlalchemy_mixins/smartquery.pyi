import sys
from typing import Union, Type, List, Optional, Iterable, Dict, Any, TypeVar

if sys.version_info > (3, 6):
    from typing import OrderedDict
else:
    OrderedDict = TypeVar('OrderedDict', bound=Any)


from sqlalchemy.orm import Query
from sqlalchemy.orm.util import AliasedClass

from sqlalchemy_mixins.eagerload import EagerLoadMixin
from sqlalchemy_mixins.inspection import InspectionMixin
from sqlalchemy_mixins.utils import classproperty


def _parse_path_and_make_aliases(
        entity: Union[Type[InspectionMixin], AliasedClass],
        entity_path: str,
        attrs: List[str],
        aliases: OrderedDict
) -> None: ...


def _get_root_cls(query: Query) -> Type[InspectionMixin]: ...

def smart_query(
        query: Query,
        filters: Optional[Dict[str, Any]] = None,
        sort_attrs: Optional[Iterable[str]] = None,
        schema: Optional[dict] = None
) -> Query: ...


class SmartQueryMixin(InspectionMixin, EagerLoadMixin):

    @classproperty
    def filterable_attributes(cls) -> List[str]: ...

    @classproperty
    def sortable_attributes(cls) -> List[str]: ...

    @classmethod
    def filter_expr(cls_or_alias, **filters: dict) -> list: ...

    @classmethod
    def order_expr(cls_or_alias, *columns: str) -> list: ...

    @classmethod
    def smart_query(
            cls,
            filters: Optional[Dict[str, Any]] = None,
            sort_attrs: Optional[Iterable[str]] = None,
            schema: Optional[dict] = None
    ) -> Query: ...

    @classmethod
    def where(cls, **filters: Any) -> Query: ...

    @classmethod
    def sort(cls, *columns: str) -> Query: ...
