import os
import time

from dynamic_protobuf import parse, DecoderFieldDefinition, WireType
from parser import ProtobufMessageDefinition
from protobuf_definition_types import ProtobufLabel, ProtobufType


def test_parser_basic_case():
    proto_definition = """syntax = "proto2";
message Example {
    optional float example_float = 1;
    optional ExampleSubMessage example_sub_message = 2;
}

message ExampleSubMessage {
    optional int32 example_int_1 = 13;
    required int32 example_int_2 = 14;
}
"""

    start = time.time()
    result = parse(proto_definition)
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.syntax == 'proto2'
    assert result.messages['Example'].fields_by_name['example_float'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_float'].type == ProtobufType.FLOAT
    assert result.messages['Example'].fields_by_name['example_float'].name == 'example_float'
    assert result.messages['Example'].fields_by_name['example_float'].number == 1

    assert result.messages['Example'].fields_by_name['example_sub_message'].label == ProtobufLabel.OPTIONAL
    assert isinstance(result.messages['Example'].fields_by_name['example_sub_message'].type, ProtobufMessageDefinition)
    assert result.messages['Example'].fields_by_name['example_sub_message'].name == 'example_sub_message'
    assert result.messages['Example'].fields_by_name['example_sub_message'].number == 2

    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].label == ProtobufLabel.OPTIONAL
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].type == ProtobufType.INT32
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].name == 'example_int_1'
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].number == 13

    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].label == ProtobufLabel.REQUIRED
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].type == ProtobufType.INT32
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].name == 'example_int_2'
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].number == 14

    assert result.messages['Example'].fields_by_name['example_sub_message'].type == result.messages['ExampleSubMessage']

    proto_message = result.Example(
        example_float=1.0,
        example_sub_message=result.ExampleSubMessage(
            example_int_1=1,
            example_int_2=2
        )
    )
    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message)

    assert proto_message == decoded_message

    print('test_parser_basic_case is valid!')


def test_parser_basic_case_compact():
    proto_definition = """syntax="proto2";message Example{optional float example_float=1;optional ExampleSubMessage example_sub_message=2;}message ExampleSubMessage{optional int32 example_int_1=13;required int32 example_int_2=14;}"""

    start = time.time()
    result = parse(proto_definition)
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.syntax == 'proto2'
    assert result.messages['Example'].fields_by_name['example_float'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_float'].type == ProtobufType.FLOAT
    assert result.messages['Example'].fields_by_name['example_float'].name == 'example_float'
    assert result.messages['Example'].fields_by_name['example_float'].number == 1

    assert result.messages['Example'].fields_by_name['example_sub_message'].label == ProtobufLabel.OPTIONAL
    assert isinstance(result.messages['Example'].fields_by_name['example_sub_message'].type, ProtobufMessageDefinition)
    assert result.messages['Example'].fields_by_name['example_sub_message'].name == 'example_sub_message'
    assert result.messages['Example'].fields_by_name['example_sub_message'].number == 2

    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].label == ProtobufLabel.OPTIONAL
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].type == ProtobufType.INT32
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].name == 'example_int_1'
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].number == 13

    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].label == ProtobufLabel.REQUIRED
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].type == ProtobufType.INT32
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].name == 'example_int_2'
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].number == 14

    assert result.messages['Example'].fields_by_name['example_sub_message'].type == result.messages['ExampleSubMessage']

    proto_message = result.Example(
        example_float=1.0,
        example_sub_message=result.ExampleSubMessage(
            example_int_1=1,
            example_int_2=2
        )
    )
    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message)

    assert proto_message == decoded_message

    print('test_parser_basic_case_compact is valid!')


def test_parser_nested_message():
    proto_definition = """syntax = "proto2";
message Example {
    optional float example_float = 1;
    optional ExampleSubMessage example_sub_message = 2;

    message ExampleSubMessage {
        optional int32 example_int_1 = 13;
        required int32 example_int_2 = 14;
    }
}
"""

    start = time.time()
    result = parse(proto_definition)
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.syntax == 'proto2'
    assert result.messages['Example'].fields_by_name['example_float'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_float'].type == ProtobufType.FLOAT
    assert result.messages['Example'].fields_by_name['example_float'].name == 'example_float'
    assert result.messages['Example'].fields_by_name['example_float'].number == 1

    assert result.messages['Example'].fields_by_name['example_sub_message'].label == ProtobufLabel.OPTIONAL
    assert isinstance(result.messages['Example'].fields_by_name['example_sub_message'].type, ProtobufMessageDefinition)
    assert result.messages['Example'].fields_by_name['example_sub_message'].name == 'example_sub_message'
    assert result.messages['Example'].fields_by_name['example_sub_message'].number == 2

    assert result.messages['Example'].fields_by_name['example_sub_message'].type.fields_by_name['example_int_1'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_sub_message'].type.fields_by_name['example_int_1'].type == ProtobufType.INT32
    assert result.messages['Example'].fields_by_name['example_sub_message'].type.fields_by_name['example_int_1'].name == 'example_int_1'
    assert result.messages['Example'].fields_by_name['example_sub_message'].type.fields_by_name['example_int_1'].number == 13

    assert result.messages['Example'].fields_by_name['example_sub_message'].type.fields_by_name['example_int_2'].label == ProtobufLabel.REQUIRED
    assert result.messages['Example'].fields_by_name['example_sub_message'].type.fields_by_name['example_int_2'].type == ProtobufType.INT32
    assert result.messages['Example'].fields_by_name['example_sub_message'].type.fields_by_name['example_int_2'].name == 'example_int_2'
    assert result.messages['Example'].fields_by_name['example_sub_message'].type.fields_by_name['example_int_2'].number == 14

    assert result.messages['Example'].fields_by_name['example_sub_message'].type == result.messages['ExampleSubMessage']

    proto_message = result.Example(
        example_float=1.0,
        example_sub_message=result.ExampleSubMessage(
            example_int_1=1,
            example_int_2=2
        )
    )

    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message)

    assert proto_message == decoded_message

    print('test_parser_nested_message is valid!')


def test_parser_enum():
    proto_definition = """syntax = "proto2";
message Example {
    optional float example_float = 1;
    optional ExampleEnum enum_value = 2;
}

enum ExampleEnum {
    EXAMPLE_ENUM_1 = 1;
    EXAMPLE_ENUM_2 = 2;
    EXAMPLE_ENUM_3 = 3;
}
"""

    start = time.time()
    result = parse(proto_definition)
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.syntax == 'proto2'
    assert result.messages['Example'].fields_by_name['example_float'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_float'].type == ProtobufType.FLOAT
    assert result.messages['Example'].fields_by_name['example_float'].name == 'example_float'
    assert result.messages['Example'].fields_by_name['example_float'].number == 1

    assert result.messages['Example'].fields_by_name['enum_value'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['enum_value'].type == result.enums['ExampleEnum']
    assert result.messages['Example'].fields_by_name['enum_value'].name == 'enum_value'
    assert result.messages['Example'].fields_by_name['enum_value'].number == 2

    assert result.enums['ExampleEnum'].values_by_name['EXAMPLE_ENUM_1'] == 1
    assert result.enums['ExampleEnum'].values_by_name['EXAMPLE_ENUM_2'] == 2
    assert result.enums['ExampleEnum'].values_by_name['EXAMPLE_ENUM_3'] == 3

    proto_message = result.Example(
        example_float=1.0,
        enum_value=result.ExampleEnum.EXAMPLE_ENUM_1
    )

    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message)

    assert proto_message == decoded_message

    print('test_parser_enum is valid!')


def test_parser_repeated():
    proto_definition = """syntax = "proto2";
message Example {
    optional float example_float = 1;
    repeated int32 example_repeated = 2;
}
"""

    start = time.time()
    result = parse(proto_definition)
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.syntax == 'proto2'
    assert result.messages['Example'].fields_by_name['example_float'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_float'].type == ProtobufType.FLOAT
    assert result.messages['Example'].fields_by_name['example_float'].name == 'example_float'
    assert result.messages['Example'].fields_by_name['example_float'].number == 1

    assert result.messages['Example'].fields_by_name['example_repeated'].label == ProtobufLabel.REPEATED
    assert result.messages['Example'].fields_by_name['example_repeated'].type == ProtobufType.INT32
    assert result.messages['Example'].fields_by_name['example_repeated'].name == 'example_repeated'
    assert result.messages['Example'].fields_by_name['example_repeated'].number == 2

    proto_message = result.Example(
        example_float=1.0,
        example_repeated=[1, 2, 3, 4, 5]
    )

    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message)

    assert proto_message == decoded_message

    print('test_parser_repeated is valid!')


def test_parser_repeated_packed():
    proto_definition = """syntax = "proto2";
message Example {
    optional float example_float = 1;
    repeated int32 example_repeated = 2 [packed=true];
}
"""

    start = time.time()
    result = parse(proto_definition)
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.syntax == 'proto2'
    assert result.messages['Example'].fields_by_name['example_float'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_float'].type == ProtobufType.FLOAT
    assert result.messages['Example'].fields_by_name['example_float'].name == 'example_float'
    assert result.messages['Example'].fields_by_name['example_float'].number == 1

    assert result.messages['Example'].fields_by_name['example_repeated'].label == ProtobufLabel.REPEATED
    assert result.messages['Example'].fields_by_name['example_repeated'].type == ProtobufType.INT32
    assert result.messages['Example'].fields_by_name['example_repeated'].name == 'example_repeated'
    assert result.messages['Example'].fields_by_name['example_repeated'].number == 2

    proto_message = result.Example(
        example_float=1.0,
        example_repeated=[1, 2, 3, 4, 5]
    )

    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message,
                                            definition={2: DecoderFieldDefinition.repeated_packed(WireType.VARINT)})

    assert proto_message == decoded_message

    print('test_parser_repeated_packed is valid!')


def test_parser_required():
    proto_definition = """syntax = "proto2";
message Example {
    required float example_float = 1;
    required int32 example_int = 2;
    required string example_string = 3;
    required bytes example_bytes = 4;
    required bool example_bool = 5;
}
"""

    start = time.time()
    result = parse(proto_definition)
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.syntax == 'proto2'
    assert result.messages['Example'].fields_by_name['example_float'].label == ProtobufLabel.REQUIRED
    assert result.messages['Example'].fields_by_name['example_float'].type == ProtobufType.FLOAT
    assert result.messages['Example'].fields_by_name['example_float'].name == 'example_float'
    assert result.messages['Example'].fields_by_name['example_float'].number == 1

    assert result.messages['Example'].fields_by_name['example_int'].label == ProtobufLabel.REQUIRED
    assert result.messages['Example'].fields_by_name['example_int'].type == ProtobufType.INT32
    assert result.messages['Example'].fields_by_name['example_int'].name == 'example_int'
    assert result.messages['Example'].fields_by_name['example_int'].number == 2

    assert result.messages['Example'].fields_by_name['example_string'].label == ProtobufLabel.REQUIRED
    assert result.messages['Example'].fields_by_name['example_string'].type == ProtobufType.STRING
    assert result.messages['Example'].fields_by_name['example_string'].name == 'example_string'
    assert result.messages['Example'].fields_by_name['example_string'].number == 3

    assert result.messages['Example'].fields_by_name['example_bytes'].label == ProtobufLabel.REQUIRED
    assert result.messages['Example'].fields_by_name['example_bytes'].type == ProtobufType.BYTES
    assert result.messages['Example'].fields_by_name['example_bytes'].name == 'example_bytes'
    assert result.messages['Example'].fields_by_name['example_bytes'].number == 4

    assert result.messages['Example'].fields_by_name['example_bool'].label == ProtobufLabel.REQUIRED
    assert result.messages['Example'].fields_by_name['example_bool'].type == ProtobufType.BOOL
    assert result.messages['Example'].fields_by_name['example_bool'].name == 'example_bool'
    assert result.messages['Example'].fields_by_name['example_bool'].number == 5

    proto_message = result.Example(
        example_float=1.0,
        example_int=1,
        example_string='test',
        example_bytes=b'test',
        example_bool=True,
    )

    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message)

    assert proto_message == decoded_message

    print('test_parser_required is valid!')


def test_parser_default_value():
    proto_definition = """syntax = "proto2";
message Example {
    required float example_float = 1 [default=1.0];
    optional int32 example_int = 2 [default=2];
    optional string example_string = 3 [default="test"];
    optional bytes example_bytes = 4 [default="test"];
    optional bool example_bool = 5 [default=true];
    optional ExampleEnum example_enum = 6 [default=EXAMPLE_ENUM_1];
}

enum ExampleEnum {
    EXAMPLE_ENUM_1 = 1;
    EXAMPLE_ENUM_2 = 2;
    EXAMPLE_ENUM_3 = 3;
}
"""

    start = time.time()
    result = parse(proto_definition)
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.syntax == 'proto2'
    assert result.messages['Example'].fields_by_name['example_float'].label == ProtobufLabel.REQUIRED
    assert result.messages['Example'].fields_by_name['example_float'].type == ProtobufType.FLOAT
    assert result.messages['Example'].fields_by_name['example_float'].name == 'example_float'
    assert result.messages['Example'].fields_by_name['example_float'].number == 1
    assert result.messages['Example'].fields_by_name['example_float'].options.get('default') == 1.0

    assert result.messages['Example'].fields_by_name['example_int'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_int'].type == ProtobufType.INT32
    assert result.messages['Example'].fields_by_name['example_int'].name == 'example_int'
    assert result.messages['Example'].fields_by_name['example_int'].number == 2
    assert result.messages['Example'].fields_by_name['example_int'].options.get('default') == 2

    assert result.messages['Example'].fields_by_name['example_string'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_string'].type == ProtobufType.STRING
    assert result.messages['Example'].fields_by_name['example_string'].name == 'example_string'
    assert result.messages['Example'].fields_by_name['example_string'].number == 3
    assert result.messages['Example'].fields_by_name['example_string'].options.get('default') == 'test'

    assert result.messages['Example'].fields_by_name['example_bytes'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_bytes'].type == ProtobufType.BYTES
    assert result.messages['Example'].fields_by_name['example_bytes'].name == 'example_bytes'
    assert result.messages['Example'].fields_by_name['example_bytes'].number == 4
    assert result.messages['Example'].fields_by_name['example_bytes'].options.get('default') == b'test'

    assert result.messages['Example'].fields_by_name['example_bool'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_bool'].type == ProtobufType.BOOL
    assert result.messages['Example'].fields_by_name['example_bool'].name == 'example_bool'
    assert result.messages['Example'].fields_by_name['example_bool'].number == 5
    assert result.messages['Example'].fields_by_name['example_bool'].options.get('default') == True

    assert result.messages['Example'].fields_by_name['example_enum'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_enum'].type == result.enums['ExampleEnum']
    assert result.messages['Example'].fields_by_name['example_enum'].name == 'example_enum'
    assert result.messages['Example'].fields_by_name['example_enum'].number == 6
    assert result.messages['Example'].fields_by_name['example_enum'].options.get('default') == result.enums['ExampleEnum'].values_by_name['EXAMPLE_ENUM_1']

    assert result.enums['ExampleEnum'].values_by_name['EXAMPLE_ENUM_1'] == 1
    assert result.enums['ExampleEnum'].values_by_name['EXAMPLE_ENUM_2'] == 2
    assert result.enums['ExampleEnum'].values_by_name['EXAMPLE_ENUM_3'] == 3

    proto_message = result.Example()
    assert proto_message.example_float == 1.0
    assert proto_message.example_int == 2
    assert proto_message.example_string == 'test'
    assert proto_message.example_bytes == b'test'
    assert proto_message.example_bool

    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message)

    assert proto_message == decoded_message

    print('test_parser_default_value is valid!')


def test_parser_comments():
    proto_definition = """syntax = "proto2";
// This is a comment
message Example {
    /* This is a multiline
     * comment */
    optional float example_float = 1; // This is a comment
    optional ExampleSubMessage example_sub_message = 2; // This is another comment
}
    
message ExampleSubMessage {
    optional int32 example_int_1 = 13;
    required int32 example_int_2 = 14;
}
"""

    start = time.time()
    result = parse(proto_definition)
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert len(result.comments) == 1
    assert result.comments[0] == 'This is a comment'

    assert len(result.messages['Example'].comments) == 1
    assert result.messages['Example'].comments[0] == 'This is a multiline comment'

    assert result.messages['Example'].fields_by_name['example_float'].comment == 'This is a comment'
    assert result.messages['Example'].fields_by_name['example_sub_message'].comment == 'This is another comment'

    assert len(result.messages['ExampleSubMessage'].comments) == 0
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].comment is None
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].comment is None

    print('test_parser_comments is valid!')


def test_parser_reserved_fields():
    proto_definition = """syntax = "proto2";
message Example {
    reserved 2, 15, 9 to 11, 13;
    optional float example_float = 1;
    optional ExampleSubMessage example_sub_message = 3;
}
    
message ExampleSubMessage {
    reserved 1, 2, 3;
    optional int32 example_int_1 = 4;
    required int32 example_int_2 = 5;
}
"""

    start = time.time()
    result = parse(proto_definition)
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')
    assert len(result.messages['Example'].reserved_field_numbers) == 6
    assert 2 in result.messages['Example'].reserved_field_numbers
    assert 15 in result.messages['Example'].reserved_field_numbers
    assert 9 in result.messages['Example'].reserved_field_numbers
    assert 10 in result.messages['Example'].reserved_field_numbers
    assert 11 in result.messages['Example'].reserved_field_numbers
    assert 13 in result.messages['Example'].reserved_field_numbers

    assert len(result.messages['ExampleSubMessage'].reserved_field_numbers) == 3
    assert 1 in result.messages['ExampleSubMessage'].reserved_field_numbers
    assert 2 in result.messages['ExampleSubMessage'].reserved_field_numbers
    assert 3 in result.messages['ExampleSubMessage'].reserved_field_numbers

    print('test_parser_reserved_fields is valid!')


def test_parser_imports_with_local_files():
    proto_definition = """syntax = "proto2";
import "custom_import.proto";
    
message Example {
    optional float example_float = 1;
    optional ExampleSubMessage example_sub_message = 2;
}
"""

    start = time.time()
    result = parse(proto_definition, imports_path='imports')
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.messages['Example'].fields_by_name['example_float'].type == ProtobufType.FLOAT
    assert result.messages['Example'].fields_by_name['example_sub_message'].type == result.messages['ExampleSubMessage']

    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].label == ProtobufLabel.OPTIONAL
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].type == ProtobufType.INT32
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].name == 'example_int_1'
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].number == 13

    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].label == ProtobufLabel.REQUIRED
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].type == ProtobufType.INT32
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].name == 'example_int_2'
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].number == 14

    assert result.messages['Example'].fields_by_name['example_sub_message'].type == result.messages['ExampleSubMessage']

    proto_message = result.Example(
        example_timestamp=2.0,
        example_sub_message=result.ExampleSubMessage(
            example_int_1=1,
            example_int_2=2
        )
    )

    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message)

    assert proto_message == decoded_message

    print('test_parser_imports is valid!')


def test_parser_imports_with_local_files_file_structure():
    proto_definition = """syntax = "proto2";
import "google/protobuf/timestamp.proto";

message Example {
    optional google.protobuf.Timestamp example_timestamp = 1;
    optional ExampleSubMessage example_sub_message = 2;
}

message ExampleSubMessage {
    optional int32 example_int_1 = 13;
    required int32 example_int_2 = 14;
}
"""

    start = time.time()
    result = parse(proto_definition, imports_path='imports')
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.messages['Example'].fields_by_name['example_timestamp'].type == result.messages[
        'google.protobuf.Timestamp']
    assert result.messages['Example'].fields_by_name['example_sub_message'].type == result.messages['ExampleSubMessage']

    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].label == ProtobufLabel.OPTIONAL
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].type == ProtobufType.INT32
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].name == 'example_int_1'
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].number == 13

    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].label == ProtobufLabel.REQUIRED
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].type == ProtobufType.INT32
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].name == 'example_int_2'
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].number == 14

    assert result.messages['Example'].fields_by_name['example_sub_message'].type == result.messages['ExampleSubMessage']

    proto_message = result.Example(
        example_timestamp=result.google.protobuf.Timestamp(seconds=1, nanos=2),
        example_sub_message=result.ExampleSubMessage(
            example_int_1=1,
            example_int_2=2
        )
    )

    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message)

    assert proto_message == decoded_message

    print('test_parser_imports is valid!')


def test_parser_public_import():
    proto_definition = """syntax = "proto2";
import "public_import.proto";

message Example {
    optional float example_float = 1;
    optional ExampleSubMessage example_sub_message = 2;
}
"""

    start = time.time()
    result = parse(proto_definition, imports_path='imports')
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.messages['Example'].fields_by_name['example_float'].type == ProtobufType.FLOAT
    assert result.messages['Example'].fields_by_name['example_sub_message'].type == result.messages['ExampleSubMessage']

    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].label == ProtobufLabel.OPTIONAL
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].type == ProtobufType.INT32
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].name == 'example_int_1'
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].number == 13

    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].label == ProtobufLabel.REQUIRED
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].type == ProtobufType.INT32
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].name == 'example_int_2'
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].number == 14

    assert result.messages['Example'].fields_by_name['example_sub_message'].type == result.messages['ExampleSubMessage']

    assert result.messages.get('OtherMessage') is None

    proto_message = result.Example(
        example_timestamp=2.0,
        example_sub_message=result.ExampleSubMessage(
            example_int_1=1,
            example_int_2=2
        )
    )

    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message)

    assert proto_message == decoded_message

    print('test_parser_imports is valid!')


def test_parser_imports_with_remote_files():
    proto_definition = """syntax = "proto2";
import "google/protobuf/timestamp.proto";

message Example {
    optional google.protobuf.Timestamp example_timestamp = 1;
    optional ExampleSubMessage example_sub_message = 2;
}

message ExampleSubMessage {
    optional int32 example_int_1 = 13;
    required int32 example_int_2 = 14;
}
"""

    start = time.time()
    result = parse(proto_definition)
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.messages['Example'].fields_by_name['example_timestamp'].type == result.messages[
        'google.protobuf.Timestamp']
    assert result.messages['Example'].fields_by_name['example_sub_message'].type == result.messages['ExampleSubMessage']

    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].label == ProtobufLabel.OPTIONAL
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].type == ProtobufType.INT32
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].name == 'example_int_1'
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_1'].number == 13

    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].label == ProtobufLabel.REQUIRED
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].type == ProtobufType.INT32
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].name == 'example_int_2'
    assert result.messages['ExampleSubMessage'].fields_by_name['example_int_2'].number == 14

    assert result.messages['Example'].fields_by_name['example_sub_message'].type == result.messages['ExampleSubMessage']

    proto_message = result.Example(
        example_timestamp=result.google.protobuf.Timestamp(seconds=1, nanos=2),
        example_sub_message=result.ExampleSubMessage(
            example_int_1=1,
            example_int_2=2
        )
    )

    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message)

    assert proto_message == decoded_message

    print('test_parser_imports is valid!')


def test_parser_extension():
    proto_definition = """syntax = "proto2";

import extension.proto;

extend ExtendableMessage {
    optional float example_float = 2;
}
"""

    start = time.time()
    result = parse(proto_definition, imports_path='imports')
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.syntax == 'proto2'
    assert result.messages['ExtendableMessage'].fields_by_name['example_int_1'].label == ProtobufLabel.OPTIONAL
    assert result.messages['ExtendableMessage'].fields_by_name['example_int_1'].type == ProtobufType.INT32
    assert result.messages['ExtendableMessage'].fields_by_name['example_int_1'].name == 'example_int_1'
    assert result.messages['ExtendableMessage'].fields_by_name['example_int_1'].number == 1

    assert result.messages['ExtendableMessage'].fields_by_name['example_float'].label == ProtobufLabel.OPTIONAL
    assert result.messages['ExtendableMessage'].fields_by_name['example_float'].type == ProtobufType.FLOAT
    assert result.messages['ExtendableMessage'].fields_by_name['example_float'].name == 'example_float'
    assert result.messages['ExtendableMessage'].fields_by_name['example_float'].number == 2

    proto_message = result.ExtendableMessage(
        example_float=1.0,
        example_int_1=1,
    )

    assert proto_message.example_int_1 == 1
    assert proto_message.example_float == 1.0

    encoded_message = proto_message.encode()
    decoded_message = result.ExtendableMessage.decode(encoded_message)

    assert proto_message == decoded_message

    print('test_parser_extension is valid!')


class PackableValue:
    def __init__(self,
                 value: int,
                 value_2: float,
                 value_3: str,
                 value_4: bytes,
                 value_5: bool):
        self.value = value
        self.value_2 = value_2
        self.value_3 = value_3
        self.value_4 = value_4
        self.value_5 = value_5

    def __eq__(self, other):
        return self.value == other.value and \
               self.value_2 == other.value_2 and \
               self.value_3 == other.value_3 and \
               self.value_4 == other.value_4 and \
               self.value_5 == other.value_5


def test_any_pickle():
    proto_definition = """syntax = "proto2";

import "google/protobuf/any.proto";

message Example {
    optional google.protobuf.Any example_any = 1;
}
"""

    start = time.time()
    result = parse(proto_definition, imports_path='imports')
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.syntax == 'proto2'
    assert result.messages['Example'].fields_by_name['example_any'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_any'].type == result.messages['google.protobuf.Any']
    assert result.messages['Example'].fields_by_name['example_any'].name == 'example_any'
    assert result.messages['Example'].fields_by_name['example_any'].number == 1

    packable_value = PackableValue(
        value=1,
        value_2=2.0,
        value_3='test',
        value_4=b'test',
        value_5=True
    )
    proto_message = result.Example(
        example_any=result.google.protobuf.Any.pack(packable_value)
    )

    assert proto_message.example_any.type_url == 'type.googleapis.com/Example'
    assert proto_message.example_any.value == (b'\n\x12\n\x05value\x12\t3int\x80\x04K\x01.\n&\n\x07value_2\x12'
                                               b'\x1b5float\x80\x04\x95\n\x00\x00\x00\x00\x00\x00\x00G@\x00\x00'
                                               b'\x00\x00\x00\x00\x00.\n"\n\x07value_3\x12\x173str\x80\x04\x95'
                                               b'\x08\x00\x00\x00\x00\x00\x00\x00\x8c\x04test\x94.\n$\n\x07value_4'
                                               b'\x12\x195bytes\x80\x04\x95\x08\x00\x00\x00\x00\x00\x00\x00C'
                                               b'\x04test\x94.\n\x14\n\x07value_5\x12\t4bool\x80\x04\x88.')

    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message)

    assert proto_message == decoded_message
    decoded_packable_value = decoded_message.example_any.unpack(PackableValue)
    assert packable_value == decoded_packable_value

    print('test_any_pickle is valid!')


def test_any_jsonpickle():
    proto_definition = """syntax = "proto2";

import "google/protobuf/any.proto";

message Example {
    optional google.protobuf.Any example_any = 1;
}
"""
    import constants
    constants.PACKING_BACKEND = 'jsonpickle'

    start = time.time()
    result = parse(proto_definition, imports_path='imports')
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.syntax == 'proto2'
    assert result.messages['Example'].fields_by_name['example_any'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_any'].type == result.messages['google.protobuf.Any']
    assert result.messages['Example'].fields_by_name['example_any'].name == 'example_any'
    assert result.messages['Example'].fields_by_name['example_any'].number == 1

    packable_value = PackableValue(
        value=1,
        value_2=2.0,
        value_3='test',
        value_4=b'test',
        value_5=True
    )
    proto_message = result.Example(
        example_any=result.google.protobuf.Any.pack(packable_value)
    )

    assert proto_message.example_any.type_url == 'type.googleapis.com/Example'
    assert proto_message.example_any.value == (b'{"py/object": "unit.test_parser_proto2.PackableValue", "value": 1, '
                                               b'"value_2": 2.0, "value_3": "test", "value_4": {"py/b64": "dGVzdA=="}, '
                                               b'"value_5": true}')

    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message)

    assert proto_message == decoded_message
    decoded_packable_value = decoded_message.example_any.unpack(PackableValue)
    assert packable_value == decoded_packable_value

    print('test_any_jsonpickle is valid!')


def test_parser_oneof():
    proto_definition = """syntax = "proto2";
message Example {
    optional float example_float = 1;
    oneof example_oneof {
        int32 example_int_1 = 13;
        int32 example_int_2 = 14;
    }
}
"""

    start = time.time()
    result = parse(proto_definition)
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.syntax == 'proto2'
    assert result.messages['Example'].fields_by_name['example_float'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_float'].type == ProtobufType.FLOAT
    assert result.messages['Example'].fields_by_name['example_float'].name == 'example_float'
    assert result.messages['Example'].fields_by_name['example_float'].number == 1

    assert result.messages['Example'].fields_by_name['example_int_1'].type == ProtobufType.INT32
    assert result.messages['Example'].fields_by_name['example_int_1'].name == 'example_int_1'
    assert result.messages['Example'].fields_by_name['example_int_1'].number == 13

    assert result.messages['Example'].fields_by_name['example_int_2'].type == ProtobufType.INT32
    assert result.messages['Example'].fields_by_name['example_int_2'].name == 'example_int_2'
    assert result.messages['Example'].fields_by_name['example_int_2'].number == 14

    proto_message = result.Example(
        example_float=1.0,
        example_int_1=1,
        example_int_2=2,
    )

    assert proto_message.example_int_1 == 0
    assert proto_message.example_int_2 == 2

    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message)

    assert proto_message == decoded_message

    print('test_parser_oneof is valid!')


def test_parser_map():
    proto_definition = """syntax = "proto2";
message Example {
    optional float example_float = 1;
    optional map<int32, int32> example_map = 2;
}
"""

    start = time.time()
    result = parse(proto_definition)
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.syntax == 'proto2'
    assert result.messages['Example'].fields_by_name['example_float'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_float'].type == ProtobufType.FLOAT
    assert result.messages['Example'].fields_by_name['example_float'].name == 'example_float'
    assert result.messages['Example'].fields_by_name['example_float'].number == 1

    assert result.messages['Example'].fields_by_name['example_map'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_map'].type == (ProtobufType.INT32, ProtobufType.INT32)
    assert result.messages['Example'].fields_by_name['example_map'].name == 'example_map'
    assert result.messages['Example'].fields_by_name['example_map'].number == 2

    proto_message = result.Example(
        example_float=1.0,
        example_map={
            1: 2,
            3: 4,
            5: 6
        }
    )

    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message)

    assert proto_message == decoded_message

    print('test_parser_map is valid!')


def test_parser_map_sub_message():
    proto_definition = """syntax = "proto2";
message Example {
    optional float example_float = 1;
    optional map<int32, ExampleSubMessage> example_map = 2;
}

message ExampleSubMessage {
    optional int32 example_int_1 = 13;
    required int32 example_int_2 = 14;
}
"""

    start = time.time()
    result = parse(proto_definition)
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert result.syntax == 'proto2'
    assert result.messages['Example'].fields_by_name['example_float'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_float'].type == ProtobufType.FLOAT
    assert result.messages['Example'].fields_by_name['example_float'].name == 'example_float'
    assert result.messages['Example'].fields_by_name['example_float'].number == 1

    assert result.messages['Example'].fields_by_name['example_map'].label == ProtobufLabel.OPTIONAL
    assert result.messages['Example'].fields_by_name['example_map'].type == (ProtobufType.INT32, result.messages['ExampleSubMessage'])
    assert result.messages['Example'].fields_by_name['example_map'].name == 'example_map'
    assert result.messages['Example'].fields_by_name['example_map'].number == 2

    proto_message = result.Example(
        example_float=1.0,
        example_map={
            1: result.ExampleSubMessage(
                example_int_1=1,
                example_int_2=2
            ),
            2: result.ExampleSubMessage(
                example_int_1=3,
                example_int_2=4
            ),
            3: result.ExampleSubMessage(
                example_int_1=5,
                example_int_2=6
            ),
        }
    )

    encoded_message = proto_message.encode()
    decoded_message = result.Example.decode(encoded_message)

    assert proto_message == decoded_message

    print('test_parser_map is valid!')


def test_parser_service():
    proto_definition = """syntax = "proto2";
service Example {
    rpc ExampleMethod (ExampleRequest) returns (ExampleResponse);
}

message ExampleRequest {
    optional float example_float = 1;
}
    
message ExampleResponse {
    optional float example_float = 1;
}
"""

    start = time.time()
    result = parse(proto_definition)
    print(f'Parsed in {(time.time() - start) * 1_000_000:.6f} microseconds')

    assert len(result.services) == 1
    assert result.services['Example'].name == 'Example'
    assert len(result.services['Example'].methods) == 1
    assert result.services['Example'].methods['ExampleMethod'].name == 'ExampleMethod'
    assert result.services['Example'].methods['ExampleMethod'].input_type == result.messages['ExampleRequest']
    assert result.services['Example'].methods['ExampleMethod'].output_type == result.messages['ExampleResponse']

    print('test_parser_service is valid!')
