from collections import Iterable

from .inspection import InspectionMixin


class SerializeMixin(InspectionMixin):
    """Mixin to make model serializable."""

    __abstract__ = True

    def to_dict(self, nested=False):
        """Return dict object with model's data.

        :param nested: flag to return nested relationships' data if true
        :type: bool
        :return: dict
        """
        result = dict()
        for key in self.columns:
            result[key] = getattr(self, key)

        if nested:
            for key in self.relations:
                obj = getattr(self, key)

                if isinstance(obj, SerializeMixin):
                    result[key] = obj.to_dict()
                elif isinstance(obj, Iterable):
                    result[key] = [o.to_dict() for o in obj]

        return result
