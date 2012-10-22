"""
Type-specific serializer/deserializer implementations that can translate
back and forth between a Python value of a given type and a git tree entry
referring to a git blob or tree.
"""

import abc
import msgpack
from dulwich.objects import (
    Tree as GitTree,
    Blob as GitBlob,
    TreeEntry as GitTreeEntry
)

from quantumkeep.tree import Tree, TreeEntry, tree_entry_modes


__all__ = ("serialize_value", "deserialize_tree_entry", "TreeEntry")
_serializers = None
_primitive = None
_blob = None

TREE_MODE = 0o40000
PACK_BLOB_MODE = 0o100644
RAW_BLOB_MODE = 0o100755


def _initialize():
    global _primitive
    global _blob
    global _serializers
    _primitive = Primitive()
    _blob = Blob()

    _serializers = {
        int: _primitive,
        float: _primitive,
        long: _primitive,
        unicode: _primitive,
        bool: _primitive,
        list: _primitive,
        dict: _primitive,
        type(None): _primitive,
        str: _blob,
    }


def serialize_value(value, git_store):
    try:
        serializer = _serializers[type(value)]
    except KeyError, ex:
        raise TypeError(
            "Don't know how to serialize value of type %s" % type(value)
        )

    return serializer.serialize(value, git_store)


def deserialize_tree_entry(tree_entry, git_store):
    mode = tree_entry.mode
    if mode == tree_entry_modes.pack_blob:
        return _primitive.deserialize(tree_entry, git_store)
    elif mode == tree_entry_modes.raw_blob:
        return _blob.deserialize(tree_entry, git_store)
    else:
        raise ValueEror("Don't know how to deserialize this item")


class Base(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def serialize(self, value, git_store):
        pass

    @abc.abstractmethod
    def deserialize(self, tree_entry, git_store):
        pass


class Blob(Base):

    def serialize(self, value, git_store):
        git_blob = GitBlob.from_string(value)
        git_store.add_object(git_blob)
        return TreeEntry(
            mode=tree_entry_modes.raw_blob,
            sha=git_blob.id,
        )

    def deserialize(self, tree_entry, git_store):
        blob = git_store[tree_entry.sha]
        return blob.as_raw_string()


class Primitive(Base):

    def serialize(self, value, git_store):
        content = msgpack.packb(value)
        git_blob = GitBlob.from_string(content)
        git_store.add_object(git_blob)
        return TreeEntry(
            mode=tree_entry_modes.pack_blob,
            sha=git_blob.id,
        )

    def deserialize(self, tree_entry, git_store):
        blob = git_store[tree_entry.sha]
        assert type(blob) == GitBlob
        result = msgpack.unpackb(
            blob.as_raw_string(),
            use_list=True,
        )
        if type(result) is str:
            return result.decode('utf8')
        else:
            # need to fix up nested strings inside lists and dicts,
            # to turn them back from utf8-encoded str to unicode
            if type(result) is list or type(result) is dict:
                # This is a bit of a cheat to avoid duplicating the list/map
                # branch inside this function: we just give it a dummy list
                # to work with, let it recurse into the single child, and
                # then throw away the dummy list.
                self._fix_up_container_out([result], [(0, result)])

            return result

    def _fix_up_container_out(self, container, iterable):
        for k, value in iterable:
            key_type = type(k)
            value_type = type(value)

            if key_type is str:
                del container[k]
                k = k.decode('utf8')
                container[k] = value

            if value_type is str:
                container[k] = value.decode('utf8')
            elif value_type is list:
                self._fix_up_container_out(value, enumerate(value))
            elif value_type is dict:
                # must use items() rather than iteritems() because we're
                # going to modify value in-place.
                self._fix_up_container_out(value, value.items())


_initialize()
