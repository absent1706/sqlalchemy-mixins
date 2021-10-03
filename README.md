![example workflow](https://github.com/absent1706/sqlalchemy-mixins/actions/workflows/test-pr.yml/badge.svg)
[![PyPI version](https://img.shields.io/pypi/v/sqlalchemy_mixins.svg)](https://pypi.python.org/pypi/sqlalchemy_mixins)

# SQLAlchemy mixins

**Note**: As of **v1.3**, only python **3.5+** is supported.

A pack of framework-agnostic, easy-to-integrate and well tested mixins for SQLAlchemy ORM.

Heavily inspired by [Django ORM](https://docs.djangoproject.com/en/1.10/topics/db/queries/)
and [Eloquent ORM](https://laravel.com/docs/5.4/eloquent)

Why it's cool:
 * framework-agnostic
 * easy integration to your existing project:
   ```python
    from sqlalchemy_mixins import AllFeaturesMixin

    class User(Base, AllFeaturesMixin):
         pass
    ```
 * clean code, splitted by modules
 * follows best practices of
    [Django ORM](https://docs.djangoproject.com/en/1.10/topics/db/queries/),
    [Peewee](http://docs.peewee-orm.com/)
    and [Eloquent ORM](https://laravel.com/docs/5.4/eloquent#retrieving-single-models),
 * 95%+ test coverage
 * already powers a big project

> Russian readers, see related **[article on habrahabr.ru](https://habrahabr.ru/post/324876/)**

## Table of Contents

1. [Installation](#installation)
1. [Quick Start](#quick-start)
    1. [Framework-agnostic](#framework-agnostic)
    1. [Usage with Flask-SQLAlchemy](#usage-with-flask-sqlalchemy)
1. [Features](#features)
    1. [Active Record](#active-record)
        1. [CRUD](#crud)
        1. [Querying](#querying)
    1. [Eager Load](#eager-load)
    1. [Django-like queries](#django-like-queries)
        1. [Filter and sort by relations](#filter-and-sort-by-relations)
        1. [Automatic eager load relations](#automatic-eager-load-relations)
    1. [All-in-one: smart_query](#all-in-one-smart_query)
    1. [Beauty \_\_repr\_\_](#beauty-__repr__)
    1. [Serialize to dict](#serialize-to-dict)
    1. [Timestamps](#timestamps)
1. [Internal architecture notes](#internal-architecture-notes)
1. [Comparison with existing solutions](#comparison-with-existing-solutions)
1. [Changelog](#changelog)

## Installation

Use pip
```
pip install sqlalchemy_mixins
```

Run tests
```
python -m unittest discover sqlalchemy_mixins/
```

## Quick Start

### Framework-agnostic
Here's a quick demo of what our mixins can do.

```python
bob = User.create(name='Bob')
post1 = Post.create(body='Post 1', user=bob, rating=3)
post2 = Post.create(body='long-long-long-long-long body', rating=2,
                    user=User.create(name='Bill'),
                    comments=[Comment.create(body='cool!', user=bob)])

# filter using operators like 'in' and 'contains' and relations like 'user'
# will output this beauty: <Post #1 body:'Post1' user:'Bill'>
print(Post.where(rating__in=[2, 3, 4], user___name__like='%Bi%').all())
# joinedload post and user
print(Comment.with_joined('user', 'post', 'post.comments').first())
# subqueryload posts and their comments
print(User.with_subquery('posts', 'posts.comments').first())
# sort by rating DESC, user name ASC
print(Post.sort('-rating', 'user___name').all())
# created_at, updated_at timestamps added automatically
print("Created Bob at ", bob.created_at)   
# serialize to dict, with relationships
print(bob.to_dict(nested=True).all())
```

![icon](http://i.piccy.info/i9/c7168c8821f9e7023e32fd784d0e2f54/1489489664/1113/1127895/rsz_18_256.png)
See [full example](examples/all_features.py)

> To interactively play with this example from CLI, [install iPython](https://ipython.org/install.html) and type `ipython -i examples\all_features.py`

### Usage with Flask-SQLAlchemy

```python
import sqlalchemy as sa
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_mixins import AllFeaturesMixin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
db = SQLAlchemy(app)

######### Models ######### 
class BaseModel(db.Model, AllFeaturesMixin):
    __abstract__ = True
    pass


class User(BaseModel):
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)

######## Initialize ########
BaseModel.set_session(db.session)

######## Create test entity ########
db.create_all()
user = User.create(name='bob')
print(user)
```

# *** Autocommit ***
This library relies on SQLAlchemy's `autocommit` flag. It needs to be set to True when initializing the session i.e:
```python
session = scoped_session(sessionmaker(bind=engine, autocommit=True))
BaseModel.set_session(session)
```
or with `Flask-SQLAlchemy`
```python
db = SQLAlchemy(app, session_options={'autocommit': True})
```

# Features

Main features are
 * [Active Record](#active-record)
 * [Eager Load](#eager-load)
 * [Django-like queries](#django-like-queries)
 * [Beauty \_\_repr\_\_](#beauty-__repr__)
 * [Timestamps](#timestamps)
 * [Serialize to dict](#serialize-to-dict)

## Active Record
provided by [`ActiveRecordMixin`](sqlalchemy_mixins/activerecord.py)

SQLAlchemy's [Data Mapper](https://en.wikipedia.org/wiki/Data_mapper_pattern)
pattern is cool, but
[Active Record](https://en.wikipedia.org/wiki/Active_record_pattern)
pattern is easiest and more [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself).

Well, we implemented it on top of Data Mapper!
All we need is to just inject [session](http://docs.sqlalchemy.org/en/latest/orm/session.html) into ORM class while bootstrapping our app:

```python
BaseModel.set_session(session)
# now we have access to BaseOrmModel.session property
```

### CRUD
We all love SQLAlchemy, but doing [CRUD](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete)
is a bit tricky there.

For example, creating an object needs 3 lines of code:
```python
bob = User(name='Bobby', age=1)
session.add(bob)
session.flush()
```

Well, having access to session from model, we can just write
```python
bob = User.create(name='Bobby', age=1)
```
that's how it's done in [Django ORM](https://docs.djangoproject.com/en/1.10/ref/models/querysets/#create)
and [Peewee](http://docs.peewee-orm.com/en/latest/peewee/querying.html#creating-a-new-record)

update and delete methods are provided as well
```python
bob.update(name='Bob', age=21)
bob.delete()
```

And, as in [Django](https://docs.djangoproject.com/en/1.10/topics/db/queries/#retrieving-a-single-object-with-get)
and [Eloquent](https://laravel.com/docs/5.4/eloquent#retrieving-single-models),
we can quickly retrieve object by id
```python
User.find(1) # instead of session.query(User).get(1)
```

and fail if such id doesn't exist
```python
User.find_or_fail(123987) # will raise sqlalchemy_mixins.ModelNotFoundError
```

![icon](http://i.piccy.info/i9/c7168c8821f9e7023e32fd784d0e2f54/1489489664/1113/1127895/rsz_18_256.png)
See [full example](examples/activerecord.py) and [tests](sqlalchemy_mixins/tests/test_activerecord.py)

### Querying
As in [Flask-SQLAlchemy](http://flask-sqlalchemy.pocoo.org/2.1/queries/#querying-records),
[Peewee](http://docs.peewee-orm.com/en/latest/peewee/api.html#Model.select)
and [Django ORM](https://docs.djangoproject.com/en/1.10/topics/db/queries/#retrieving-objects),
you can quickly query some class
```python
User.query # instead of session.query(User)
```

Also we can quickly retrieve first or all objects:
```python
User.first() # instead of session.query(User).first()
User.all() # instead of session.query(User).all()
```

![icon](http://i.piccy.info/i9/c7168c8821f9e7023e32fd784d0e2f54/1489489664/1113/1127895/rsz_18_256.png)
See [full example](examples/activerecord.py) and [tests](sqlalchemy_mixins/tests/test_activerecord.py)

## Eager load
provided by [`EagerLoadMixin`](sqlalchemy_mixins/eagerload.py)

### Nested eager load
If you use SQLAlchemy's [eager loading](http://docs.sqlalchemy.org/en/latest/orm/tutorial.html#eager-loading),
you may find it not very convenient, especially when we want, say,
load user, all his posts and comments to every his post in the same query.

Well, now you can easily set what ORM relations you want to eager load
```python
User.with_({
    'posts': {
        'comments': {
            'user': JOINED
        }
    }
}).all()
```

or we can write class properties instead of strings:
```python
User.with_({
    User.posts: {
        Post.comments: {
            Comment.user: JOINED
        }
    }
}).all()
```

### Subquery load
Sometimes we want to load relations in separate query, i.e. do [subqueryload](http://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html#sqlalchemy.orm.subqueryload).
For example, we load posts on page like [this](http://www.qopy.me/3V4Tsu_GTpCMJySzvVH1QQ),
and for each post we want to have user and all comments (and comment authors).

To speed up query, we load comments in separate query, but, in this separate query, join user
```python
from sqlalchemy_mixins import JOINED, SUBQUERY
Post.with_({
    'user': JOINED, # joinedload user
    'comments': (SUBQUERY, {  # load comments in separate query
        'user': JOINED  # but, in this separate query, join user
    })
}).all()
```

Here, posts will be loaded on first query, and comments with users - in second one.
See [SQLAlchemy docs](http://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html)
for explaining relationship loading techniques.

### Quick eager load
For simple cases, when you want to just 
[joinedload](http://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html#sqlalchemy.orm.joinedload)
or [subqueryload](http://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html#sqlalchemy.orm.subqueryload) 
a few relations, we have easier syntax for you:

```python
Comment.with_joined('user', 'post', 'post.comments').first()
User.with_subquery('posts', 'posts.comments').all()
```

> Note that you can split relations with dot like `post.comments`
> due to [this SQLAlchemy feature](http://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html#sqlalchemy.orm.subqueryload_all)


![icon](http://i.piccy.info/i9/c7168c8821f9e7023e32fd784d0e2f54/1489489664/1113/1127895/rsz_18_256.png)
See [full example](examples/eagerload.py) and [tests](sqlalchemy_mixins/tests/test_eagerload.py)

## Filter and sort by relations
provided by [`SmartQueryMixin`](sqlalchemy_mixins/smartquery.py)

### Django-like queries
We implement Django-like
[field lookups](https://docs.djangoproject.com/en/1.10/topics/db/queries/#field-lookups)
and
[automatic relation joins](https://docs.djangoproject.com/en/1.10/topics/db/queries/#lookups-that-span-relationships).

It means you can **filter and sort dynamically by attributes defined in strings!**

So, having defined `Post` model with `Post.user` relationship to `User` model,
you can write
```python
Post.where(rating__gt=2, user___name__like='%Bi%').all() # post rating > 2 and post user name like ...
Post.sort('-rating', 'user___name').all() # sort by rating DESC, user name ASC
```
(`___` splits relation and attribute, `__` splits attribute and operator)

> If you need more flexibility, you can use low-level `filter_expr` method `session.query(Post).filter(*Post.filter_expr(rating__gt=2, body='text'))`, [see example](examples/smartquery.py#L232).
>
> It's like [`filter_by` in SQLALchemy](http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.filter_by), but also allows magic operators like `rating__gt`.
>
> Note: `filter_expr` method is very low-level and does NOT do magic Django-like joins. Use [`smart_query`](#all-in-one-smart_query) for that.

> **All relations used in filtering/sorting should be _explicitly set_, not just being a backref**
>
> In our example, `Post.user` relationship should be defined in `Post` class even if `User.posts` is defined too.
>
> So, you can't type
> ```python
> class User(BaseModel):
>     # ...
>     user = sa.orm.relationship('User', backref='posts')
> ```
> and skip defining `Post.user` relationship. You must define it anyway:
>
> ```python
> class Post(BaseModel):
>     # ...
>     user = sa.orm.relationship('User') # define it anyway
> ```

For DRY-ifying your code and incapsulating business logic, you can use
SQLAlchemy's [hybrid attributes](http://docs.sqlalchemy.org/en/latest/orm/extensions/hybrid.html)
and [hybrid_methods](http://docs.sqlalchemy.org/en/latest/orm/extensions/hybrid.html?highlight=hybrid_method#sqlalchemy.ext.hybrid.hybrid_method).
Using them in our filtering/sorting is straightforward (see examples and tests).

![icon](http://i.piccy.info/i9/c7168c8821f9e7023e32fd784d0e2f54/1489489664/1113/1127895/rsz_18_256.png)
See [full example](examples/smartquery.py) and [tests](sqlalchemy_mixins/tests/test_smartquery.py)

### Automatic eager load relations
Well, as [`SmartQueryMixin`](sqlalchemy_mixins/smartquery.py) does auto-joins for filtering/sorting,
there's a sense to tell sqlalchemy that we already joined that relation.

So that relations are automatically set to be joinedload if they were used for filtering/sorting.


So, if we write
```python
comments = Comment.where(post___public=True, post___user___name__like='Bi%').all()
```
then no additional query will be executed if we will access used relations
```python
comments[0].post
comments[0].post.user
```

Cool, isn't it? =)

![icon](http://i.piccy.info/i9/c7168c8821f9e7023e32fd784d0e2f54/1489489664/1113/1127895/rsz_18_256.png)
See [full example](examples/smartquery.py) and [tests](sqlalchemy_mixins/tests/test_smartquery.py)

### All-in-one: smart_query
#### Filter, sort and eager load in one smartest method.
provided by [`SmartQueryMixin`](sqlalchemy_mixins/smartquery.py)

In real world, we want to filter, sort and also eager load some relations at once.
Well, if we use the same, say, `User.posts` relation in filtering and sorting,
it **should not be joined twice**.

That's why we combined filter, sort and eager load in one smartest method:
```python
Comment.smart_query(
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
```

> ** New in 0.2.3 **
> In real world, you may need to "smartly" apply filters/sort/eagerload to any arbitrary query.
> And you can do this with standalone `smart_query` function:
> ```python
> smart_query(any_query, filters=...)
> ```
> It's especially useful for filtering/sorting/eagerloading [relations with lazy='dynamic'](http://docs.sqlalchemy.org/en/latest/orm/collections.html#dynamic-relationship)
>  for pages like [this](http://www.qopy.me/LwfSCu_ETM6At6el8wlbYA):
> ```python
> smart_query(user.comments_, filters=...)
> ```
> See [this example](examples/smartquery.py#L386)


> ** Experimental ** 
> Additional logic (OR, AND, NOT etc) can be expressed using a nested structure for filters, with sqlalchemy operators (or any callable) as keys:
> ```
> from sqlalchemy import or_
> Comment.smart_query(filters={ or_: {
>     'post___public': True, 
>     'user__isnull': False
> }})
> ```
> See [this example](examples/smartquery.py#L409) for more details


![icon](http://i.piccy.info/i9/c7168c8821f9e7023e32fd784d0e2f54/1489489664/1113/1127895/rsz_18_256.png)
See [full example](examples/smartquery.py) and [tests](sqlalchemy_mixins/tests/test_smartquery.py)

## Beauty \_\_repr\_\_
provided by [`ReprMixin`](sqlalchemy_mixins/repr.py)

As developers, we need to debug things with convenience.
When we play in REPL, we can see this

```
>>> session.query(Post).all()
[<myapp.models.Post object at 0x04287A50>, <myapp.models.Post object at 0x04287A90>]
```

Well, using our mixin, we can have more readable output with post IDs:

```
>>> session.query(Post).all()
[<Post #11>, <Post #12>]
```

Even more, in `Post` model, we can define what else (except id) we want to see:

```python
class User(BaseModel):
    __repr_attrs__ = ['name']
    # ...


class Post(BaseModel):
    __repr_attrs__ = ['user', 'body'] # body is just column, user is relationship
    # ...

```

Now we have
```
>>> session.query(Post).all()
[<Post #11 user:<User #1 'Bill'> body:'post 11'>,
 <Post #12 user:<User #2 'Bob'> body:'post 12'>]

```

Long attributes will be cut:

```
long_post = Post(body='Post 2 long-long body', user=bob)

>>> long_post
<Post #2 body:'Post 2 long-lon...' user:<User #1 'Bob'>>
```

And you can customize max `__repr__` length:
```
class Post(BaseModel):
    # ...
    __repr_max_length__ = 25
    # ...
    
>>> long_post
<Post #2 body:'Post 2 long-long body' user:<User #1 'Bob'>>   
```

![icon](http://i.piccy.info/i9/c7168c8821f9e7023e32fd784d0e2f54/1489489664/1113/1127895/rsz_18_256.png)
See [full example](examples/repr.py) and [tests](sqlalchemy_mixins/tests/test_repr.py)

## Serialize to dict
provided by [`SerializeMixin`](sqlalchemy_mixins/serialize.py)

You can convert your model to dict.

```python
# 1. Without relationships
#
# {'id': 1, 'name': 'Bob'}
print(user.to_dict())

# 2. With relationships
#
# {'id': 1,
# 'name': 'Bob',
# 'posts': [{'body': 'Post 1', 'id': 1, 'user_id': 1},
#           {'body': 'Post 2', 'id': 2, 'user_id': 1}]}
print(user.to_dict(nested=True))
```
![icon](http://i.piccy.info/i9/c7168c8821f9e7023e32fd784d0e2f54/1489489664/1113/1127895/rsz_18_256.png)
See [full example](examples/serialize.py)

## Timestamps
provided by [`TimestampsMixin`](sqlalchemy_mixins/timestamp.py)

You can view the created and updated timestamps.

```python
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
# Updated Bob:     2019-03-04 03:53:58.613044
```
![icon](http://i.piccy.info/i9/c7168c8821f9e7023e32fd784d0e2f54/1489489664/1113/1127895/rsz_18_256.png)
See [full example](examples/timestamp.py)

# Internal architecture notes
Some mixins re-use the same functionality. It lives in [`SessionMixin`](sqlalchemy_mixins/session.py) (session access) and [`InspectionMixin`](sqlalchemy_mixins/inspection.py) (inspecting columns, relations etc.) and other mixins inherit them.

You can use these mixins standalone if you want.

Here's a UML diagram of mixin hierarchy:
![Mixin hierarchy](http://i.piccy.info/i9/4030c604ef387101a6ec30b7c357134c/1490694900/42743/1127895/diagram.png)

# Comparison with existing solutions
There're a lot of extensions for SQLAlchemy, but most of them are not so universal.

## Active record
We found several implementations of this pattern.

**[ActiveAlchemy](https://github.com/mardix/active-alchemy/)**

Cool, but it forces you to use [their own way](https://github.com/mardix/active-alchemy/#create-the-model) to instantiate SQLAlchemy
while to use [`ActiveRecordMixin`](sqlalchemy_mixins/activerecord.py) you should just make you model to inherit it.

**[Flask-ActiveRecord](https://github.com/kofrasa/flask-activerecord)**

Cool, but tightly coupled with Flask.

**[sqlalchemy-activerecord](https://github.com/deespater/sqlalchemy-activerecord)**

Framework-agnostic, but lacks of functionality (only `save` method is provided) and Readme.

## Django-like queries
There exists [sqlalchemy-django-query](https://github.com/mitsuhiko/sqlalchemy-django-query)
package which does similar things and it's really awesome.

But:
 * it doesn't [automatic eager load relations](#automatic-eager-load-relations)
 * it doesn't work with [hybrid attributes](http://docs.sqlalchemy.org/en/latest/orm/extensions/hybrid.html)
   and [hybrid_methods](http://docs.sqlalchemy.org/en/latest/orm/extensions/hybrid.html?highlight=hybrid_method#sqlalchemy.ext.hybrid.hybrid_method)

### Beauty \_\_repr\_\_
[sqlalchemy-repr](https://github.com/manicmaniac/sqlalchemy-repr) already does this,
but there you can't choose which columns to output. It simply prints all columns, which can lead to too big output.

# Changelog

## v0.2

More clear methods in [`EagerLoadMixin`](sqlalchemy_mixins/eagerload.py):

 * *added* `with_subquery` method: it's like `with_joined`, but for [subqueryload](http://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html#sqlalchemy.orm.subqueryload).
   So you can now write:
   
   ```python
   User.with_subquery('posts', 'comments').all()
   ```  
 * `with_joined` method *arguments change*: instead of

    ```python
    Comment.with_joined(['user','post'])
    ```

    now simply write

    ```python
    Comment.with_joined('user','post')
    ```

 * `with_` method *arguments change*: it now accepts *only dict schemas*. If you want to quickly joinedload relations, use `with_joined`
 * `with_dict` method *removed*. Instead, use `with_` method   

Other changes in [`EagerLoadMixin`](sqlalchemy_mixins/eagerload.py):

 * constants *rename*: use cleaner `JOINED` and `SUBQUERY` instead of `JOINEDLOAD` and `SUBQUERYLOAD`
 * do not allow `None` in schema anymore, so instead of
     ```python
     Comment.with_({'user': None})
     ```

     write
     ```python
     Comment.with_({'user': JOINED})
     ```

### v0.2.1

Fix in [`InspectionMixin.columns`](sqlalchemy_mixins/inspection.py) property.

It didn't return columns inherited from other class. Now it works correct: 

```python
class Parent(BaseModel):
    __tablename__ = 'parent'
    id = sa.Column(sa.Integer, primary_key=True)


class Child(Parent):
    some_prop = sa.Column(sa.String)
    
Child.columns # before it returned ['some_prop']
              # now it returns ['id', 'some_prop'] 
```

### v0.2.2
Fixed bug in [`ReprMixin`](sqlalchemy_mixins/repr.py): it [crashed](http://www.qopy.me/8UgySS2DTNOScdef_IuqAw) for objects without ID (newly created ones, not added yet to the session).

### v0.2.3
[`SmartQueryMixin`](sqlalchemy_mixins/smartquery.py): decoupled `smart_query` function from ORM classes
so now you can use it with any query like
> ```python
> smart_query(any_query, filters=...)
> ```
See [description](#all-in-one-smart_query) (at the end of paragraph) and [example](examples/smartquery.py#L386)

### v1.0.1

1. Added [SerializationMixin](#serialize-to-dict) (thanks, [jonatasleon](https://github.com/jonatasleon))

1. Added `ne` operator (thanks, [https://github.com/sophalch](sophalch)), so now you can write something like

```python
Post.where(rating__ne=2).all()
```

### v1.2

> This version contains breaking change, reverted in v1.2.1.
> So:
>   * v1.2 was removed from PyPi to avoid confusions
>   * for those who already downloaded v1.2, we hardly recommend to switch to 1.2.1.
>
> Just use [v1.2.1](#v121) instead


> By mistake, v1.2 code was released on PyPi as v1.1. 
> It has been deleted from PyPi to avoid confusion. 
> Sorry for any inconvenience guys.  

1. **Removed Python 2, Python 3.2 compatibility**.

1. Added Python 3.7, 3.8 compatibility. 
 
1. Added [TimestampsMixin](#timestamps) (thanks, [jonatasleon](https://github.com/jonatasleon)). 

1. (**Breaking change**, fixed in [v1.2.1](#v121)) [TimestampsMixin](#timestamps) was **included it to [AllFeaturesMixin](sqlalchemy_mixins/__init__.py)** which means `created_at` and `updated_at` fields were added to all models using `AllFeaturesMixin` which means you need to write migrations adding these fields.  

1. Added [`contains` operator](https://github.com/absent1706/sqlalchemy-mixins/pull/29/files) (thanks, [alexbredo](https://github.com/alexbredo)).

1. Added [date comparison operators](https://github.com/absent1706/sqlalchemy-mixins/pull/27/files) (thanks, [proteusvacuum](https://github.com/proteusvacuum)), so now you can write something like

```python
Post.where(created_at__year_ge=2014).all()
Post.where(created_at__month_gt=10).all()
Post.where(created_at__day_le=30).all()
```

### v1.2.1

Reverted breaking change introduced in [1.2](#v12):

removed [TimestampsMixin](#timestamps) from [AllFeaturesMixin](sqlalchemy_mixins/__init__.py). This addition in [v1.2](#v12) forced package users to write and run migration to add `created_at` and `updated_at` fields to all tables whose ORM models used `AllFeaturesMixin`.
   Now you should add `TimestampsMixin` separately:
   
   ```python
   class BaseModel(Base, AllFeaturesMixin, TimestampsMixin):
       # ...
   ```


### v1.3

Add support for SQLAlchemy 1.4
