from collections import Iterable


class SerializeMixin:
    """Mixin to make model serializable."""

    def to_dict(self, nested=False):
        """Return dict object with model's data.

        :param nested: flag to return nested relationships' data if true
        :type: bool
        :return: dict
        """
        result = dict()
        for key in self.__mapper__.c.keys():
            result[key] = getattr(self, key)

        if nested:
            for key in self.__mapper__.relationships.keys():
                obj = getattr(self, key)

                if isinstance(obj, SerializeMixin):
                    result[key] = obj.to_dict()
                elif isinstance(obj, Iterable):
                    result[key] = [o.to_dict() for o in obj]

        return result
