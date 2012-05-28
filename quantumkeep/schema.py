
from weakref import WeakValueDictionary as weakdict


__all__ = ["Schema", "Attribute", "PrimitiveType"]


class Attribute(object):

    def __init__(self, key, type, caption=None):
        self.key = key
        self.type = type
        if caption is not None:
            self.caption = caption
        else:
            self.caption = key


class Type(object):

    def __hash__(self):
        # The schema class works to make sure type objects are singletons,
        # so the id of the object is enough to hash it.
        return id(self)

    def __repr__(self):
        return "<quantumkeep.schema.Type %s>" % self.display_name


class ObjectType(Type):

    def __init__(self, name, attributes):
        self.name = name
        self.attributes = tuple(attributes)

    @property
    def display_name(self):
        return self.name if self.name is not None else "(anon)"


class PrimitiveType(Type):

    def __init__(self, display_name):
        self._display_name = display_name

    @classmethod
    def get_by_name(cls, name):
        return cls._by_name[name]

    @property
    def display_name(self):
        return self._display_name

PrimitiveType._by_name = {}
for primitive_type_name in ("integer", "float", "bytes", "string", "boolean"):
    primitive_type = PrimitiveType(primitive_type_name)
    setattr(PrimitiveType, primitive_type_name, primitive_type)
    PrimitiveType._by_name[primitive_type_name] = primitive_type


class ListType(Type):

    def __init__(self, item_type):
        self.item_type = item_type

    @property
    def display_name(self):
        return "list<%s>" % self.item_type.display_name


class MapType(Type):

    def __init__(self, key_type, value_type):
        self.key_type = key_type
        self.value_type = value_type

    @property
    def display_name(self):
        return "map<%s,%s>" % (
            self.key_type.display_name,
            self.value_type.display_name,
        )


class Container(object):
    pass


class Schema(object):

    def __init__(self):
        self._object_types = {}
        self._map_types = weakdict()
        self._list_types = weakdict()

    def add_object_type(self, name, attributes):
        if name in self._object_types:
            raise KeyError("Schema already has an object type called %s" % name)
        else:
            self._object_types[name] = ObjectType(name, attributes)

    def object_type(self, name):
        return self._object_types[name]

    def map_type(self, key_type, value_type):
        key = (key_type, value_type)
        if key not in self._map_types:
            new_type = MapType(key_type, value_type)
            self._map_types[key] = new_type
        return self._map_types[key]

    def list_type(self, item_type):
        if item_type not in self._list_types:
            new_type = ListType(item_type)
            self._list_types[item_type] = new_type
        return self._list_types[item_type]

    def primitive_type(self, name):
        return PrimitiveType.get_by_name(name)
