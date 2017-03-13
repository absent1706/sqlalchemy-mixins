import unittest

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from sqlalchemy_mixins.session import SessionMixin, NoSessionError

Base = declarative_base()
engine = create_engine('sqlite:///:memory:', echo=False)
session = Session(engine)


class BaseModel(Base, SessionMixin):
    __abstract__ = True
    pass


class User(BaseModel):
    __tablename__ = 'user'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)


class Post(BaseModel):
    __tablename__ = 'post'
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)


class TestSessionMixin(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)

    def test_set_session(self):
        # before setting session, error is raised
        with self.assertRaises(NoSessionError):
            _ = BaseModel.session
        with self.assertRaises(NoSessionError):
            _ = User.session
        with self.assertRaises(NoSessionError):
            _ = Post.session

        # query doesn't work too
        with self.assertRaises(NoSessionError):
            _ = User.query
        with self.assertRaises(NoSessionError):
            _ = Post.query

        # after setting session, all is OK
        BaseModel.set_session(session)
        self.assertEqual(BaseModel.session, session)
        self.assertEqual(User.session, session)
        self.assertEqual(Post.session, session)

        self.assertEqual(User.query.first(), session.query(User).first())
        self.assertEqual(Post.query.first(), session.query(Post).first())

    def tearDown(self):
        Base.metadata.create_all(engine)

if __name__ == '__main__': # pragma: no cover
    unittest.main()
