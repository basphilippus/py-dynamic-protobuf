import struct
from dynamic_protobuf.constants import most_significant_bit_mask, value_mask, WireType


def _encode_varint(int_value: int) -> list[int]:
    encoded_value: list[int] = []
    # If the int_value is negative, we convert it to a positive value by adding 2^64.
    # This is because Python does not have unsigned integers.
    if int_value < 0:
        int_value += (1 << 64)

    while True:
        # A varint can be split up over multiple bytes. The most significant bit of each byte indicates whether
        # there are more bytes to follow. If the most significant bit is 0, this is the last byte.
        # We check if the most significant bit is 1 by shifting the int_value 7 bits to the right and checking if
        # the result is larger than 0.
        if (int_value >> 7) > 0:
            # We apply the value mask using the & operator to get only the value bits. After that, we apply the
            # most significant bit mask using the | operator to set the most significant bit to 1.
            value = (int_value & value_mask) | most_significant_bit_mask
            encoded_value.append(value)
            # if value == int_value:
            #     break
        else:
            # If the most significant bit is 0, this is the last byte.
            encoded_value.append(int_value & value_mask)
            break

        # We shift the int_value 7 bits to the right to get rid of the 7 bits we just encoded.
        int_value = int_value >> 7

    return encoded_value


wire_type_table = {
    float: WireType.FIXED32,
    int: WireType.VARINT,
    bool: WireType.VARINT,
    dict: WireType.LENGTH_DELIMITED,
    str: WireType.LENGTH_DELIMITED,
    bytes: WireType.LENGTH_DELIMITED,
    list: WireType.LENGTH_DELIMITED,
}


def _determine_wire_type(value: int | float | dict | bool) -> WireType | None:
    return wire_type_table.get(type(value))


def _encode_value(encoded_bytes: list[int], field_number: int, value: int | float | dict | bool, wire_type: WireType,
                  packed_repeated_value: bool, determine_wire_types: bool, include_field_number: bool = True):

    # The first 3 bits contain the wire type, the last 5 bits contain the field number,
    # so we shift the field number 3 bits to the left and add the wire type.
    # The result is encoded as a varint, as specified in the Protobuf specification.
    if include_field_number:
        encoded_bytes.extend(_encode_varint(field_number << 3 | wire_type.value))

    if wire_type.value == WireType.VARINT.value:
        if isinstance(value, bool):
            # Booleans are encoded as 0 or 1.
            value = int(value)

        encoded_bytes.extend(_encode_varint(value))
    elif wire_type.value == WireType.FIXED32.value:
        # The struct module is used to convert the float to a 32-bit float.
        encoded_bytes.extend(struct.pack('f', value))
    elif wire_type.value == WireType.FIXED64.value:
        # The struct module is used to convert the float to a 64-bit float.
        encoded_bytes.extend(struct.pack('d', value))
    elif wire_type.value == WireType.LENGTH_DELIMITED.value:
        # Length delimited value are either a sub-message or a string.
        if packed_repeated_value:
            # This is a packed repeated value
            packed_wire_type, packed_list = value

            packed_field_bytes: list[int] = []
            for packed_value in packed_list:
                _encode_value(packed_field_bytes, field_number=field_number, value=packed_value,
                              wire_type=packed_wire_type, packed_repeated_value=False,
                              determine_wire_types=determine_wire_types, include_field_number=False)
            length_delimited_value = _encode_varint(len(packed_field_bytes))
            length_delimited_value.extend(packed_field_bytes)
            encoded_bytes.extend(length_delimited_value)
        else:
            if isinstance(value, dict):
                encoded_value = encode(value, determine_wire_types=determine_wire_types)
            else:
                if isinstance(value, str):
                    value = bytes(value, 'utf-8')
                encoded_value = value
            # Length delimited values are encoded as a varint containing the length of the value in bytes,
            # followed by the encoded value itself.
            encoded_bytes.extend(_encode_varint(len(encoded_value)))
            encoded_bytes.extend(encoded_value)


def encode(proto_dict: dict[int, tuple[WireType, int | float | dict | bool] | int | float | dict | bool],
           determine_wire_types=False) -> bytes:
    """
    The proto_dict should be a dictionary with the field number as key and a tuple of wire type and value as
    value. The wire type should be a WireType enum value and the value should be an int, float or dict.
    Example:
    {
        1: (WireType.FIXED32, 0.003),
        2: (WireType.LENGTH_DELIMITED,
            {
                13: (WireType.VARINT, 3),
                14: (WireType.VARINT, 1)
            })
    }
    The equivalent Protobuf definition would be:
    message Example {
        optional float example_float = 1;
        optional ExampleSubMessage example_sub_message = 2;
    }

    message ExampleSubMessage {
        optional int32 example_int32 = 13;
        optional int32 example_int32 = 14;
    }

    Alternatively, the proto_dict can be a dictionary with the field number as key and the value as value, in which
    case the wire type will be determined automatically. The value should be an int, float, dict, str or bytes.
    Be aware that this can cause incorrect wire types for large floats, which might need to be encoded as
    64-bit floats.
    Example:
    {
        1: 0.003,
        2: {
                13: 3,
                14: 1
            }
    }

    :param proto_dict: The dictionary to encode.
    :param determine_wire_types: Whether to determine the wire types automatically.
    """
    encoded_bytes: list[int] = []
    for field_number, value in proto_dict.items():
        wire_type: WireType | None = None
        if isinstance(value, tuple):
            wire_type, value = value
        elif determine_wire_types:
            wire_type = _determine_wire_type(value)

        if not wire_type:
            raise ValueError('Wire type could not be determined for value: {}'.format(value))

        packed_repeated_value = False
        if isinstance(value, tuple) and isinstance(value[1], list):
            packed_repeated_value = True

        if not isinstance(value, list):
            value = [value]

        for list_value in value:
            _encode_value(encoded_bytes, field_number=field_number, value=list_value, wire_type=wire_type,
                          packed_repeated_value=packed_repeated_value, determine_wire_types=determine_wire_types)

    return bytes(encoded_bytes)
