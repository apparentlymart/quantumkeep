
from quantumkeep import git


class Store(object):

    def __init__(self, dir):
        self.repo = git.Repository(dir)

    def get_object(self, ref):
        name = self.repo.parse_commitish(ref)
        commit = self.repo.get_commit(name)
        return Object._from_git_commit(self, name, commit)


class Object(object):

    @classmethod
    def _from_git_commit(cls, store, commit_name, commit):
        self = cls()
        self.commit_name = commit_name
        self.store = store
        self.commit = commit
        self.dict = None # lazy-loaded
        return self

    def _get_dict(self):
        if self.dict is None:
            tree = self.store.repo.get_tree(self.commit.tree_name)
            self.dict = Dict._from_git_tree(self.store, tree)

        return self.dict

    def __getitem__(self, key):
        dict = self._get_dict()
        return dict[key]

    def __len__(self, key):
        dict = self._get_dict()
        return len(dict)

    def __repr__(self):
        dict = self._get_dict()
        return "<qk Object %s, %r>" % (self.commit_name, dict)


class Dict(object):

    @classmethod
    def _from_git_tree(cls, store, tree):
        self = cls()
        self.store = store
        self.tree = tree
        return self

    def __getitem__(self, key):
        item = self.tree.items[key]
        target_type = item.target_type
        target_name = item.target_name
        if target_type == "blob":
            return self.store.repo.get_blob(target_name)
        if target_type == "tree":
            child_tree = self.store.repo.get_tree(target_name)
            return Dict._from_git_tree(self.store, child_tree)
        if target_type == "commit":
            child_commit = self.store.repo.get_commit(target_name)
            return Object._from_git_commit(self.store, child_commit)
        else:
            raise Exception("Don't know how to deal with a "+target_type+" git object")

    def __len__(self, key):
        return len(self.tree.items)

    def __repr__(self):
        disp_dict = {}
        for key in self.tree.items:
            disp_dict[key] = self[key]
        return "<qk Dict %r>" % disp_dict

