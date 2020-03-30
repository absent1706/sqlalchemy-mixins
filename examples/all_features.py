"""
Demonstrates how to use AllFeaturesMixin.
It just combines other mixins, so look to their examples for details
"""
from __future__ import print_function
import sqlalchemy as sa
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_mixins import AllFeaturesMixin, TimestampsMixin

Base = declarative_base()


class BaseModel(Base, AllFeaturesMixin, TimestampsMixin):
    __abstract__ = True
    pass


class User(BaseModel):
    __tablename__ = 'user'
    __repr_attrs__ = ['name']

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)


class Post(BaseModel):
    __tablename__ = 'post'
    __repr_attrs__ = ['body', 'user']

    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    rating = sa.Column(sa.Integer)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))

    # we use this relation in smart_query, so it should be explicitly set
    # (not just a backref from User class)
    user = sa.orm.relationship('User', backref='posts') # but for eagerload
                                                        # backref is OK
    comments = sa.orm.relationship('Comment')


class Comment(BaseModel):
    __tablename__ = 'comment'

    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    post_id = sa.Column(sa.Integer, sa.ForeignKey('post.id'))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))

    post = sa.orm.relationship('Post')
    user = sa.orm.relationship('User')


engine = sa.create_engine('sqlite:///:memory:', echo=False)
session = scoped_session(sessionmaker(bind=engine))

Base.metadata.create_all(engine)
BaseModel.set_session(session)

bob = User.create(name='Bob')
post1 = Post.create(body='Post 1', user=bob, rating=3)
post2 = Post.create(body='long-long-long-long-long body', rating=2,
                    user=User.create(name='Bill'),
                    comments=[Comment.create(body='cool!', user=bob)])

# filter using operators like 'in' and 'contains' and relations like 'user'
# will output this beauty: <Post #1 body:'Post1' user:'Bill'>
print(Post.where(rating__in=[2, 3, 4], user___name__like='%Bi%').all())

# joinedload post and user
print(Comment.with_joined('user', 'post', 'post.comments').first())

# subqueryload posts and their comments
print(User.with_subquery('posts', 'posts.comments').first())

# sort by rating DESC, user name ASC
print(Post.sort('-rating', 'user___name').all())

# {'id': 1, 'body': 'Post 1', 'user_id': 1, 'created_at': ..., 'updated_at': ...}
print('User serialized (no relationships):', post1.to_dict())

# {'id': 1,
# 'name': 'Bob',
# 'created_at': datetime.datetime(2020, 3, 27, 10, 19, 33, 655841),
# 'updated_at': datetime.datetime(2020, 3, 27, 10, 19, 33, 655841)
# 'posts': [{'body': 'Post 1', 'id': 1, 'user_id': 1},
#           {'body': 'Post 2', 'id': 2, 'user_id': 1}]}
print('User serialized with relationships:', bob.to_dict(nested=True))

# Created Bob:     2020-03-27 10:19:33.655841
print("Created Bob:    ", bob.created_at)
bob.update(name='Bobby')
# Updated Bob:     2020-03-27 10:19:33.705463
print("Updated Bob:    ", bob.updated_at)
