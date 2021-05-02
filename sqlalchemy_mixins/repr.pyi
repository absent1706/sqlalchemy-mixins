class ReprMixin:
    __repr_attrs__: list
    __repr_max_length__: int

    @property
    def _id_str(self) -> str: ...

    @property
    def _repr_attrs_str(self) -> str: ...

    def __repr__(self) -> str: ...