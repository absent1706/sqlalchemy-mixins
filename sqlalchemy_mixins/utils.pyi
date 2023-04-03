from typing import Callable, Any, List, Type

from sqlalchemy.orm import DeclarativeBase, RelationshipProperty


class classproperty(object):

    def __init__(self, fget: Callable) -> None: ...

    def __get__(self, owner_self: Any, owner_cls: Any) -> Any: ...

def get_relations(cls: Type[DeclarativeBase]) -> List[RelationshipProperty]: ...
