import unittest
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from sqlalchemy_mixins import TimestampMixin

Base = declarative_base()


class BaseModel(Base, TimestampMixin):
    """Model to use as base."""

    __abstract__ = True

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)


class User(BaseModel):
    """User model exemple."""

    __tablename__ = 'user'


class UserCustomDatimeCallback(BaseModel):
    """User model with custom `__datetime_callback__`."""

    __tablename__ = 'user_custom_datetime_callback'
    __datetime_callback__ = datetime.now


class TestTimestamp(unittest.TestCase):
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

        user_2 = UserCustomDatimeCallback(name='Custom Datetime callback')
        self.session.add(user_2)
        self.session.commit()

    def tearDown(self):
        Base.metadata.drop_all(self.engine)

    def test_timestamp_must_be_abstract(self):
        """Test whether TimestampMixin is abstract."""
        self.assertTrue(hasattr(TimestampMixin, '__abstract__'),
                        'TimestampMixin must have attribute __abstract__')
        self.assertTrue(TimestampMixin.__abstract__,
                        '__abstract__ must be True')

    def test_timestamp_has_datetime_columns(self):
        """Test whether TimestampMixin has attrs created_at and updated_at."""
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

    def test_datetime_callback_could_be_customized(self):
        """Test whether __datetime_callback__ is customized."""
        expected = 'now'
        result = UserCustomDatimeCallback.__datetime_callback__.__name__

        self.assertNotEqual(TimestampMixin.__datetime_callback__.__name__,
                            result)
        self.assertEqual(expected, result,
                         '__datetime_callback__ was\'t custom')


if __name__ == '__main__':
    unittest.main()
