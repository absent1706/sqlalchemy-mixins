import unittest

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import sessionmaker

from sqlalchemy_mixins import InspectionMixin

Base = declarative_base()
engine = create_engine('sqlite:///:memory:', echo=False)


class BaseModel(Base, InspectionMixin):
    __abstract__ = True
    pass


class User(BaseModel):
    __tablename__ = 'user'
    id = sa.Column(sa.Integer, primary_key=True)
    first_name = sa.Column(sa.String)
    last_name = sa.Column(sa.String)

    posts = sa.orm.relationship('Post', backref='user')
    posts_viewonly = sa.orm.relationship('Post', viewonly=True)

    @hybrid_property
    def surname(self):
        return self.last_name

    @surname.expression
    def surname(cls):
        return cls.last_name

    @hybrid_method
    def with_first_name(cls):
        return cls.first_name != None


class Post(BaseModel):
    __tablename__ = 'post'
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))


class Parent(BaseModel):
    __tablename__ = 'parent'
    id = sa.Column(sa.Integer, primary_key=True)


class Child(Parent):
    some_prop = sa.Column(sa.String)


class ModelWithTwoPks(BaseModel):
    __tablename__ = 'two_pks'
    pk1 = sa.Column(sa.Integer, primary_key=True)
    pk2 = sa.Column(sa.Integer, primary_key=True)


class TestSessionMixin(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)

    def test_columns(self):
        self.assertEqual(set(User.columns), {'id', 'first_name', 'last_name'})
        self.assertEqual(set(Post.columns), {'id', 'body', 'user_id'})

    def test_nested_columns(self):
        self.assertEqual(set(Parent.columns), {'id'})
        self.assertEqual(set(Child.columns), {'id', 'some_prop'})

    def test_primary_keys(self):
        self.assertEqual(set(User.primary_keys), {'id'})
        self.assertEqual(set(ModelWithTwoPks.primary_keys), {'pk1', 'pk2'})

    def test_relations(self):
        self.assertEqual(set(User.relations), {'posts', 'posts_viewonly'})
        # backref also works!
        self.assertEqual(set(Post.relations), {'user'})

    def test_settable_relations(self):
        self.assertEqual(set(User.settable_relations), {'posts'})

    def test_hybrid_attributes(self):
        self.assertEqual(set(User.hybrid_properties), {'surname'})
        self.assertEqual(Post.hybrid_properties, [])

    def test_hybrid_methods(self):
        self.assertEqual(set(User.hybrid_methods), {'with_first_name'})
        self.assertEqual(Post.hybrid_methods, [])

    def tearDown(self):
        Base.metadata.create_all(engine)

if __name__ == '__main__': # pragma: no cover
    unittest.main()
