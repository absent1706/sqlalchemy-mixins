from sqlalchemy.orm import Session, scoped_session, Query
from sqlalchemy import select
from .utils import classproperty


class NoSessionError(RuntimeError):
    pass


class SessionMixin:
    _session = None
    _isAsync = False

    @classmethod
    def set_session(cls, session, isAsync=False):
        """
        :type session: scoped_session | async_scoped_session | Session
        """
        cls._session = session
        cls._isAsync = isAsync

    @classproperty
    def session(cls):
        """
        :rtype: scoped_session | Session
        """
        if cls._session is not None:
            return cls._session
        else:
            raise NoSessionError('Cant get session.'
                                 'Please, call SaActiveRecord.set_session()')

    @classproperty
    def query(cls):
        """
        :rtype: Query
        """
        if cls._isAsync or not hasattr(cls.session, "query"):
            return select(cls)
        return cls.session.query(cls)
