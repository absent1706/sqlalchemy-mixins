import unittest
import datetime

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import Session
from sqlalchemy_mixins import SmartQueryMixin, smart_query
from sqlalchemy_mixins.eagerload import JOINED, SUBQUERY

Base = declarative_base()
engine = create_engine('sqlite:///:memory:', echo=False)

sess = Session(engine)
# sess = scoped_session(sessionmaker(bind=engine))


class BaseModel(Base, SmartQueryMixin):
    __abstract__ = True
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


class BaseTest(unittest.TestCase):
    def setUp(self):
        sess.rollback()

        BaseModel.set_session(None)
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

        BaseModel.set_session(sess)

    def _seed(self):
        u1 = User(name='Bill u1')
        sess.add(u1)
        sess.flush()

        u2 = User(name='Alex u2')
        sess.add(u2)
        sess.flush()

        u3 = User(name='Bishop u3')
        sess.add(u3)
        sess.flush()

        sess.flush()

        p11 = Post(
            id=11,
            body='1234567890123',
            archived=True,
            user=u1
        )
        sess.add(p11)
        sess.flush()

        p12 = Post(
            id=12,
            body='1234567890',
            user=u1
        )
        sess.add(p12)
        sess.flush()

        p21 = Post(
            id=21,
            body='p21 by u2',
            user=u2
        )
        sess.add(p21)
        sess.flush()

        p22 = Post(
            id=22,
            body='p22 by u2',
            user=u2
        )
        sess.add(p22)
        sess.flush()

        cm11 = Comment(
            id=11,
            body='cm11 to p11',
            user=u1,
            post=p11,
            rating=1,
            created_at=datetime.datetime(2014, 1, 1)
        )
        sess.add(cm11)
        sess.flush()

        cm12 = Comment(
            id=12,
            body='cm12 to p12',
            user=u2,
            post=p12,
            rating=2,
            created_at=datetime.datetime(2015, 10, 20)
        )
        sess.add(cm12)
        sess.flush()

        cm21 = Comment(
            id=21,
            body='cm21 to p21',
            user=u1,
            post=p21,
            rating=1,
            created_at=datetime.datetime(2015, 11, 21)
        )
        sess.add(cm21)
        sess.flush()

        cm22 = Comment(
            id=22,
            body='cm22 to p22',
            user=u3,
            post=p22,
            rating=3,
            created_at=datetime.datetime(2016, 11, 20)
        )
        sess.add(cm22)
        sess.flush()

        cm_empty = Comment(
            id=29,
            # no body
            # no user
            # no post
            # no rating
        )
        sess.add(cm_empty)
        sess.flush()

        return u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty


# noinspection PyUnusedLocal
class TestFilterExpr(BaseTest):
    # def setUp(self):
    #     Base.metadata.create_all(engine)

    def test_filterable_attributes(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        self.assertEqual(set(User.filterable_attributes),
                         {'id', 'name',  # normal columns
                          'posts', 'comments'  # relations
                          })
        self.assertNotIn('posts_viewonly', set(User.filterable_attributes))

        self.assertEqual(set(Post.filterable_attributes),
                         {'id', 'body', 'user_id', 'archived',
                          # normal columns
                          'user', 'comments',  # relations
                          'public',  # hybrid attributes
                          'is_public', 'is_commented_by_user'  # hybrid methods
                          })
        self.assertEqual(set(Comment.filterable_attributes),
                         {  # normal columns
                             'id', 'body', 'post_id', 'user_id', 'rating',
                             'created_at',
                             'user', 'post'  # hybrid attributes
                         })

    def test_incorrect_expr(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        with self.assertRaises(KeyError):
            _ = sess.query(Post).filter(
                *Post.filter_expr(INCORRECT_ATTR='nomatter')).all()

    def test_columns(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        # users having posts which are commented by user 2
        res = sess.query(Post).filter(
            *Post.filter_expr(user=u1)).all()
        self.assertEqual(set(res), {p11, p12})

        res = sess.query(Post).filter(
            *Post.filter_expr(user=u1, archived=False)).all()
        self.assertEqual(set(res), {p12})

    def test_hybrid_properties(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        self.assertEqual(
            sess.query(Post).filter(*Post.filter_expr(public=True)).all(),
            sess.query(Post).filter(*Post.filter_expr(archived=False)).all()
        )

        res = sess.query(Post).filter(*Post.filter_expr(public=True)).all()
        self.assertEqual(set(res), {p12, p21, p22})

        res = sess.query(Post).filter(*Post.filter_expr(archived=False)).all()
        self.assertEqual(set(res), {p12, p21, p22})

    def test_hybrid_methods(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        # posts which are commented by user 1
        res = sess.query(Post).filter(
            *Post.filter_expr(is_commented_by_user=u1)
        ).all()
        self.assertEqual(set(res), {p11, p21})

        # posts which are commented by user 2
        res = sess.query(Post).filter(
            *Post.filter_expr(is_commented_by_user=u2)
        ).all()
        self.assertEqual(set(res), {p12})

    def test_combinations(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        # non-public posts commented by user 1
        res = sess.query(Post).filter(
            *Post.filter_expr(public=False, is_commented_by_user=u1)
        ).all()
        self.assertEqual(set(res), {p11})

    def test_operators(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        def test(filters, expected_result):
            res = sess.query(Comment).filter(
                *Comment.filter_expr(**filters)
            ).all()
            self.assertEqual(set(res), expected_result)

        # test incorrect attribute
        with self.assertRaises(KeyError):
            test(dict(rating__INCORRECT_OPERATOR='nomatter'), {'nomatter'})

        # rating == None
        test(dict(rating=None), {cm_empty})
        test(dict(rating__isnull=2), {cm_empty})

        # rating == 2
        test(dict(rating=2), {cm12})  # when no operator, 'exact' is assumed
        test(dict(rating__exact=2), {cm12})
        
        # rating != 2
        test(dict(rating__ne=2), {cm11, cm21, cm22})

        # rating > 2
        test(dict(rating__gt=2), {cm22})
        # rating >= 2
        test(dict(rating__ge=2), {cm12, cm22})
        # rating < 2
        test(dict(rating__lt=2), {cm11, cm21})
        # rating <= 2
        test(dict(rating__le=2), {cm11, cm12, cm21})

        # rating in [1,3]
        test(dict(rating__in=[1, 3]), {cm11, cm21, cm22})  # list
        test(dict(rating__in=(1, 3)), {cm11, cm21, cm22})  # tuple
        test(dict(rating__in={1, 3}), {cm11, cm21, cm22})  # set

        # rating not in [1,3]
        test(dict(rating__notin=[1, 3]), {cm12})  # list
        test(dict(rating__notin=(1, 3)), {cm12})  # tuple
        test(dict(rating__notin={1, 3}), {cm12})  # set

        # rating between 2 and 3
        test(dict(rating__between=[2, 3]), {cm12, cm22})  # list
        test(dict(rating__between=(2, 3)), {cm12, cm22})  # set

        # likes
        test(dict(body__like='cm12 to p12'), {cm12})
        test(dict(body__like='%cm12%'), {cm12})
        test(dict(body__ilike='%CM12%'), {cm12})
        test(dict(body__startswith='cm1'), {cm11, cm12})
        test(dict(body__istartswith='CM1'), {cm11, cm12})
        test(dict(body__endswith='to p12'), {cm12})
        test(dict(body__iendswith='TO P12'), {cm12})

        # dates
        # year
        test(dict(created_at__year=2014), {cm11})
        test(dict(created_at__year=2015), {cm12, cm21})
        # month
        test(dict(created_at__month=1), {cm11})
        test(dict(created_at__month=11), {cm21, cm22})
        # day
        test(dict(created_at__day=1), {cm11})
        test(dict(created_at__day=20), {cm12, cm22})
        # whole date
        test(dict(created_at__year=2014, created_at__month=1,
                  created_at__day=1), {cm11})
        test(dict(created_at=datetime.datetime(2014, 1, 1)), {cm11})

        # date comparisons
        test(dict(created_at__year_ge=2014), {cm11, cm12, cm21, cm22})
        test(dict(created_at__year_gt=2014), {cm12, cm21, cm22})
        test(dict(created_at__year_le=2015), {cm11, cm12, cm21})
        test(dict(created_at__month_lt=10), {cm11})



# noinspection PyUnusedLocal
class TestOrderExpr(BaseTest):
    def test_incorrect_expr(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        with self.assertRaises(KeyError):
            _ = sess.query(Post).filter(
                *Post.order_expr('INCORRECT_ATTR')).all()

        with self.assertRaises(KeyError):
            _ = sess.query(Post).filter(
                *Post.order_expr('*body')).all()

    def test_asc(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        res = sess.query(Comment).order_by(*Comment.order_expr('rating')).all()
        self.assertEqual(res[0], cm_empty)
        # cm11 and cm21 have equal ratings, so they can occur in any order
        self.assertEqual(set(res[1:3]), {cm11, cm21})
        self.assertEqual(res[3:], [cm12, cm22])

    def test_desc(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        res = sess.query(Comment).order_by(*Comment.order_expr('-rating'))\
            .all()
        self.assertEqual(res[:2], [cm22, cm12])
        # cm11 and cm21 have equal ratings, so they can occur in any order
        self.assertEqual(set(res[2:4]), {cm11, cm21})
        self.assertEqual(res[-1], cm_empty)

    def test_hybrid_properties(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        res = sess.query(Post).order_by(*Post.order_expr('public')).all()
        self.assertEqual(res[0], p11)

        res = sess.query(Post).order_by(*Post.order_expr('-public')).all()
        self.assertEqual(res[-1], p11)

    def test_combinations(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        """ test various combinations """

        # 1. rating ASC, created_at ASC
        res = sess.query(Comment).order_by(
            *Comment.order_expr('rating', 'created_at')).all()
        # cm11 and cm21 have equal rating, but not equal created_at
        #  we sort 'rating ASC, created_at ASC', so cm11 will be first
        self.assertEqual(res, [cm_empty, cm11, cm21, cm12, cm22])

        # 2. rating ASC, created_at DESC
        res = sess.query(Comment).order_by(
            *Comment.order_expr('rating', '-created_at')).all()
        # cm11 and cm21 have equal rating, but not equal created_at
        #  we sort 'rating ASC, created_at DESC', so cm21 will be first
        self.assertEqual(res, [cm_empty, cm21, cm11, cm12, cm22])

        # 3. rating DESC, created_at ASC
        res = sess.query(Comment).order_by(
            *Comment.order_expr('-rating', 'created_at')).all()
        # cm11 and cm21 have equal rating, but not equal created_at
        #  we sort 'rating DESC, created_at ASC', so cm11 will be first
        self.assertEqual(res, [cm22, cm12, cm11, cm21, cm_empty])

        # 4. rating DESC, created_at DESC
        res = sess.query(Comment).order_by(
            *Comment.order_expr('-rating', '-created_at')).all()
        # cm11 and cm21 have equal rating, but not equal created_at
        #  we sort 'rating DESC, created_at DESC', so cm21 will be first
        self.assertEqual(res, [cm22, cm12, cm21, cm11, cm_empty])


# noinspection PyUnusedLocal
class TestSmartQueryFilters(BaseTest):
    def test_incorrect_expr(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        with self.assertRaises(KeyError):
            _ = User.where(INCORRECT_ATTR='nomatter').all()

    def test_is_a_shortcut_to_filter_expr_in_simple_cases(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        """when have no joins, where() is a shortcut for filter_expr """
        res = sess.query(Comment).filter(
            *Comment.filter_expr(rating__gt=2, body__startswith='cm1')).all()
        self.assertEqual(
            res,
            Comment.where(rating__gt=2, body__startswith='cm1').all())

    def test_is_a_shortcut_to_smart_query(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        """test that where() is just a shortcut for smart_query()"""
        self.assertEqual(Comment.where(rating__gt=2).all(),
                         Comment.smart_query(filters=dict(rating__gt=2)).all())

    def test_incorrect_relation_name(self):
        with self.assertRaises(KeyError):
            _ = User.where(INCORRECT_RELATION='nomatter').all()

        with self.assertRaises(KeyError):
            _ = User.where(post___INCORRECT_RELATION='nomatter').all()

    def test_relations(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        # users having posts which are commented by user 2
        res = User.where(posts___comments___user_id=u2.id).all()
        self.assertEqual(set(res), {u1})

        # comments where user name starts with 'Bi'
        res = Comment.where(user___name__startswith='Bi').all()
        self.assertEqual(set(res), {cm11, cm21, cm22})

        # comments on posts where author name starts with 'Bi'
        # !! ATTENTION !!
        # about Comment.post:
        #  although we have Post.comments relationship,
        #   it's important to **add relationship Comment.post** too,
        #   not just use backref !!!
        res = Comment.where(post___user___name__startswith='Bi').all()
        self.assertEqual(set(res), {cm11, cm12})

    def test_combinations(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        # non-public posts commented by user 1
        res = Post.where(public=False, is_commented_by_user=u1).all()
        self.assertEqual(set(res), {p11})


# noinspection PyUnusedLocal
class TestSmartQuerySort(BaseTest):
    def test_incorrect_expr(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        with self.assertRaises(KeyError):
            _ = Post.sort('INCORRECT_ATTR').all()

        with self.assertRaises(KeyError):
            _ = Post.sort('*body').all()

    def test_is_a_shortcut_to_order_expr_in_simple_cases(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        """when have no joins, sort() is a shortcut for order_expr """
        res = sess.query(Comment).order_by(*Comment.order_expr('rating')).all()
        self.assertEqual(res, Comment.sort('rating').all())

        res = sess.query(Comment).order_by(
            *Comment.order_expr('rating', 'created_at')).all()
        self.assertEqual(res, Comment.sort('rating', 'created_at').all())

        # hybrid properties
        res = sess.query(Post).order_by(*Post.order_expr('public')).all()
        self.assertEqual(res, Post.sort('public').all())

    def test_is_a_shortcut_to_smart_query(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        """test that sort() is just a shortcut for smart_query() """
        self.assertEqual(Comment.sort('rating').all(),
                         Comment.smart_query(sort_attrs=['rating']).all())

    def test_incorrect_relation_name(self):
        with self.assertRaises(KeyError):
            _ = User.sort('INCORRECT_RELATION').all()

        with self.assertRaises(KeyError):
            _ = User.sort('post___INCORRECT_RELATION').all()

    def test_relations(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        """test that sort() is just a shortcut for smart_query() """
        res = Comment.sort('user___name').all()
        self.assertEqual(res[:2], [cm_empty, cm12])
        # cm11 and cm21 were commented by u1, so they can occur in any order
        self.assertEqual(set(res[2:4]), {cm11, cm21})
        self.assertEqual(res[4], cm22)

        res = Comment.sort('user___name', '-created_at').all()
        self.assertEqual(res, [cm_empty, cm12, cm21, cm11, cm22])

        # hybrid_property
        res = Comment.sort('-post___public', 'post___user___name').all()
        self.assertEqual(set(res[:2]), {cm21, cm22})  # posts by same user
        self.assertEqual(res[2:], [cm12, cm11, cm_empty])


# noinspection PyUnusedLocal
class TestFullSmartQuery(BaseTest):
    def test_schema_with_strings(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        # standalone function
        query = Comment.query
        res = smart_query(query,
            filters={
                'post___public': True,
                'user__isnull': False
            },
            sort_attrs=['user___name', '-created_at'],
            schema={
                'post': {
                    'user': JOINED
                }
            }).all()
        self.assertEqual(res, [cm12, cm21, cm22])

        # class method
        res = Comment.smart_query(
            filters={
                'post___public': True,
                'user__isnull': False
            },
            sort_attrs=['user___name', '-created_at'],
            schema={
                'post': {
                    'user': JOINED
                }
            }).all()
        self.assertEqual(res, [cm12, cm21, cm22])

    def test_schema_with_class_properties(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        # standalone function
        query = Comment.query
        res = smart_query(query,
            filters={
                'post___public': True,
                'user__isnull': False
            },
            sort_attrs=['user___name', '-created_at'],
            schema={
                Comment.post: {
                    Post.user: JOINED
                }
            }).all()
        self.assertEqual(res, [cm12, cm21, cm22])

        # class method
        res = Comment.smart_query(
            filters={
                'post___public': True,
                'user__isnull': False
            },
            sort_attrs=['user___name', '-created_at'],
            schema={
                Comment.post: {
                    Post.user: JOINED
                }
            }).all()
        self.assertEqual(res, [cm12, cm21, cm22])


# noinspection PyUnusedLocal
class TestSmartQueryAutoEagerLoad(BaseTest):
    """
    Smart_query does auto-joins for filtering/sorting,
    so there's a sense to tell sqlalchemy that we alreeady joined that relation

    So we test that relations are set to be joinedload
     if they were used in smart_query()
    """

    def _seed(self):
        result = BaseTest._seed(self)

        self.query_count = 0

        @event.listens_for(sess.connection(), 'before_cursor_execute')
        def before_cursor_execute(conn, cursor, statement, parameters,
                                  context, executemany):
            self.query_count += 1

        return result

    def test_sort(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        self.query_count = 0
        res = Comment.sort('-post___public', 'post___user___name').all()
        self.assertEqual(self.query_count, 1)

        _ = res[0].post
        # no additional query needed: we used 'post' relation in smart_query()
        self.assertEqual(self.query_count, 1)

        _ = res[0].post.user
        # no additional query needed: we used 'post' relation in smart_query()
        self.assertEqual(self.query_count, 1)

        _ = res[0].post.comments
        # we didn't use post___comments, so additional query is needed
        self.assertEqual(self.query_count, 2)

    def test_where(self):
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        self.query_count = 0
        res = Comment.where(post___public=True,
                            post___user___name__like='Bi%').all()
        self.assertEqual(self.query_count, 1)

        _ = res[0].post
        # no additional query needed: we used 'post' relation in smart_query()
        self.assertEqual(self.query_count, 1)

        _ = res[0].post.user
        # no additional query needed: we used 'post' relation in smart_query()
        self.assertEqual(self.query_count, 1)

        _ = res[0].post.comments
        # we didn't use post___comments, so additional query is needed
        self.assertEqual(self.query_count, 2)

    def test_explicitly_set_in_schema_joinedload(self):
        """
        here we explicitly set in schema that we additionally want to load
         post___comments
        """
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        self.query_count = 0
        res = Comment.smart_query(
            filters=dict(post___public=True, post___user___name__like='Bi%'),
            schema={
                'post': {
                    'comments': JOINED
                }
            }
        )
        res = res.all()

        self.assertEqual(self.query_count, 1)

        _ = res[0].post
        # no additional query needed: we used 'post' relation in smart_query()
        self.assertEqual(self.query_count, 1)

        _ = res[0].post.user
        # no additional query needed: we used 'post' relation in smart_query()
        self.assertEqual(self.query_count, 1)

        # we didn't use post___comments,
        # BUT we explicitly set it in schema!
        # so additional query is NOT needed
        _ = res[0].post.comments
        self.assertEqual(self.query_count, 1)

    def test_explicitly_set_in_schema_subqueryload(self):
        """
        here we explicitly set in schema that we additionally want to load
         post___comments
        """
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        self.query_count = 0
        res = Comment.smart_query(
            filters=dict(post___public=True, post___user___name__like='Bi%'),
            schema={
                'post': {
                    'comments': SUBQUERY
                }
            }
        ).all()
        self.assertEqual(self.query_count, 2)

        _ = res[0].post
        # no additional query needed: we used 'post' relation in smart_query()
        self.assertEqual(self.query_count, 2)

        _ = res[0].post.user
        # no additional query needed: we used 'post' relation in smart_query()
        self.assertEqual(self.query_count, 2)

        # we didn't use post___comments,
        # BUT we explicitly set it in schema!
        # so additional query is NOT needed
        _ = res[0].post.comments
        self.assertEqual(self.query_count, 2)

    # TODO: implement below logic
    @unittest.expectedFailure
    def test_override_eagerload_method_in_schema(self):
        """
        here we use 'post' relation in filters,
        but we want to load 'post' relation in SEPARATE QUERY (subqueryload)
        so we set load method in schema
        """
        u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty = \
            self._seed()

        self.query_count = 0
        res = Comment.smart_query(
            filters=dict(post___public=True, post___user___name__like='Bi%'),
            schema={
                'post': SUBQUERY
            }
        ).all()
        self.assertEqual(self.query_count, 2)

        _ = res[0].post
        # no additional query needed: we used 'post' relation in smart_query()
        self.assertEqual(self.query_count, 2)

if __name__ == '__main__': # pragma: no cover
    unittest.main()
