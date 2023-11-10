import struct
from minimal_protobuf.constants import most_significant_bit_mask, value_mask, WireType


def serialize(protoscope_dict: dict[int, tuple[WireType, int | float | dict]]) -> bytes:
    # The protoscope_dict should be a dictionary with the field number as key and a tuple of wire type and value as
    # value. The wire type should be a WireType enum value and the value should be an int, float or dict.
    # Example:
    # {
    #     1: (WireType.FIXED32, 0.003),
    #     2: (WireType.LENGTH_DELIMITED,
    #         {
    #             13: (WireType.VARINT, 3),
    #             14: (WireType.VARINT, 1)
    #         })
    # }
    serialized_bytes = []
    for field_number, (wire_type, value) in protoscope_dict.items():
        # The first 3 bits contain the wire type, the last 5 bits contain the field number,
        # so we shift the field number 3 bits to the left and add the wire type.
        # The result is encoded as a varint, as specified in the Protobuf specification.
        serialized_bytes.extend(encode_varint(field_number << 3 | wire_type.value))

        if wire_type == WireType.VARINT:
            serialized_bytes.extend(encode_varint(value))
        elif wire_type == WireType.FIXED32:
            # The struct module is used to convert the float to a 32-bit float.
            serialized_bytes.extend(struct.pack('f', value))
        elif wire_type == WireType.FIXED64:
            # The struct module is used to convert the float to a 64-bit float.
            serialized_bytes.extend(struct.pack('d', value))
        elif wire_type == WireType.LENGTH_DELIMITED:
            # Length delimited value are either a sub-message or a string.
            if isinstance(value, dict):
                serialized_value = serialize(value)
            else:
                serialized_value = bytes(value, 'utf-8')
            # Length delimited values are encoded as a varint containing the length of the value in bytes,
            # followed by the serialized value itself.
            serialized_bytes.extend(encode_varint(len(serialized_value)))
            serialized_bytes.extend(serialized_value)

    return bytes(serialized_bytes)


def encode_varint(int_value: int) -> bytes:
    encoded_value = []
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
            encoded_value.append((int_value & value_mask) | most_significant_bit_mask)
        else:
            # If the most significant bit is 0, this is the last byte.
            encoded_value.append(int_value & value_mask)
            break

        # We shift the int_value 7 bits to the right to get rid of the 7 bits we just encoded.
        int_value = int_value >> 7

    return bytes(encoded_value)
