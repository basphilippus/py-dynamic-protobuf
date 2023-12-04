from dynamic_protobuf import WireType, encode, decode
from protobuf_definition_types import protobuf_type_wire_type_table, ProtobufLabel


class ProtobufEnumType(type):

    def __new__(mcs, name, enum_definition=None, **kwargs):
        protobuf_enum_type = super().__new__(mcs, name, (ProtobufEnum,), {})
        protobuf_enum_type.definition = enum_definition
        return protobuf_enum_type()

    def __init__(cls, *args, **_):
        super().__init__(*args)


class ProtobufMessageType(type):

    def __new__(mcs, name, message_definition=None, **kwargs):
        protobuf_message_type = ProtobufMessage
        fully_qualified_name = message_definition.get_fully_qualified_name()
        if fully_qualified_name == 'google.protobuf.Any':
            from any import AnyMessage
            protobuf_message_type = AnyMessage

        protobuf_message_type = super().__new__(mcs, name, (protobuf_message_type,), {})
        protobuf_message_type.definition = message_definition
        return protobuf_message_type

    def __init__(cls, *args, **_):
        super().__init__(*args)

    def __getattr__(self, item):
        if self.definition.messages.get(item):
            return self.definition.messages[item]

        if self.definition.enums.get(item):
            return self.definition.enums[item]


class ProtobufMap:
    definition = None

    def __init__(self, dictionary):
        self.dictionary = {}
        for key, value in dictionary.items():
            if isinstance(value, dict):
                value_type = self.definition[1].definition.message_classes.get(self.definition[1].name)
                value = value_type(**value)
            self.dictionary[key] = value

    def _get_proto_dict(self):
        proto_dict = {}
        for key, value in self.dictionary.items():
            if isinstance(value, ProtobufMessage):
                value = value._get_proto_dict()
            proto_dict[key] = value
        return proto_dict

    def __repr__(self):
        return repr(self.dictionary)

    def __eq__(self, other):
        return self.dictionary == other.dictionary

    @classmethod
    def _proto_dict_numbers_to_names(cls, proto_dict):
        key_definition, value_definition = cls.definition

        proto_dict_with_names = {}
        for key, value in proto_dict.items():
            from protobuf_definition import ProtobufMessageDefinition
            if isinstance(value_definition, ProtobufMessageDefinition):
                value = value_definition.definition.message_classes[value_definition.name]._proto_dict_numbers_to_names(value)
            proto_dict_with_names[key] = value
        return proto_dict_with_names


class ProtobufEnum:
    definition = None

    def __init__(self):
        pass

    def __repr__(self):
        return f'{self.__class__.__name__}({self.definition.values_by_number[self.value]})'

    def __eq__(self, other):
        if self.definition != other.definition:
            return False
        return self.value == other.value

    def __getattr__(self, item):
        if item == 'get':
            return self.__getitem__

        return self.definition.values_by_name[item]

    def __getitem__(self, item):
        return self.definition.values_by_name[item]


class ProtobufMessage:
    definition = None

    def __init__(self, **kwargs):
        self.__dict__.update(self.definition.render(**kwargs))

    def _get_proto_dict(self):
        proto_dict = {}
        message_definition = self.definition.definition.messages.get(self.definition.name)
        for field_number, field in self.definition.fields_by_number.items():
            field_value = getattr(self, field.name, None)
            if field_value and isinstance(field_value, ProtobufMessage):
                field_wire_type = WireType.LENGTH_DELIMITED
            else:
                from protobuf_definition import ProtobufEnumDefinition
                if isinstance(field.type, ProtobufEnumDefinition):
                    field_wire_type = WireType.VARINT
                else:
                    if isinstance(field.type, tuple):
                        field_wire_type = WireType.LENGTH_DELIMITED
                    else:
                        field_wire_type = protobuf_type_wire_type_table[field.type]

            original_wire_type = None
            if field.options.get('packed'):
                original_wire_type = field_wire_type
                field_wire_type = WireType.LENGTH_DELIMITED

            if not field_value:
                if field.label == ProtobufLabel.REQUIRED:
                    default_value = message_definition.get_default_value(field)
                    proto_dict[field_number] = (field_wire_type, default_value)

                continue

            if isinstance(field_value, ProtobufMessage) or isinstance(field_value, ProtobufMap):
                field_value = field_value._get_proto_dict()

            if field.options.get('packed'):
                proto_dict[field_number] = (field_wire_type, (original_wire_type, field_value))
            else:
                proto_dict[field_number] = (field_wire_type, field_value)
        return proto_dict

    def encode(self):
        proto_dict = self._get_proto_dict()
        return encode(proto_dict, determine_wire_types=True)

    @classmethod
    def _proto_dict_numbers_to_names(cls, proto_dict):
        numbers_to_names = {field.number: field.name for field in cls.definition.fields_by_number.values()}
        proto_dict_with_names = {}
        fully_qualified_name = cls.definition.get_fully_qualified_name()
        for field_number, field_value in proto_dict.items():
            field_name = numbers_to_names[field_number]
            if isinstance(field_value, dict):
                if isinstance(cls.definition.fields_by_name[field_name].type, tuple):
                    map_type = ProtobufMap
                    map_type.definition = cls.definition.fields_by_name[field_name].type
                    field_value = ProtobufMap._proto_dict_numbers_to_names(field_value)
                else:
                    if fully_qualified_name != 'google.protobuf.Any':
                        # Stop recursion for AnyMessage as these values are processed later
                        field_type = cls.definition.fields_by_name[field_name].type.name
                        field_value = cls.definition.definition.message_classes[field_type]._proto_dict_numbers_to_names(field_value)

            if fully_qualified_name == 'google.protobuf.Any' and field_name == 'value':
                from constants import PACKING_BACKEND
                if PACKING_BACKEND == 'pickle':
                    from any import AnyMessage

                    # Convert hex to bytes
                    for map_entry in field_value[1]:
                        map_entry[2] = bytes.fromhex(map_entry[2])
                    # # re-pack the value
                    field_value = AnyMessage.pack(field_value).value

            proto_dict_with_names[field_name] = field_value
        return proto_dict_with_names

    @classmethod
    def decode(cls, byte_blob: bytes, definition: dict | None = None):
        proto_dict = decode(byte_blob, definition)
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

    def __eq__(self, other):
        if self.definition != other.definition:
            return False

        for field_number, field in self.definition.fields_by_number.items():
            field_value = getattr(self, field.name, None)
            other_field_value = getattr(other, field.name, None)
            if field_value != other_field_value:
                return False

        return True

    def __getattr__(self, item):
        if item == 'get':
            return self.__getitem__

        if self.__dict__.get(item):
            return self.__dict__[item]

        return self.definition.get_default_value(self.definition.fields_by_name[item])