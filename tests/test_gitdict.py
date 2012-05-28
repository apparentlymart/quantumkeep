
import unittest

from dulwich.repo import MemoryRepo
from quantumkeep.gitdict import GitDict, GitBlob, GitTree, TREE_MODE


# An empty tree always hashes to the following
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


class TestGitDict(unittest.TestCase):

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
        gitdict = GitDict(self.repo, tree_id)
        self.assertEqual(gitdict["test_blob_1"], "test blob 1")
        self.assertEqual(gitdict["test_blob_2"], "test blob 2")
        child_gitdict = gitdict["test_tree_1"]
        self.assertEqual(type(child_gitdict), GitDict)
        self.assertEqual(child_gitdict["test_subtree_blob"], "test blob 1")
        # A second call should return the same GitDict instance
        self.assertEqual(id(child_gitdict), id(gitdict["test_tree_1"]))
        keys = tuple(sorted(gitdict.__iter__()))
        self.assertEqual(keys, (
            'test_blob_1', 'test_blob_2', 'test_tree_1',
        ))
        for key, value in gitdict.iteritems():
            self.assertEqual(value, gitdict[key])

    def test_make_subtree(self):
        tree_id = self.make_tree_fixture()
        gitdict = GitDict(self.repo, tree_id)
        child_gitdict = gitdict.make_subtree("test_make_subtree")
        child_child_gitdict = child_gitdict.make_subtree("another_subtree")
        new_tree_id = gitdict.write_to_repo()
        self.assertEqual(
            type(gitdict["test_make_subtree"]), GitDict
        )
        self.assertEqual(
            type(gitdict["test_make_subtree"]["another_subtree"]), GitDict
        )
        child_git_tree = self.repo[new_tree_id]
        child_tree_mode, child_tree_id = child_git_tree["test_make_subtree"]
        child_child_git_tree = self.repo[child_tree_id]
        child_child_tree_mode, child_child_tree_id = child_child_git_tree["another_subtree"]
        self.assertEqual(child_child_tree_id, EMPTY_TREE)

    def test_blob(self):
        gitdict = GitDict(self.repo)
        gitdict["blob1"] = "blob1"
        gitdict["blob2"] = "blob2"
        self.assertEqual(tuple(sorted(gitdict)), ("blob1", "blob2"))
        tree_id = gitdict.write_to_repo()
        git_tree = self.repo[tree_id]
        self.assertEqual(tuple(sorted(git_tree)), ("blob1", "blob2"))
        blob2_id = git_tree["blob2"][1]
        git_blob2 = self.repo[blob2_id]
        self.assertEqual(git_blob2.as_raw_string(), "blob2")

        gitdict["blob2"] = "blob2.2"
        tree_id = gitdict.write_to_repo()
        git_tree = self.repo[tree_id]
        blob2_id = git_tree["blob2"][1]
        git_blob2 = self.repo[blob2_id]
        self.assertEqual(git_blob2.as_raw_string(), "blob2.2")

    def test_write_to_repo(self):
        tree_id = self.make_tree_fixture()
        gitdict = GitDict(self.repo, tree_id)

        # write_to_repo with no changes yields the same tree id
        self.assertEqual(tree_id, gitdict.write_to_repo())

        child_gitdict = gitdict.make_subtree("blah")

        new_tree_id = gitdict.write_to_repo()

        # new_tree_id should be different
        self.assertNotEqual(new_tree_id, tree_id)

        # write_to_repo with no changes yields the same tree id again
        self.assertEqual(new_tree_id, gitdict.write_to_repo())

        # New tree should be in the repo
        new_git_tree = self.repo[new_tree_id]
        entry = new_git_tree["blah"]
        self.assertEqual(entry[1], EMPTY_TREE)

        # The empty tree should also be in the repo
        empty_tree = self.repo[EMPTY_TREE]
