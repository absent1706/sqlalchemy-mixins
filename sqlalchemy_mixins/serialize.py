from collections.abc import Iterable
from datetime import datetime, date, time

from .inspection import InspectionMixin


class SerializeMixin(InspectionMixin):
    """Mixin to make model serializable."""

    __abstract__ = True

    def to_dict(self,nested = False, hybrid_attributes = False, exclude = None):
        """Return dict object with model's data.

        :param nested: flag to return nested relationships' data if true
        :type: bool
        :param hybrid_attributes: flag to include hybrid attributes if true
        :type: bool
        :return: dict
        """
        if exclude is None:
             view_cols = self.columns
        else :
             view_cols = filter(lambda e: e not in exclude, self.columns)

        result = {key: self.__validate_datetime(key) for key in view_cols}
        if hybrid_attributes:
            for key in self.hybrid_properties:
                result[key] = self.__validate_datetime(key)

        if nested:
            for key in self.relations:
                obj = self.__validate_datetime(key)

                if isinstance(obj, SerializeMixin):
                    result[key] = obj.to_dict(hybrid_attributes=hybrid_attributes)
                elif isinstance(obj, Iterable):
                    result[key] = [
                        o.to_dict(hybrid_attributes=hybrid_attributes) for o in obj
                        if isinstance(o, SerializeMixin)
                    ]

        return result
    
    def __validate_datetime(self, key):
        attr = getattr(self, key)

        if isinstance(attr, (datetime, date, time)):
            return attr.__str__()
        return attr

