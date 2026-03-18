# JRef Python Serializer

A lightweight Python utility for serializing and deserializing complex object graphs using **JSON Pointers** (RFC 6901).

## Features

- 🔄 **Circular Reference Support**: Serialize objects that reference themselves without recursion errors.
- 🤝 **Object Sharing**: Preserve object identity. If multiple keys point to the same object, they will point to the same instance after deserialization.
- 📂 **JSON Pointer Syntax**: Fully compliant with RFC 6901, including character escaping (`~0`, `~1`).
- 🛠️ **Custom Object Support**: Automatically handles standard Python classes by serializing their `__dict__`.
- ⚙️ **Customizable**: Supply your own reference builders or object identification logic.

## Installation

Simply include `serializer.py` in your project or install via your internal package manager.

```python
from jref.serializer import serialize, deserialize
```

## Usage

### 1. Handling Shared References
In standard JSON, the shared "inner" object would be duplicated. `jref` preserves the link.

```python
shared_item = {"name": "Shared"}
data = {
    "first": shared_item,
    "second": shared_item
}

serialized = serialize(data)
# Output: {'first': {'name': 'Shared'}, 'second': {'$ref': '#/first'}}

reconstructed = deserialize(serialized)
assert reconstructed["first"] is reconstructed["second"]
```

### 2. Circular References
`jref` handles back-references seamlessly.

```python
node_a = {"name": "Node A"}
node_b = {"name": "Node B"}
node_a["child"] = node_b
node_b["parent"] = node_a

serialized = serialize(node_a)
# Resulting 'parent' will be: {"$ref": "#"}
```

### 3. Custom Python Objects
You can serialize custom class instances directly.

```python
class User:
    def __init__(self, username):
        self.username = username

user = User("alice")
serialized = serialize(user)
# Output: {"username": "alice"}
```

## API Reference

### `serialize(subject, ...)`
Converts a Python object graph into a JSON-serializable dictionary.
- `subject`: The object to serialize.
- `objectnamefield`: Field to use for object ID (defaults to `name`, falls back to `id()`).
- `refbuilderfn`: A function that returns the reference dict (defaults to `{"$ref": "#/path"}`).

### `deserialize(subject)`
Resolves JSON pointers within a dictionary back into live object references.
- `subject`: The dictionary/list containing `$ref` keys.
- **Note**: This function modifies lists/dicts in-place.

## Requirements
- Python 3.6+
- No external dependencies.

