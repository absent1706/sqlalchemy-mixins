from typing import List, Protocol, Dict

from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.orm import Mapper
from sqlalchemy.orm.interfaces import MapperProperty

from sqlalchemy_mixins.utils import classproperty


class MappingProtocol(Protocol):
    __mapper__: Mapper

class InspectionMixin:

    @classproperty
    def columns(cls) -> List[str]: ...

    @classproperty
    def primary_keys_full(cls: MappingProtocol) -> List[MapperProperty]: ...

    @classproperty
    def primary_keys(cls) -> List[str]: ...

    @classproperty
    def relations(cls: MappingProtocol) -> List[str]: ...

    @classproperty
    def settable_relations(cls) -> List[str]: ...

    @classproperty
    def hybrid_properties(cls) -> List[str]: ...

    @classproperty
    def hybrid_methods_full(cls) -> Dict[str, hybrid_method]: ...

    @classproperty
    def hybrid_methods(cls) -> List[str]: ...