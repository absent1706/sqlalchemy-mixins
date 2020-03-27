from __future__ import print_function

import time
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from sqlalchemy_mixins import TimestampsMixin

Base = declarative_base()
engine = sa.create_engine("sqlite:///:memory:")
session = scoped_session(sessionmaker(bind=engine))


class BaseModel(Base, TimestampsMixin):
    __abstract__ = True
    pass


class User(BaseModel):
    """User Model to example."""

    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)


Base.metadata.create_all(engine)


print("Current time:   ", datetime.utcnow())
# Current time:    2019-03-04 03:53:53.605602

bob = User(name="Bob")
session.add(bob)
session.flush()

print("Created Bob:    ", bob.created_at)
# Created Bob:     2019-03-04 03:53:53.606765

print("Pre-update Bob: ", bob.updated_at)
# Pre-update Bob:  2019-03-04 03:53:53.606769

time.sleep(2)

bob.name = "Robert"
session.commit()

print("Updated Bob:    ", bob.updated_at)
# Updated Bob:     2019-03-04 03:53:55.613044
