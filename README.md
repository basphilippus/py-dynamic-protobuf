Python dynamic Protobuf
-----

This repository contains a minimal implementation of the encoding and decoding of the Protobuf specification in Python.

The reason for creating this repository is that I have a need for generating on-the-fly dynamic protobuf messages in Python. I have not found any existing libraries that can do this, so I decided to create my own.

With this repository you can encode and decode Protobuf messages using a structure that resembles Protoscope format.
More information about Protoscope can be found here: https://github.com/protocolbuffers/protoscope

Protobuf encoding consists of two parts:
1. Compiling a .proto file to a (Python) class that can be used to interface between user code and Protobuf messages, this parts does not encode or decode messages, but instead produces a structure that is similar to the Protoscope format.
2. Takes the Protoscope format and encodes to- or decodes from the wire format (bytes).

This repository only focuses on the second part, it does not implement .proto file compilation or provide Python classes to interface with .proto definitions.

Encoding and decoding Protobuf messages do not require a .proto file or any compilation with this library.
The standard Python Protobuf library uses expensive reflection to encode and decode messages. 

This library uses a simpler approach that is much faster, in some basic benchmarking that I did it was about 200 times faster than the standard Python Protobuf library.

-----

Usage
-----

Encoding a message
-----

To encode the equivalent of the following Protobuf message and definition:

```json
{
    "my_float": 0.003,
    "my_other_message": {
        "my_int": 3,
        "my_other_int": 1
    }
}
```

```protobuf
syntax = "proto2";

message MyMessage {
    optional float my_float = 1;
    optional MyOtherMessage my_other_message = 2;
}

message MyOtherMessage {
    optional int32 my_int = 13;
    optional int32 my_other_int = 14;
}
```

You can use the following Python code:

```python
from dynamic_protobuf import encode, WireType

message = {
    1: (WireType.FIXED32, 0.003),
    2: (WireType.LENGTH_DELIMITED,
        {
            13: (WireType.VARINT, 3),
            14: (WireType.VARINT, 1)
        })
}

encoded_bytes = encode(message)
print(encoded_bytes)
```

Output:
```python
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

Alternatively you can let the encoder infer the wire type from the Python datatype by setting determine_wire_types to True:

```python
from dynamic_protobuf import encode

message = {
    1: 0.003,
    2: {
        13: 3,
        14: 1
    }
}

encoded_bytes = encode(message)
print(encoded_bytes)
```

Output:
```python
b'\r\xa6\x9bD;\x12\x04h\x03p\x01'
```

In this case, the output is the same as in the previous example. 

However, if you use large floats that require the FIXED64 wire type, the encoder won't be able to infer the wire type and encode it as FIXED32 instead. If you want to avoid this, you can set determine_wire_types to False and specify the wire type manually.


Decoding a message
-----

You can use the following Python code to decode the encoded message from the previous example:

```python
from dynamic_protobuf import decode

encoded_bytes = b'\r\xa6\x9bD;\x12\x04h\x03p\x01'
decoded_message = decode(encoded_bytes)
print(decoded_message)
```

Output (raw):
```python
{1: 0.003, 2: {13: 3, 14: 1}}
```

Output (formatted):
```python
{
  1: 0.003, 
  2: {
      13: 3, 
      14: 1
  }
}
```

As you can see, for the output the wire types are not returned. The wire types are part of the encoding and no longer needed after the value has been decoded.

-----

Future work
-----

- [ ] Implement support for repeated fields
- [ ] Implement support for packed repeated fields
- [ ] Implement support for maps
- [ ] Parsing .proto definitions and generating Python classes