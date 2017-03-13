from .utils import classproperty


class NoSessionError(RuntimeError):
    pass


class SessionMixin:
    _session = None

    @classmethod
    def set_session(cls, _session):
        cls._session = _session

    @classproperty
    def session(cls):
        # raise error if no db found
        if cls._session is not None:
            return cls._session
        else:
            raise NoSessionError('Cant get session.'
                                 'Please, call SaActiveRecord.set_session()')

    @classproperty
    def query(cls):
        return cls.session.query(cls)
