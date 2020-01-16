from __future__ import print_function
import os

import datetime
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Query, scoped_session, sessionmaker

from sqlalchemy_mixins import SmartQueryMixin, ReprMixin, JOINED, smart_query


def log(msg):
    print('\n{}\n'.format(msg))


#################### setup ######################
Base = declarative_base()


# we also use ReprMixin which is optional
class BaseModel(Base, SmartQueryMixin, ReprMixin):
    __abstract__ = True
    __repr__ = ReprMixin.__repr__
    pass


class User(BaseModel):
    __tablename__ = 'user'
    __repr_attrs__ = ['name']
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)

    # to smart query relationship, it should be explicitly set,
    # not to be a backref
    posts = sa.orm.relationship('Post')
    comments = sa.orm.relationship('Comment')
    # below relationship will just return query (without executing)
    # this query can be customized
    # see http://docs.sqlalchemy.org/en/latest/orm/collections.html#dynamic-relationship
    #
    # we will use this relationship for demonstrating real-life example
    #  of how smart_query() function works (see 3.2.2)
    comments_ = sa.orm.relationship('Comment', lazy="dynamic")  # this will return query


class Post(BaseModel):
    __tablename__ = 'post'
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    archived = sa.Column(sa.Boolean, default=False)

    # to smart query relationship, it should be explicitly set,
    # not to be a backref
    user = sa.orm.relationship('User')
    comments = sa.orm.relationship('Comment')

    @hybrid_property
    def public(self):
        return not self.archived

    @public.expression
    def public(cls):
        return ~cls.archived

    @hybrid_method
    def is_commented_by_user(cls, user, mapper=None):
        # in real apps, Comment class can be obtained from relation
        #  to avoid cyclic imports like so:
        #     Comment = cls.comments.property.argument()
        mapper = mapper or cls
        # from sqlalchemy import exists
        # return exists().where((Comment.post_id == mapper.id) & \
        #                       (Comment.user_id == user.id))
        return mapper.comments.any(Comment.user_id == user.id)

    @hybrid_method
    def is_public(cls, value, mapper=None):
        # in real apps, Comment class can be obtained from relation
        #  to avoid cyclic imports like so:
        #     Comment = cls.comments.property.argument()
        mapper = mapper or cls
        return mapper.public == value


class Comment(BaseModel):
    __tablename__ = 'comment'
    __repr_attrs__ = ['body']
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    post_id = sa.Column(sa.Integer, sa.ForeignKey('post.id'))
    rating = sa.Column(sa.Integer)
    created_at = sa.Column(sa.DateTime)

    # to smart query relationship, it should be explicitly set,
    # not to be a backref
    user = sa.orm.relationship('User')
    post = sa.orm.relationship('Post')


#################### setup ORM ######################

db_file = os.path.join(os.path.dirname(__file__), 'test.sqlite')
engine = create_engine('sqlite:///{}'.format(db_file), echo=True)

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

session = scoped_session(sessionmaker(bind=engine))

BaseModel.set_session(session)

#################### setup some data ######################
u1 = User(name='Bill u1')
session.add(u1)
session.commit()

u2 = User(name='Alex u2')
session.add(u2)
session.commit()

u3 = User(name='Bishop u3')
session.add(u3)
session.commit()

session.commit()

p11 = Post(
    id=11,
    body='1234567890123',
    archived=True,
    user=u1
)
session.add(p11)
session.commit()

p12 = Post(
    id=12,
    body='1234567890',
    user=u1
)
session.add(p12)
session.commit()

p21 = Post(
    id=21,
    body='p21',
    user=u2
)
session.add(p21)
session.commit()

p22 = Post(
    id=22,
    body='p22',
    user=u2
)
session.add(p22)
session.commit()

cm11 = Comment(
    id=11,
    body='cm11',
    user=u1,
    post=p11,
    rating=1,
    created_at=datetime.datetime(2014, 1, 1)
)
session.add(cm11)
session.commit()

cm12 = Comment(
    id=12,
    body='cm12',
    user=u2,
    post=p12,
    rating=2,
    created_at=datetime.datetime(2015, 10, 20)
)
session.add(cm12)
session.commit()

cm21 = Comment(
    id=21,
    body='cm21',
    user=u1,
    post=p21,
    rating=1,
    created_at=datetime.datetime(2015, 11, 21)
)
session.add(cm21)
session.commit()

cm22 = Comment(
    id=22,
    body='cm22',
    user=u3,
    post=p22,
    rating=3,
    created_at=datetime.datetime(2016, 11, 20)
)
session.add(cm22)
session.commit()

cm_empty = Comment(
    id=29,
    # no body
    # no user
    # no post
    # no rating
)
session.add(cm_empty)
session.commit()

#################### Demo ######################

# ['id', 'body', 'user_id', 'archived',  # normal columns
#  'user', 'comments',  # relations
#  'public',  # hybrid attributes
#  'is_public', 'is_commented_by_user'  # hybrid methods
# ]
log(Post.filterable_attributes)

#### 1. Filters ####

##### 1.1 filter by hybrid_property 'public' #####
# low-level filter_expr()
log(session.query(Post).filter(*Post.filter_expr(user=u1, public=True)).all())
# high-level SmartQueryMixin.where() method
log(Post.where(user=u1, public=True).all())
# you can unpack dict (in real world app you will do this)
filters = {'user': u1, 'public': True}
log(Post.where(**filters).all())

##### 1.2 filter by hybrid_method 'is_commented_by_user' #####
# low-level filter_expr()
log(session.query(Post).filter(
    *Post.filter_expr(is_commented_by_user=u1)).all())
# high-level SmartQueryMixin.where() method
log(Post.where(is_commented_by_user=u1).all())

##### 1.3 operators #####
# rating == None
log(Comment.where(rating=None).all())  # cm_empty
log(Comment.where(rating__isnull=2).all())  # cm_empty

# rating == 2
# when no operator, 'exact' operator is assumed
log(Comment.where(rating=2).all())  # cm12
# assumed
log(Comment.where(rating__exact=2).all())  # cm12

# rating > 2
log(Comment.where(rating__gt=2).all())  # cm22
# rating >= 2
log(Comment.where(rating__ge=2).all())  # cm12, cm22
# rating < 2
log(Comment.where(rating__lt=2).all())  # cm11, cm21
# rating <= 2
log(Comment.where(rating__le=2).all())  # cm11, cm12, cm21

# rating in [1,3]
log(Comment.where(rating__in=[1, 3]).all())  # cm11, cm21, cm22
log(Comment.where(rating__in=(1, 3)).all())  # cm11, cm21, cm22
log(Comment.where(rating__in={1, 3}).all())  # cm11, cm21, cm22

# rating between 2 and 3
log(Comment.where(rating__between=[2, 3]).all())  # cm12, cm22
log(Comment.where(rating__between=(2, 3)).all())  # cm12, cm22

# likes
log(Comment.where(body__like=u'cm12 to p12').all())  # cm12
log(Comment.where(body__like='%cm12%').all())  # cm12
log(Comment.where(body__ilike='%CM12%').all())  # cm12
log(Comment.where(body__startswith='cm1').all())  # cm11, cm12
log(Comment.where(body__istartswith='CM1').all())  # cm11, cm12
log(Comment.where(body__endswith='to p12').all())  # cm12
log(Comment.where(body__iendswith='TO P12').all())  # cm12

# dates
# year
log(Comment.where(created_at__year=2014).all())  # cm11
log(Comment.where(created_at__year=2015).all())  # cm12, cm21
# month
log(Comment.where(created_at__month=1).all())  # cm11
log(Comment.where(created_at__month=11).all())  # cm21, cm22
# day
log(Comment.where(created_at__day=1).all())  # cm11
log(Comment.where(created_at__day=20).all())  # cm12, cm22
# whole date
log(Comment.where(created_at__year=2014, created_at__month=1,
                  created_at__day=1).all())  # cm11
# date comparisons
log(Comment.where(created_at__year_gt=2014).all())  # cm12, cm21, cm22

##### 1.4 where() with auto-joined relations #####

# when have no joins, where() is a shortcut for filter_expr
log(session.query(Comment).filter(
    *Comment.filter_expr(rating__gt=2, body__startswith='cm1')).all())
log(Comment.where(rating__gt=2, body__startswith='cm1').all())

# but where() can automatically join relations

# users having posts which are commented by user 2
log(User.where(posts___comments___user_id=u2.id).all())

# comments where user name starts with 'Bi'
# !! ATTENTION !!
# about Comment.post:
#  although we have Post.comments relationship,
#   it's important to **add relationship Comment.post** too,
#   not just use backref !!!
log(Comment.where(user___name__startswith='Bi').all())

# non-public posts commented by user 1
log(Post.where(public=False, is_commented_by_user=u1).all())

#### 2. sort ####

#### 2.1 simple demo ####

##### 2.1.1 low-level order_expr()
# '-rating', 'created_at' means 'ORDER BY rating DESC, created_at ASC'
log(session.query(Comment).order_by(
    *Comment.order_expr('-rating', 'created_at')).all())

##### 2.1.2 high-level sort()
log(Comment.sort('-rating', 'created_at'))
# in real world apps, you will keep attrs in list
sort_attrs = ['-rating', 'created_at']
log(Comment.sort(*sort_attrs))

##### 2.1.3 hybrid properties
log(session.query(Post).order_by(*Post.order_expr('-public')).all())
log(Post.sort('-public').all())

#### 2.2 sort() with auto-joined relations ####
# sort by name of user ASC (user relation will be auto-joined), then by
#  created_at DESC
log(Comment.sort('user___name', '-created_at').all())
# get comments on public posts first, then order by post user name
# Post and User tables will be auto-joined
log(Comment.sort('-post___public', 'post___user___name').all())


#### 3. smart_query() : combination of where(), sort() and eager load ####

schema = {
    'post': {
        'user': JOINED
    }
}
# schema can use class properties too (see EagerLoadMixin):
# schema = {
#     Comment.post: {
#         Post.user: JOINED
#     }
# }

##### 3.1 high-level smart_query() class method #####
res = Comment.smart_query(
    filters={
        'post___public': True,
        'user__isnull': False
    },
    sort_attrs=['user___name', '-created_at'],
    schema=schema).all()
log(res)  # cm12, cm21, cm22

##### 3.2 more flexible smart_query() function #####

##### 3.2.1. The same as 3.1
query = Comment.query  # could be any query you want
res = smart_query(query,
    filters={
        'post___public': True,
        'user__isnull': False
    },
    sort_attrs=['user___name', '-created_at'],
    schema=schema).all()
log(res)  # cm12, cm21, cm22

##### 3.2.2. Real-life example with lazy='dynamic' relationship
# let's imagine we want to display some user relations
#  and flexibly filter, sort and eagerload them
# like this http://www.qopy.me/LwfSCu_ETM6At6el8wlbYA
#  (no sort on screenshot, but you've git the idea)

# so we have a user
user = session.query(User).first()
# and we have initial query for his/her comments
#  (see User.comments_ relationship)
query = user.comments_
# now we just smartly apply all filters, sorts and eagerload. Perfect!
res = smart_query(query,
    filters={
        'post___public': True,
        'user__isnull': False
    },
    sort_attrs=['user___name', '-created_at'],
    schema=schema).all()
log(res)  # cm21

##### 3.3 auto eager load in where() and sort() with auto-joined relations ####
"""
Smart_query does auto-joins for filtering/sorting,
so there's a sense to tell sqlalchemy that we alreeady joined that relation

So we test that relations are set to be joinedload
 if they were used in smart_query()
"""

##### 3.3.1 where()

# comments on public posts where posted user name like ...
res = Comment.where(post___public=True, post___user___name__like='Bi%').all()
log(res)
# no additional query needed: we used 'post' and 'post__user'
#  relations in smart_query()
log(res[0].post)
log(res[0].post.user)
# we didn't use post___comments in filters, so additional query is needed
log(res[0].post.comments)

##### 3.3.2 sort()
res = Comment.sort('-post___public', 'post___user___name').all()
log(res)
# no additional query needed: we used 'post' and 'post__user'
#  relations in smart_query()
log(res[0].post)
log(res[0].post.user)
# we didn't use post___comments in filters, so additional query is needed
log(res[0].post.comments)
