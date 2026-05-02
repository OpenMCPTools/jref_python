# JRef Python Implementation (local only)

A lightweight Python utility for building and resolving **JSON Pointers** (RFC 6901) references in complex object graphs. 

## Features

- 🔄 **Circular Reference Support**: Build and resolve references to objects that reference themselves without recursion errors.
- 📂 **JSON Pointer Syntax**: Fully compliant with RFC 6901, including character escaping (`~0`, `~1`).
- 🛠️ **Custom Object Support**: Automatically handles standard Python classes by serializing their `__dict__`.
- ⚙️ **Customizable**: Supply your own reference builders or object identification logic.

## Installation

Simply include `jref.py` in your project or install via your internal package manager.

```python
from jref import buildRefs, resolveRefs
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

refs = buildRefs(data)
# Output: {'first': {'name': 'Shared'}, 'second': {'$ref': '#/first'}}

resolved = resolveRefs(refs)
assert resolved["first"] is resolved["second"]
```

### 2. Circular References
`jref` handles back-references seamlessly.

```python
node_a = {"name": "Node A"}
node_b = {"name": "Node B"}
node_a["child"] = node_b
node_b["parent"] = node_a

refs = buildRefs(node_a)
# Resulting 'parent' will be: {"$ref": "#"}
```

### 3. Custom Python Objects
You can serialize custom class instances directly.

```python
class User:
    def __init__(self, username):
        self.username = username

user = User("alice")
refs = buildRefs(user)
# Output: {"username": "alice"}
```

## API Reference

### `buildRefs(subject, ...)`
Converts a Python object graph into a JSON-serializable dictionary with > 1 refs to a given object replaced with json pointer
- `subject`: The object graph.
- `objectnamefield`: Field to use for object ID (defaults to `name`, falls back to `id()`).
- `refbuilderfn`: A function that returns the reference dict (defaults to `{"$ref": "#/path"}`).

### `resolveRefs(subject)`
Resolves JSON pointers live object references
- `subject`: The dictionary/list containing `$ref` keys.
- **Note**: This function modifies lists/dicts in-place.

## Requirements
- Python 3.6+
- No external dependencies.

