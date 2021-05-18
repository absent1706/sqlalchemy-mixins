from sqlalchemy_mixins.inspection import InspectionMixin
from typing import Optional , List

class SerializeMixin(InspectionMixin):

    def to_dict(self, nested: bool = False, hybrid_attributes: bool = False, exclude: Optional[List[str]] = None) -> dict: ...
