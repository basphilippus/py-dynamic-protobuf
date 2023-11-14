import time

from dynamic_protobuf import parse, WireType
from parser import ProtobufLabel, ProtobufType, ProtobufMessageDefinition


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

    print('test_parser_basic_case is valid!')
