
import msgpack
from quantumkeep.schema import PrimitiveType, ObjectType, ListType, MapType


__all__ = ["transform_in", "transform_out", "pack", "unpack"]


def _transform_integer(value):
    if type(value) is bool:
        return 1 if value else 0
    return int(value)


def _transform_bytes(value):
    if type(value) is not str:
        raise TypeError("bytes field must have 'str' value")
    return value


_primitive_transforms = {
    PrimitiveType.boolean: bool,
    PrimitiveType.float: float,
    PrimitiveType.bytes: _transform_bytes,
    PrimitiveType.integer: _transform_integer,
}


def transform_in(value_type, value):
    if value is None:
        return None
    if value_type in _primitive_transforms:
        return _primitive_transforms[value_type](value)
    if value_type is PrimitiveType.string:
        return unicode.encode(unicode(value), "utf8")
    if isinstance(value_type, ObjectType):
        cls = value_type.python_class
        if not isinstance(value, cls):
            raise TypeError("value must be an instance of %r" % cls)
        ret = {}
        for attr in value_type.attributes:
            child_value = transform_in(
                attr.type,
                getattr(value, attr.key, None),
            )
            ret[attr.key] = child_value
        return ret
    if isinstance(value_type, ListType):
        item_type = value_type.item_type
        return [
            transform_in(item_type, item) for item in value
        ]
    if isinstance(value_type, MapType):
        if not getattr(value, "iteritems", None):
            raise TypeError("value must be something that supports iteritems()")
        child_key_type = value_type.key_type
        child_value_type = value_type.value_type
        ret = {}
        for child_key, child_value in value.iteritems():
            ret[transform_in(child_key_type, child_key)] = (
                transform_in(child_value_type, child_value)
            )
        return ret

    # Should never happen
    raise Exception("Don't know how to transform_in %r" % value_type)


def transform_out(value_type, value):
    if value is None:
        return None
    if value_type in _primitive_transforms:
        return _primitive_transforms[value_type](value)
    if value_type is PrimitiveType.string:
        return str(value).decode("utf8")
    if isinstance(value_type, ObjectType):
        if not isinstance(value, dict):
            raise TypeError("value must be a dictionary")

        cls = value_type.python_class
        ret = cls()

        for attr in value_type.attributes:
            child_value = transform_out(
                attr.type,
                value.get(attr.key, None),
            )
            setattr(ret, attr.key, child_value)

        return ret
    if isinstance(value_type, ListType):
        item_type = value_type.item_type
        return [
            transform_out(item_type, item) for item in value
        ]
    if isinstance(value_type, MapType):
        child_key_type = value_type.key_type
        child_value_type = value_type.value_type
        ret = {}
        for child_key, child_value in value.iteritems():
            ret[transform_out(child_key_type, child_key)] = (
                transform_out(child_value_type, child_value)
            )
        return ret

    # Should never happen
    raise Exception("Don't know how to transform_out %r" % value_type)


def pack(value_type, value):
    return msgpack.packb(transform_in(value_type, value))


def unpack(value_type, value):
    return transform_out(value_type, msgpack.unpackb(value))
