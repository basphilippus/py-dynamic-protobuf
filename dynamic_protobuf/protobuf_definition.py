from any import AnyMessage
from protobuf_definition_types import ProtobufLabel, ProtobufType, default_value_table


class ProtobufEnumDefinition:

    def __init__(self,
                 definition,
                 name: str):
        self.definition = definition
        self.name = name
        self.values_by_name: dict[str, int] = {}
        self.values_by_number: dict[int, str] = {}


class ProtobufField:

    def __init__(self,
                 message,
                 label: str,
                 _type: str,
                 name: str,
                 number: int | str,
                 comment: str | None = None):
        self.message = message

        if label and isinstance(label, str):
            label = ProtobufLabel(label)
        if not label:
            # Proto3
            label = ProtobufLabel.REQUIRED
        self.label: ProtobufLabel = label

        if isinstance(_type, str):
            if _type.startswith('map'):
                key_type, value_type = _type[4:-1].split(',')
                key_type = key_type.strip()
                value_type = value_type.strip()

                try:
                    key_type = ProtobufType(key_type)
                except ValueError:
                    sub_message = message.definition.unknown_references.get(key_type)
                    if not sub_message:
                        message.definition.unknown_references[self] = key_type
                    key_type = sub_message

                try:
                    value_type = ProtobufType(value_type)
                except ValueError:
                    sub_message = message.definition.unknown_references.get(value_type)
                    if not sub_message:
                        message.definition.unknown_references[self] = value_type
                    value_type = sub_message

                _type = (key_type, value_type)
            else:
                try:
                    _type = ProtobufType(_type)
                except ValueError:
                    sub_message = message.definition.unknown_references.get(_type)
                    if not sub_message:
                        message.definition.unknown_references[self] = _type
                    _type = sub_message
        self.type: (ProtobufType | ProtobufMessageDefinition |
                    tuple[ProtobufType | ProtobufMessageDefinition, ProtobufType | ProtobufMessageDefinition]) = _type

        self.name: str = name
        if isinstance(number, str):
            number = int(number)
        self.number: int = number

        self.options: dict[str, bool | int | float] = {}

        self.comment = comment

    def __repr__(self):
        if self.type:
            if isinstance(self.type, tuple):
                type_value = f'map<{self.type[0]}, {self.type[1]}>'
            else:
                type_value = self.type.value if isinstance(self.type, ProtobufType) else self.type.name
                type_value = f'{type_value} '
        else:
            type_value = ''
        options_string = ''
        if self.options:
            options_string = ' [' + ', '.join([f'{key} = {value}' for key, value in self.options.items()]) + ']'
        return f'{self.label.value} {type_value}{self.name} = {self.number}{options_string};'


class ProtobufMessageDefinition:

    def __init__(self,
                 definition,
                 name: str):

        self.definition = definition
        self.name = name
        self.fields_by_name = {}
        self.fields_by_number = {}

        self.oneofs: dict[str, list[ProtobufField]] = {}
        self.oneof_fields: dict[ProtobufField, str] = {}

        self.reserved_field_numbers: set[int] = set()

        self.comments: list[str] = []

    def add_field(self, field: ProtobufField):
        self.fields_by_name[field.name] = field
        self.fields_by_number[field.number] = field

    def render(self, **kwargs):
        message_instance = {}
        for field_name, field in self.fields_by_name.items():
            if field_name not in kwargs:
                continue
            field_value = kwargs[field_name]

            if field.type == ProtobufType.BYTES and isinstance(field_value, str):
                field_value = field_value.encode()

            if field.options.get('default') and field_value == self.get_default_value(field):
                continue

            if isinstance(field_value, dict):
                if isinstance(field.type, tuple):
                    # Map
                    from protobuf_instance import ProtobufMap
                    field_type = ProtobufMap
                    field_type.definition = field.type
                    field_value = field_type(field_value)
                else:
                    field_value_dict = field.type.render(**field_value)
                    field_value = self.definition.message_classes[field.type.name](**field_value_dict)

            if isinstance(field_value, AnyMessage):
                type_url_value = self.name
                if self.definition.package:
                    type_url_value = f'{self.definition.package}.{type_url_value}'
                field_value.type_url = f'type.googleapis.com/{type_url_value}'

            if field.type == ProtobufType.BYTES and isinstance(field_value, str):
                field_value = field_value.encode()

            oneof = self.definition[self.name].definition.oneof_fields.get(field_name)
            if oneof:
                oneof_fields = self.definition[self.name].definition.oneofs[oneof]
                for oneof_field in oneof_fields:
                    if message_instance.get(oneof_field.name):
                        del message_instance[oneof_field.name]

            message_instance[field_name] = field_value
        return message_instance

    def get_fully_qualified_name(self):
        return f'{self.definition.package}.{self.name}'

    def get_default_value(self, field: ProtobufField):
        if field.options.get('default'):
            return field.options['default']

        if field.type in default_value_table:
            return default_value_table[field.type]
        return self.definition.message_classes[field.type.name]()

    def __repr__(self):
        opening_curly_brace = '{'
        return (f'message {self.name} {opening_curly_brace}\n' +
                '\n'.join(['\t' + repr(field) for field in self.fields_by_number.values()])) + '\n}'


class ProtobufMethodDefinition:

    def __init__(self,
                 definition,
                 name: str,
                 input_type: str,
                 output_type: str):
        self.definition = definition
        self.name = name
        self.input_type = input_type
        self.output_type = output_type


class ProtobufServiceDefinition:

    def __init__(self,
                 definition,
                 name: str):
        self.definition = definition
        self.name = name
        self.methods: dict[str, ProtobufMethodDefinition] = {}


class ProtobufDefinition:

    def __init__(self):
        self.syntax: str = None
        self.importer = None
        self.import_level = 0

        self.package: str = None

        self.messages: dict[str, ProtobufMessageDefinition] = {}
        from protobuf_instance import ProtobufMessageType
        self.message_classes: dict[str, ProtobufMessageType] = {}

        self.enums: dict[str, ProtobufEnumDefinition] = {}
        from protobuf_instance import ProtobufEnumType
        self.enum_classes: dict[str, ProtobufEnumType] = {}

        self.comments: list[str] = []

        self.services: dict[str, ProtobufServiceDefinition] = {}

        self.unknown_references = {}
        self.unknown_options = {}

    def __repr__(self):
        return f'syntax = "{self.syntax}";\n\n' + '\n\n'.join([repr(message) for message in self.messages.values()])

    def __getattr__(self, item):
        if item == 'get':
            return self.__getitem__

        message = self.messages.get(item)
        if message:
            return self.message_classes[item]

        for message_name in self.messages:
            if '.' in message_name:
                parts = message_name.split('.')
                for part in parts:
                    if part == item:
                        return self

        enum = self.enums.get(item)
        if enum:
            return self.enum_classes[item]

        return ValueError(f'No message or enum with name {item}')

    def __getitem__(self, item):
        message = self.messages.get(item)
        if message:
            return self.message_classes[item]
        enum = self.enums.get(item)
        if enum:
            return self.enum_classes[item]

        return ValueError(f'No message or enum with name {item}')
