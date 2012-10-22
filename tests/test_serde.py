
import unittest2
import msgpack
from quantumkeep.serde import (
    serialize_value,
    deserialize_tree_entry,
    TreeEntry,
)
import dulwich.object_store
import dulwich.objects
import logging
import functools


DEFAULT = object()


class TestSerDe(unittest2.TestCase):

    def setUp(self):
        self.git_store = dulwich.object_store.MemoryObjectStore()

    def assert_serialize_result(self, value, expected_sha, expected_mode=None,
                                expected_value=DEFAULT):
        tree_entry = serialize_value(value, self.git_store)

        self.assertEqual(type(tree_entry), TreeEntry)

        blob = self.git_store[tree_entry.sha]
        self.assertEqual(type(blob), dulwich.objects.Blob)

        self.assertEqual(
            (tree_entry.mode, tree_entry.sha),
            (expected_mode, expected_sha),
        )

        if expected_value == DEFAULT:
            expected_value = value

        got_value = deserialize_tree_entry(tree_entry, self.git_store)
        self.assertEqual(got_value, expected_value)
        self.assertEqual(type(got_value), type(expected_value))

    def test_primitive_serde(self):
        test_serialize = functools.partial(
            self.assert_serialize_result,
            expected_mode=0o100644,
        )

        test_serialize(1, "6b2aaa7640726588bcd3d57e1de4b1315b7f315e")
        test_serialize(129, "7f2a378569147197e2a0deabe46094f97b122486")
        test_serialize(1024, "a5e0f54f2ab2f7ef67193ba3387de65893bcdd61")
        test_serialize(100000, "57e4b862378cca7d540a7295b0b2d7b82f0d98cf")
        test_serialize(2 ** 34, "f6694445da22cc39b3d5222130f132776bc086a1")
        test_serialize(-2, "050ac90ecbd9ce5a88212058fad711b4231d104d")
        test_serialize(-34, "037581176b08ab378e9b4c2bb53bd74e79725e02")
        test_serialize(-1025, "508c54e578fd05df60ffabbe415b979d71c1ab6e")
        test_serialize(-1000000, "25147a99cd168e51c053a91fc96f5e287d6038e2")
        test_serialize(-2 ** 34, "c3d272b93e25a89b9c541d4dfb18950a7b6e7e31")
        test_serialize(None, "e7754cae5adecf1f21102527fbdeae39280f8e24")
        test_serialize(True, "6b10f9584314d9e7304b2c13c480fc3d01acabe9")
        test_serialize(False, "52771883833a931bf221105e2eb19fdc30a1631a")
        test_serialize(1.2, "7d87e19be23cd6516528d9bdab42a1de80e7a36f")
        test_serialize(u"hello", "c136b0ba92af9ae8be9592b29e65dd4c287a9470")
        test_serialize(u"\u270d", "bb352929d616325745d66e415cd72a7bf409c1b9")
        test_serialize(
            u"\u0001d11e",
            "39bc48fa9bb2251ab4fad12add0b2ec6513b8ae1"
        )
        test_serialize(
            u"1234567890" * 5,
            "483371c0f70cad47339f36cd4b4c47d6f0e6d554",
        )
        test_serialize([1, 2, 3], "dfedbc05a6a1b7cdfcc9e7d7cbe97a0360f0b2a5")
        test_serialize(
            [1, 2, 3, 4, 5] * 4,
            "9899758d9939eab3901bf70779e7689fcdb1bb96",
        )
        test_serialize(
            {1: 1, 2: 2, 3: 3},
            "bc4ec3a7e1fd9d73746e19bec95ad14c2f52aa76",
        )
        test_serialize(
            dict(((x, x) for x in xrange(0, 20))),
            "a1ff004033c499c7ca4ed75105290bab41595983",
        )
        test_serialize(
            dict(((x, x) for x in xrange(0, 65540))),
            "d5a02689d02a39bc13f37c0dfe158d0fdcd2e17f",
        )
        test_serialize(
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 65540,
            "69a35df7a70b5f295903102b60e590183f2e6f39",
        )
        test_serialize(
            u"1234567890" * 65540,
            "e0edf0aaac0296d2b8bbc3cf6555460175e2866e",
        )
        test_serialize([u"\u270d"], "489e6fe49efc56ea3057798a8cb5bc86802be35f")
        test_serialize(
            [[u"\u270d"]], "be5fc328fab309c8341d905759ad7f8cb45d4a26"
        )
        test_serialize(
            {u"\u270d":u"\u270d"},
            "2436a4f4ecfb7b49a9d1c5e6aeca75222a9c4e67",
        )
        test_serialize(
            {u"\u270d":[u"\u270d"]},
            "1c24f60df7a2f4295d0ddc92365da2dca34a8df9",
        )

    def test_blob_serde(self):
        test_serialize = functools.partial(
            self.assert_serialize_result,
            expected_mode=0o100755,
        )

        test_serialize('abc123', '49fbc054731540fa68b565e398d3574fde7366e9')
        test_serialize('', 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391')
        test_serialize(
            '\xF0\x9D\x84\x9E', # valid utf8
            '632101dafbd67f673d01df8b069388c2e1301414',
        )
        test_serialize(
            '\x47\x49\x46\x38\x39\x61\x01\xfe\x01', # not utf8 at all
            '99ff76f380bb9d8bd7281d43d8040d275ee64e9b',
        )
