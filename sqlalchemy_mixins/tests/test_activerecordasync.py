import unittest
import asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

from sqlalchemy_mixins.activerecord import ModelNotFoundError
from sqlalchemy_mixins import ActiveRecordMixinAsync, SmartQueryMixin


Base = declarative_base()

class AsyncBaseModel(Base, ActiveRecordMixinAsync, SmartQueryMixin):
    __abstract__ = True

class User(AsyncBaseModel):
    __tablename__ = 'user'
    __repr_attrs__ = ['name']
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    posts = relationship('Post', backref='user', lazy="selectin")
    posts_viewonly = relationship('Post', viewonly=True)


class Post(AsyncBaseModel):
    __tablename__ = 'post'
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    archived = sa.Column(sa.Boolean, default=False)
    comments = relationship('Comment', backref='post', lazy="selectin")

    @hybrid_property
    def public(self):
        return not self.archived

    @public.setter
    def public(self, public):
        self.archived = not public

class Comment(AsyncBaseModel):
    __tablename__ = 'comment'
    __repr_attrs__ = ['body']
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    post_id = sa.Column(sa.Integer, sa.ForeignKey('post.id'))
    user = relationship('User', backref='comments', lazy="selectin")


class TestAsyncActiveRecord(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine('sqlite+aiosqlite:///:memory:', echo=False)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        AsyncBaseModel.set_session(self.async_session)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_settable_attributes(self):
        self.assertEqual(set(User.settable_attributes),
                         {'id', 'name', 'posts', 'comments'})
        self.assertNotIn('posts_viewonly', set(User.settable_attributes))

        self.assertEqual(set(Post.settable_attributes),
                         {'id', 'body', 'user_id', 'archived',
                          'user', 'comments', 'public'})

        self.assertEqual(set(Comment.settable_attributes),
                         {'id', 'body', 'post_id', 'user_id',
                          'user', 'post'})

    async def test_create_and_save_async(self):
        u1 = User(name='Bill u1')
        await u1.save_async()

        async with self.async_session() as session:
            result = await session.execute(sa.select(User))
            saved = result.scalars().first()
            self.assertEqual(u1.id, saved.id)

        p11 = Post(body='p11', user=u1, public=False)
        await p11.save_async()

        async with self.async_session() as session:
            result = await session.execute(sa.select(Post))
            saved_post = result.scalars().first()
            self.assertEqual(p11.body, saved_post.body)
            self.assertEqual(saved_post.archived, True)

    async def test_create_async(self):
        u1 = await User.create_async(name='Bill u1')
        
        async with self.async_session() as session:
            result = await session.execute(sa.select(User))
            saved = result.scalars().first()
            self.assertEqual(u1.id, saved.id)

        p11 = await Post.create_async(body='p11', user=u1, public=False)
        
        async with self.async_session() as session:
            result = await session.execute(sa.select(Post))
            saved_post = result.scalars().first()
            self.assertEqual(p11.id, saved_post.id)
            self.assertEqual(saved_post.archived, True)

    async def test_update_async(self):
        u1 = await User.create_async(name='Bill', id=1)
        u2 = await User.create_async(name='Bishop', id=2)
        p11 = await Post.create_async(body='p11', user=u1, public=False, id=11)

        async with self.async_session() as session:
            result = await session.execute(
                sa.select(Post).options(selectinload(Post.user))
                .filter_by(id=11)
            )
            post = result.scalars().first()
            self.assertEqual(post.body, 'p11')
            self.assertEqual(post.public, False)
            self.assertEqual(post.user.id, u1.id)

        await p11.update_async(body='new body', public=True, user=u2)

        async with self.async_session() as session:
            result = await session.execute(
                sa.select(Post).options(selectinload(Post.user))
                .filter_by(id=11)
            )
            updated_post = result.scalars().first()
            self.assertEqual(updated_post.body, 'new body')
            self.assertEqual(updated_post.public, True)
            self.assertEqual(updated_post.user.id, u2.id)

    async def test_delete_async(self):
        u1 = await User.create_async(name='Bill', id=1)

        async with self.async_session() as session:
            result = await session.execute(sa.select(User).filter_by(id=1))
            saved = result.scalars().first()
            self.assertEqual(saved.id, u1.id)

        await u1.delete_async()

        async with self.async_session() as session:
            result = await session.execute(sa.select(User).filter_by(id=1))
            self.assertEqual(result.scalars().first(), None)

    async def test_destroy_async(self):
        u1 = await User.create_async(name='Bill', id=1)
        p11 = await Post.create_async(body='p11', user=u1, id=11)
        p12 = await Post.create_async(body='p12', user=u1, id=12)
        p13 = await Post.create_async(body='p13', user=u1, id=13)

        async with self.async_session() as session:
            result = await session.execute(sa.select(Post))
            self.assertEqual(set([u.id for u in result.scalars().all()]), {p11.id, p12.id, p13.id})

        await Post.destroy_async(11, 12)

        async with self.async_session() as session:
            result = await session.execute(sa.select(Post))
            got = result.scalars().all()
            self.assertEqual(len(got), 1)
            self.assertEqual(got[0].id, p13.id)

    async def test_all_async(self):
        u1 = await User.create_async(name='Bill', id=1)
        u2 = await User.create_async(name='Bishop', id=2)

        users = await User.all_async()
        self.assertEqual(set([u.id for u in users]), {u1.id, u2.id})

    async def test_first_async(self):
        u1 = await User.create_async(name='Bill', id=1)
        u2 = await User.create_async(name='Bishop', id=2)

        first_user = await User.first_async()
        self.assertEqual(first_user.id, u1.id)

    async def test_find_async(self):
        u1 = await User.create_async(name='Bill', id=1)
        u2 = await User.create_async(name='Bishop', id=2)

        found_user = await User.find_async(1)
        self.assertEqual(found_user.id, u1.id)

        not_found_user = await User.find_async(3)
        self.assertEqual(not_found_user, None)

    async def test_find_or_fail_async(self):
        u1 = await User.create_async(name='Bill', id=1)
        u2 = await User.create_async(name='Bishop', id=2)

        found_user = await User.find_or_fail_async(1)
        self.assertEqual(found_user.id, u1.id)

        with self.assertRaises(ModelNotFoundError):
            await User.find_or_fail_async(3)

if __name__ == '__main__':
    asyncio.run(unittest.main())