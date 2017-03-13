"""
Demonstrates how to use AllFeaturesMixin.
It just combines other mixins, so look to their examples for details
"""
from __future__ import print_function
import sqlalchemy as sa
from sqlalchemy_mixins import AllFeaturesMixin

Base = sa.ext.declarative.declarative_base()


class BaseModel(Base, AllFeaturesMixin):
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
    user = sa.orm.relationship('User')


engine = sa.create_engine('sqlite:///:memory:')
session = sa.orm.scoped_session(sa.orm.sessionmaker(bind=engine))

Base.metadata.create_all(engine)
BaseModel.set_session(session)

bob = User.create(name='Bob')
post1 = Post.create(body='Post 1', user=bob, rating=3)
post2 = Post.create(body='long-long-long-long-long body', rating=2,
                    user=User.create(name='Bill'))

# filter using operators like 'in' and 'contains' and relations like 'user'
print(Post.where(rating__in=[2, 3, 4], user___name__like='%Bi%').all())
# eager load user with post
print(Post.with_(['user']).first())
# sort by rating DESC, user name ASC
print(Post.sort('-rating', 'user___name').all())
