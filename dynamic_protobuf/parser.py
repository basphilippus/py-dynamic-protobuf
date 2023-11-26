import re

from dynamic_protobuf import WireType
from parser_classes import ProtobufType, ProtobufEnumDefinition, ProtobufDefinition, ProtobufMessageDefinition, \
    ProtobufField, ProtobufMessageType, ProtobufEnumType

syntax_regex = re.compile(r'syntax = "([^"]+)"')
message_regex = re.compile(r'message ([a-zA-Z]+) {([^}]+)}')
field_regex = re.compile(r'(optional|required) ([a-zA-Z0-9]+) ([a-zA-Z_0-9]+) = ([0-9]+);')
enum_regex = re.compile(r'([a-zA-Z0-9_]+) ?= ?([0-9]+);')


def find_syntax_scope(definition_lines: list[str], line_index) -> tuple[list[str], int]:
    return [definition_lines[0]], line_index + 1


def parse_syntax(proto_definition: ProtobufDefinition, scope: list[str]):
    statement = scope[0]
    statements = [statement for statement in statement.split(' ') if statement]
    value = statements[2].replace('"', '').replace(';', '')
    proto_definition.syntax = value


def find_message_scope(definition_lines: list[str], line_index) -> tuple[list[str], int]:
    scope = []
    level = 0
    for line in [line.strip() for line in definition_lines]:
        if not line:
            continue
        if line.startswith('message') and line.endswith('{'):
            level += 1
        if line.startswith('}'):
            level -= 1
            if level == 0:
                scope.append(line)
                break
        scope.append(line)
    return scope, line_index + len(scope) + 1


def parse_message(proto_definition: ProtobufDefinition, scope: list[str]):
    message_name = scope[0].split(' ')[1]
    field_lines = []

    new_line_index = 0
    message_body = scope[1:]
    for line_index, line in enumerate(message_body):
        if line_index < new_line_index:
            continue

        if line.startswith('message'):
            sub_scope, new_line_index = find_message_scope(message_body[line_index:], line_index)
            parse_message(proto_definition, sub_scope)
        else:
            field_lines.append(line)

    proto_message = ProtobufMessageDefinition(proto_definition, message_name)
    proto_definition.messages[message_name] = proto_message

    found_fields = field_regex.findall('\n'.join(field_lines))
    for found_field in found_fields:
        field = ProtobufField(proto_message, *found_field)
        proto_message.add_field(field)


def find_enum_scope(definition_lines: list[str], line_index) -> tuple[list[str], int]:
    scope = []
    level = 0
    for line in [line.strip() for line in definition_lines]:
        if not line:
            continue
        if line.startswith('enum') and line.endswith('{'):
            level += 1
        if line.startswith('}'):
            level -= 1
            if level == 0:
                scope.append(line)
                break
        scope.append(line)
    return scope, line_index + len(scope) + 1


def parse_enum(proto_definition: ProtobufDefinition, scope: list[str]):
    enum_name = scope[0].split(' ')[1]

    proto_enum = ProtobufEnumDefinition(proto_definition, enum_name)
    proto_definition.enums[enum_name] = proto_enum

    found_values = enum_regex.findall('\n'.join(scope))
    for found_value in found_values:
        proto_enum.values_by_name[found_value[0]] = int(found_value[1])
        proto_enum.values_by_number[int(found_value[1])] = found_value[0]


keywords = {
    'syntax': (find_syntax_scope, parse_syntax),
    'message': (find_message_scope, parse_message),
    'enum': (find_enum_scope, parse_enum),
}


def _parse_definition(definition: str) -> ProtobufDefinition:
    proto_definition = ProtobufDefinition()

    new_line_index = 0

    definition_lines = definition.split('\n')
    for line_index, line in enumerate(definition_lines):
        if not line:
            continue

        if line_index < new_line_index:
            continue

        statements = [statement for statement in line.split(' ') if statement]
        if statements:
            keyword = statements[0]
            scope_function, parse_function = keywords.get(keyword)
            scope, new_line_index = scope_function(definition_lines[line_index:], line_index)
            parse_function(proto_definition, scope)

    return proto_definition


def parse(definition: str) -> ProtobufDefinition:
    proto_definition = _parse_definition(definition)

    to_be_removed_unknown_references = []
    for unknown_field, unknown_message_name in proto_definition.unknown_references.items():
        message_type = proto_definition.messages.get(unknown_message_name)
        if message_type:
            unknown_field.type = message_type
            to_be_removed_unknown_references.append(unknown_field)
            continue

        enum_type = proto_definition.enums.get(unknown_message_name)
        if enum_type:
            unknown_field.type = enum_type
            to_be_removed_unknown_references.append(unknown_field)
            continue

    for unknown_field in to_be_removed_unknown_references:
        del proto_definition.unknown_references[unknown_field]

    if proto_definition.unknown_references:
        raise Exception(f'Unknown message references: {proto_definition.unknown_references}')

    for message_name, message_definition in proto_definition.messages.items():
        proto_definition.message_classes[message_name] = ProtobufMessageType(message_name,
                                                                             message_definition=message_definition)

    for enum_name, enum_definition in proto_definition.enums.items():
        proto_definition.enum_classes[enum_name] = ProtobufEnumType(enum_name, enum_definition=enum_definition)

    return proto_definition
