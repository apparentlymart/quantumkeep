
from dulwich.repo import Repo, MemoryRepo
from dulwich.client import get_transport_and_path


class Store(object):

    def __init__(self, repo):
        self.repo = repo

    @classmethod
    def open(cls, path):
        return cls(Repo(path))

    @classmethod
    def create(cls, path):
        from os import mkdir
        mkdir(path)
        repo = Repo.init_bare(path)
        _create_initial_commit(repo)
        return cls(repo)

    @classmethod
    def in_memory(cls):
        repo = MemoryRepo.init_bare([], {})
        _create_initial_commit(repo)
        return cls(repo)


def _create_initial_commit(repo, author="system"):
    # Every repo must start with a skeleton structure with an empty
    # schema and empty dataset. The code for manipulating the store
    # assumes the presence of this basic skeleton.
    from dulwich.objects import Commit
    from quantumkeep.gitdict import GitDict
    from time import time
    initial_dict = GitDict(repo)
    initial_dict["schema"] = {
        "object_types": {},
        "containers": {},
    }
    initial_dict["data"] = {}
    tree_id = initial_dict.write_to_repo()
    commit = Commit()
    commit.tree = tree_id
    commit.author = author
    commit.committer = author
    commit.commit_time = commit.author_time = int(time())
    commit.commit_timezone = commit.author_timezone = 0
    commit.encoding = "UTF-8"
    commit.message = "Initialize new store"
    repo.object_store.add_object(commit)
    repo.refs['refs/heads/master'] = commit.id
