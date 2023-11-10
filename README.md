Python minimal Protobuf
-----

This repository contains a minimal implementation of the Protobuf specification in Python.

The reason for creating this repository is that I have a need for generating on-the-fly dynamic protobuf messages in Python. I have not found any existing libraries that can do this, so I decided to create my own.

With this repository you can deserialize serialized protobuf messages in a format that resembles the protoscope format. You can also serialize messages to protobuf using the protoscope format:
More information about protoscope can be found here: https://github.com/protocolbuffers/protoscope

Serializing and deserializing Protobuf messages do not require a .proto file or any compilation. The messages are created dynamically in Python.
The Python protobuf library uses expensive reflection to serialize and deserialize messages. This library uses a much simpler approach that is much faster,
in some basic benchmarking that I did it was about 200 times faster than the Python protobuf library.

Usage
-----

Serializing a message
-----

```python
from minimal_protobuf import serialize, WireType

message = {
    1: (WireType.FIXED32, 0.003),
    2: (WireType.LENGTH_DELIMITED,
        {
            13: (WireType.VARINT, 3),
            14: (WireType.VARINT, 1)
        })
}

serialized_bytes = serialize(message)
print(serialized_bytes)
```

Output:
```
b'\r\xa6\x9bD;\x12\x04h\x03p\x01'
```

A table of what Python datatypes belong to which wire type can be found here:

| ID   | Name               | Used For                                | 
|------|--------------------|-----------------------------------------|
| 0    | VARINT             | int, bool, enums (which are just int)   |
| 1    | FIXED64            | float (with larger precision)           |
| 2    | LENGTH_DELIMITED   | str, bytes, dict                        |
| 3    | START_GROUP        | Deprecated, not implemented             |
| 4    | END_GROUP          | Deprecated, not implemented             |
| 5    | FIXED32            | float                                   |

Alternatively you can let thie serializer infer the wire type from the Python datatype by seting determine_wire_types to True:

```python
from minimal_protobuf import serialize, WireType

message = {
    1: 0.003,
    2: {
        13: 3,
        14: 1
    }
}

serialized_bytes = serialize(message)
print(serialized_bytes)
```

Output:
```
b'\r\xa6\x9bD;\x12\x04h\x03p\x01'
```

In this case, the output is the same as in the previous example. 

However, if you use large floats that require the FIXED64 wire type, the serializer won't be able to infer the wire type and serialize it as FIXED32 instead. If you want to avoid this, you can set determine_wire_types to False and specify the wire type manually.


Deserializing a message
-----

```python
from minimal_protobuf import deserialize

serialized_bytes = b'\r\xa6\x9bD;\x12\x04h\x03p\x01'
deserialized_message = deserialize(serialized_bytes)
print(deserialized_message)
```

Output:
```
{1: 0.003, 2: {13: 3, 14: 1}}
```

Future work
-----

- [ ] Implement support for repeated fields
- [ ] Implement support for packed repeated fields
- [ ] Implement support for extensions
- [ ] Implement support for maps
