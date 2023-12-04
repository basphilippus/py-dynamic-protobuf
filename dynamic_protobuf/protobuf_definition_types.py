from enum import Enum
from dynamic_protobuf import WireType


class ProtobufLabel(Enum):
    OPTIONAL = 'optional'
    REQUIRED = 'required'
    REPEATED = 'repeated'


class ProtobufType(Enum):
    FLOAT = 'float'
    INT32 = 'int32'
    INT64 = 'int64'
    UINT32 = 'uint32'
    UINT64 = 'uint64'
    SINT32 = 'sint32'
    SINT64 = 'sint64'
    FIXED32 = 'fixed32'
    FIXED64 = 'fixed64'
    SFIXED32 = 'sfixed32'
    SFIXED64 = 'sfixed64'
    BOOL = 'bool'
    STRING = 'string'
    BYTES = 'bytes'


default_value_table = {
    ProtobufType.FLOAT: 0.0,
    ProtobufType.INT32: 0,
    ProtobufType.INT64: 0,
    ProtobufType.UINT32: 0,
    ProtobufType.UINT64: 0,
    ProtobufType.SINT32: 0,
    ProtobufType.SINT64: 0,
    ProtobufType.FIXED32: 0,
    ProtobufType.FIXED64: 0,
    ProtobufType.SFIXED32: 0,
    ProtobufType.SFIXED64: 0,
    ProtobufType.BOOL: False,
    ProtobufType.STRING: '',
    ProtobufType.BYTES: b'',
}

protobuf_type_wire_type_table = {
    ProtobufType.FLOAT: WireType.FIXED32,
    ProtobufType.INT32: WireType.VARINT,
    ProtobufType.INT64: WireType.VARINT,
    ProtobufType.UINT32: WireType.VARINT,
    ProtobufType.UINT64: WireType.VARINT,
    ProtobufType.SINT32: WireType.VARINT,
    ProtobufType.SINT64: WireType.VARINT,
    ProtobufType.FIXED32: WireType.FIXED32,
    ProtobufType.FIXED64: WireType.FIXED64,
    ProtobufType.SFIXED32: WireType.FIXED32,
    ProtobufType.SFIXED64: WireType.FIXED64,
    ProtobufType.BOOL: WireType.VARINT,
    ProtobufType.STRING: WireType.LENGTH_DELIMITED,
    ProtobufType.BYTES: WireType.LENGTH_DELIMITED,
}
