from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import RelationshipProperty

from .utils import classproperty


Base = declarative_base()


class InspectionMixin(Base):
    __abstract__ = True

    @classproperty
    def columns(cls):
        return inspect(cls).columns.keys()

    @classproperty
    def primary_keys_full(cls):
        """Get primary key properties for a SQLAlchemy cls.
        Taken from marshmallow_sqlalchemy
        """
        mapper = cls.__mapper__
        return [
            mapper.get_property_by_column(column)
            for column in mapper.primary_key
        ]

    @classproperty
    def primary_keys(cls):
        return [pk.key for pk in cls.primary_keys_full]

    @classproperty
    def relations(cls):
        """Return a `list` of relationship names or the given model
        """
        return [c.key for c in cls.__mapper__.iterate_properties
                if isinstance(c, RelationshipProperty)]

    @classproperty
    def settable_relations(cls):
        """Return a `list` of relationship names or the given model
        """
        return [r for r in cls.relations
                if getattr(cls, r).property.viewonly is False]

    @classproperty
    def hybrid_properties(cls):
        items = inspect(cls).all_orm_descriptors
        return [item.__name__ for item in items
                if isinstance(item, hybrid_property)]

    @classproperty
    def hybrid_methods_full(cls):
        items = inspect(cls).all_orm_descriptors
        return {item.func.__name__: item
                for item in items if type(item) == hybrid_method}

    @classproperty
    def hybrid_methods(cls):
        return list(cls.hybrid_methods_full.keys())
