
import collections
from dulwich.objects import (
    Tree as GitTree,
    Blob as GitBlob,
    TreeEntry as GitTreeEntry
)

__all__ = ("Tree", "tree_entry_modes", "TreeEntry")


class Tree(collections.MutableMapping, collections.MutableSequence):

    def __init__(self, git_tree=GitTree(), git_store=None):
        self._entries = [
            (name, TreeEntry(mode, sha=sha, git_store=git_store))
            for name, mode, sha in git_tree.iteritems()
        ]
        self._git_store = git_store

    def __getitem__(self, key):
        kt = type(key)
        if kt is int or kt is slice:
            return self._entries[key]
        elif kt is str:
            for name, entry in self._entries:
                if key == name:
                    return entry
            raise KeyError(key)
        else:
            raise KeyError(key)

    def __len__(self):
        return len(self._entries)

    def __setitem__(self, key, value):
        def prepare_value(value):
            vt = type(value)
            if vt is TreeEntry:
                value.git_store = self._git_store
                return value
            elif vt is Tree:
                return TreeEntry(
                    mode=tree_entry_modes.tree,
                    target=value,
                    git_store=self.git_store,
                )
            else:
                raise TypeError("Can't coerce %r into a tree entry" % value)
        def prepare_row(row):
            if type(row) is tuple:
                if len(row) == 2:
                    return (row[0], prepare_value(row[1]))
                else:
                    raise ValueError("Must assign (name, entry) tuple")
            else:
                raise TypeError("Must assign (name, entry) tuple")

        kt = type(key)
        if kt is int:
            self._entries[key] = prepare_row(value)
        elif kt is str:
            value = prepare_value(value)
            for i, row in enumerate(self._entries):
                if key == row[0]:
                   self._entries[i] = value
                   return
            self._entries.append((key, value))
        elif kt is slice:
            self._entries[key] = (prepare_row(x) for x in value)
        else:
            raise KeyError(key)

    def __delitem__(self, key):
        kt = type(key)
        if kt is int or kt is slice:
            del self._entries[key]
        elif kt is str:
            for i, row in enumerate(self._entries):
                if key == row[0]:
                    del self._entries[i]
                    return
            raise KeyError(key)
        else:
            raise KeyError(key)

    def insert(self, i, value):
        self[i:i] = (value,)

    def write_git_tree(self):
        git_tree = GitTree()
        for key, entry in self._entries:
            git_tree.add(
                name=key,
                mode=entry.mode,
                hexsha=entry.sha,
            )
        self._git_store.add_object(git_tree)
        return git_tree.id

    @property
    def git_store(self):
        return self._git_store

    @git_store.setter
    def git_store(self, value):
        if self._git_store == value:
            pass
        elif self._git_store is None:
            self._git_store = value
            for key, entry in self._entries:
                entry.git_store = value
        else:
            raise Exception("%r already has a git store" % self)


    def __repr__(self):
        return "<quantumkeep.tree.Tree %r>" % self._entries


class tree_entry_modes(object):
    tree = 0o40000
    tree_type = 0o100644
    pack_blob = 0o100644
    raw_blob = 0o100755



class TreeEntry(object):
    _mode = None
    _orig_sha = None
    _target = None

    def __init__(self, mode, target=None, sha=None, git_store=None):
        self._mode = mode
        self._orig_sha = sha
        self._git_store = git_store
        self.target = target

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        self._mode = value

    @property
    def sha(self):
        if self._target is not None:
            target = self._target
            if type(target) is str:
                git_blob = GitBlob.from_string(target)
                if self._git_store is not None:
                    self._git_store.add_object(git_blob)
                return git_blob.id
            elif type(target) is Tree:
                tree_id = target.write_git_tree()
                return tree_id
            else:
                raise TypeError("Invalid target type %s" % type(target))
        else:
            return self._orig_sha

    @property
    def target(self):
        if self._target is None:
            git_obj = self._git_store[self._orig_sha]
            if type(git_obj) is GitTree:
                self._target = Tree(
                    git_tree=git_obj,
                    git_store=self._git_store,
                )
            else:
                # assume it's a blob
                self._target = git_obj.as_raw_string()

        return self._target

    @target.setter
    def target(self, value):
        if type(value) is Tree:
            value.git_store = self._git_store
        self._target = value

    def as_git_tree_entry(self, name):
        return GitTreeEntry(
            sha=self.sha,
            mode=self.mode,
            path=name,
        )

    @property
    def git_store(self):
        return self._git_store

    @git_store.setter
    def git_store(self, value):
        if self._git_store == value:
            pass
        elif self._git_store is None:
            self._git_store = value
            if type(self._target) is Tree:
                self._target.git_store = value
        else:
            raise Exception("%r already has a git store" % self)

    def __repr__(self):
        return "<quantumkeep.tree.TreeEntry %s %s>" % (
            oct(self.mode),
            self.sha,
        )
