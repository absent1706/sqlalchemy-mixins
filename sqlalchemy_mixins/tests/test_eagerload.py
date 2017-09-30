import unittest

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Query
from sqlalchemy.orm import Session

from sqlalchemy_mixins import EagerLoadMixin
from sqlalchemy_mixins.eagerload import JOINED, SUBQUERY, eager_expr

Base = declarative_base()
engine = create_engine('sqlite:///:memory:', echo=False)
sess = Session(engine)
# sess = scoped_session(sessionmaker(bind=engine))


class BaseModel(Base, EagerLoadMixin):
    __abstract__ = True
    pass


class User(BaseModel):
    __tablename__ = 'user'
    __repr_attrs__ = ['name']
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    posts = sa.orm.relationship('Post')


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
    __repr_attrs__ = ['body']
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    post_id = sa.Column(sa.Integer, sa.ForeignKey('post.id'))
    rating = sa.Column(sa.Integer)

    user = sa.orm.relationship('User')
    post = sa.orm.relationship('Post')


class TestEagerLoad(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

        BaseModel.set_session(sess)
        u1 = User(name='Bill u1')
        sess.add(u1)
        sess.commit()

        u2 = User(name='Alex u2')
        sess.add(u2)
        sess.commit()

        u3 = User(name='Bishop u3')
        sess.add(u3)
        sess.commit()

        # u4 = User()
        # u4.name = 'u4'
        # sess.add(u4)
        # sess.commit()

        sess.commit()

        p11 = Post(
            id=11,
            body='1234567890123',
            archived=True
        )
        p11.user = u1
        sess.add(p11)
        sess.commit()

        p12 = Post(
            id=12,
            body='1234567890',
            user=u1
        )
        sess.add(p12)
        sess.commit()

        p21 = Post(
            id=21,
            body='p21 by u2',
            user=u2
        )
        sess.add(p21)
        sess.commit()

        p22 = Post(
            id=22,
            body='p22 by u2',
            user=u2
        )
        sess.add(p22)
        sess.commit()

        cm11 = Comment(
            id=11,
            body='cm11 to p11',
            user=u1,
            post=p11,
            rating=1
        )
        sess.add(cm11)
        sess.commit()

        cm12 = Comment(
            id=12,
            body='cm12 to p12',
            user=u2,
            post=p11,
            rating=2
        )
        sess.add(cm12)
        sess.commit()

        cm21 = Comment(
            id=21,
            body='cm21 to p21',
            user=u1,
            post=p21,
            rating=1
        )
        sess.add(cm21)
        sess.commit()

        cm22 = Comment(
            id=22,
            body='cm22 to p22',
            user=u3,
            post=p22,
            rating=3
        )
        sess.add(cm22)
        sess.commit()

        self.query_count = 0

        # noinspection PyUnusedLocal
        @event.listens_for(sess.connection(), 'before_cursor_execute')
        def before_cursor_execute(conn, cursor, statement, parameters,
                                  context, executemany):
            self.query_count += 1


class TestNoEagerLoad(TestEagerLoad):
    def test_no_eagerload(self):
        self.assertEqual(self.query_count, 0)
        post = Post.query.get(11)
        self.assertEqual(self.query_count, 1)

        # to get relationship, ADDITIONAL query is needed
        comment = post.comments[0]
        self.assertEqual(self.query_count, 2)

        # to get relationship, ADDITIONAL query is needed
        _ = comment.user
        self.assertEqual(self.query_count, 3)


class TestEagerExpr(TestEagerLoad):
    """test of low-level eager_expr function"""
    def _test_ok(self, schema):
        self.assertEqual(self.query_count, 0)
        user = sess.query(User).options(*eager_expr(schema)).get(1)
        self.assertEqual(self.query_count, 2)

        # now, to get relationships, NO additional query is needed
        post = user.posts[0]
        _ = post.comments[0]
        self.assertEqual(self.query_count, 2)

    def test_ok_strings(self):
        schema = {
            User.posts: (SUBQUERY, {
                Post.comments: JOINED
            })
        }
        self._test_ok(schema)

    def test_ok_class_properties(self):
        schema = {
            'posts': (SUBQUERY, {
                'comments': JOINED
            })
        }
        self._test_ok(schema)

    def test_bad_join_method(self):
        # None
        schema = {
            'posts': None
        }
        with self.assertRaises(ValueError):
            sess.query(User).options(*eager_expr(schema)).get(1)

        # strings
        schema = {
            'posts': ('WRONG JOIN METHOD', {
                Post.comments: 'OTHER WRONG JOIN METHOD'
            })
        }
        with self.assertRaises(ValueError):
            sess.query(User).options(*eager_expr(schema)).get(1)

        # class properties
        schema = {
            User.posts: ('WRONG JOIN METHOD', {
                Post.comments: 'OTHER WRONG JOIN METHOD'
            })
        }
        with self.assertRaises(ValueError):
            sess.query(User).options(*eager_expr(schema)).get(1)


class TestOrmWithJoinedStrings(TestEagerLoad):
    def test(self):
        self.assertEqual(self.query_count, 0)
        # take post with user and comments (including comment author)
        # NOTE: you can separate relations with dot.
        # Its due to SQLAlchemy: https://goo.gl/yM2DLX
        post = Post.with_joined('user', 'comments', 'comments.user').get(11)
        self.assertEqual(self.query_count, 1)

        # now, to get relationship, NO additional query is needed
        _ = post.user
        _ = post.comments[1]
        _ = post.comments[1].user
        self.assertEqual(self.query_count, 1)


class TestOrmWithJoinedClassProperties(TestEagerLoad):
    def _test(self):
        self.assertEqual(self.query_count, 0)
        post = Post.with_joined(Post.comments, Post.user).get(11)
        self.assertEqual(self.query_count, 1)

        # now, to get relationship, NO additional query is needed
        _ = post.comments[0]
        _ = post.user
        self.assertEqual(self.query_count, 1)


class TestOrmWithSubquery(TestEagerLoad):
    def test(self):
        self.assertEqual(self.query_count, 0)
        # take post with user and comments (including comment author)
        # NOTE: you can separate relations with dot.
        # Its due to SQLAlchemy: https://goo.gl/yM2DLX
        post = Post.with_subquery('user', 'comments', 'comments.user').get(11)

        # 3 queries were executed:
        #   1 - on posts
        #   2 - on user (eagerload subquery)
        #   3 - on comments (eagerload subquery)
        #   4 - on comments authors (eagerload subquery)
        self.assertEqual(self.query_count, 4)

        # now, to get relationship, NO additional query is needed
        _ = post.user
        _ = post.comments[0]
        _ = post.comments[0].user
        self.assertEqual(self.query_count, 4)


class TestOrmWithSubqueryClassProperties(TestEagerLoad):
    def test(self):
        self.assertEqual(self.query_count, 0)
        post = Post.with_subquery(Post.comments, Post.user).get(11)
        # 3 queries were executed:
        #   1 - on posts
        #   2 - on comments (eagerload subquery)
        #   3 - on user (eagerload subquery)
        self.assertEqual(self.query_count, 3)

        # now, to get relationship, NO additional query is needed
        _ = post.comments[0]
        _ = post.user
        self.assertEqual(self.query_count, 3)


class TestOrmWithDict(TestEagerLoad):
    def _test_joinedload(self, schema):
        self.assertEqual(self.query_count, 0)
        post = Post.with_(schema).get(11)
        self.assertEqual(self.query_count, 1)

        # now, to get relationship, NO additional query is needed
        _ = post.comments[0]
        self.assertEqual(self.query_count, 1)

    def test_joinedload_strings(self):
        schema = {'comments': JOINED}
        self._test_joinedload(schema)

    def test_joinedload_class_properties(self):
        schema = {Post.comments: JOINED}
        self._test_joinedload(schema)

    def _test_subqueryload(self, schema):
        self.assertEqual(self.query_count, 0)
        post = Post.with_(schema).get(11)
        self.assertEqual(self.query_count, 2)

        # to get relationship, NO additional query is needed
        _ = post.comments[0]
        self.assertEqual(self.query_count, 2)

    def test_subqueryload_strings(self):
        schema = {'comments': SUBQUERY}
        self._test_subqueryload(schema)

    def test_subqueryload_class_properties(self):
        schema = {Post.comments: SUBQUERY}
        self._test_subqueryload(schema)

    def _test_combined_load(self, schema):
        self.assertEqual(self.query_count, 0)
        user = User.with_(schema).get(1)
        self.assertEqual(self.query_count, 2)

        # now, to get relationships, NO additional query is needed
        post = user.posts[0]
        _ = post.comments[0]
        self.assertEqual(self.query_count, 2)

    def test_combined_load_strings(self):
        schema = {
            User.posts: (SUBQUERY, {
                Post.comments: JOINED
            })
        }
        self._test_combined_load(schema)

    def test_combined_load_class_properties(self):
        schema = {
            'posts': (SUBQUERY, {
                'comments': JOINED
            })
        }
        self._test_combined_load(schema)

    def _test_combined_load_2(self, schema):
        self.assertEqual(self.query_count, 0)
        user = User.with_(schema).get(1)
        self.assertEqual(self.query_count, 2)

        # now, to get relationships, NO additional query is needed
        post = user.posts[0]
        comment = post.comments[0]
        _ = comment.user
        self.assertEqual(self.query_count, 2)


if __name__ == '__main__': # pragma: no cover
    unittest.main()
