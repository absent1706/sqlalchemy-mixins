from __future__ import print_function

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from sqlalchemy_mixins import ReprMixin

Base = declarative_base()
engine = sa.create_engine('sqlite:///:memory:')
session = scoped_session(sessionmaker(bind=engine))


class BaseModel(Base, ReprMixin):
    __abstract__ = True
    __repr__ = ReprMixin.__repr__
    pass


class User(BaseModel):
    __tablename__ = 'user'
    __repr_attrs__ = ['name']

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    posts = sa.orm.relationship('Post', backref='user')


class Post(BaseModel):
    __tablename__ = 'post'
    __repr_attrs__ = ['body', 'user']
    __repr_max_length__ = 25

    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))


Base.metadata.create_all(engine)

bob = User(name='Bob')
session.add(bob)
session.flush()

post1 = Post(body='Post 1', user=bob)
session.add(post1)
session.flush()

post2 = Post(body='Post 2 long-long body', user=bob)
session.add(post2)
session.flush()

# <User #1 'Bob'>
print(bob)

# <Post #1 body: 'Post 1' user: <User #1 ...>
print(post1)

# <Post #2 body: 'Post 2 long-...' user: <User #1 ...>
print(post2)
