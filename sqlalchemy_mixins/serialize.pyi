from sqlalchemy_mixins.inspection import InspectionMixin


class SerializeMixin(InspectionMixin):

    def to_dict(self, nested: bool = False, hybrid_attributes: bool = False) -> dict: ...