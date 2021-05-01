from typing import Optional

from sqlalchemy.orm import Session, Query

from sqlalchemy_mixins.utils import classproperty



class SessionMixin:
    _session: Optional[Session]

    @classmethod
    def set_session(cls, session: Session) -> None: ...

    @classproperty
    def session(cls) -> Session: ...

    @classproperty
    def query(cls) -> Query: ...