from sqlalchemy.orm import RelationshipProperty, Mapper


# noinspection PyPep8Naming
class classproperty(object):
    """
    @property for @classmethod
    taken from http://stackoverflow.com/a/13624858
    """

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def get_relations(cls):
    if isinstance(cls, Mapper):
        mapper = cls
    else:
        mapper = cls.__mapper__
    return [c for c in mapper.attrs
            if isinstance(c, RelationshipProperty)]


def path_to_relations_list(cls, path):
    path_as_list = path.split('.')
    relations = get_relations(cls)
    relations_list = []
    for item in path_as_list:
        for rel in relations:
            if rel.key == item:
                relations_list.append(rel)
                relations = get_relations(rel.entity)
                break
    return relations_list