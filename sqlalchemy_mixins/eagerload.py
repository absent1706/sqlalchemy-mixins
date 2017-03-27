try:
    from typing import List
except ImportError: # pragma: no cover
    pass

from sqlalchemy.orm import joinedload
from sqlalchemy.orm import subqueryload
from sqlalchemy.orm.attributes import InstrumentedAttribute

from .session import SessionMixin

JOINED = 'joined'
SUBQUERY = 'subquery'


def eager_expr(schema):
    """
    :type schema: dict
    """
    flat_schema = _flatten_schema(schema)
    return _eager_expr_from_flat_schema(flat_schema)


def _flatten_schema(schema):
    """
    :type schema: dict
    """
    def _flatten(schema, parent_path, result):
        """
        :type schema: dict
        """
        for path, value in schema.items():
            # for supporting schemas like Product.user: {...},
            # we transform, say, Product.user to 'user' string
            if isinstance(path, InstrumentedAttribute):
                path = path.key

            if isinstance(value, tuple):
                join_method, inner_schema = value[0], value[1]
            elif isinstance(value, dict):
                join_method, inner_schema = JOINED, value
            else:
                join_method, inner_schema = value, None

            full_path = parent_path + '.' + path if parent_path else path
            result[full_path] = join_method

            if inner_schema:
                _flatten(inner_schema, full_path, result)

    result = {}
    _flatten(schema, '', result)
    return result


def _eager_expr_from_flat_schema(flat_schema):
    """
    :type flat_schema: dict
    """
    result = []
    for path, join_method in flat_schema.items():
        if join_method == JOINED:
            result.append(joinedload(path))
        elif join_method == SUBQUERY:
            result.append(subqueryload(path))
        else:
            raise ValueError('Bad join method `{}` in `{}`'
                             .format(join_method, path))
    return result


class EagerLoadMixin(SessionMixin):
    __abstract__ = True

    @classmethod
    def with_(cls, schema):
        """
        Query class and eager load schema at once.
        :type schema: dict

        Example:
            schema = {
                'user': JOINED, # joinedload user
                'comments': (SUBQUERY, {  # load comments in separate query
                    'user': JOINED  # but, in this separate query, join user
                })
            }
            # the same schema using class properties:
            schema = {
                Post.user: JOINED,
                Post.comments: (SUBQUERY, {
                    Comment.user: JOINED
                })
            }
            User.with_(schema).first()
        """
        return cls.query.options(*eager_expr(schema or {}))

    @classmethod
    def with_joined(cls, *paths):
        """
        Eagerload for simple cases where we need to just
         joined load some relations
        In strings syntax, you can split relations with dot 
         due to this SQLAlchemy feature: https://goo.gl/yM2DLX
         
        :type paths: *List[str] | *List[InstrumentedAttribute]

        Example 1:
            Comment.with_joined('user', 'post', 'post.comments').first()

        Example 2:
            Comment.with_joined(Comment.user, Comment.post).first()
        """
        options = [joinedload(path) for path in paths]
        return cls.query.options(*options)

    @classmethod
    def with_subquery(cls, *paths):
        """
        Eagerload for simple cases where we need to just
         joined load some relations
        In strings syntax, you can split relations with dot 
         (it's SQLAlchemy feature)

        :type paths: *List[str] | *List[InstrumentedAttribute]

        Example 1:
            User.with_subquery('posts', 'posts.comments').all()

        Example 2:
            User.with_subquery(User.posts, User.comments).all()
        """
        options = [subqueryload(path) for path in paths]
        return cls.query.options(*options)
