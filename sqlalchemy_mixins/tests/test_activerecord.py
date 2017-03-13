import unittest

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Query, Session

from sqlalchemy_mixins import ActiveRecordMixin
from sqlalchemy_mixins.activerecord import ModelNotFoundError

Base = declarative_base()
engine = create_engine('sqlite:///:memory:', echo=False)
sess = Session(engine)
# sess = scoped_session(sessionmaker(bind=engine))


class BaseModel(Base, ActiveRecordMixin):
    __abstract__ = True
    pass


class User(BaseModel):
    __tablename__ = 'user'
    __repr_attrs__ = ['name']
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    posts = sa.orm.relationship('Post', backref='user')
    posts_viewonly = sa.orm.relationship('Post', viewonly=True)


class Post(BaseModel):
    __tablename__ = 'post'
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    archived = sa.Column(sa.Boolean, default=False)

    # user = backref from User.post
    comments = sa.orm.relationship('Comment', backref='post')

    @hybrid_property
    def public(self):
        return not self.archived

    @public.setter
    def public(self, public):
        self.archived = not public


class Comment(BaseModel):
    __tablename__ = 'comment'
    __repr_attrs__ = ['body']
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    post_id = sa.Column(sa.Integer, sa.ForeignKey('post.id'))

    user = sa.orm.relationship('User', backref='comments')
    # post = backref from Post.comments


class TestActiveRecord(unittest.TestCase):
    def setUp(self):
        sess.rollback()

        BaseModel.set_session(None)
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

        BaseModel.set_session(sess)

    def test_settable_attributes(self):
        self.assertEqual(set(User.settable_attributes),
                         {'id', 'name',  # normal columns
                          'posts', 'comments'  # relations
                          })
        self.assertNotIn('posts_viewonly', set(User.settable_attributes))

        self.assertEqual(set(Post.settable_attributes),
                         {'id', 'body', 'user_id', 'archived',
                          # normal columns
                          'user', 'comments',  # relations
                          'public'  # hybrid attributes
                          })
        self.assertEqual(set(Comment.settable_attributes),
                         {'id', 'body', 'post_id', 'user_id',  # normal columns
                          'user', 'post'  # hybrid attributes
                          })

    def test_fill_and_save(self):
        u1 = User()
        u1.fill(name='Bill u1')
        u1.save()

        self.assertEqual(u1, sess.query(User).first())

        p11 = Post()
        p11.fill(body='p11', user=u1, public=False)
        p11.save()

        self.assertEqual(p11, sess.query(Post).first())
        self.assertEqual(p11.archived, True)

    def test_create(self):
        u1 = User.create(name='Bill u1')
        self.assertEqual(u1, sess.query(User).first())

        p11 = Post.create(body='p11', user=u1, public=False)
        self.assertEqual(p11, sess.query(Post).first())
        self.assertEqual(p11.archived, True)

    @staticmethod
    def _seed():
        u1 = User(name='Bill', id=1)
        sess.add(u1)
        sess.flush()

        u2 = User(name='Bishop', id=2)
        sess.add(u2)
        sess.flush()

        p11 = Post(body='p11', user=u1, public=False, id=11)
        sess.add(p11)
        sess.flush()

        p12 = Post(body='p12', user=u2, id=12)
        sess.add(p12)
        sess.flush()

        p13 = Post(body='p13', user=u1, id=13)
        sess.add(p13)
        sess.flush()

        return u1, u2, p11, p12, p13

    def test_update(self):
        u1, u2, p11, p12, p13 = self._seed()

        self.assertEqual(sess.query(Post).get(11).body, 'p11')
        self.assertEqual(sess.query(Post).get(11).public, False)
        self.assertEqual(sess.query(Post).get(11).user, u1)
        p11.update(body='new body', public=True, user=u2)
        self.assertEqual(sess.query(Post).get(11).body, 'new body')
        self.assertEqual(sess.query(Post).get(11).public, True)
        self.assertEqual(sess.query(Post).get(11).user, u2)

    def test_fill_wrong_attribute(self):
        u1 = User(name='Bill u1')
        sess.add(u1)
        sess.flush()

        with self.assertRaises(KeyError):
            u1.fill(INCORRECT_ATTRUBUTE='nomatter')

        with self.assertRaises(KeyError):
            u1.update(INCORRECT_ATTRUBUTE='nomatter')

        with self.assertRaises(KeyError):
            User.create(INCORRECT_ATTRUBUTE='nomatter')

    def test_delete(self):
        u1, u2, p11, p12, p13 = self._seed()

        self.assertEqual(sess.query(User).get(1), u1)
        u1.delete()
        self.assertEqual(sess.query(User).get(1), None)

    def test_destroy(self):
        u1, u2, p11, p12, p13 = self._seed()

        self.assertEqual(set(sess.query(Post).all()), {p11, p12, p13})
        Post.destroy(11, 12)
        self.assertEqual(set(sess.query(Post).all()), {p13})

    def test_all(self):
        u1, u2, p11, p12, p13 = self._seed()

        self.assertEqual(set(User.all()), {u1, u2})
        self.assertEqual(set(Post.all()), {p11, p12, p13})

    def test_first(self):
        u1 = User()
        sess.add(u1)
        sess.flush()

        self.assertEqual(User.first(), u1)

    def test_find(self):
        u1, u2, p11, p12, p13 = self._seed()

        self.assertEqual(User.find(1), u1)
        self.assertEqual(User.find(2), u2)

        self.assertEqual(User.find(123456789), None)

    def test_find_or_fail(self):
        u1, u2, p11, p12, p13 = self._seed()

        self.assertEqual(User.find_or_fail(1), u1)
        self.assertEqual(User.find_or_fail(2), u2)

        with self.assertRaises(ModelNotFoundError):
            _ = User.find_or_fail(123456789)


if __name__ == '__main__': # pragma: no cover
    unittest.main()
