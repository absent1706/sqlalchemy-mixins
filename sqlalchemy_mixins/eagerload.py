from sqlalchemy.orm.strategy_options import _AbstractLoad

try:
    from typing import List
except ImportError: # pragma: no cover
    pass

from sqlalchemy.orm import joinedload, Load
from sqlalchemy.orm import subqueryload

from .session import SessionMixin

JOINED = 'joined'
SUBQUERY = 'subquery'


def eager_expr(schema):
    """
    :type schema: dict
    """
    return _eager_expr_from_schema(schema)


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
            attr = path
            path = path.key


            if isinstance(value, tuple):
                join_method, inner_schema = value[0], value[1]
            elif isinstance(value, dict):
                join_method, inner_schema = JOINED, value
            else:
                join_method, inner_schema = value, None

            full_path = parent_path + '.' + path if parent_path else path
            result[attr] = join_method

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

def _eager_expr_from_schema(schema):
    def _get_expr(schema, result):
        for path, value in schema.items():
            if isinstance(value, tuple):
                join_method, inner_schema = value[0], value[1]
                load_option = _create_eager_load_option(path, join_method)
                result.append(load_option.options(*_eager_expr_from_schema(inner_schema)))
            elif isinstance(value, dict):
                join_method, inner_schema = JOINED, value
                load_option = _create_eager_load_option(path, join_method)
                result.append(load_option.options(*_eager_expr_from_schema(inner_schema)))
                # load_option = _create_eager_load_option(path, value)
            else:
                result.append(_create_eager_load_option(path, value))

    result = []
    _get_expr(schema, result)
    return result

def _create_eager_load_option(path, join_method):
    if join_method == JOINED:
        return joinedload(path)
    elif join_method == SUBQUERY:
        return subqueryload(path)
    else:
        raise ValueError('Bad join method `{}` in `{}`'
                         .format(join_method, path))



class EagerLoadMixin(SessionMixin):
    __abstract__ = True

    @classmethod
    def with_(cls, schema):
        """
        Query class and eager load schema at once.
        :type schema: dict

        Example:
            schema = {
                Post.user: JOINED,  # joinedload user
                Post.comments: (SUBQUERY, { # load comments in separate query
                    Comment.user: JOINED  # but, in this separate query, join user
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
        You can only load direct relationships.
         
        :type paths: *List[QueryableAttribute]

        Example 1:
            Comment.with_joined(Comment.user, Comment.post).first()
        """
        options = [joinedload(path) for path in paths]
        return cls.query.options(*options)

    @classmethod
    def with_subquery(cls, *paths):
        """
        Eagerload for simple cases where we need to just
         joined load some relations
        You can only load direct relationships.

        :type paths: *List[QueryableAttribute]

        Example 1:
            User.with_subquery(User.posts, User.comments).all()
        """
        options = [subqueryload(path) for path in paths]
        return cls.query.options(*options)
