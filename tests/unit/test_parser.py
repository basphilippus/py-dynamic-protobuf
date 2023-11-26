import time

from dynamic_protobuf import parse
from parser import ProtobufType, ProtobufMessageDefinition
from parser_classes import ProtobufLabel


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
