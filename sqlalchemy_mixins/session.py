from sqlalchemy.orm import Session, scoped_session, Query
from .utils import classproperty


class NoSessionError(RuntimeError):
    pass


class SessionMixin:
    _session = None

    @classmethod
    def set_session(cls, session):
        """
        :type session: scoped_session | Session
        """
        cls._session = session

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
        return cls.session.query(cls)
