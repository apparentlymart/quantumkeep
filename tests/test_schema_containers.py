
import unittest

from quantumkeep.schema import Schema, Attribute, PrimitiveType, ObjectType


class TestSchemaContainers(unittest.TestCase):

    def setUp(self):
        schema = Schema()
        schema.add_object_type("Article", (
            Attribute("title", PrimitiveType.string,
                      caption="Title"),
            Attribute("body", PrimitiveType.string),
            Attribute("key", PrimitiveType.string),
            Attribute("month", PrimitiveType.integer),
            Attribute("year", PrimitiveType.integer),
        )),
        self.schema = schema
        self.ot = schema.object_type("Article")

        schema.add_container("articles", self.ot, ("year","month","key"))
        self.container = schema.container("articles")

    def test_container(self):
        cont = self.container
        self.assertEqual(type(cont.item_type), ObjectType)
        self.assertEqual(cont.item_type, self.ot)
        self.assertEqual(type(cont.item_key_attrs[0]), Attribute)
        self.assertEqual(cont.item_key_attrs[0].key, "year")
        self.assertEqual(cont.item_key_attrs[1].key, "month")
        self.assertEqual(cont.item_key_attrs[2].key, "key")
        self.assertEqual(len(cont.item_key_attrs), 3)

    def test_container_path_chunks_for_item(self):
        cont = self.container
        item = self.ot.python_class()
        item.title = "Hello World"
        item.body = "This is a test"
        item.key = "hello_world"
        item.month = 3
        item.year = 2012
        chunks = cont.path_chunks_for_item(item)
        self.assertEqual(chunks, ["2012", "3", "hello_world"])

        item.month = None
        self.assertRaises(ValueError, lambda : (
            cont.path_chunks_for_item(item)
        ))

    def test_container_path_chunks_for_key(self):
        cont = self.container
        chunks = cont.path_chunks_for_key(
            year=2011,
            month=6,
            key="cheese_pizza",
        )
        self.assertEqual(chunks, ["2011", "6", "cheese_pizza"])

        self.assertRaises(ValueError, lambda : (
            cont.path_chunks_for_key(
                year=2011,
                key="cheese_pizza",
            )
        ))
        self.assertRaises(ValueError, lambda : (
            cont.path_chunks_for_key(
                year=2011,
                month=None,
                key="cheese_pizza",
            )
        ))
