
import unittest2
import dulwich.object_store
import dulwich.objects
import logging

from quantumkeep.tree import *


class TestTree(unittest2.TestCase):

    def setUp(self):
        self.git_store = dulwich.object_store.MemoryObjectStore()

    def test_tree_append(self):
        tree = Tree(git_store=self.git_store)
        self.assertEqual(list(tree), [])
        msg1 = "Hello World"
        tree.append((
            "hi",
            TreeEntry(
                mode=tree_entry_modes.raw_blob,
                target=msg1,
            ),
        ))
        (k, entry) = tree[0]
        self.assertEqual(k, "hi")
        self.assertEqual(entry.target, msg1)
        self.assertEqual(tree["hi"].target, msg1)

    def test_tree_slice(self):
        tree = Tree(git_store=self.git_store)
        self.assertEqual(list(tree), [])
        for i in xrange(0, 11):
            tree.append((
                "key%i" % i,
                TreeEntry(
                    mode=tree_entry_modes.raw_blob,
                    target="value%i" % i
                ),
            ))

        def row_tuples(iterable):
            return [(key, entry.target) for key, entry in iterable]

        def expected_tuples(iterable):
            return [("key%i" % i, "value%i" % i) for i in iterable]

        s1 = tree[2:]
        self.assertEqual(
            row_tuples(s1),
            expected_tuples(xrange(2, 11)),
        )

        del tree[4:]
        self.assertEqual(
            row_tuples(tree),
            expected_tuples(xrange(0, 4))
        )

        tree[2:4] = [(
            "key16",
            TreeEntry(
                mode=tree_entry_modes.raw_blob,
                target="value16",
            ),
        )]
        self.assertEqual(
            row_tuples(tree),
            expected_tuples((0, 1, 16))
        )

    def test_subtree(self):
        tree = Tree(git_store=self.git_store)
        subtree = Tree()
        subtree.append((
            "hi",
            TreeEntry(
                mode=tree_entry_modes.raw_blob,
                target="Hello World",
            ),
        ))
        tree["foo"] = subtree
        entry = tree["foo"]
        self.assertEqual(type(entry.target), Tree)
        self.assertEqual(entry.mode, tree_entry_modes.tree)
        self.assertEqual(entry.target["hi"].target, "Hello World")

    def test_write(self):
        tree = Tree(git_store=self.git_store)
        subtree = Tree()
        subtree.append((
            "hi",
            TreeEntry(
                mode=tree_entry_modes.raw_blob,
                target="Hello World",
            ),
        ))
        tree["foo"] = subtree
        git_tree_id = tree.write_git_tree()
        git_tree = self.git_store[git_tree_id]
        git_subtree_id = git_tree["foo"][1]
        git_subtree = self.git_store[git_subtree_id]
        git_blob_id = git_subtree["hi"][1]
        git_blob = self.git_store[git_blob_id]
        self.assertEqual(git_blob.as_raw_string(), "Hello World")
