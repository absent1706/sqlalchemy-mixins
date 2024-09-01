from typing import Dict, Iterable, List, Any, Optional

from sqlalchemy_mixins.inspection import InspectionMixin
from sqlalchemy_mixins.session import SessionMixin
from sqlalchemy_mixins.utils import classproperty
from sqlalchemy.orm import Query, QueryableAttribute


class ActiveRecordMixinAsync(InspectionMixin, SessionMixin):

    @classproperty
    def settable_attributes(cls) -> List[str]: ...

    async def save_async(self) -> "ActiveRecordMixinAsync": ...

    @classmethod
    async def create_async(cls, **kwargs: Any) -> "ActiveRecordMixinAsync": ...

    async def update_async(self, **kwargs: dict) -> "ActiveRecordMixinAsync": ...

    async def delete_async(self) -> None: ...

    @classmethod
    async def destroy_async(cls, *ids: list) -> None: ...

    @classmethod
    async def all_async(cls) -> List["ActiveRecordMixinAsync"]: ...

    @classmethod
    async def first_async(cls) -> Optional["ActiveRecordMixinAsync"]: ...

    @classmethod
    async def find_async(cls, id_: Any) -> Optional["ActiveRecordMixinAsync"]: ...

    @classmethod
    async def find_or_fail_async(cls, id_: Any) -> "ActiveRecordMixinAsync": ...
    
    @classmethod
    async def select_async(cls, 
        stmt:Optional[str] = None, 
        filters: Optional[Dict[str, Any]] = None,
        sort_attrs: Optional[Iterable[str]] = None,
        schema: Optional[dict] = None
    ) -> "ActiveRecordMixinAsync": ...

    @classmethod
    async def where_async(cls, **filters: Any) -> Query: ...

    @classmethod
    async def sort_async(cls, *columns: str) -> Query: ...

    @classmethod
    async def with_async(cls, schema: dict) -> Query: ...

    @classmethod
    async def with_joined_async(cls, *paths: List[QueryableAttribute]) -> Query: ...

    @classmethod
    async def with_subquery_async(cls, *paths: List[QueryableAttribute]) -> Query: ...
