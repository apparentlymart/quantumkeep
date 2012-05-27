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


TREE_MODE = 0400000


class Tree(object):

    def __init__(self, repo, tree_id):
        self.repo = repo
        base_tree = repo[tree_id]
        if type(base_tree) is not GitTree:
            raise ValueError("%r does not represent a tree" % tree_id)

        self._tree_items = {}
        self._live_children = {}

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
                child_tree = Tree(self.repo, tree_entry[1])
                self._live_children[key] = child_tree
                return child_tree
            else:
                blob = self.repo[tree_entry[1]]
                if type(blob) is not GitBlob:
                    raise Exception("Expected blob but got %r" % blob)
                return blob.as_raw_string()

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __iter__(self):
        live = self._live_children
        for key in live:
            yield key
        for key in self._tree_items:
            if key not in live:
                yield key

    def iteritems(self):
        for key in self.__iter__():
            yield (key, self[key])
