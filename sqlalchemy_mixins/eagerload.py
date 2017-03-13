try:
    from typing import List
except ImportError:
    pass

from sqlalchemy.orm import joinedload
from sqlalchemy.orm import subqueryload
from sqlalchemy.orm.attributes import InstrumentedAttribute

from .session import SessionMixin

JOINEDLOAD = 'joined'
SUBQUERYLOAD = 'subquery'


def eager_expr(schema):
    flat_schema = _flatten_schema(schema)
    return _eager_expr_from_flat_schema(flat_schema)


def _flatten_schema(schema):
    def _flatten(schema, parent_path, result):
        for path, value in schema.items():
            # for supporting schemas like Product.user: {...},
            # we transform, say, Product.user to 'user' string
            if isinstance(path, InstrumentedAttribute):
                path = path.key

            if isinstance(value, tuple):
                join_method, inner_schema = value[0], value[1]
            elif isinstance(value, dict):
                join_method, inner_schema = JOINEDLOAD, value
            else:
                join_method, inner_schema = value or JOINEDLOAD, None

            full_path = parent_path + '.' + path if parent_path else path
            result[full_path] = join_method

            if inner_schema:
                _flatten(inner_schema, full_path, result)

    result = {}
    _flatten(schema, '', result)
    return result


def _eager_expr_from_flat_schema(flat_schema):
    result = []
    for path, join_method in flat_schema.items():
        if join_method == JOINEDLOAD:
            result.append(joinedload(path))
        elif join_method == SUBQUERYLOAD:
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
        Schema is list (with_joined() will be called)
         or dict(with_dict() will be called)
        :type schema: dict | List[basestring] | List[InstrumentedAttribute]
        """
        return cls.with_dict(schema) if isinstance(schema, dict) \
            else cls.with_joined(schema)

    @classmethod
    def with_dict(cls, schema):
        """
        Query class and eager load schema at once.

        Example 1:
            schema = {
                User.educator_school: {
                    School.educators: (SUBQUERYLOAD, None),
                    School.district: None
                },
                User.educator_district: {
                    District.schools: (SUBQUERYLOAD, {
                        School.educators: None
                    })
                }
            }
            User.with_dict(schema).first()

        Example 2 (with strings, not recommended):
            schema = {
                'educator_school': {
                    'educators': (SUBQUERYLOAD, None),
                    'district': None
                },
                'educator_district': {
                    'schools': (SUBQUERYLOAD, {
                        'educators': None
                    })
                }
            }
            User.with_dict(schema).first()
        """
        return cls.query.options(*eager_expr(schema or {}))

    @classmethod
    def with_joined(cls, paths):
        """
        Eagerload for simple cases where we need to just
         joined load some relations without nesting
            :type paths: List[str] | List[InstrumentedAttribute]

        Example 1:
            Product.with_dict(Product.grade_from, Product.grade_to).first()

        Example 2 (with strings, not recommended):
            Product.with_dict('grade_from', 'grade_to').first()
        """
        flat_schema = {path: JOINEDLOAD for path in paths}
        return cls.query.options(*_eager_expr_from_flat_schema(flat_schema))
