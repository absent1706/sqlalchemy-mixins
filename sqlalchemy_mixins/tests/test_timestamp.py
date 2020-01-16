import unittest
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from sqlalchemy_mixins import TimestampsMixin

Base = declarative_base()


class BaseModel(Base, TimestampsMixin):
    """Model to use as base."""

    __abstract__ = True

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)


class User(BaseModel):
    """User model exemple."""

    __tablename__ = 'user'


class TestTimestamps(unittest.TestCase):
    """Test case for Timestamp mixin."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('sqlite:///:memory:', echo=False)

    def setUp(self):
        self.session = Session(self.engine)
        Base.metadata.create_all(self.engine)

        user_1 = User(name='User')
        self.session.add(user_1)
        self.session.commit()

    def tearDown(self):
        Base.metadata.drop_all(self.engine)

    def test_timestamp_must_be_abstract(self):
        """Test whether TimestampsMixin is abstract."""
        self.assertTrue(hasattr(TimestampsMixin, '__abstract__'),
                        'TimestampsMixin must have attribute __abstract__')
        self.assertTrue(TimestampsMixin.__abstract__,
                        '__abstract__ must be True')

    def test_timestamp_has_datetime_columns(self):
        """Test whether TimestampsMixin has attrs created_at and updated_at."""
        user = self.session.query(User).first()

        self.assertTrue(hasattr(User, 'created_at'),
                        'Timestamp doesn\'t have created_at attribute.')
        self.assertEqual(datetime, type(user.created_at),
                         'created_at column should be datetime')

        self.assertTrue(hasattr(User, 'updated_at'),
                        'Timestamp doesn\'t have updated_at attribute.')
        self.assertEqual(datetime, type(user.updated_at),
                         'updated_at column should be datetime')

    def test_updated_at_column_must_change_value(self):
        """Test whether updated_at value is most recently after update."""
        user = self.session.query(User).first()
        dt_1 = user.updated_at

        user.name = 'New name'
        self.session.commit()

        dt_2 = user.updated_at

        self.assertLess(dt_1, dt_2, 'dt_1 should be older than dt_2')


if __name__ == '__main__':
    unittest.main()
