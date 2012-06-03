
from dulwich.objects import Commit as GitCommit, Tag as GitTag
from quantumkeep.gitdict import GitDict
from quantumkeep.schema import Schema


class Commit(object):

    def __init__(self, store, git_commit):
        self.store = store
        self.git_commit = git_commit


class Head(object):

    def __init__(self, store, head_name=None, commit_id=None):
        self.store = store
        self._schema = None
        if head_name is not None:
            self.ref_name = "refs/heads/" + head_name
        else:
            self.ref_name = None
        if commit_id is not None:
            self.latest_commit_id = commit_id
        else:
            if self.ref_name is not None:
                try:
                    self.latest_commit_id = store.repo.refs[self.ref_name]
                except KeyError:
                    raise ValueError("There is no head called %s" % head_name)
            else:
                raise Exception("Must pass head_name if no commit_id is passed")

    def open_data_transaction(self):
        full_dict = self._make_latest_commit_gitdict()
        data_dict = full_dict["data"]

        return DataTransaction(self.latest_commit_id, self.schema, data_dict)

    def commit_transaction(self, transaction, commit_message):
        # TODO: Implement this
        pass

    def data_transaction(self, commit_message):
        return TransactionContextManager(self, commit_message)

    def _make_latest_commit_gitdict(self):
        git_commit = self.store.repo[self.latest_commit_id]
        tree_id = git_commit.tree
        return GitDict(self.store.repo, tree_id)

    @property
    def schema(self):
        if self._schema is None:
            full_dict = self._make_latest_commit_gitdict()
            self._schema = Schema.from_schema_dict(full_dict["schema"])
        return self._schema


class Tag(object):
    pass


class DataTransaction(object):

    def __init__(self, base_commit_id, schema, data_dict):
        self.base_commit_id = base_commit_id
        self.schema = schema
        self.data_dict = data_dict
        self._open_containers = {}

    def __getitem__(self, key):
        if key not in self._open_containers:
            container = self.schema.container(key)
            container_data_dict = self.data_dict[key]
            self._open_containers[key] = (
                DataTransactionContainer(container, container_data_dict)
            )
        return self._open_containers[key]


class DataTransactionContainer(object):

    def __init__(self, container, data_dict):
        self.container = container
        self.dict = data_dict


class TransactionContextManager(object):
    def __init__(self, branch, commit_message):
        self.branch = branch
        self.commit_message = commit_message

    def __enter__(self):
        self.transaction = self.branch.open_transaction()
        return self.transaction

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_value is not None:
            self.branch.commit_transaction(
                self.transaction,
                self.commit_message,
            )
