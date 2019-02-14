from __future__ import print_function

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from sqlalchemy_mixins import SerializeMixin

Base = declarative_base()
engine = sa.create_engine('sqlite:///:memory:')
session = scoped_session(sessionmaker(bind=engine))


class BaseModel(Base, SerializeMixin):
    __abstract__ = True
    pass


class User(BaseModel):
    __tablename__ = 'user'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    posts = sa.orm.relationship('Post', backref='user')


class Post(BaseModel):
    __tablename__ = 'post'

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

post2 = Post(body='Post 2', user=bob)
session.add(post2)
session.flush()

# {'id': 1, 'name': 'Bob'}
print(bob.to_dict())

# {'id': 1,
# 'name': 'Bob',
# 'posts': [{'body': 'Post 1', 'id': 1, 'user_id': 1},
#           {'body': 'Post 2', 'id': 2, 'user_id': 1}]}
print(bob.to_dict(nested=True))

# {'id': 1, 'body': 'Post 1', 'user_id': 1}
print(post1.to_dict())

# {'id': 2, 'body': 'Post 2', 'user_id': 1, 'user': {'id': 1, 'name': 'Bob'}}
print(post2.to_dict(nested=True))
