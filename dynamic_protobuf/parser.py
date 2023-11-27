import re

from parser_classes import ProtobufEnumDefinition, ProtobufDefinition, ProtobufMessageDefinition, \
    ProtobufField, ProtobufMessageType, ProtobufEnumType

syntax_regex = re.compile(r'syntax = "([^"]+)"')
message_regex = re.compile(r'message ([a-zA-Z]+) {([^}]+)}')
field_regex = re.compile(r'(optional|required|repeated) ([a-zA-Z0-9]+) ([a-zA-Z_0-9]+) = ([0-9]+) ?(\[[a-zA-Z]* ?= ?(?:[a-zA-Z0-9-_.,"\']*)\])?;(?:(?: |\n)\/\/ ?([a-zA-Z-0-9 _+-]*))?')
enum_regex = re.compile(r'([a-zA-Z0-9_]+) ?= ?([0-9]+);')
line_regex = re.compile(r'([;{}])')
equals_regex = re.compile(r'([a-zA-Z0-9\"\']?=[a-zA-Z0-9\"\']?)')


def find_syntax_scope(definition_lines: list[str], line_index) -> tuple[list[str], int]:
    return [definition_lines[0]], line_index + 1


def parse_syntax(proto_definition: ProtobufDefinition, scope: list[str]):
    statement = scope[0]
    statements = [statement for statement in statement.split(' ') if statement]
    value = statements[2].replace('"', '').replace(';', '')
    proto_definition.syntax = value


def parse_options(proto_definition: ProtobufDefinition,
                  field: ProtobufField,
                  _type: str,
                  options_string: str) -> dict[str, bool | int | float]:
    options = {}

    if options_string.startswith('[') and options_string.endswith(']'):
        options_string = options_string[1:-1]

    for option in options_string.split(','):
        key, value = option.split('=')
        key = key.strip()
        value = value.strip()
        if key == 'default':
            if _type == 'float':
                value = float(value)
            elif _type == 'int32' or _type == 'int64':
                value = int(value)
            elif _type == 'bool':
                value = value == 'true'
            elif _type == 'string':
                value = value.replace('"', '')
            elif _type == 'bytes':
                value = value.replace('"', '').encode('utf-8')
            else:
                message = proto_definition.messages.get(_type)
                if message:
                    options[key] = message
                    continue

                enum = proto_definition.enums.get(_type)
                if enum:
                    options[key] = enum
                    continue

                proto_definition.unknown_options[field] = (key, _type, value)
                continue
        elif key == 'packed':
            value = value == 'true'
        else:
            if '.' in value:
                value = float(value)
            elif value == 'true' or value == 'false':
                value = value == 'true'
            else:
                value = int(value)

        options[key] = value
    return options


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
    return scope, line_index + len(scope)


def parse_reserved(proto_message: ProtobufMessageDefinition, line: str):
    line = line.replace('reserved', '')[:-1]
    reserved_field_number_entries = [entry.strip() for entry in line.split(',')]
    for entry in reserved_field_number_entries:
        if entry.isdigit():
            proto_message.reserved_field_numbers.add(int(entry))
        elif 'to' in entry:
            start, end = entry.split('to')
            start = start.strip()
            end = end.strip()
            for number in range(int(start), int(end) + 1):
                proto_message.reserved_field_numbers.add(number)
        else:
            raise Exception(f'Unknown reserved entry: {entry}')


def parse_message(proto_definition: ProtobufDefinition, scope: list[str]):
    message_name = scope[0].split(' ')[1]
    if message_name.endswith('{'):
        message_name = message_name[:-1]

    proto_message = ProtobufMessageDefinition(proto_definition, message_name)
    proto_definition.messages[message_name] = proto_message

    field_lines = []

    new_line_index = 0
    message_body = scope[1:]
    multiline_comment = ""
    for line_index, line in enumerate(message_body):
        if line_index < new_line_index:
            continue

        uncompact_equals = equals_regex.findall(line)
        if uncompact_equals:
            for uncompact_equal in uncompact_equals:
                if len(uncompact_equal) == 3:
                    # No space on either side of the equals sign
                    line = line.replace(uncompact_equal, uncompact_equal.replace('=', ' = '))
                    message_body[line_index] = line
                elif len(uncompact_equal) == 2:
                    # Space on one side of the equals sign
                    if uncompact_equal.startswith('='):
                        line = line.replace(uncompact_equal, uncompact_equal.replace('=', ' ='))
                    else:
                        line = line.replace(uncompact_equal, uncompact_equal.replace('=', '= '))
                    message_body[line_index] = line

        if line.startswith('message'):
            sub_scope, new_line_index = find_message_scope(message_body[line_index:], line_index)
            parse_message(proto_definition, sub_scope)
        elif line.startswith('reserved'):
            parse_reserved(proto_message, line)
        elif line.startswith('/*'):
            multiline_comment += line[2:]
            if line.endswith('*/'):
                multiline_comment = multiline_comment[:-2]
                proto_message.comments.append(multiline_comment.strip())
                multiline_comment = ""

        elif line.startswith('*'):
            multiline_comment += line[1:]
            if line.endswith('*/'):
                multiline_comment = multiline_comment[:-2]
                proto_message.comments.append(multiline_comment.strip())
                multiline_comment = ""
        else:
            field_lines.append(line)

    found_fields = field_regex.findall('\n'.join(field_lines))
    for found_field in found_fields:
        label, _type, name, number, option, comment = found_field
        if not comment:
            comment = None

        field = ProtobufField(proto_message, label, _type, name, number, comment)
        proto_message.add_field(field)

        options = {}
        if option:
            options = parse_options(proto_definition, field, _type, option)
        field.options = options


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


def find_single_line_comment_scope(definition_lines: list[str], line_index) -> tuple[list[str], int]:
    return [definition_lines[0]], line_index + 1


def parse_single_line_comment(proto_definition: ProtobufDefinition, scope: list[str]):
    comment = scope[0][3:]
    proto_definition.comments.append(comment)


keywords = {
    'syntax': (find_syntax_scope, parse_syntax),
    'message': (find_message_scope, parse_message),
    'enum': (find_enum_scope, parse_enum),
    '//': (find_single_line_comment_scope, parse_single_line_comment),
}


def _parse_definition(definition: str) -> ProtobufDefinition:
    proto_definition = ProtobufDefinition()

    new_line_index = 0

    lines = []
    definition_lines = definition.split('\n')
    for line_index, line in enumerate(definition_lines):
        capture_groups = line_regex.split(line)
        if len(capture_groups) % 2 == 1:
            capture_groups.append('')
        # Combine in groups of 2
        sub_lines = [capture_groups[i] + capture_groups[i + 1] for i in range(0, len(capture_groups), 2)]
        lines.extend(sub_lines)

    lines = [line for line in lines if line]

    for line_index, line in enumerate(lines):
        if not line:
            continue

        if line_index < new_line_index:
            continue

        uncompact_equals = equals_regex.findall(line)
        if uncompact_equals:
            for uncompact_equal in uncompact_equals:
                if len(uncompact_equal) == 3:
                    # No space on either side of the equals sign
                    line = line.replace(uncompact_equal, uncompact_equal.replace('=', ' = '))
                    lines[line_index] = line
                elif len(uncompact_equal) == 2:
                    # Space on one side of the equals sign
                    if uncompact_equal.startswith('='):
                        line = line.replace(uncompact_equal, uncompact_equal.replace('=', ' ='))
                    else:
                        line = line.replace(uncompact_equal, uncompact_equal.replace('=', '= '))
                    lines[line_index] = line

        statements = [statement for statement in line.split(' ') if statement]
        if statements:
            keyword = statements[0]
            scope_function, parse_function = keywords.get(keyword)
            scope, new_line_index = scope_function(lines[line_index:], line_index)
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

    to_be_removed_unknown_options = []
    for unknown_field, (unknown_option_key, unknown_option_type, unknown_option_value) in proto_definition.unknown_options.items():
        message_type = proto_definition.messages.get(unknown_option_type)
        if message_type:
            raise Exception('Not sure what to do here...')

        enum_type = proto_definition.enums.get(unknown_option_type)
        if enum_type:
            value = enum_type.values_by_name.get(unknown_option_value)
            unknown_field.options[unknown_option_key] = value
            to_be_removed_unknown_options.append(unknown_field)
            continue

    for unknown_field in to_be_removed_unknown_options:
        del proto_definition.unknown_options[unknown_field]

    if proto_definition.unknown_options:
        raise Exception(f'Unknown options: {proto_definition.unknown_options}')

    for message_name, message_definition in proto_definition.messages.items():
        proto_definition.message_classes[message_name] = ProtobufMessageType(message_name,
                                                                             message_definition=message_definition)

    for enum_name, enum_definition in proto_definition.enums.items():
        proto_definition.enum_classes[enum_name] = ProtobufEnumType(enum_name, enum_definition=enum_definition)

    return proto_definition
