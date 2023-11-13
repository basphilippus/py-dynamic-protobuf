import time

import pytest

from dynamic_protobuf import encode, WireType

test_cases = {
    # basic cases
    'basic_case_1': (
        {
            1: (WireType.VARINT, 150)
        }, b'\x08\x96\x01'),
    'basic_case_2': (
        {
            1: (WireType.FIXED64, 123456789.1011121314)}
        , b'\t\xf0\x89gT4o\x9dA'),
    'basic_case_3': (
        {
            1: (WireType.VARINT, True)}
        , b'\x08\x01'),
    'basic_case_4': (
        {
            1: (WireType.VARINT, False)}
        , b'\x08\x00'),

    # varints of various byte sizes
    'varint_case_1': (
        {
            33: (WireType.VARINT, 123)
        }, b'\x88\x02{'),
    'varint_case_2': (
        {
            34: (WireType.VARINT, 123)
        }, b'\x90\x02{'),
    'varint_case_3': (
        {
            37: (WireType.VARINT, 123)
        }, b'\xa8\x02{'),
    'varint_case_4': (
        {
            250: (WireType.VARINT, 123)
        }, b'\xd0\x0f{'),
    'varint_case_5': (
        {
            512: (WireType.VARINT, 123)
        }, b'\x80 {'),
    'varint_case_6': (
        {
            550: (WireType.VARINT, 123)
        }, b'\xb0"{'),
    'varint_case_7': (
        {
            1023: (WireType.VARINT, 123)
        }, b'\xf8?{'),
    'varint_case_8': (
        {
            1024: (WireType.VARINT, 123)
        }, b'\x80@{'),
    'varint_case_9': (
        {
            1025: (WireType.VARINT, 123)
        }, b'\x88@{'),
    'varint_case_10': (
        {
            1500: (WireType.VARINT, 123)
        }, b'\xe0]{'),
    'varint_case_11': (
        {
            2047: (WireType.VARINT, 123)
        }, b'\xf8\x7f{'),
    'varint_case_12': (
        {
            2048: (WireType.VARINT, 123)
        }, b'\x80\x80\x01{'),
    'varint_case_13': (
        {
            9001: (WireType.VARINT, 123)
        }, b'\xc8\xb2\x04{'),
    'varint_case_14': (
        {
            262144: (WireType.VARINT, 123)
        }, b'\x80\x80\x80\x01{'),
    'varint_case_15': (
        {
            536870911: (WireType.VARINT, 123)
        }, b'\xf8\xff\xff\xff\x0f{'),

    # sub message case
    'sub_message_case_1': (
        {
            1: (WireType.FIXED32, 0.003),
            2: (WireType.LENGTH_DELIMITED,
                {
                    13: (WireType.VARINT, 3),
                    14: (WireType.VARINT, 1)
                })
        }, b'\r\xa6\x9bD;\x12\x04h\x03p\x01'),
    'sub_message_case_2': (
        {
            1: (WireType.FIXED32, 0.003),
            2: (WireType.LENGTH_DELIMITED,
                {
                    13: (WireType.VARINT, 3),
                    14: (WireType.VARINT, 1),
                    15: (WireType.LENGTH_DELIMITED,
                         {
                            1: (WireType.VARINT, 3),
                            2: (WireType.VARINT, 1)
                         })
                })
        }, b'\r\xa6\x9bD;\x12\nh\x03p\x01z\x04\x08\x03\x10\x01'),

    # complex case
    'complex_case_1': (
        {
            1: (WireType.FIXED32, float('nan')),
            2: (WireType.LENGTH_DELIMITED,
                {
                    1: (WireType.VARINT, 1),
                    2: (WireType.LENGTH_DELIMITED, {1: (WireType.VARINT, 1637313826)}),
                    3: (WireType.VARINT, 0),
                    4: (WireType.VARINT, 0),
                    5: (WireType.VARINT, 0),
                    6: (WireType.VARINT, 0),
                    7: (WireType.VARINT, 0),
                    8: (WireType.VARINT, 0),
                    9: (WireType.VARINT, 0),
                    10: (WireType.VARINT, 0),
                    11: (WireType.VARINT, 2),
                })
        }, b'\r\x00\x00\xc0\x7f\x12\x1c\x08\x01\x12\x06\x08\xa2\xda\xdd\x8c\x06\x18\x00 \x00(\x000\x008\x00@\x00H\x00P'
           b'\x00X\x02'),

}

dynamic_wire_type_test_cases = {
    # dynamic wire type detection cases
    'dynamic_wire_type_detection_case_1': (
        {
            1: 0.003,
            2: {
                    13: 3,
                    14: 1,
                }
        }, b'\r\xa6\x9bD;\x12\x04h\x03p\x01'),
    'dynamic_wire_type_detection_case_2': (
        {
            1: float('nan'),
            2: {
                    1: 1,
                    2: {1: 1637313826},
                    3: 0,
                    4: 0,
                    5: 0,
                    6: 0,
                    7: 0,
                    8: 0,
                    9: 0,
                    10: 0,
                    11: 2,
                }
        }, b'\r\x00\x00\xc0\x7f\x12\x1c\x08\x01\x12\x06\x08\xa2\xda\xdd\x8c\x06\x18\x00 \x00(\x000\x008\x00@\x00H\x00P'
           b'\x00X\x02'),
}

@pytest.mark.parametrize('test_case_name, test_case', test_cases.items())
def test_encode(test_case_name, test_case):
    test_case, expected_result = test_case
    print(f'testing use case {test_case}')
    start = time.time()
    result = encode(test_case)
    print(f'Encoded in {(time.time() - start) * 1_000_000:.6f} microseconds')
    print(f'result is: {result}')
    assert result == expected_result

    print(f'test case {test_case} is valid!')


@pytest.mark.parametrize('test_case_name, test_case', dynamic_wire_type_test_cases.items())
def test_encode_dynamic_wire_type(test_case_name, test_case):
    test_case, expected_result = test_case
    print(f'testing use case {test_case}')
    start = time.time()
    result = encode(test_case, determine_wire_types=True)
    print(f'Encoded in {(time.time() - start) * 1_000_000:.6f} microseconds')
    print(f'result is: {result}')
    assert result == expected_result

    print(f'test case {test_case} is valid!')
