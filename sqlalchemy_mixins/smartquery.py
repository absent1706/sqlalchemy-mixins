try:
    # noinspection PyUnresolvedReferences
    from typing import List
except ImportError:  # pragma: no cover
    pass

from collections import abc, OrderedDict


from sqlalchemy import asc, desc, inspect
from sqlalchemy.orm import aliased, contains_eager
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql import operators, extract

# noinspection PyProtectedMember
from .eagerload import _flatten_schema, _eager_expr_from_flat_schema, \
    EagerLoadMixin, SUBQUERY
from .inspection import InspectionMixin
from .utils import classproperty

RELATION_SPLITTER = '___'
OPERATOR_SPLITTER = '__'

DESC_PREFIX = '-'


def _flatten_filter_keys(filters):
    """
    :type filters: dict|list
    Flatten the nested filters, extracting keys where they correspond 
    to smart_query paths, e.g. 
    {or_: {'id__gt': 1000, and_ : {
        'id__lt': 500,
        'related___property__in': (1,2,3) 
    }}}
    
    Yields:

    'id__gt', 'id__lt', 'related___property__in'

    Also allow lists (any abc.Sequence subclass) to enable support
    of expressions like.

    (X OR Y) AND (W OR Z)

    { and_: [
        {or_: {'id__gt': 5, 'related_id__lt': 10}},
        {or_: {'related_id2__gt': 1, 'name__like': 'Bob' }}
    ]}
    """

    if isinstance(filters, abc.Mapping):
        for key, value in filters.items():
            if callable(key):
                yield from _flatten_filter_keys(value)
            else:
                yield key

    elif isinstance(filters, abc.Sequence):
        for f in filters:
            yield from _flatten_filter_keys(f)

    else:
        raise TypeError(
            "Unsupported type (%s) in filters: %r", (type(filters), filters)
        )


def _parse_path_and_make_aliases(entity, entity_path, attrs, aliases):
    """
    :type entity: InspectionMixin
    :type entity_path: str
    :type attrs: list
    :type aliases: OrderedDict

    Sample values:

    attrs: ['product__subject_ids', 'user_id', '-group_id',
            'user__name', 'product__name', 'product__grade_from__order']
    relations: {'product': ['subject_ids', 'name'], 'user': ['name']}

    """
    relations = {}
    # take only attributes that have magic RELATION_SPLITTER
    for attr in attrs:
        # from attr (say, 'product__grade__order')  take
        # relationship name ('product') and nested attribute ('grade__order')
        if RELATION_SPLITTER in attr:
            relation_name, nested_attr = attr.split(RELATION_SPLITTER, 1)
            if relation_name in relations:
                relations[relation_name].append(nested_attr)
            else:
                relations[relation_name] = [nested_attr]

    for relation_name, nested_attrs in relations.items():
        path = (
            entity_path + RELATION_SPLITTER + relation_name
            if entity_path
            else relation_name
        )
        if relation_name not in entity.relations:
            raise KeyError(
                "Incorrect path `{}`: "
                "{} doesnt have `{}` relationship ".format(path, entity, relation_name)
            )
        relationship = getattr(entity, relation_name)
        alias = aliased(relationship.property.mapper.class_)
        aliases[path] = alias, relationship
        _parse_path_and_make_aliases(alias, path, nested_attrs, aliases)

def _get_root_cls(query):
    # sqlalchemy < 1.4.0
    if hasattr(query, '_entity_zero'):
        return query._entity_zero().class_

    # sqlalchemy >= 1.4.0
    else:
        if hasattr(query, '_entity_from_pre_ent_zero'):
            return query._entity_from_pre_ent_zero().class_
    raise ValueError('Cannot get a root class from`{}`'
                     .format(query))

def smart_query(query, filters=None, sort_attrs=None, schema=None):
    """
    Does magic Django-ish joins like post___user___name__startswith='Bob'
     (see https://goo.gl/jAgCyM)
    Does filtering, sorting and eager loading at the same time.
    And if, say, filters and sorting need the same joinm it will be done
     only one. That's why all stuff is combined in single method

    :param query: sqlalchemy.orm.query.Query
    :param filters: dict
    :param sort_attrs: List[basestring]
    :param schema: dict
    """
    if not filters:
        filters = {}
    if not sort_attrs:
        sort_attrs = []

    #  Load schema early since we need it to check whether we should eager load a relationship
    if schema:
        flat_schema = _flatten_schema(schema)
        print(flat_schema)
    else:
        flat_schema = {}

    # sqlalchemy >= 1.4.0, should probably a. check something else to determine if we need to convert
    # AppenderQuery to a query, b. probably not hack it like this
    # noinspection PyProtectedMember
    if type(query).__name__ == 'AppenderQuery' and query._statement:
        sess = query.session
        # noinspection PyProtectedMember
        query = query._statement
        query.session = sess

    root_cls = _get_root_cls(query)  # for example, User or Post
    attrs = list(_flatten_filter_keys(filters)) + \
        list(map(lambda s: s.lstrip(DESC_PREFIX), sort_attrs))
    aliases = OrderedDict({})
    _parse_path_and_make_aliases(root_cls, '', attrs, aliases)

    loaded_paths = []
    for path, al in aliases.items():
        relationship_path = path.replace(RELATION_SPLITTER, '.')
        if not (relationship_path in flat_schema and flat_schema[relationship_path] == SUBQUERY):
            query = query.outerjoin(al[0], al[1]) \
                .options(contains_eager(relationship_path, alias=al[0]))
            loaded_paths.append(relationship_path)

    def recurse_filters(_filters):
        if isinstance(_filters, abc.Mapping):
            for attr, value in _filters.items():
                if callable(attr):
                    # E.g. or_, and_, or other sqlalchemy expression
                    yield attr(*recurse_filters(value))
                    continue
                if RELATION_SPLITTER in attr:
                    parts = attr.rsplit(RELATION_SPLITTER, 1)
                    entity, attr_name = aliases[parts[0]][0], parts[1]
                else:
                    entity, attr_name = root_cls, attr
                try:
                    yield from entity.filter_expr(**{attr_name: value})
                except KeyError as e:
                    raise KeyError("Incorrect filter path `{}`: {}".format(attr, e))

        elif isinstance(_filters, abc.Sequence):
            for f in _filters:
                yield from recurse_filters(f)

    query = query.filter(*recurse_filters(filters))

    for attr in sort_attrs:
        if RELATION_SPLITTER in attr:
            prefix = ''
            if attr.startswith(DESC_PREFIX):
                prefix = DESC_PREFIX
                attr = attr.lstrip(DESC_PREFIX)
            parts = attr.rsplit(RELATION_SPLITTER, 1)
            entity, attr_name = aliases[parts[0]][0], prefix + parts[1]
        else:
            entity, attr_name = root_cls, attr
        try:
            query = query.order_by(*entity.order_expr(attr_name))
        except KeyError as e:
            raise KeyError("Incorrect order path `{}`: {}".format(attr, e))

    if flat_schema:
        not_loaded_part = {path: v for path, v in flat_schema.items()
                           if path not in loaded_paths}
        query = query.options(*_eager_expr_from_flat_schema(
            not_loaded_part))

    return query


class SmartQueryMixin(InspectionMixin, EagerLoadMixin):
    __abstract__ = True

    _operators = {
        'isnull': lambda c, v: (c == None) if v else (c != None),
        'exact': operators.eq,
        'ne': operators.ne,  # not equal or is not (for None)

        'gt': operators.gt,  # greater than , >
        'ge': operators.ge,  # greater than or equal, >=
        'lt': operators.lt,  # lower than, <
        'le': operators.le,  # lower than or equal, <=

        'in': operators.in_op,
        'notin': operators.notin_op,
        'between': lambda c, v: c.between(v[0], v[1]),

        'like': operators.like_op,
        'ilike': operators.ilike_op,
        'startswith': operators.startswith_op,
        'istartswith': lambda c, v: c.ilike(v + '%'),
        'endswith': operators.endswith_op,
        'iendswith': lambda c, v: c.ilike('%' + v),
        'contains': lambda c, v: c.ilike('%{v}%'.format(v=v)),

        'year': lambda c, v: extract('year', c) == v,
        'year_ne': lambda c, v: extract('year', c) != v,
        'year_gt': lambda c, v: extract('year', c) > v,
        'year_ge': lambda c, v: extract('year', c) >= v,
        'year_lt': lambda c, v: extract('year', c) < v,
        'year_le': lambda c, v: extract('year', c) <= v,

        'month': lambda c, v: extract('month', c) == v,
        'month_ne': lambda c, v: extract('month', c) != v,
        'month_gt': lambda c, v: extract('month', c) > v,
        'month_ge': lambda c, v: extract('month', c) >= v,
        'month_lt': lambda c, v: extract('month', c) < v,
        'month_le': lambda c, v: extract('month', c) <= v,

        'day': lambda c, v: extract('day', c) == v,
        'day_ne': lambda c, v: extract('day', c) != v,
        'day_gt': lambda c, v: extract('day', c) > v,
        'day_ge': lambda c, v: extract('day', c) >= v,
        'day_lt': lambda c, v: extract('day', c) < v,
        'day_le': lambda c, v: extract('day', c) <= v,
    }

    @classproperty
    def filterable_attributes(cls):
        return cls.relations + cls.columns + \
               cls.hybrid_properties + cls.hybrid_methods

    @classproperty
    def sortable_attributes(cls):
        return cls.columns + cls.hybrid_properties

    @classmethod
    def filter_expr(cls_or_alias, **filters):
        """
        forms expressions like [Product.age_from = 5,
                                Product.subject_ids.in_([1,2])]
        from filters like {'age_from': 5, 'subject_ids__in': [1,2]}

        Example 1:
            db.query(Product).filter(
                *Product.filter_expr(age_from = 5, subject_ids__in=[1, 2]))

        Example 2:
            filters = {'age_from': 5, 'subject_ids__in': [1,2]}
            db.query(Product).filter(*Product.filter_expr(**filters))


        ### About alias ###:
        If we will use alias:
            alias = aliased(Product) # table name will be product_1
        we can't just write query like
            db.query(alias).filter(*Product.filter_expr(age_from=5))
        because it will be compiled to
            SELECT * FROM product_1 WHERE product.age_from=5
        which is wrong: we select from 'product_1' but filter on 'product'
        such filter will not work

        We need to obtain
            SELECT * FROM product_1 WHERE product_1.age_from=5
        For such case, we can call filter_expr ON ALIAS:
            alias = aliased(Product)
            db.query(alias).filter(*alias.filter_expr(age_from=5))

        Alias realization details:
          * we allow to call this method
            either ON ALIAS (say, alias.filter_expr())
            or on class (Product.filter_expr())
          * when method is called on alias, we need to generate SQL using
            aliased table (say, product_1), but we also need to have a real
            class to call methods on (say, Product.relations)
          * so, we have 'mapper' that holds table name
            and 'cls' that holds real class

            when we call this method ON ALIAS, we will have:
                mapper = <product_1 table>
                cls = <Product>
            when we call this method ON CLASS, we will simply have:
                mapper = <Product> (or we could write <Product>.__mapper__.
                                    It doesn't matter because when we call
                                    <Product>.getattr, SA will magically
                                    call <Product>.__mapper__.getattr())
                cls = <Product>
        """
        if isinstance(cls_or_alias, AliasedClass):
            mapper, cls = cls_or_alias, inspect(cls_or_alias).mapper.class_
        else:
            mapper = cls = cls_or_alias

        expressions = []
        valid_attributes = cls.filterable_attributes
        for attr, value in filters.items():
            # if attribute is filtered by method, call this method
            if attr in cls.hybrid_methods:
                method = getattr(cls, attr)
                expressions.append(method(value, mapper=mapper))
            # else just add simple condition (== for scalars or IN for lists)
            else:
                # determine attrbitute name and operator
                # if they are explicitly set (say, id___between), take them
                if OPERATOR_SPLITTER in attr:
                    attr_name, op_name = attr.rsplit(OPERATOR_SPLITTER, 1)
                    if op_name not in cls._operators:
                        raise KeyError('Expression `{}` has incorrect '
                                       'operator `{}`'.format(attr, op_name))
                    op = cls._operators[op_name]
                # assume equality operator for other cases (say, id=1)
                else:
                    attr_name, op = attr, operators.eq

                if attr_name not in valid_attributes:
                    raise KeyError('Expression `{}` '
                                   'has incorrect attribute `{}`'
                                   .format(attr, attr_name))

                column = getattr(mapper, attr_name)
                expressions.append(op(column, value))

        return expressions

    @classmethod
    def order_expr(cls_or_alias, *columns):
        """
        Forms expressions like [desc(User.first_name), asc(User.phone)]
          from list like ['-first_name', 'phone']

        Example for 1 column:
          db.query(User).order_by(*User.order_expr('-first_name'))
          # will compile to ORDER BY user.first_name DESC

        Example for multiple columns:
          columns = ['-first_name', 'phone']
          db.query(User).order_by(*User.order_expr(*columns))
          # will compile to ORDER BY user.first_name DESC, user.phone ASC

        About cls_or_alias, mapper, cls: read in filter_expr method description
        """
        if isinstance(cls_or_alias, AliasedClass):
            mapper, cls = cls_or_alias, inspect(cls_or_alias).mapper.class_
        else:
            mapper = cls = cls_or_alias

        expressions = []
        for attr in columns:
            fn, attr = (desc, attr[1:]) if attr.startswith(DESC_PREFIX) \
                        else (asc, attr)
            if attr not in cls.sortable_attributes:
                raise KeyError('Cant order {} by {}'.format(cls, attr))

            expr = fn(getattr(mapper, attr))
            expressions.append(expr)
        return expressions

    @classmethod
    def smart_query(cls, filters=None, sort_attrs=None, schema=None):
        """
        Does magic Django-ish joins like post___user___name__startswith='Bob'
         (see https://goo.gl/jAgCyM)
        Does filtering, sorting and eager loading at the same time.
        And if, say, filters and sorting need the same joinm it will be done
         only one. That's why all stuff is combined in single method

        :param filters: dict
        :param sort_attrs: List[basestring]
        :param schema: dict
        """
        return smart_query(cls.query, filters, sort_attrs, schema)

    @classmethod
    def where(cls, **filters):
        """
        Shortcut for smart_query() method
        Example 1:
          Product.where(subject_ids__in=[1,2], grade_from_id=2).all()

        Example 2:
          filters = {'subject_ids__in': [1,2], 'grade_from_id': 2}
          Product.where(**filters).all()

        Example 3 (with joins):
          Post.where(public=True, user___name__startswith='Bi').all()
        """
        return cls.smart_query(filters)

    @classmethod
    def sort(cls, *columns):
        """
        Shortcut for smart_query() method
        Example 1:
            User.sort('first_name','-user_id')
        This is equal to
            db.query(User).order_by(*User.order_expr('first_name','-user_id'))

        Example 2:
            columns = ['first_name','-user_id']
            User.sort(*columns)
        This is equal to
            columns = ['first_name','-user_id']
            db.query(User).order_by(*User.order_expr(*columns))

        Exanple 3 (with joins):
            Post.sort('comments___rating', 'user___name').all()
        """
        return cls.smart_query({}, columns)
