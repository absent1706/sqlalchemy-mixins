from __future__ import print_function
import os

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import scoped_session, sessionmaker

from sqlalchemy_mixins import ActiveRecordMixin, ReprMixin, ModelNotFoundError


def log(msg):
    print('\n{}\n'.format(msg))

#################### setup ######################
Base = declarative_base()


# we also use ReprMixin which is optional
class BaseModel(Base, ActiveRecordMixin, ReprMixin):
    __abstract__ = True
    __repr__ = ReprMixin.__repr__
    pass


class User(BaseModel):
    __tablename__ = 'user'
    __repr_attrs__ = ['name']  # we want to display name in repr string
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    age = sa.Column(sa.Integer)
    posts = sa.orm.relationship('Post', backref='user')


class Post(BaseModel):
    __tablename__ = 'post'
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    archived = sa.Column(sa.Boolean, default=False)

    # user = backref from User.post

    @hybrid_property
    def public(self):
        return not self.archived

    @public.setter
    def public(self, public):
        self.archived = not public

#################### setup ORM ######################
db_file = os.path.join(os.path.dirname(__file__), 'test.sqlite')
engine = create_engine('sqlite:///{}'.format(db_file), echo=True)
# autocommit=True - it's to make you see data in 3rd party DB view tool
session = scoped_session(sessionmaker(bind=engine, autocommit=True))

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

# setup base model: inject session so it can be accessed from model
BaseModel.set_session(session)

#################### CRUD demo ######################

# ['id', 'body', 'user_id', 'archived', # normal columns
#  'user', 'comments',  # relations
#  'public']  # hybrid attributes
print(Post.settable_attributes)

#### 1. ActiveRecordMixin.fill() and ActiveRecordMixin.save() ####
user1 = User()
# equal to
#  user1.name = 'Billy'
#  user1.age = 1
#  session.flush()
user1.fill(name='Billy', age=1)

# you can use kwargs as above or, in real-world apps, unpack dict as below
data = {'name': 'Bill', 'age': 21}
user1.fill(**data)

# equal to
#  session.add(user1)
#  session.flush()
user1.save()

#### 2. ActiveRecordMixin.create(): ####
# equal to
#  user2 = User(name='Bob')
#  session.add(user2)
#  session.flush()
user2 = User.create(name='Bob')
post1 = Post.create(body='post1', user=user2)

#### 3. ActiveRecordMixin.update(): ####
# equal to
#   post1.fill(...)
#   post1.save()
post1.update(body='new body', public=True, user=user1)

#### 4. ActiveRecordMixin.delete(): ####
# equal to
#  session.delete(post_to_be_deleted)
#  session.flush()
post_to_be_deleted = Post.create()
post_to_be_deleted.delete()

#### 5. ActiveRecordMixin.destroy() ####
# equal to
#  session.delete(session.query(User).get(91))
#  session.delete(session.query(User).get(92))
#  session.flush()
_ = User.create(id=91)
__ = User.create(id=92)
User.destroy(91, 92)


#################### Query demo ######################

#### 1. ActiveRecordMixin.all() ####
# equal to
#  session.query(User).all()
log('all users: ' + str(User.all()))

#### 2. ActiveRecordMixin.first() ####
# equal to
#  session.query(User).first()
log('first user: ' + str(User.first()))

#### 3. ActiveRecordMixin.find() ####
# equal to
#  session.query(User).get()
user3 = User.create(name='Bishop', id=3)
log('user with id=3: ' + str(User.find(3)))

#### 4. ActiveRecordMixin.find_or_fail() ####
# closest code on raw sqlalchemy will be
#  session.query(User).filter_by(id=<ID>).one()
# but one() method throws common error without describing which ID was not
#  found, which is inconvenient: http://www.qopy.me/c5Csw1vWTCuOMKuP07J7iA
try:
    print(User.find_or_fail(123987))
except ModelNotFoundError as e:
    log('!! find_or_fail: model not found !! \n' + str(e))
