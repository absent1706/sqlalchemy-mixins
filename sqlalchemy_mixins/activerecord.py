from .utils import classproperty
from .session import SessionMixin
from .inspection import InspectionMixin


class ModelNotFoundError(ValueError):
    pass


class ActiveRecordMixin(InspectionMixin, SessionMixin):
    __abstract__ = True

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

    def save(self, commit=True):
        """Saves the updated model to the current entity db.
        :param commit: where to commit the transaction
        """
        self.session.add(self)
        if commit:
            self._commit_or_fail()
        return self

    @classmethod
    def create(cls, commit=True, **kwargs):
        """Create and persist a new record for the model
        :param commit: where to commit the transaction
        :param kwargs: attributes for the record
        :return: the new model instance
        """
        return cls().fill(**kwargs).save(commit=commit)

    def update(self, commit=True, **kwargs):
        """Same as :meth:`fill` method but persists changes to database.
        :param commit: where to commit the transaction
        """
        return self.fill(**kwargs).save(commit=commit)

    def delete(self, commit=True):
        """Removes the model from the current entity session and mark for deletion.
        :param commit: where to commit the transaction
        """
        self.session.delete(self)
        if commit:
            self._commit_or_fail()

    def _commit_or_fail(self):
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise

    @classmethod
    def destroy(cls, *ids, commit=True):
        """Delete the records with the given ids
        :type ids: list
        :param ids: primary key ids of records
        :param commit: where to commit the transaction
        """
        for pk in ids:
            obj = cls.find(pk)
            if obj:
                obj.delete(commit=commit)
        cls.session.flush()

    @classmethod
    def all(cls):
        return cls.query.all()

    @classmethod
    def first(cls):
        return cls.query.first()

    @classmethod
    def find(cls, id_):
        """Find record by the id
        :param id_: the primary key
        """
        return cls.query.get(id_)

    @classmethod
    def find_or_fail(cls, id_):
        # assume that query has custom get_or_fail method
        result = cls.find(id_)
        if result:
            return result
        else:
            raise ModelNotFoundError("{} with id '{}' was not found"
                                     .format(cls.__name__, id_))
