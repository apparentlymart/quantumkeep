
from weakref import WeakValueDictionary as weakdict


__all__ = ["Schema", "Attribute", "PrimitiveType"]


class Attribute(object):

    def __init__(self, key, type, caption=None, differ=None):
        self.key = key
        self.type = type
        if caption is not None:
            self.caption = caption
        else:
            self.caption = key
        if differ is not None:
            if differ.can_derive_for_type(type):
                self.differ = differ
            else:
                raise ValueError(
                    "Differ %s is not compatible with attribute '%s' of type %s" % (
                        differ.key,
                        key,
                        type.display_name,
                    )
                )
        else:
            from quantumkeep.diff import value_diff
            self.differ = value_diff.replace
        self._python_accessor_descriptor = None

    @property
    def python_accessor_descriptor(self):
        if self._python_accessor_descriptor is None:
            key = self.key

            # TODO: Maybe make these descriptors do some write-time
            # type checking, but for now they're just there to ensure
            # that the expected attrs are present on instances
            # even if they aren't set to anything yet.

            class Descriptor(object):
                def __get__(self, instance, owner):
                    return instance.__dict__.get(key, None)

                def __set__(self, instance, value):
                    instance.__dict__[key] = value

                def __delete__(self, instance):
                    raise TypeError(
                        "Can't delete attribute of class for object type"
                    )

            Descriptor.__name__ = key

            self._python_accessor_descriptor = Descriptor()

        return self._python_accessor_descriptor


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
        self._python_class = None

    @property
    def display_name(self):
        return self.name if self.name is not None else "(anon)"

    @property
    def python_class(self):
        if self._python_class is None:
            class ObjectTypeStub(object):
                pass

            ObjectTypeStub.__name__ = self.name

            for attr in self.attributes:
                setattr(
                    ObjectTypeStub, attr.key,
                    attr.python_accessor_descriptor,
                )

            self._python_class = ObjectTypeStub

        return self._python_class


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

    def __init__(self, name, item_type, item_key_attrs):
        self.name = name
        self.item_type = item_type
        item_type_attrs = {}
        for attr in item_type.attributes:
            item_type_attrs[attr.key] = attr
        self.item_key_attrs = [
            item_type_attrs[x] for x in item_key_attrs
        ]

    def path_chunks_for_item(self, item):
        ret = []
        for attr in self.item_key_attrs:
            attr_key = attr.key
            attr_type = attr.type
            value = getattr(item, attr_key, None)
            if value is None:
                raise ValueError(
                    "Item has no value for key attribute " + attr_key
                )

            # TEMP: For now, we just make a chunk for each item
            # in the key. In the longer term this should do something
            # more clever, like split up large strings into multiple
            # levels of heirarchy, or maybe create a btree out of
            # git trees.

            from quantumkeep.marshall import transform_in
            ret.append(str(transform_in(attr_type, value)))
        return ret

    def path_chunks_for_key(self, **kwargs):
        ret = []
        for attr in self.item_key_attrs:
            attr_key = attr.key
            attr_type = attr.type
            value = kwargs.get(attr_key, None)
            if value is None:
                raise ValueError(
                    "No value passed for key parameter " + attr_key
                )
            from quantumkeep.marshall import transform_in
            ret.append(str(transform_in(attr_type, value)))
        return ret

class Schema(object):

    def __init__(self):
        self._object_types = {}
        self._containers = {}
        self._map_types = weakdict()
        self._list_types = weakdict()

    def add_container(self, name, item_type, item_key_attrs):
        if name in self._containers:
            raise KeyError("Schema already has a container called %s" % name)
        else:
            self._containers[name] = Container(name, item_type, item_key_attrs)

    def container(self, name):
        return self._containers[name]

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
