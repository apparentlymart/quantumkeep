
import unittest

from dulwich.repo import MemoryRepo
from quantumkeep.git import Tree, GitBlob, GitTree, TREE_MODE


class TestGit(unittest.TestCase):

    def setUp(self):
        self.repo = MemoryRepo.init_bare([], {})

    def make_tree_fixture(self):
        test_blob_1 = GitBlob.from_string("test blob 1")
        test_blob_2 = GitBlob.from_string("test blob 2")
        test_tree_1 = GitTree()
        test_tree_1.add("test_subtree_blob", 0, test_blob_1.id)
        test_tree_2 = GitTree()
        test_tree_2.add("test_tree_1", TREE_MODE, test_tree_1.id)
        test_tree_2.add("test_blob_2", 0, test_blob_2.id)
        test_tree_2.add("test_blob_1", 0, test_blob_1.id)
        self.repo.object_store.add_object(test_blob_1)
        self.repo.object_store.add_object(test_blob_2)
        self.repo.object_store.add_object(test_tree_1)
        self.repo.object_store.add_object(test_tree_2)
        return test_tree_2.id

    def test_read(self):
        tree_id = self.make_tree_fixture()
        tree = Tree(self.repo, tree_id)
        self.assertEqual(tree["test_blob_1"], "test blob 1")
        self.assertEqual(tree["test_blob_2"], "test blob 2")
        child_tree = tree["test_tree_1"]
        self.assertEqual(type(child_tree), Tree)
        self.assertEqual(child_tree["test_subtree_blob"], "test blob 1")
        # A second call should return the same Tree instance
        self.assertEqual(id(child_tree), id(tree["test_tree_1"]))
