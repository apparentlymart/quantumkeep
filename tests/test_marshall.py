
import unittest

from quantumkeep.schema import PrimitiveType, Schema, Attribute
from quantumkeep.marshall import (
    transform_in,
    pack_in,
)

class TestMarshall(unittest.TestCase):

    def setUp(self):
        schema = Schema()
        schema.add_object_type("SomeObject", (
            Attribute("some_integer", PrimitiveType.integer),
            Attribute("some_boolean", PrimitiveType.boolean),
            Attribute("some_bytes", PrimitiveType.bytes),
            Attribute("some_float", PrimitiveType.float),
            Attribute("some_string", PrimitiveType.string),
        ))
        self.schema = schema
        self.object_type = schema.object_type("SomeObject")

    def assertTI(self, value_type, value, expected):
        got = transform_in(value_type, value)
        self.assertEqual(expected, got)
        self.assertEqual(type(expected), type(got))

    def assertTIRaises(self, value_type, value, exc_type):
        self.assertRaises(exc_type, lambda :
            transform_in(value_type, value)
        )

    def assertBoth(self, value_type, value, expected):
        self.assertTI(value_type, value, expected)

    def assertBothRaises(self, value_type, value, exc_type):
        self.assertTIRaises(value_type, value, exc_type)

    def test_transform_string(self):
        pt = PrimitiveType

        # transform_in
        self.assertTI(pt.string, None, None)
        self.assertTI(pt.string, "foo", "foo")
        self.assertTI(pt.string, u"foo", "foo")
        self.assertTI(pt.string, u"\u2704", "\xe2\x9c\x84")
        # FIXME: this'll raise on a 'narrow' Python build.
        # what to do instead? Just skip this test?
        self.assertTI(pt.string, unichr(0x1d11e), "\xf0\x9d\x84\x9e")
        self.assertTI(pt.string, True, "True")
        self.assertTI(pt.string, 1, "1")
        self.assertTI(pt.string, 1L, "1")
        self.assertTI(pt.string, 1.5, "1.5")
        self.assertTI(pt.string, [], "[]")
        self.assertTI(pt.string, {}, "{}")
        self.assertTIRaises(pt.string, "\xe5", UnicodeDecodeError)

    def test_transform_bidirectional_primitives(self):
        pt = PrimitiveType

        # Boolean
        self.assertBoth(pt.boolean, None, None)
        self.assertBoth(pt.boolean, True, True)
        self.assertBoth(pt.boolean, False, False)
        self.assertBoth(pt.boolean, 1, True)
        self.assertBoth(pt.boolean, 1.2, True)
        self.assertBoth(pt.boolean, "a", True)
        self.assertBoth(pt.boolean, ["a"], True)
        self.assertBoth(pt.boolean, 0, False)
        self.assertBoth(pt.boolean, "", False)
        self.assertBoth(pt.boolean, [], False)

        # Integer
        self.assertBoth(pt.integer, None, None)
        self.assertBoth(pt.integer, 1, 1)
        self.assertBoth(pt.integer, 1L, 1)
        self.assertBoth(pt.integer, 34643563456345, 34643563456345L)
        self.assertBoth(pt.integer, 1.2, 1)
        self.assertBoth(pt.integer, "12", 12)
        self.assertBoth(pt.integer, True, 1)
        self.assertBoth(pt.integer, False, 0)
        self.assertBothRaises(pt.integer, "a", ValueError)

        # Float
        self.assertBoth(pt.float, None, None)
        self.assertBoth(pt.float, 1, 1.0)
        self.assertBoth(pt.float, 1L, 1.0)
        self.assertBoth(pt.float, 34643563456345, 34643563456345.0)
        self.assertBoth(pt.float, 1.2, 1.2)
        self.assertBoth(pt.float, "12", 12.0)
        self.assertBoth(pt.float, "12.5", 12.5)
        self.assertBoth(pt.float, True, 1.0)
        self.assertBothRaises(pt.float, "a", ValueError)

        # Bytes
        self.assertBoth(pt.bytes, None, None)
        self.assertBoth(pt.bytes, "a", "a")
        self.assertBoth(pt.bytes, "\xe2\x9c\x84", "\xe2\x9c\x84")
        self.assertBothRaises(pt.bytes, u"a", TypeError)
        self.assertBothRaises(pt.bytes, True, TypeError)
        self.assertBothRaises(pt.bytes, 1, TypeError)
        self.assertBothRaises(pt.bytes, 1.2, TypeError)
        self.assertBothRaises(pt.bytes, 1L, TypeError)

    def test_transform_object_types(self):
        ot = self.object_type
        self.assertTI(ot, None, None)

        # TODO: test the rest once we actually have the ability to get
        # a class representing an object type.

    def test_transform_list_types(self):
        lt = self.schema.list_type(PrimitiveType.string)

        self.assertTI(lt, None, None)
        self.assertTI(lt, [], [])
        self.assertTI(lt, [None], [None])
        self.assertTI(lt, ["a"], ["a"])
        self.assertTI(lt, [5], ["5"])
        self.assertTI(lt, [5, 6], ["5", "6"])
        self.assertTI(lt, "a", ["a"])
        self.assertTI(lt, (), [])
        self.assertTI(lt, (5,), ["5"])
        self.assertTI(lt, iter(("a","b")), ["a", "b"])
        self.assertTIRaises(lt, 5, TypeError)
        self.assertTIRaises(lt, True, TypeError)

        llt = self.schema.list_type(lt)

        self.assertTI(llt, None, None)
        self.assertTI(llt, [], [])
        self.assertTI(llt, [[]], [[]])
        self.assertTI(llt, [[], []], [[], []])
        self.assertTI(llt, [[1, 2], [3, 4]], [["1", "2"], ["3", "4"]])

    def test_transform_map_types(self):
        mt = self.schema.map_type(PrimitiveType.string, PrimitiveType.string)

        self.assertTI(mt, None, None)
        self.assertTI(mt, {}, {})
        self.assertTI(mt, {1:2}, {"1":"2"})
        self.assertTI(mt, {True:False}, {"True":"False"})
        self.assertTI(mt, {"1":None}, {"1":None})
        self.assertTI(mt, {"a":"b"}, {"a":"b"})
        self.assertTIRaises(mt, [], TypeError)
        self.assertTIRaises(mt, 1, TypeError)
        self.assertTIRaises(mt, "a", TypeError)

        mmt = self.schema.map_type(PrimitiveType.string, mt)
        self.assertTI(mmt, None, None)
        self.assertTI(mmt, {}, {})
        self.assertTI(mmt, {"A":{}}, {"A":{}})
        self.assertTI(mmt, {"A":None}, {"A":None})
        self.assertTI(mmt, {"A":{"B":"C"}}, {"A":{"B":"C"}})
        self.assertTI(mmt, {"A":{"B":None}}, {"A":{"B":None}})

    def test_pack_in(self):
        import msgpack
        value = ["hi", "world"]
        expected = msgpack.packb(value)
        got = pack_in(self.schema.list_type(PrimitiveType.string), value)
        self.assertEquals(expected, got)
        self.assertEquals(type(got), str)
