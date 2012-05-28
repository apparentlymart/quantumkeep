
import unittest

from quantumkeep.schema import Schema, Attribute, PrimitiveType
from quantumkeep.diff import value_diff, ValueConflict, NoDifference


class TestDiffValue(unittest.TestCase):

    def setUp(self):
        schema = Schema()
        schema.add_object_type("SomeType", (
            Attribute("some_integer", PrimitiveType.integer,
                      differ=value_diff.numeric_sum),
            Attribute("some_boolean", PrimitiveType.boolean),
            Attribute("some_bytes", PrimitiveType.bytes),
            Attribute("some_float", PrimitiveType.float),
            Attribute("some_string", PrimitiveType.string),
        ))
        self.schema = schema
        self.object_type = schema.object_type("SomeType")

    def test_replace(self):
        replace_diff = value_diff.replace(
            PrimitiveType.string,
            "a",
            "b",
        )
        self.assertEqual(replace_diff("a"), "b")
        self.assertRaises(ValueConflict, lambda : replace_diff("b"))
        self.assertRaises(ValueConflict, lambda : replace_diff("c"))
        self.assertRaises(NoDifference, lambda : value_diff.replace(
            PrimitiveType.string,
            "a",
            "a"
        ))

    def test_numeric_sum(self):
        add_diff = value_diff.numeric_sum(
            PrimitiveType.integer,
            5,
            10,
        )
        self.assertEquals(add_diff.diff, 5)
        self.assertEquals(add_diff(10), 15)

        sub_diff = value_diff.numeric_sum(
            PrimitiveType.integer,
            10,
            8,
        )
        self.assertEquals(sub_diff.diff, -2)
        self.assertEquals(sub_diff(15), 13)

        float_diff = value_diff.numeric_sum(
            PrimitiveType.float,
            5.0,
            6.5,
        )
        self.assertEquals(float_diff.diff, 1.5)
        self.assertEquals(float_diff(10.0), 11.5)

        self.assertRaises(NoDifference, lambda : value_diff.numeric_sum(
            PrimitiveType.integer,
            1,
            1,
        ))
        self.assertRaises(NoDifference, lambda : value_diff.numeric_sum(
            PrimitiveType.integer,
            1.5,
            1.5,
        ))
