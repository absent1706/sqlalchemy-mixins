from typing import List

from sqlalchemy.orm import Query
from sqlalchemy.orm.strategy_options import Load

from sqlalchemy_mixins.session import SessionMixin


JOINED: str
SUBQUERY: str


def eager_expr(schema: dict) -> List[Load]: ...

def _flatten_schema(schema: dict) -> dict: ...

def _eager_expr_from_flat_schema(flat_schema: dict) -> List[Load]: ...


class EagerLoadMixin(SessionMixin):

    @classmethod
    def with_(cls, schema: dict) -> Query: ...

    @classmethod
    def with_joined(cls, *paths: List[str]) -> Query: ...

    @classmethod
    def with_subquery(cls, *paths: List[str]) -> Query: ...