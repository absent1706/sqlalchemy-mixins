from typing import Optional

from sqlalchemy.orm import Session, Query
from sqlalchemy.ext.asyncio.session import AsyncSession

from sqlalchemy_mixins.utils import classproperty



class SessionMixin:
    _session: Optional[Session | AsyncSession]

    @classmethod
    def set_session(cls, session: Session | AsyncSession, isAsync: bool) -> None: ...

    @classproperty
    def session(cls) -> Session: ...

    @classproperty
    def query(cls) -> Query: ...