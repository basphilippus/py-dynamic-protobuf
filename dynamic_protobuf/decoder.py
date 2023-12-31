import math
import struct
from enum import Enum

from dynamic_protobuf.constants import most_significant_bit_mask, value_mask, wire_type_mask, seven_decimals, \
    fifteen_decimals, WireType


class DecoderFieldType(Enum):
    OPTIONAL = 0
    REQUIRED = 1
    REPEATED = 2
    REPEATED_PACKED = 3
    MAP = 4


class DecoderFieldDefinition:

    type: DecoderFieldType = None
    wire_type: WireType | None = None

    def __init__(self, _type: DecoderFieldType, wire_type: WireType | None = None):
        self.type = _type
        self.wire_type = wire_type

    @classmethod
    def optional(cls):
        return cls(DecoderFieldType.OPTIONAL)

    @classmethod
    def required(cls):
        return cls(DecoderFieldType.REQUIRED)

    @classmethod
    def repeated(cls):
        return cls(DecoderFieldType.REPEATED)

    @classmethod
    def repeated_packed(cls, wire_type: WireType | None):
        return cls(DecoderFieldType.REPEATED_PACKED, wire_type)

    @classmethod
    def map(cls):
        return cls(DecoderFieldType.MAP)


def _get_relevant_bytes(byte_blob: bytes, index: int) -> tuple[list[int], int]:
    # in varint parsing, the most significant bit (continuation bit) indicates
    # whether the next byte is part of the varint.
    byte = byte_blob[index]

    # The current byte is always relevant.
    relevant_bytes = [byte]

    # Bitmask the byte to get the most significant bit (continuation bit).
    continuation_bit = byte & most_significant_bit_mask

    # The next byte to process is always at least the next byte
    next_index = index + 1

    # Loop until the most significant bit (continuation bit) is 0.
    while continuation_bit != 0:
        next_byte = byte_blob[next_index]
        relevant_bytes.append(next_byte)
        continuation_bit = next_byte & most_significant_bit_mask
        next_index += 1
    return relevant_bytes, next_index


def _parse_varint(byte_blob: bytes, index: int,
                  field_definition: DecoderFieldDefinition | None) -> tuple[int, int]:
    # Varints are variable in size, so we need to determine how many bytes to process.
    relevant_bytes, next_index = _get_relevant_bytes(byte_blob, index)

    # We add all the relevant bytes together to get the value, starting at zero.
    value = 0
    # We add the relevant bytes in reverse order, starting with the least significant byte.
    for byte in reversed(relevant_bytes):
        # The existing value is shifted 7 bits to the left to make room for the next byte.
        # The byte is masked to get rid of the most significant bit (continuation bit).
        value = (value << 7) | (byte & value_mask)
    return value, next_index


def _parse_packed_repeated(byte_blob: bytes, wire_type: WireType) -> list[int | float]:
    # packed repeated fields can only be decoded with a known wire type, because the values are not prefixed
    # with a field number and wire type.
    wire_type_function = wire_type_table[wire_type.value]

    values = []
    new_index = None
    for index, byte in enumerate(byte_blob):
        if new_index and index < new_index:
            continue

        value, new_index = wire_type_function(byte_blob, index, None)
        values.append(value)

    return values


def _parse_length_delimited(byte_blob: bytes, index: int,
                            field_definition: DecoderFieldDefinition | dict | None) -> tuple[int, int]:
    # The first bytes of a length delimited value contain the length of the value as a varint.
    length_bytes, next_index = _get_relevant_bytes(byte_blob, index)
    length = 0
    for byte in reversed(length_bytes):
        length = (length << 7) | (byte & value_mask)

    # The next byte is the first byte of the length delimited value.
    # The index is increased by 1 to skip the length byte.
    # next_
    index = next_index - 1

    if (field_definition and isinstance(field_definition, DecoderFieldDefinition)
            and field_definition.type == DecoderFieldType.REPEATED_PACKED):
        # The inside of the length delimited value can be processed as a separate byte blob.
        value = _parse_packed_repeated(byte_blob[index + 1:index + 1 + length], field_definition.wire_type)
        return value, index + 1 + length

    # The inside of the length delimited value can be processed as a separate byte blob.
    try:
        value = decode(byte_blob[index + 1:index + 1 + length], field_definition)
    except:
        # If the decoding fails, we return the raw bytes as a hexidecimal value.
        bytes_value = byte_blob[index + 1:index + 1 + length]
        if '\\x' not in bytes_value.__repr__():
            return bytes_value.decode(), index + 1 + length

        value = bytes_value.hex()
    return value, index + 1 + length


def _parse_32_bit(byte_blob: bytes, index: int,
                  field_definition: DecoderFieldDefinition | None) -> tuple[float, int]:
    # 32 bits = 4 bytes
    bytes_32_bit = byte_blob[index:index + 4]

    # We only store floats as 32 bits values, so we can unpack the 4 bytes as a float.
    value = struct.unpack('f', bytes_32_bit)[0]

    # If the value is NaN, it does not equal itself.
    if value == value:
        # If the value is not NaN, we round it to 7 decimals to get rid of floating point errors.
        # We do this by getting the last digit of the value checking if it's a 0 or a 9.
        last_digit = math.ceil(value * seven_decimals % 10) - 1
        if last_digit == 0:
            # If the last digit is a 0, we round down.
            value = math.floor(value * seven_decimals) / seven_decimals
        elif last_digit == 9:
            # If the last digit is a 9, we round up.
            value = math.ceil(value * seven_decimals) / seven_decimals
        elif last_digit == -1:
            # If the last digit is a -1, we do not round, because the value is already rounded.
            value = value
        else:
            raise Exception(f'Unexpected float error: last digit {last_digit} for value {value}')
    return value, index + 4


def _parse_64_bit(byte_blob: bytes, index: int,
                  field_definition: DecoderFieldDefinition | None) -> tuple[float, int]:
    # 64 bits = 8 bytes
    bytes_64_bit = byte_blob[index:index + 8]

    # We only store floats as 64 bits values, so we can unpack the 8 bytes as a float.
    value = struct.unpack('d', bytes_64_bit)[0]

    # If the value is NaN, it does not equal itself.
    if value == value:
        # If the value is not NaN, we round it to 15 decimals to get rid of floating point errors.
        # We do this by getting the last digit of the value checking if it's a 0 or a 9.
        last_digit = math.ceil(value * fifteen_decimals % 10) - 1
        if last_digit == 0:
            # If the last digit is a 0, we round down.
            value = math.floor(value * fifteen_decimals) / fifteen_decimals
        elif last_digit == 9:
            # If the last digit is a 9, we round up.
            value = math.ceil(value * fifteen_decimals) / fifteen_decimals
        elif last_digit == -1:
            # If the last digit is a -1, we do not round, because the value is already rounded.
            value = value
        else:
            raise Exception(f'Unexpected float error: last digit {last_digit} for value {value}')
    return value, index + 8


wire_type_table = {
    0: _parse_varint,  # varint
    1: _parse_64_bit,  # 64-bit
    2: _parse_length_delimited,  # length-delimited
    # 3: 'start group',  # deprecated and unused
    # 4: 'end group',  # deprecated and unused
    5: _parse_32_bit  # 32-bit
}


def decode(byte_blob: bytes, definition: dict | None = None) -> dict[int, int | float | dict]:
    """
    Decode a byte blob into a dictionary.
    The byte blob should be a valid Protobuf message.

    Example:
    b'\x08\x96\x01' is a valid Protobuf message, which would be decoded into {1: 150}.

    :param byte_blob: The byte blob to decode.
    :param definition: The Protobuf definition to use for decoding.
    :return: A dictionary containing the decoded values.
    """
    decoded_object = {}

    # The wire type is the encoding method used for the next variable.
    # This is found by looking at the first byte (after a variable).
    wire_type_function = None

    # The field number is the identifier of the next variable. Indicated in the Protobuf schema by the number.
    field_number = None

    new_index = None
    for index, byte in enumerate(byte_blob):
        if new_index and index < new_index:
            continue

        if not wire_type_function:
            # If no wire type and field number are known yet,
            # we are dealing with a new value and the current byte contains both.

            # The first 3 bits contain the wire type, the last 5 bits contain the field number,
            # which we can easily get by shifting the byte 3 bits to the right.
            wire_type_function = wire_type_table[byte & wire_type_mask]

            # Get the relevant bytes for the field number, indicated by the most significant bit.
            relevant_bytes, new_index = _get_relevant_bytes(byte_blob, index)

            # The first byte contains the first 5 bits of the field number and needs to be treated differently.
            # A mask is applied to get rid of the most significant bit and shifted
            # 3 bits to the right to get rid of the wire type.
            first_byte = relevant_bytes[0]
            field_number = (first_byte & value_mask) >> 3

            # The remaining bytes contain more significant parts of the field type.
            # These are shifted 4 bits to the left to add to the other bits of the first field type byte.
            for byte_index, relevant_byte in enumerate(relevant_bytes[1:]):
                field_number = field_number + ((relevant_byte & value_mask) << 4 + 7 * byte_index)

        else:
            field_definition = None
            if definition:
                field_definition = definition.get(field_number)

            if wire_type_function:
                value, new_index = wire_type_function(byte_blob, index, field_definition)
            else:
                raise Exception(f'Unsupported wire type {wire_type_function}')

            field_value = decoded_object.get(field_number)
            if not field_value:
                decoded_object[field_number] = value
            else:
                if isinstance(field_value, list):
                    field_value.append(value)
                else:
                    decoded_object[field_number] = [field_value, value]
            wire_type_function = None
            field_number = None

    return decoded_object
