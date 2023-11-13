import time

import pytest

from minimal_protobuf import decode

test_cases = {
    # basic cases
    b'\x08\x96\x01': {1: 150},
    b'\t\xf0\x89gT4o\x9dA': {1: 123456789.1011121314},

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
    b'\r\x00\x00\xc0\x7f\x12\x1c\x08\x01\x12\x06\x08\xa2\xda\xdd\x8c\x06\x18\x00 \x00(\x000\x008\x00@\x00H\x00P\x00X\x02':
        {1: float('nan'), 2: {1: 1, 2: {1: 1637313826}, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 2}},
}


@pytest.mark.parametrize('test_case, expected_result', test_cases.items())
def test_deserialize(test_case, expected_result):
    print(f'testing use case {test_case}')
    start = time.time()
    result = decode(test_case)
    print(f'Decoded in {(time.time() - start) * 1_000_000:.6f} microseconds')
    print(f'result is: {result}')
    if expected_result.get(1):
        # NaN values do not equal themselves
        if expected_result[1] == expected_result[1]:
            assert expected_result[1] == result[1]
        else:
            assert result[1] != result[1]
    else:
        assert expected_result == result

    if expected_result.get(2):
        assert expected_result[2] == result[2]

    print(f'test case {test_case} is valid!')
