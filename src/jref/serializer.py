
'''JRef/Json Pointer serialization.  See serialize and deserialize functions below"""

@copyright: Jason Desrosiers <jdesrosi@gmail.com> and Scott Lewis <scottslewis@gmail.com>
'''
from typing import Optional, Callable, Generator, Union, Iterable, Dict, List, Any
from urllib.parse import quote as encode_uri
from urllib.parse import unquote as decode_uri

# Type aliases to match the API
Json = Union[None, bool, int, float, str, list, dict]
Getter = Callable[[Json], Optional[Json]]

nil: str = ""

def pointerSegments(pointer: str) -> Generator[str, None, None]:
    if len(pointer) > 0 and not pointer.startswith("/"):
        raise ValueError("Invalid JSON Pointer")
    
    segmentStart = 1
    segmentEnd = 0
    
    while segmentEnd < len(pointer):
        position = pointer.find("/", segmentStart)
        segmentEnd = len(pointer) if position == -1 else position
        segment = pointer[segmentStart:segmentEnd]
        segmentStart = segmentEnd + 1
        
        yield unescape(segment)

def get(pointer: str, subject: Optional[Json] = None) -> Union[Optional[Json], Getter]:
    if subject is None:
        segments = list(pointerSegments(pointer))
        return lambda subject: _get(segments, subject)
    else:
        return _get(pointerSegments(pointer), subject)


def _get(segments: Iterable[str], subject: Optional[Json]) -> Optional[Json]:
    cursor: str = nil
    for segment in segments:
        subject = applySegment(subject, segment, cursor)
        cursor = append(segment, cursor)
    
    return subject

def append(segment: Union[str, int], pointer: str) -> str:
    return pointer + "/" + escape(str(segment))


def escape(segment: str) -> str:
    return str(segment).replace("~", "~0").replace("/", "~1")

def unescape(segment: str) -> str:
    return str(segment).replace("~1", "/").replace("~0", "~")

def computeSegment(value: Optional[Json], segment: str) -> Union[str, int]:
    if isinstance(value, list):
        return len(value) if segment == "-" else int(segment)
    else:
        return segment

def applySegment(value: Optional[Json], segment: Union[str, int], cursor: str = "") -> Optional[Json]:
    if value is None:
        raise TypeError(f"Value at '{cursor}' is {'None' if cursor else 'undefined'} and does not have property '{segment}'")
    elif isScalar(value):
        value_type = type(value).__name__ if value is not None else "null"
        raise TypeError(f"Value at '{cursor}' is a {value_type} and does not have property '{segment}'")
    else:
        computedSegment = computeSegment(value, str(segment))
        if isinstance(value, dict):
            if computedSegment in value:
                return value[computedSegment]
        elif isinstance(value, list):
            if isinstance(computedSegment, int) and 0 <= computedSegment < len(value):
                return value[computedSegment]
        return None

def isScalar(value: Json) -> bool:
    """Check if a value is a scalar (not an object or array)."""
    return value is None or not isinstance(value, (dict, list))

# Type alias for JSON values
Json = Union[None, bool, int, float, str, List[Any], Dict[str, Any]]

_REF_KEY = '$ref'

def _build_ptr(uri: str) -> Dict:
    return { _REF_KEY: '#' + encode_uri(uri)}

####################################################################
# serialize python object graph to dict representation
# 
# During serialization, if the same object is referred to
# multiple times, the first serialized copy will have
# the object contents, and all subsequent references will
# use jref/json pointer to refer to the first serialized instance
#########################################################3##########
def serialize(subject: Json, 
              pointers: Optional[Dict[int, str]] = None, 
              location: str = "", 
              objectnamefield: str = "name",
              refbuilderfn: Callable[str, dict] = _build_ptr) -> Json:

    if pointers is None:
        pointers = {}
    # Handle boolean, float, bool, str
    if isinstance(subject, bool):
        return subject
    elif isinstance(subject, (int, float)) and not isinstance(subject, bool):
        return subject
    elif isinstance(subject, str):
        return subject
    # Handle None
    elif subject is None:
        return subject
    # Handle lists
    elif isinstance(subject, list):
        # Store location for this list
        pointers[id(subject)] = location
        # result is array
        result = []
        # Process array elements and append to result
        for index, value in enumerate(subject):
            if isinstance(value, (list, dict)) and id(value) in pointers:
                # If value is in pointers, then we call the refbuilderfn with the id of the value
                result.append(refbuilderfn(pointers[id(value)]))
            else:
                # otherwise we call ourselves recursively (depth first) and 
                # append to the location with the index
                result.append(serialize(value, pointers, append(str(index), location)))

        return result
    # Dictionaries
    elif isinstance(subject, dict):
        # store location for this obj_id (dict)
        pointers[id(subject)] = location
        # result is dictionary
        result = {}
        # Process dict key values
        for key, value in subject.items():
            if isinstance(value, (list, dict)) and id(value) in pointers:
                # If value is in pointers, then we create a json pointer to it
                result[key] = refbuilderfn(pointers[id(value)])
            else:
                # otherwise we call ourselves recursively (depth first) and 
                # append the key to the location
                result[key] = serialize(value, pointers, append(key, location))
        
        return result
    # Handle python objects
    elif isinstance(subject, object):
        # If it's an object
        try:
            # We first try to get it's name property if it has one
            obj_id = getattr(subject,objectnamefield)
        except Exception:
            # If it does not have a name then we get an object id
            obj_id = id(subject)
        # If the object id is already in pointers, then we return a json pointer
        if obj_id in pointers:
            return refbuilderfn(pointers[obj_id])
        else:
            pointers[obj_id] = location
            return serialize(subject.__dict__, pointers, location)
    else:
        # Fallback for any other type
        return subject

def deserialize(subject: Any, root = None, location: str = "") -> Any:
    if (isinstance(subject, (bool, int, float, str, type(None)))):
        return subject
    if not root:
        root = subject
    if isinstance(subject, list):
        for index, value in enumerate(subject):
            subject[index] = deserialize(value, root, append(str(index), location))
        return subject
    if isinstance(subject, dict):
        ref = subject.get(_REF_KEY, None)
        if isinstance(ref, str):
            fragment = ref.split('#', 2)[1]
            pointer = decode_uri(fragment)
            ref_value = get(pointer, root)
            if not ref_value:
                raise Exception("Invalid reference")
            return ref_value
    if isinstance(subject, object):
        obj_dict = subject if isinstance(subject, dict) else subject.__dict__
        for key, value in obj_dict.items():
            subject[key] = deserialize(value, root, append(key, location))
    return subject    

