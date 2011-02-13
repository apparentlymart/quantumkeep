
from quantumkeep import git


class Store(object):

    def __init__(self, dir):
        self.repo = git.Repository(dir)

    def get_object(self, ref):
        name = self.repo.parse_commitish(ref)
        commit = self.repo.get_commit(name)
        return Object._from_git_commit(self, name, commit)

    def create_object(self, dict):
        return self._create_object(dict)

    def _create_object(self, new_dict, parent=None):

        # First we need to recursively create all of the trees
        # and blobs to represent our dictionary.
        def tree_for_dict(new_dict):

            new_tree = git.Tree()

            for key in new_dict:
                value = new_dict[value]
                value_type = type(value)
                if value_type == dict:
                    subtree_name = tree_for_dict(value)
                    # TODO: add a tree item
                elif value_type == str:
                    # TODO: create a blob for this value
                    # TODO: add a blob item
                    pass
                elif value_type == Object:
                    # TODO: add a commit item referring to the object's commit_name
                    pass

            # TODO: write the tree object into the git repo
            # TODO: return the tree object's name

        tree_name = tree_for_dict(new_dict)

        # TODO: write out a commit to the git repo pointing at this tree
        
        pass


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

    def as_native_dict(self):
        dict = self._get_dict()
        return dict.as_native_dict()

    def create_successor(self, dict):
        return self.store._create_object(dict, self)

    def get_predecessors(self):
        parent_names = self.commit.parent_names
        ret = []
        for parent_name in parent_names:
            ret.append(self.store.get_object(parent_name))
        return ret

    predecessors = property(get_predecessors)

    def __getitem__(self, key):
        dict = self._get_dict()
        return dict[key]

    def __len__(self, key):
        dict = self._get_dict()
        return len(dict)

    def __repr__(self):
        dict = self._get_dict()
        return "<qk Object %s %r>" % (self.commit_name, self.as_native_dict())


class Dict(object):

    @classmethod
    def _from_git_tree(cls, store, tree):
        self = cls()
        self.store = store
        self.tree = tree
        return self

    def as_native_dict(self):
        ret = {}
        for key in self.tree.items:
            
            value = self[key]
            if value.__class__ is self.__class__:
                # Recursively native-ize
                value = value.as_native_dict()

            ret[key] = value

        return ret

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
        return "<qk Dict %r>" % self.as_native_dict()

