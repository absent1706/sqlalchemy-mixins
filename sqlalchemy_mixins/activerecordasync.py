from .utils import classproperty
from .session import SessionMixin
from .inspection import InspectionMixin
from .activerecord import ModelNotFoundError


class ActiveRecordMixinAsync(InspectionMixin, SessionMixin):
    __abstract__ = True

    @classproperty
    def settable_attributes(cls):
        return cls.columns + cls.hybrid_properties + cls.settable_relations

    async def fill(self, **kwargs):
        for name in kwargs.keys():
            if name in self.settable_attributes:
                setattr(self, name, kwargs[name])
            else:
                raise KeyError("Attribute '{}' doesn't exist".format(name))

        return self

    async def save(self):
        """Saves the updated model to the current entity db.
        """
        try:
            async with self.session() as session:
                session.add(self)
                await session.commit()
                return self
        except:
            async with self.session() as session:
                await session.rollback()
                raise

    @classmethod
    async def create(cls, **kwargs):
        """Create and persist a new record for the model
        :param kwargs: attributes for the record
        :return: the new model instance
        """
        return await cls().fill(**kwargs).save()

    async def update(self, **kwargs):
        """Same as :meth:`fill` method but persists changes to database.
        """
        return await self.fill(**kwargs).save()

    async def delete(self):
        """Removes the model from the current entity session and mark for deletion.
        """
        try:
            async with self.session() as session:
                session.delete(self)
                await session.commit()
        except:
            async with self.session() as session:
                await session.rollback()
                raise

    @classmethod
    async def destroy(cls, *ids):
        """Delete the records with the given ids
        :type ids: list
        :param ids: primary key ids of records
        """
        for pk in ids:
            obj = await cls.find(pk)
            if obj:
                await obj.delete()
        async with cls.session() as session:
            await session.flush()

    @classmethod
    async def all(cls):
        async with cls.session() as session:
            result = await session.execute(cls.query)
            return result.scalars().all()

    @classmethod
    async def first(cls):
        async with cls.session() as session:
            result = await session.execute(cls.query)
            return result.scalars().first()

    @classmethod
    async def find(cls, id_):
        """Find record by the id
        :param id_: the primary key
        """
        async with cls.session() as session:
            return await session.get(cls, id_)
        

    @classmethod
    async def find_or_fail(cls, id_):
        # assume that query has custom get_or_fail method
        result = await cls.find(id_)
        if result:
            return result
        else:
            raise ModelNotFoundError("{} with id '{}' was not found"
                                     .format(cls.__name__, id_))


