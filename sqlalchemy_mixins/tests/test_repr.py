from __future__ import print_function
import unittest

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Query
from sqlalchemy.orm import Session

from sqlalchemy_mixins import ReprMixin

Base = declarative_base()
engine = create_engine('sqlite:///:memory:', echo=False)
sess = Session(engine)
# sess = scoped_session(sessionmaker(bind=engine))


class BaseModel(Base, ReprMixin):
    __abstract__ = True
    # !!! IMPORTANT !!!
    # include below string to make mixin work
    __repr__ = ReprMixin.__repr__
    pass


class User(BaseModel):
    __tablename__ = 'user'
    __repr_attrs__ = ['name']

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    posts = sa.orm.relationship('Post')


class Post(BaseModel):
    __tablename__ = 'post'
    __repr_attrs__ = ['body', 'user']

    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    archived = sa.Column(sa.Boolean, default=False)

    user = sa.orm.relationship('User')
    comments = sa.orm.relationship('Comment')


class Comment(BaseModel):
    __tablename__ = 'comment'
    __repr_attrs__ = ['body', 'post', 'user']

    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    post_id = sa.Column(sa.Integer, sa.ForeignKey('post.id'))
    rating = sa.Column(sa.Integer)

    user = sa.orm.relationship('User')
    post = sa.orm.relationship('Post')


class TestEagerLoad(unittest.TestCase):
    def test(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

        u1 = User(name='Bill u1', id=1)
        sess.add(u1)
        sess.commit()

        u2 = User(name='Alex u2', id=2)
        sess.add(u2)
        sess.commit()

        sess.commit()

        p11 = Post(
            id=11,
            body='very very very very very long long long long long',
            archived=True
        )
        p11.user = u1
        sess.add(p11)
        sess.commit()

        cm11 = Comment(
            id=11,
            body='c11',
            user=u1,
            post=p11,
            rating=1
        )
        sess.add(cm11)
        sess.commit()

        user_not_in_session = User()

        # tests. see output in console

        print(repr(u1))
        self.assertIn('Bill', repr(u1))
        self.assertIn('#1', repr(u1))

        print(repr(u2))
        self.assertIn('Alex', repr(u2))
        self.assertIn('#2', repr(u2))

        print(repr(p11))
        self.assertIn('very', repr(p11))
        self.assertIn('...', repr(p11))

        print(repr(cm11))
        self.assertIn('c11', repr(cm11))
        self.assertIn('Bill', repr(cm11))

        print(user_not_in_session)
        self.assertIn('None', repr(user_not_in_session))

        Comment.__repr_attrs__ = ['INCORRECT ATTR']
        with self.assertRaises(KeyError):
            print(repr(cm11))


if __name__ == '__main__': # pragma: no cover
    unittest.main()
