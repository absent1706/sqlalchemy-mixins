from __future__ import print_function
import os

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Query, scoped_session, sessionmaker

from sqlalchemy_mixins import EagerLoadMixin, ReprMixin
from sqlalchemy_mixins.eagerload import SUBQUERYLOAD, eager_expr


def log(msg):
    print('\n{}\n'.format(msg))

#################### setup ######################
Base = declarative_base()


# we also use ReprMixin which is optional
class BaseModel(Base, EagerLoadMixin, ReprMixin):
    __abstract__ = True
    __repr__ = ReprMixin.__repr__
    pass


class User(BaseModel):
    __tablename__ = 'user'
    __repr_attrs__ = ['name']  # we want to display name in repr string
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    posts = sa.orm.relationship('Post')
    comments = sa.orm.relationship('Comment')


class Post(BaseModel):
    __tablename__ = 'post'
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    archived = sa.Column(sa.Boolean, default=False)

    user = sa.orm.relationship('User')
    comments = sa.orm.relationship('Comment')


class Comment(BaseModel):
    __tablename__ = 'comment'
    __repr_attrs__ = ['body', 'post']  # we want to display body and post
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    post_id = sa.Column(sa.Integer, sa.ForeignKey('post.id'))
    rating = sa.Column(sa.Integer)

    user = sa.orm.relationship('User')
    post = sa.orm.relationship('Post')

#################### setup ORM ######################

db_file = os.path.join(os.path.dirname(__file__), 'test.sqlite')
engine = create_engine('sqlite:///{}'.format(db_file), echo=True)

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)


# sqlalchemy caches data in session, so to not use cache, we recreate session
def reset_session():
    session = scoped_session(sessionmaker(bind=engine))
    BaseModel.set_session(session)
    return session

#################### setup some data ######################

session = reset_session()

u1 = User(name='Bill u1', id=1)
session.add(u1)
session.commit()

u2 = User(name='Alex u2')
session.add(u2)
session.commit()

session.commit()

p11 = Post(
    id=11,
    body='1234567890123',
    archived=True
)
p11.user = u1
session.add(p11)
session.commit()

p12 = Post(
    id=12,
    body='1234567890',
    user=u1
)
session.add(p12)
session.commit()

cm11 = Comment(
    id=11,
    body='cm11 to p11',
    user=u1,
    post=p11,
    rating=1
)
session.add(cm11)
session.commit()

cm12 = Comment(
    id=12,
    body='cm12 to p12',
    user=u2,
    post=p12,
    rating=2
)
session.add(cm12)
session.commit()

#################### Demo ######################

#### 0. simple flat joinedload/subqueryload ####
# in simplest cases, you may want to just eager load a few relations.
# for such cases, EagerLoadMixin has simple syntax

#### 0.1 joinedload ####
reset_session()
comment = Comment.with_joined('user', 'post').first()
# same using class properties:
# comment = Comment.with_joined(Comment.user, Comment.post).first()

# SQL will be like
# note that we select user as parent entity and as post.comments.user
# EagerLoadMixin will make table aliases for us
"""
SELECT comment.*, user_1.*, post_1.*
FROM comment
LEFT OUTER JOIN user AS user_1 ON user_1.id = comment.user_id
LEFT OUTER JOIN post AS post_1 ON post_1.id = comment.post_id
LIMIT 1 OFFSET 1
"""
# now, to get relationships, NO additional query is needed
post = comment.post
user = comment.user

#### 0.2 subqueryload ####
reset_session()
users = User.with_subquery('posts', 'comments').all()
# same using class properties:
# users = User.with_subquery(User.posts, User.comments).all()

# there will be 3 queries:
## first. on users:
"""
SELECT user.* FROM user
"""
# second. on posts:
"""
SELECT post.* FROM (SELECT user.id AS user_id FROM user) AS anon_1
JOIN post ON anon_1.user_id = post.user_id
"""
# third. on comments
"""
SELECT comment.* FROM (SELECT user.id AS user_id FROM user) AS anon_1
JOIN comment ON anon_1.user_id = comment.user_id
"""
# now, to get relationships, NO additional query is needed
posts = users[0].posts
comments = users[0].comments

#### 1. nested joinedload ####
# for nested eagerload, you should use dict instead of lists|
schema = {
    'posts': {  # joined-load posts
                # here,
                #  'posts': { ... }
                # is equal to
                #  'posts': (JOINEDLOAD, { ... })
        'comments': {  # to each post join its comments
            'user': None  # and join user to each comment
        }
    }
}
# same schema using class properties
# schema = {
#     User.posts: {
#         Post.comments: {
#             Comment.user: None
#         }
#     }
# }
session = reset_session()
###### 1.1 query-level: more flexible
user = session.query(User).options(*eager_expr(schema)).get(1)

# SQL will be like
# note that we select user as parent entity and as post.comments.user
# EagerLoadMixin will make table aliases for us
"""
SELECT user.*, user_1.*, comment_1.*, post_1.*
FROM user
LEFT OUTER JOIN post AS post_1 ON user.id = post_1.user_id
LEFT OUTER JOIN comment AS comment_1 ON post_1.id = comment_1.post_id
LEFT OUTER JOIN user AS user_1 ON user_1.id = comment_1.user_id
WHERE user.id = 1
"""

reset_session()
###### 1.2 ORM-level: more convenient
user = User.with_(schema).get(1)

# now, to get relationships, NO additional query is needed
post = user.posts[0]
comment = post.comments[0]
comment_user = comment.user

#### 2. combination of joinedload and subqueryload ####

# sometimes we want to load relations in separate query.
#  i.g. when we load posts, to each post we want to have user and all comments.
#  when we load many posts, join comments and comments to each user
schema = {
    'comments': (SUBQUERYLOAD, {  # load posts in separate query
        'user': None  # but, in this separate query, join user
    })
}
# the same schema using class properties:
schema = {
    Post.comments: (SUBQUERYLOAD, {  # load posts in separate query
        Comment.user: None  # but, in this separate query, join comments
    })
}

###### 2.1 query-level: more flexible
reset_session()
posts = session.query(Post).options(*eager_expr(schema)).all()

###### 2.1 query-level: more flexible
reset_session()
posts = Post.with_(schema).all()

# there will be 2 queries:
## first:
"""
SELECT post.* FROM post
"""
# second query loads comments with joined comment users
# it uses first query to get comments for specific posts
"""
SELECT comment.*, user_1.*
FROM (SELECT post.id AS post_id FROM post) AS anon_1
JOIN comment ON anon_1.post_id = comment.post_id
LEFT OUTER JOIN user AS user_1 ON user_1.id = comment.user_id
"""
# now, to get relationships, NO additional query is needed
comments1 = posts[0].comments
comments2 = posts[1].comments
user1 = posts[0].comments[0].user
user2 = posts[1].comments[0].user