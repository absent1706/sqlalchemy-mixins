from sqlalchemy import select
from sqlalchemy.orm import Query
from sqlalchemy.exc import InvalidRequestError
from .utils import classproperty
from .session import SessionMixin
from .inspection import InspectionMixin
from .activerecord import ModelNotFoundError
from . import smartquery as SmaryQuery

get_root_cls = SmaryQuery._get_root_cls
def async_root_cls(query: Query):
    """Monkey patch SmaryQuery to handle async queries."""
    try:
        return get_root_cls(query)
    except ValueError:
        # Handle async queries
        if query.__dict__["_propagate_attrs"]["plugin_subject"].class_:
            return query.__dict__["_propagate_attrs"]["plugin_subject"].class_
        raise

SmaryQuery._get_root_cls = lambda query: async_root_cls(query)


class ActiveRecordMixinAsync(InspectionMixin, SessionMixin):
    __abstract__ = True

    @classmethod
    def _get_primary_key_name(cls) -> str:
        """
        Gets the primary key of the model.

        Note: This method can only be used if the model has a single primary key.
        :return: The name of the primary key.
        :raises InvalidRequestError: If the model does not have a primary key or 
        has a composite primary key.
        """
        primary_keys = cls.__table__.primary_key.columns
        if primary_keys is None:
            raise InvalidRequestError(
                f"Model {cls.__name__} does not have a primary key.")
        if len(primary_keys) > 1:
            raise InvalidRequestError(
                f"Model {cls.__name__} has a composite primary key.")

        return primary_keys[0].name

    @classproperty
    def settable_attributes(cls):
        return cls.columns + cls.hybrid_properties + cls.settable_relations

    def fill(self, **kwargs):
        for name in kwargs.keys():
            if name in self.settable_attributes:
                setattr(self, name, kwargs[name])
            else:
                raise KeyError("Attribute '{}' doesn't exist".format(name))

        return self
    
    @classproperty
    def query(cls):
        """
        Override the default query property to handle async session.
        """
        if not hasattr(cls.session, "query"):
            return select(cls)

        return cls.session.query(cls)
    
    async def save_async(self):
        """
        Async version of :meth:`save` method.

        :see: :meth:`save` method for more information.
        """
        async with self.session() as session:
            try:
                session.add(self)
                await session.commit()
                return self
            except:
                await session.rollback()
                raise

    @classmethod
    async def create_async(cls, **kwargs):
        """
        Async version of :meth:`create` method.

        :see: :meth:`create`
        """
        return await cls().fill(**kwargs).save_async()
    
    async def update_async(self, **kwargs):
        """
        Async version of :meth:`update` method.

        :see: :meth:`update`
        """
        return await self.fill(**kwargs).save_async()

    async def delete_async(self):
        """
        Async version of :meth:`delete` method.

        :see: :meth:`delete`
        """
        async with self.session() as session:
            try:
                session.sync_session.delete(self)
                await session.commit()
                return self
            except:
                await session.rollback()
                raise
            finally:
                await session.flush()

    @classmethod
    async def destroy_async(cls, *ids):
        """
        Async version of :meth:`destroy` method.

        :see: :meth:`destroy`
        """
        primary_key = cls._get_primary_key_name()
        if primary_key:
            async with cls.session() as session:
                try:
                    for row in await cls.where_async(**{f"{primary_key}__in": ids}):
                        session.sync_session.delete(row)
                    await session.commit()
                except:
                    await session.rollback()
                    raise
                await session.flush()

    @classmethod
    async def select_async(cls, stmt=None, filters=None, sort_attrs=None, schema=None):
        async with cls.session() as session:
            if stmt is None:
                stmt = SmaryQuery.smart_query(query=cls.query,
                    filters=filters, sort_attrs=sort_attrs, schema=schema)
            return (await session.execute(stmt)).scalars()

    @classmethod
    async def where_async(cls, **filters):
        """
        Aync version of where method.

        :see: :meth:`where` method for more details.
        """
        return await cls.select_async(filters=filters)

    @classmethod
    async def sort_async(cls, *columns):
        """
        Async version of sort method.

        :see: :meth:`sort` method for more details.
        """
        return await cls.select_async(sort_attrs=columns)

    @classmethod
    async def all_async(cls):
        """
        Async version of all method.
        This is same as calling ``(await select_async()).all()``.

        :see: :meth:`all` method for more details.
        """
        return (await cls.select_async()).all()

    @classmethod
    async def first_async(cls):
        """
        Async version of first method.
        This is same as calling ``(await select_async()).first()``.

        :see: :meth:`first` method for more details.
        """
        return (await cls.select_async()).first()

    @classmethod
    async def find_async(cls, id_):
        """
        Async version of find method.

        :see: :meth:`find` method for more details.
        """
        primary_key = cls._get_primary_key_name()
        if primary_key:
            return (await cls.where_async(**{primary_key: id_})).first()
        return None

    @classmethod
    async def find_or_fail_async(cls, id_):
        """
        Async version of find_or_fail method.

        :see: :meth:`find_or_fail` method for more details.
        """
        cursor = await cls.find_async(id_)
        if cursor:
            return cursor
        else:
            raise ModelNotFoundError("{} with id '{}' was not found"
                                     .format(cls.__name__, id_))

    @classmethod
    async def with_async(cls, schema):
        """
        Async version of with method.

        :see: :meth:`with` method for more details.
        """
        return await cls.select_async(cls.with_(schema))

    @classmethod
    async def with_joined_async(cls, *paths):
        """
        Async version of with_joined method.

        :see: :meth:`with_joined` method for more details.
        """
        return await cls.select_async(cls.with_joined(*paths))

    @classmethod
    async def with_subquery_async(cls, *paths):
        """
        Async version of with_subquery method.

        :see: :meth:`with_subquery` method for more details.
        """
        return await cls.select_async(cls.with_subquery(*paths))
