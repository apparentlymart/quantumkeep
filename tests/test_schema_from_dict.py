
import unittest

from quantumkeep.schema import Schema, Attribute, PrimitiveType, ObjectType
from quantumkeep.gitdict import GitDict
from quantumkeep.store import Store
from msgpack import packb
from quantumkeep.schema import (
    Schema, ObjectType, PrimitiveType, Container, _schemas_by_tree_id
)


class TestSchemaFromDict(unittest.TestCase):

    def setUp(self):
        store = Store.in_memory()
        repo = store.repo

        commit_id = repo.refs["refs/heads/master"]
        commit = repo[commit_id]
        tree_id = commit.tree

        git_dict = GitDict(repo, tree_id)
        self.schema_dict = git_dict["schema"]
        self.object_types_dict = self.schema_dict["object_types"]
        self.containers_dict = self.schema_dict["containers"]

    def test_schema_from_dict(self):
        article_type_dict = {
            "attributes": [
                {
                    "key": "title",
                    "type": ["primitive", "string"],
                },
                {
                    "key": "body",
                    "type": ["primitive", "string"],
                },
                {
                    "key": "year",
                    "type": ["primitive", "integer"],
                },
                {
                    "key": "month",
                    "type": ["primitive", "integer"],
                },
                {
                    "key": "url_name",
                    "type": ["primitive", "string"],
                },
            ],
        }
        articles_container_dict = {
            "item_type": "Article",
            "item_key_attrs": ["year", "month", "url_name"],
        }
        self.object_types_dict["Article"] = packb(article_type_dict)
        self.containers_dict["articles"] = packb(articles_container_dict)

        schema = Schema.from_schema_dict(self.schema_dict)
        article_type = schema.object_type("Article")
        self.assertEqual(type(article_type), ObjectType)
        self.assertEqual(article_type.attributes[4].key, "url_name")
        self.assertEqual(article_type.attributes[4].type, PrimitiveType.string)

        container = schema.container("articles")
        self.assertEqual(type(container), Container)
        self.assertEqual(container.item_type, article_type)
        self.assertEqual(container.item_key_attrs[2], article_type.attributes[4])

        # Schema should be cached against the tree id
        schema_tree_id = self.schema_dict.write_to_repo()
        self.assertEqual(_schemas_by_tree_id[schema_tree_id], schema)

        # But only as long as someone's holding a reference to it.
        # (it's a weakref inside the schema module.)
        schema = None
        self.assertEqual(_schemas_by_tree_id.get(schema_tree_id), None)
