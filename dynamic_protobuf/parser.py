import re
from enum import Enum

from dynamic_protobuf import WireType, encode, decode

syntax_regex = re.compile(r'syntax = "([^"]+)"')
message_regex = re.compile(r'message ([a-zA-Z]+) {([^}]+)}')
field_regex = re.compile(r'(optional|required) ([a-zA-Z0-9]+) ([a-zA-Z_0-9]+) = ([0-9]+);')


class ProtobufLabel(Enum):
    OPTIONAL = 'optional'
    REQUIRED = 'required'
    REPEATED = 'repeated'
    MAP = 'map'


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


class ProtobufMessageType(type):

    def __new__(mcs, name, message_definition=None, **kwargs):
        protobuf_message_type = super().__new__(mcs, name, (ProtobufMessage,), {})
        protobuf_message_type.definition = message_definition
        return protobuf_message_type

    def __init__(cls, *args, **_):
        super().__init__(*args)


class ProtobufMessage:
    definition = None

    def __init__(self, **kwargs):
        self.__dict__.update(self.definition.render(**kwargs))

    def _get_default_value(self, field):
        if field.type in default_value_table:
            return default_value_table[field.type]
        return self.definition.message_classes[field.type.name]()

    def _get_proto_dict(self):
        proto_dict = {}
        for field_number, field in self.definition.fields_by_number.items():
            field_value = getattr(self, field.name, None)
            if field_value and isinstance(field_value, ProtobufMessage):
                field_wire_type = WireType.LENGTH_DELIMITED
            else:
                field_wire_type = protobuf_type_wire_type_table[field.type]

            if not field_value:
                if field.label == ProtobufLabel.REQUIRED:
                    default_value = self._get_default_value(field)
                    proto_dict[field_number] = (field_wire_type, default_value)
                    continue

            if isinstance(field_value, ProtobufMessage):
                field_value = field_value._get_proto_dict()
            proto_dict[field_number] = (field_wire_type, field_value)
        return proto_dict

    def encode(self):
        proto_dict = self._get_proto_dict()
        return encode(proto_dict, determine_wire_types=True)

    @classmethod
    def _proto_dict_numbers_to_names(cls, proto_dict):
        numbers_to_names = {field.number: field.name for field in cls.definition.fields_by_number.values()}
        proto_dict_with_names = {}
        for field_number, field_value in proto_dict.items():
            field_name = numbers_to_names[field_number]
            if isinstance(field_value, dict):
                field_type = cls.definition.fields_by_name[field_name].type.name
                field_value = cls.definition.definition.message_classes[field_type]._proto_dict_numbers_to_names(
                    field_value)
            proto_dict_with_names[field_name] = field_value
        return proto_dict_with_names

    @classmethod
    def decode(cls, byte_blob: bytes):
        proto_dict = decode(byte_blob)
        proto_dict_with_names = cls._proto_dict_numbers_to_names(proto_dict)
        return cls(**proto_dict_with_names)

    def __repr__(self):
        representation = {}
        for field_number, field in self.definition.fields_by_number.items():
            field_value = getattr(self, field.name, None)
            if not field_value:
                continue
            if isinstance(field_value, ProtobufMessage):
                field_value = repr(field_value)
            representation[field.name] = field_value
        return f'{self.__class__.__name__}({representation})'


class ProtobufField:

    def __init__(self,
                 message,
                 label: str,
                 _type: str,
                 name: str,
                 number: int | str):
        self.message = message

        if isinstance(label, str):
            label = ProtobufLabel(label)
        self.label: ProtobufLabel = label

        if isinstance(_type, str):
            try:
                _type = ProtobufType(_type)
            except ValueError:
                sub_message = message.definition.unknown_message_references.get(_type)
                if not sub_message:
                    message.definition.unknown_message_references[self] = _type
                _type = sub_message
        self.type: ProtobufType | ProtobufMessageDefinition = _type

        self.name: str = name
        if isinstance(number, str):
            number = int(number)
        self.number: int = number

    def __repr__(self):
        type_value = self.type.value if isinstance(self.type, ProtobufType) else self.type.name
        return f'{self.label.value} {type_value} {self.name} = {self.number};'


class ProtobufMessageDefinition:

    def __init__(self,
                 definition,
                 name: str):

        self.definition = definition
        self.name = name
        self.fields_by_name = {}
        self.fields_by_number = {}

    def add_field(self, field: ProtobufField):
        self.fields_by_name[field.name] = field
        self.fields_by_number[field.number] = field

    def render(self, **kwargs):
        message_instance = {}
        for field_name, field in self.fields_by_name.items():
            if field_name not in kwargs:
                continue
            field_value = kwargs[field_name]
            if isinstance(field_value, dict):
                field_value_dict = field.type.render(**field_value)
                field_value = self.definition.message_classes[field.type.name](**field_value_dict)
            message_instance[field_name] = field_value
        return message_instance

    def __repr__(self):
        opening_curly_brace = '{'
        return (f'message {self.name} {opening_curly_brace}\n' +
                '\n'.join(['\t' + repr(field) for field in self.fields_by_number.values()])) + '\n}'


class ProtobufDefinition:

    def __init__(self,
                 syntax: str):
        self.syntax = syntax
        self.messages = {}
        self.message_classes = {}
        self.unknown_message_references = {}

    def __repr__(self):
        return f'syntax = "{self.syntax}";\n\n' + '\n\n'.join([repr(message) for message in self.messages.values()])

    def __getattr__(self, item):
        if item == 'get':
            return self.__getitem__
        return self.message_classes[item]

    def __getitem__(self, item):
        return self.message_classes[item]


def parse(definition: str) -> ProtobufDefinition:
    syntax = syntax_regex.findall(definition)[0]
    proto_definition = ProtobufDefinition(syntax)

    messages = message_regex.findall(definition)
    for message in messages:
        message_name, message_body = message

        proto_message_definition = ProtobufMessageDefinition(proto_definition, message_name)
        proto_definition.messages[message_name] = proto_message_definition

        found_fields = field_regex.findall(message_body)
        for found_field in found_fields:
            field = ProtobufField(proto_message_definition, *found_field)
            proto_message_definition.add_field(field)

    to_be_removed_unknown_message_references = []
    for unknown_message_field, unknown_message_name in proto_definition.unknown_message_references.items():
        unknown_message_field.type = proto_definition.messages[unknown_message_name]
        to_be_removed_unknown_message_references.append(unknown_message_field)

    for unknown_message_field in to_be_removed_unknown_message_references:
        del proto_definition.unknown_message_references[unknown_message_field]

    if proto_definition.unknown_message_references:
        raise Exception(f'Unknown message references: {proto_definition.unknown_message_references}')

    for message_name, message_definition in proto_definition.messages.items():
        proto_definition.message_classes[message_name] = ProtobufMessageType(message_name,
                                                                             message_definition=message_definition)

    return proto_definition
