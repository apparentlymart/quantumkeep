
import unittest
from quantumkeep.store import Store
from quantumkeep.gitdict import TREE_MODE


# Our initial tree always hashes to the following
INITIAL_TREE = "21ec73b6f4d71131d3214c591bf504a4c5277e2e"


class TestStore(unittest.TestCase):

    def test_store_init(self):
        store = Store.in_memory()
        repo = store.repo
        commit_id = repo.refs["refs/heads/master"]
        commit = repo[commit_id]
        self.assertEquals(commit.author, "system")
        self.assertEquals(commit.committer, "system")
        self.assertEquals(commit.message, "Initialize new store")
        self.assertEquals(commit.tree, INITIAL_TREE)