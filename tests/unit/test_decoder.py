import time

import pytest

from dynamic_protobuf import decode, DecoderFieldDefinition, WireType

test_cases = {
    # basic cases
    b'\x08\x96\x01': {1: 150},
    b'\t\xf0\x89gT4o\x9dA': {1: 123456789.1011121314},

    # repeated field cases (non-packed)
    b'\x08\x01\x08\x02\x08\x03': {1: [1, 2, 3]},
    b'\r\xcd\xcc\x8c?\r\xcd\xcc\x0c@\r33S@': {1: [1.1, 2.2, 3.3]},

    # repeated field cases (packed) (can not be done without a definition)
    b'\n\x03\x01\x02\x03': {1: '010203'},
    b'\n\x0c\xcd\xcc\x8c?\xcd\xcc\x0c@33S@': {1: 'cdcc8c3fcdcc0c4033335340'},

    # varints of various byte sizes
    b'\x88\x02{': {33: 123},
    b'\x90\x02{': {34: 123},
    b'\xa8\x02{': {37: 123},
    b'\xd0\x0f{': {250: 123},
    b'\x80 {': {512: 123},
    b'\xb0"{': {550: 123},
    b'\xf8?{': {1023: 123},
    b'\x80@{': {1024: 123},
    b'\x88@{': {1025: 123},
    b'\xe0]{': {1500: 123},
    b'\xf8\x7f{': {2047: 123},
    b'\x80\x80\x01{': {2048: 123},
    b'\xc8\xb2\x04{': {9001: 123},
    b'\x80\x80\x80\x01{': {262144: 123},
    b'\xf8\xff\xff\xff\x0f{': {536870911: 123},

    # sub message case
    b'\r\xa6\x9bD;\x12\x04h\x03p\x01': {1: 0.003, 2: {13: 3, 14: 1}},

    # complex case
    b'\r\x00\x00\xc0\x7f\x12\x1c\x08\x01\x12\x06\x08\xa2\xda\xdd\x8c\x06\x18\x00 '
    b'\x00(\x000\x008\x00@\x00H\x00P\x00X\x02':
        {1: float('nan'), 2: {1: 1, 2: {1: 1637313826}, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 2}},

    # map case
    b'\n\t\n\x05key_1\x10\x00\n\t\n\x05key_2\x10\x01': {1: [{1: 'key_1', 2: 0}, {1: 'key_2', 2: 1}]},
}

test_cases_with_definition = {
    # repeated field cases (packed)
    'repeated_field_case_packed_1': (b'\n\x03\x01\x02\x03', {
        1: DecoderFieldDefinition.repeated_packed(WireType.VARINT)
    }, {1: [1, 2, 3]}),
    'repeated_field_case_packed_2': (b'\n\x0c\xcd\xcc\x8c?\xcd\xcc\x0c@33S@', {
        1: DecoderFieldDefinition.repeated_packed(WireType.FIXED32)
    }, {1: [1.1, 2.2, 3.3]}),

    # basic definition cases
    'basic_definition_case_1': (b'\x08\x96\x01', {
        1: DecoderFieldDefinition.optional()
    }, {1: 150}),
    'basic_definition_case_2': (b'\t\xf0\x89gT4o\x9dA', {
        1: DecoderFieldDefinition.optional()
    }, {1: 123456789.1011121314}),
    'basic_definition_case_3': (b'\r\xa6\x9bD;\x12\x04h\x03p\x01', {
        1: DecoderFieldDefinition.optional(),
        2: {13: DecoderFieldDefinition.optional(), 14: DecoderFieldDefinition.optional()}
    }, {1: 0.003, 2: {13: 3, 14: 1}}),
}


@pytest.mark.parametrize('test_case, expected_result', test_cases.items())
def test_deserialize(test_case: bytes, expected_result: dict):
    print(f'testing use case {test_case}')
    start = time.time()
    result = decode(test_case)
    print(f'Decoded in {(time.time() - start) * 1_000_000:.6f} microseconds')
    print(f'result is: {result}')
    if isinstance(result.get(1), list):
        assert result == expected_result

    else:
        if expected_result.get(1):
            # NaN values do not equal themselves
            if expected_result[1] == expected_result[1]:
                assert result[1] == expected_result[1]
            else:
                assert result[1] != result[1]
        else:
            assert result == expected_result

        if expected_result.get(2):
            assert result[2] == expected_result[2]

    print(f'test case {test_case} is valid!')


@pytest.mark.parametrize('test_case_name, expected_result', test_cases_with_definition.items())
def test_deserialize_with_definition(test_case_name: str, expected_result: tuple[bytes, dict, dict]):
    test_case, definition, expected_result = expected_result
    print(f'testing use case {test_case}')
    start = time.time()
    result = decode(test_case, definition)
    print(f'Decoded in {(time.time() - start) * 1_000_000:.6f} microseconds')
    print(f'result is: {result}')
    assert result == expected_result

    print(f'test case {test_case} is valid!')
