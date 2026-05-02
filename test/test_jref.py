import unittest
from jref import resolveRefs, buildRefs

class TestSerializer(unittest.TestCase):

    def test_serialize_scalars(self):
        """Test serialization of basic scalar types."""
        self.assertEqual(buildRefs(None), None)
        self.assertEqual(buildRefs(True), True)
        self.assertEqual(buildRefs(False), False)
        self.assertEqual(buildRefs(123), 123)
        self.assertEqual(buildRefs(1.23), 1.23)
        self.assertEqual(buildRefs("hello world"), "hello world")

    def test_serialize_simple_structures(self):
        """Test serialization of simple lists and dictionaries."""
        self.assertEqual(buildRefs([1, 2, 3]), [1, 2, 3])
        self.assertEqual(buildRefs({"a": 1, "b": "c"}), {"a": 1, "b": "c"})
        self.assertEqual(buildRefs({"list": [1, 2], "val": 3}), {"list": [1, 2], "val": 3})

    def test_serialize_multiple_references(self):
        """Test that multiple references to the same object use JSON pointers."""
        inner = {"key": "value"}
        outer = {"first": inner, "second": inner}
        
        # The first occurrence is serialized fully, the second as a reference
        expected = {
            "first": {"key": "value"},
            "second": {"$ref": "#/first"}
        }
        self.assertEqual(buildRefs(outer), expected)

    def test_serialize_circular_references(self):
        """Test serialization of circular object graphs."""
        node_a = {"name": "A"}
        node_b = {"name": "B", "parent": node_a}
        node_a["child"] = node_b
        
        # node_a at ""
        # node_a["child"] at "/child" (node_b content)
        # node_b["parent"] should be a ref to node_a at ""
        res = buildRefs(node_a)
        self.assertEqual(res["name"], "A")
        self.assertEqual(res["child"]["name"], "B")
        self.assertEqual(res["child"]["parent"], {"$ref": "#"})

    def test_serialize_list_references(self):
        """Test references within lists."""
        item = {"id": 1}
        data = [item, item]
        
        expected = [{"id": 1}, {"$ref": "#/0"}]
        self.assertEqual(buildRefs(data), expected)

    def test_serialize_escaping(self):
        """Test that JSON pointer escaping works for keys with ~ and /."""
        inner = {"val": 1}
        data = {
            "a/b": inner,
            "c~d": inner
        }
        # Pointers should be escaped: / becomes ~1, ~ becomes ~0
        res = buildRefs(data)
        self.assertEqual(res["c~d"], {"$ref": "#/a~1b"})

    def test_serialize_custom_object(self):
        """Test serialization of arbitrary Python objects."""
        class User:
            def __init__(self, name, email):
                self.name = name
                self.email = email
        
        user = User("Alice", "alice@example.com")
        res = buildRefs(user)
        # Objects are serialized as their __dict__
        self.assertEqual(res, {"name": "Alice", "email": "alice@example.com"})

    def test_serialize_custom_object_references(self):
        """Test that repeated custom objects use references."""
        class Item:
            def __init__(self, name):
                self.name = name
        
        it = Item("shared")
        data = {"one": it, "two": it}
        res = buildRefs(data)
        self.assertEqual(res["one"], {"name": "shared"})
        self.assertEqual(res["two"], {"$ref": "#/one"})

    def test_serialize_objectnamefield(self):
        """Test using a custom field for object identification instead of id()."""
        class Entity:
            def __init__(self, eid, data):
                self.eid = eid
                self.data = data
        
        e1 = Entity("id123", "data1")
        e2 = Entity("id124", e1) 
        
        data = [e1, e2]
        res = buildRefs(data, objectnamefield="eid")
        self.assertEqual(res[0], {"eid": "id123", "data": "data1"})
        self.assertEqual(res[1], {"eid": "id124", "data": { "$ref": "#/0"} })

    def test_deserialize_basic(self):
        """Test basic deserialization without references."""
        data = {"a": 1, "b": [2, 3]}
        res = resolveRefs(data)
        self.assertEqual(res, data)

    def test_deserialize_with_refs(self):
        """Test resolving JSON pointers during deserialization."""
        data = {
            "shared": {"x": 10},
            "other": {"$ref": "#/shared"}
        }
        res = resolveRefs(data)
        self.assertEqual(res["other"], {"x": 10})
        # Check that it's the exact same object instance
        self.assertIs(res["other"], res["shared"])

    def test_deserialize_nested_refs(self):
        """Test complex nested references."""
        data = {
            "users": [
                {"name": "Alice", "id": 1},
                {"name": "Bob", "id": 2}
            ],
            "admin": {"$ref": "#/users/0"}
        }
        res = resolveRefs(data)
        self.assertEqual(res["admin"]["name"], "Alice")
        self.assertIs(res["admin"], res["users"][0])

    def test_deserialize_circular(self):
        """Test deserialization of circular references."""
        data = {
            "child": {
                "parent": {"$ref": "#"}
            }
        }
        res = resolveRefs(data)
        self.assertIs(res["child"]["parent"], res)

    def test_deserialize_invalid_ref(self):
        """Test that invalid references raise an Exception."""
        data = {
            "a": 1,
            "b": {"$ref": "#/nonexistent"}
        }
        with self.assertRaises(Exception) as cm:
            resolveRefs(data)
        self.assertEqual(str(cm.exception), "Invalid reference")

    def test_deserialize_escaped_refs(self):
        """Test deserialization with escaped pointer segments."""
        data = {
            "a/b": {"val": 42},
            "ref": {"$ref": "#/a~1b"}
        }
        res = resolveRefs(data)
        self.assertEqual(res["ref"]["val"], 42)
        self.assertIs(res["ref"], res["a/b"])

if __name__ == "__main__":
    unittest.main()
