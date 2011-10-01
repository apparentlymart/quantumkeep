
from quantumkeep import git
import uuid
import re


class Store(object):

    def __init__(self, dir):
        self.repo = git.Repository(dir)

    def get_collection(self, name):
        return Collection(self, name)

    def _get_object_version(self, version_id):
        commit = self.repo.get_commit(version_id)
        return ObjectVersion._from_git_commit(self, version_id, commit)

    def _object_ref_name(self, collection_name, object_id):
        return "refs/%s_coll/%s/%s/%s.obj" % (collection_name, object_id[0:2], object_id[2:4], object_id[4:])

    def _collection_ref_prefix(self, collection_name):
        return "refs/%s_coll" % collection_name

    def _get_object_current_version(self, collection_name, object_id):
        ref = self._object_ref_name(collection_name, object_id)
        version_id = self.repo.parse_commitish(ref)
        return self._get_object_version(version_id)

    def _update_object(self, collection_name, object_id, new_version, old_version=None):
        ref_name = self._object_ref_name(collection_name, object_id)
        try:
            self.repo.update_ref(ref_name, new_version.version_id, old_version.version_id if old_version is not None else None)
        except git.GitError, ex:
            raise UpdateConflictError(collection_name, object_id, old_version, new_version)

    def iterate_all_objects(self, collection=None):
        if collection is not None:
            coll_match = collection.name
        else:
            coll_match = r'\w+'

        ref_match_re = re.compile(r'refs/(%s)_coll/(\w\w)/(\w\w)/(\w+).obj' % coll_match)

        for (commit_id, ref) in self.repo.iterate_refs():
            match = ref_match_re.match(ref)
            if match:
                if collection is None:
                    collection_name = match.group(1)
                    collection = self.get_collection(collection_name)

                current_version = self._get_object_version(commit_id)
                object_id = "%s%s%s" % (match.group(2), match.group(3), match.group(4))

                # We now have all of the information we need to make the object
                # without any further I/O. Yay!
                yield Object._from_current_version(collection, object_id, current_version)


    def _create_object_version(self, new_dict, author, message, parent=None):

        # First we need to recursively create all of the trees
        # and blobs to represent our dictionary.
        def tree_for_dict(new_dict):

            items = []

            for key in new_dict:
                value = new_dict[key]
                value_type = type(value)
                if value_type == dict:
                    subtree_name = tree_for_dict(value)
                    new_item = git.TreeItem()
                    new_item.mode = "040000"
                    new_item.target_type = "tree"
                    new_item.target_name = subtree_name
                    new_item.filename = key
                    items.append(new_item)
                elif value_type == str:
                    blob_name = self.repo.put_blob(value)
                    new_item = git.TreeItem()
                    new_item.mode = "100644"
                    new_item.target_type = "blob"
                    new_item.target_name = blob_name
                    new_item.filename = key
                    items.append(new_item)
                else:
                    raise Exception("Can't store %r value %r", value_type, value)

            return self.repo.put_tree(items)

        tree_name = tree_for_dict(new_dict)
        commit_name = self.repo.put_commit(
            tree_name=tree_name,
            message=message,
            parent_names=[ parent.version_id ] if parent is not None else [],
            author_name=author.name,
            author_email=author.email,
        )

        version_id = commit_name
        return version_id


class Collection(object):

    def __init__(self, store, name):
        self.store = store
        self.name = name

    def create_object(self, new_dict, author, message="Create new object"):
        first_version_id = self.store._create_object_version(new_dict, author, message)
        first_version = self.store._get_object_version(first_version_id)
        object_id = uuid.uuid4().hex
        self.store._update_object(self.name, object_id, first_version)
        return Object._from_current_version(self, object_id, first_version)

    def get_object(self, object_id):
        current_version = self.store._get_object_current_version(self.name, object_id)
        return Object._from_current_version(self, object_id, current_version)

    def iterate_all_objects(self):
        return self.store.iterate_all_objects(collection=self)


class UpdateConflictError(Exception):
    def __init__(self, collection_name, object_id, old_version, new_version):
        self.collection_name = collection_name
        self.object_id = object_id
        self.old_version = old_version
        self.new_version = new_version
        Exception.__init__(self, "Conflict while updating %s:%s" % (collection_name, object_id), old_version, new_version)


class Object(object):

    @classmethod
    def _from_current_version(cls, collection, object_id, current_version):
        self = cls()
        self.current_version = current_version
        self.object_id = object_id
        self.collection = collection
        self.store = collection.store
        return self

    def as_native_dict(self):
        return self.current_version.as_native_dict()

    def create_new_version(self, new_dict, author, message="New version"):
        new_version_id = self.store._create_object_version(new_dict, author, message, parent=self.current_version)
        new_version = self.store._get_object_version(new_version_id)
        self.store._update_object(self.collection.name, self.object_id, new_version, self.current_version)
        self.current_version = new_version
        return new_version

    def get_previous_versions(self):
        return self.current_version.get_previous_versions()

    previous_versions = property(get_previous_versions)

    def __getitem__(self, key):
        return self.current_version[key]

    def __len__(self):
        return len(self.current_version)

    def __repr__(self):
        return "<qk Object %s:%s>" % (self.collection.name, self.object_id)


class ObjectVersion(object):

    @classmethod
    def _from_git_commit(cls, store, version_id, commit):
        self = cls()
        self.version_id = version_id
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

    def get_previous_versions(self):
        parent_names = self.commit.parent_names
        ret = []
        for parent_name in parent_names:
            ret.append(self.store._get_object_version(parent_name))
        return ret

    previous_versions = property(get_previous_versions)

    def __getitem__(self, key):
        dict = self._get_dict()
        return dict[key]

    def __len__(self):
        dict = self._get_dict()
        return len(dict)

    def __repr__(self):
        dict = self._get_dict()
        return "<qk ObjectVersion %s %r>" % (self.commit_name, self.as_native_dict())


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
        else:
            raise Exception("Don't know how to deal with a "+target_type+" git object")

    def __len__(self, key):
        return len(self.tree.items)

    def __repr__(self):
        return "<qk Dict %r>" % self.as_native_dict()


class Author:

    def __init__(self, name, email):
        self.name = name
        self.email = email

