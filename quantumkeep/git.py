
import subprocess


PIPE=subprocess.PIPE


class Repository(object):

    def __init__(self, git_dir, git_executable="git"):
        self.git_dir = git_dir
        self.git_executable = git_executable

    def _run(self, command, *args, **kwargs):
        cmd = (self.git_executable, command) + args

        stdin = kwargs.get("stdin", None)
        env = kwargs.get("env", {})

        env["GIT_DIR"] = self.git_dir
        proc = subprocess.Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE, env=env)
        (output, errput) = proc.communicate(input=stdin)
        status = proc.returncode
        if status != 0:
            raise GitError(status, errput)
        return output

    def get_blob(self, name):
        return self._run("cat-file", "blob", name)

    def get_tree(self, name):
        return Tree._from_ls_tree_output(self._run("ls-tree", name))

    def get_commit(self, name):
        return Commit._from_pretty_output(self._run("cat-file", "-p", name))

    def parse_commitish(self, commitish):
        return self._run("rev-parse", commitish).rstrip()


class Commit(object):

    def __init__(self):
        self.tree_name = None
        self.message = None
        self.author = None
        self.author_time = None
        self.committer = None
        self.commit_time = None
        self.parent_names = None

    @classmethod
    def _from_pretty_output(cls, output):
        self = cls()

        message_lines = []
        parents = []
        other_fields = {}
        reached_message = False

        for line in output.split("\n"):
            if reached_message or line:
                if reached_message:
                    message_lines.append(line)
                else:
                    (key, value) = line.split(" ", 1)
                    if key == "parent":
                        parents.append(value)
                    else:
                        other_fields[key] = value
            else:
                reached_message = True

        self.tree_name = other_fields["tree"]
        self.message = "\n".join(message_lines)
        self.parent_names = parents

        # FIXME: Parse the author and committer

        return self


class Tree(object):

    def __init__(self):
        self.items = {}

    @classmethod
    def _from_ls_tree_output(cls, output):
        self = cls()
        for line in output.split("\n"):
            if line:
                item = TreeItem._from_ls_tree_line(line)
                self.items[item.filename] = item
        return self

    def add_item(self, item):
        self.items[item.filename] = item

    def get_item(self, filename, default=None):
        return self.items.get(filename, default)


class TreeItem(object):

    @classmethod
    def _from_ls_tree_line(cls, line):
        self = cls()
        (meta, filename) = line.split("\t", 1)
        self.filename = filename
        (mode, target_type, target_name) = meta.split(" ", 2)
        self.mode = mode
        self.target_type = target_type
        self.target_name = target_name
        return self


class GitError(Exception):

    def __init__(self, status, errstr):
        self.status = status
        self.errstr = errstr
        super(GitError, self).__init__(errstr)
