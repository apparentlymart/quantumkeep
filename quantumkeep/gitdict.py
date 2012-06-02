"""
A slightly higher-level wrapper around dulwich that provides a more convenient
interface for the sorts of operations we tend to do.

The responsibility of this layer is to represent a mutable heirarchy of
trees and blobs and keep track of what needs to be written out to the
git repo in order to persist it. This allows a bunch of simple blob/tree
writes to be done without hitting disk and then the net result written out
as real trees and blobs on disk when the heirarchy is in a "finished" state.

This layer only deals in trees and blobs, leaving other constructs like
commits and tags to be handled by the caller where needed.
"""

import weakref

from dulwich.objects import Tree as GitTree, Blob as GitBlob
from dulwich.diff_tree import tree_changes_for_merge, tree_changes


TREE_MODE = 0o40000


class GitDict(object):

    def __init__(self, repo, tree_id=None):
        self.repo = repo

        self._tree_items = {}
        self._live_children = {}

        self._base_tree_id = tree_id

        if tree_id is not None:
            base_tree = repo[tree_id]
            if type(base_tree) is not GitTree:
                raise ValueError("%r does not represent a tree" % tree_id)
            for item_name, item_mode, item_id in base_tree.iteritems():
                self._tree_items[item_name] = (item_mode, item_id)

    @property
    def parent(self):
        if self._parent_ref is not None:
            return self._parent_ref()
        else:
            return None

    def _unlink_parent(self):
        self._parent_ref = None

    def __getitem__(self, key):
        try:
            return self._live_children[key]
        except KeyError:
            tree_entry = self._tree_items[key]
            if tree_entry[0] & TREE_MODE:
                child_tree = GitDict(self.repo, tree_entry[1])
                self._live_children[key] = child_tree
                try:
                    del self._tree_items[key]
                except KeyError:
                    pass
                return child_tree
            else:
                blob = self.repo[tree_entry[1]]
                if type(blob) is not GitBlob:
                    raise Exception("Expected blob but got %r" % blob)
                return blob.as_raw_string()

    def __setitem__(self, key, value):
        value_type = type(value)
        if value_type is str:
            self._live_children[key] = value

            try:
                del self._tree_items[key]
            except KeyError:
                pass
        elif value_type is dict:
            child_gitdict = self.make_subdict(key)
            for child_key, child_value in value.iteritems():
                child_gitdict[child_key] = value[child_key]
        else:
            raise TypeError("GitDict value (for %r) must be a byte string or a native dict" % key)

    def __delitem__(self, key):
        try:
            del self._tree_items[key]
        except KeyError:
            del self._live_children[key]

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __iter__(self):
        for key in tuple(self._live_children):
            yield key
        for key in tuple(self._tree_items):
            yield key

    def iteritems(self):
        for key in self.__iter__():
            yield (key, self[key])

    def make_subdict(self, key):
        child_gitdict = GitDict(self.repo)
        self._live_children[key] = child_gitdict
        try:
            del self._tree_items[key]
        except KeyError:
            pass
        return child_gitdict

    def write_to_repo(self):
        """
        Write any new blob and tree objects to the underlying git repository
        and return the id (hex sha1) of the top-level tree object that results.
        """

        # Don't do anything if we have no live objects,
        # since that means we've not actually changed anything.
        if self._base_tree_id is not None and len(self._live_children) == 0:
            return self._base_tree_id

        git_tree = GitTree()

        # First add the items that haven't changed at all.

        for key, item_def in self._tree_items.iteritems():
            git_tree.add(key, item_def[0], item_def[1])

        # Now cook and add the live objects

        for key, value in self._live_children.items():
            if type(value) is GitDict:
                child_tree_id = value.write_to_repo()
                git_tree.add(key, TREE_MODE, child_tree_id)
            else:
                git_blob = GitBlob.from_string(value)
                self.repo.object_store.add_object(git_blob)
                git_tree.add(key, 0, git_blob.id)

        self.repo.object_store.add_object(git_tree)

        self._base_tree_id = git_tree.id
        return self._base_tree_id

    def as_native_dict(self):
        ret = {}
        for key, value in self.iteritems():
            if type(value) is GitDict:
                ret[key] = value.as_native_dict()
            else:
                ret[key] = value
        return ret

    def __repr__(self):
        return "<GitDict %r>" % self.as_native_dict()


def find_changed_leaves(repo, old_tree_id, new_tree_id):
    store = repo.object_store
    changes = tree_changes(store, old_tree_id, new_tree_id)
    for change in changes:
        path = change.new.path if change.new.path is not None else change.old.path
        path_chunks = path.split("/")
        yield (
            tuple(path_chunks),
            change.type,
        )
