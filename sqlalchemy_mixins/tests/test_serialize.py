import unittest

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Session

from sqlalchemy_mixins import SerializeMixin

Base = declarative_base()


class BaseModel(Base, SerializeMixin):
    __abstract__ = True
    pass


class User(BaseModel):
    __tablename__ = 'user'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    posts = sa.orm.relationship('Post')

    @hybrid_property
    def posts_count(self):
        return len(self.posts)


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

    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    post_id = sa.Column(sa.Integer, sa.ForeignKey('post.id'))
    rating = sa.Column(sa.Integer)

    user = sa.orm.relationship('User')
    post = sa.orm.relationship('Post')


class TestSerialize(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('sqlite:///:memory:', echo=False)

    def setUp(self):
        self.session = Session(self.engine)
        Base.metadata.create_all(self.engine)

        user_1 = User(name='Bill u1', id=1)
        self.session.add(user_1)
        self.session.commit()

        user_2 = User(name='Alex u2', id=2)
        self.session.add(user_2)
        self.session.commit()

        post_11 = Post(
            id=11,
            body='Post 11 body.',
            archived=True
        )
        post_11.user = user_1
        self.session.add(post_11)
        self.session.commit()

        comment_11 = Comment(
            id=11,
            body='Comment 11 body',
            user=user_1,
            post=post_11,
            rating=1
        )
        self.session.add(comment_11)
        self.session.commit()

    def tearDown(self):
        Base.metadata.drop_all(self.engine)

    def test_serialize_single(self):
        result = self.session.query(User).first().to_dict()
        expected = {
            'id': 1,
            'name': 'Bill u1'
        }
        self.assertDictEqual(result, expected)

    def test_serialize_list(self):
        result = [user.to_dict() for user in self.session.query(User).all()]
        expected = [
            {
                'id': 1,
                'name': 'Bill u1'
            },
            {
                'id': 2,
                'name': 'Alex u2'
            },
        ]

        self.assertListEqual(expected, result)

    def test_serialize_nested(self):
        result = self.session.query(Post).first().to_dict(nested=True)
        expected = {
            'id': 11,
            'body': 'Post 11 body.',
            'archived': True,
            'user_id': 1,
            'user': {
                'id': 1,
                'name': 'Bill u1'
            },
            'comments': [
                {
                    'id': 11,
                    'body': 'Comment 11 body',
                    'user_id': 1,
                    'post_id': 11,
                    'rating': 1,
                }
            ]
        }
        self.assertDictEqual(result, expected)

    def test_serialize_single__with_hybrid(self):
        result = self.session.query(User).first().to_dict(hybrid_attributes=True)
        expected = {
            'id': 1,
            'name': 'Bill u1',
            'posts_count': 1
        }
        self.assertDictEqual(result, expected)

    def test_serialize_nested__with_hybrid(self):
        result = self.session.query(Post).first().to_dict(nested=True, hybrid_attributes=True)
        expected = {
            'id': 11,
            'body': 'Post 11 body.',
            'archived': True,
            'user_id': 1,
            'user': {
                'id': 1,
                'name': 'Bill u1',
                'posts_count': 1
            },
            'comments': [
                {
                    'id': 11,
                    'body': 'Comment 11 body',
                    'user_id': 1,
                    'post_id': 11,
                    'rating': 1,
                }
            ]
        }
        self.assertDictEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
