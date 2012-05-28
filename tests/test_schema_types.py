
import unittest

from quantumkeep.schema import Schema, Attribute, PrimitiveType


class TestSchemaTypes(unittest.TestCase):

    def setUp(self):
        schema = Schema()
        schema.add_object_type("Article", (
            Attribute("title", PrimitiveType.string, "Title"),
            Attribute("body", PrimitiveType.string),
            Attribute("some_integer", PrimitiveType.integer),
            Attribute("some_boolean", PrimitiveType.boolean),
            Attribute("some_bytes", PrimitiveType.bytes),
            Attribute("some_float", PrimitiveType.float),
            Attribute("some_string", PrimitiveType.string),
        ))
        self.schema = schema

    def test_object_types(self):
        schema = self.schema
        article_type = schema.object_type("Article")
        self.assertEqual(article_type.display_name, "Article")
        self.assertEqual(id(article_type), id(schema.object_type("Article")))
        self.assertEqual(
            [x.key for x in article_type.attributes],
            [
                "title",
                "body",
                "some_integer",
                "some_boolean",
                "some_bytes",
                "some_float",
                "some_string"
            ],
        )
        self.assertEqual(
            [x.caption for x in article_type.attributes],
            [
                "Title",
                "body",
                "some_integer",
                "some_boolean",
                "some_bytes",
                "some_float",
                "some_string"
            ],
        )
        self.assertEqual(
            [x.type for x in article_type.attributes],
            [
                PrimitiveType.string,
                PrimitiveType.string,
                PrimitiveType.integer,
                PrimitiveType.boolean,
                PrimitiveType.bytes,
                PrimitiveType.float,
                PrimitiveType.string
            ],
        )

    def test_primitive_types(self):
        schema = self.schema
        for type_name in ("integer", "float", "bytes", "string", "boolean"):
            self.assertEqual(
                id(getattr(PrimitiveType, type_name)),
                id(schema.primitive_type(type_name))
            )

    def test_list_types(self):
        schema = self.schema
        list_of_string = schema.list_type(PrimitiveType.string)
        self.assertEqual(
            id(list_of_string),
            id(schema.list_type(PrimitiveType.string)),
        )
        self.assertEqual(
            id(list_of_string.item_type),
            id(PrimitiveType.string),
        )
        self.assertEqual(list_of_string.display_name, "list<string>")
        list_of_list_of_string = schema.list_type(
            schema.list_type(PrimitiveType.string)
        )
        self.assertEqual(list_of_list_of_string.display_name, "list<list<string>>")
        self.assertEqual(
            id(list_of_string),
            id(list_of_list_of_string.item_type),
        )

    def test_map_types(self):
        schema = self.schema
        map_string_to_string = schema.map_type(
            PrimitiveType.string,
            PrimitiveType.string,
        )
        self.assertEqual(map_string_to_string.display_name, "map<string,string>")
        self.assertEqual(map_string_to_string.key_type, PrimitiveType.string)
        self.assertEqual(map_string_to_string.value_type, PrimitiveType.string)
