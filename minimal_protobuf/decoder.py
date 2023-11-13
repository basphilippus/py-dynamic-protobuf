import struct
from minimal_protobuf.constants import most_significant_bit_mask, value_mask, wire_type_mask


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


def _parse_varint(byte_blob: bytes, index: int) -> tuple[int, int]:
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


def _parse_length_delimited(byte_blob: bytes, index: int) -> tuple[int, int]:
    # The first byte of a length delimited value contains the length of the value.
    length = byte_blob[index]
    # The inside of the length delimited value can be processed as a separate byte blob.
    value = decode(byte_blob[index + 1:index + 1 + length])
    return value, index + 1 + length


def _parse_32_bit(byte_blob: bytes, index: int) -> tuple[float, int]:
    # 32 bits = 4 bytes
    bytes_32_bit = byte_blob[index:index + 4]

    # We only store floats as 32 bits values, so we can unpack the 4 bytes as a float.
    value = struct.unpack('f', bytes_32_bit)[0]

    # If the value is NaN, it does not equal itself.
    if value == value:
        # If the value is not NaN, we round it to 8 decimals, to get rid of floating point errors.
        value = int(value * 100_000_000) / 100_000_000
    return value, index + 4


def _parse_64_bit(byte_blob: bytes, index: int) -> tuple[float, int]:
    # 64 bits = 8 bytes
    bytes_64_bit = byte_blob[index:index + 8]

    # We only store floats as 64 bits values, so we can unpack the 8 bytes as a float.
    value = struct.unpack('d', bytes_64_bit)[0]

    # If the value is NaN, it does not equal itself.
    if value == value:
        # If the value is not NaN, we round it to 16 decimals, to get rid of floating point errors.
        value = int(value * 100_000_000_000_000) / 100_000_000_000_000
    return value, index + 8


wire_type_table = {
    0: _parse_varint,  # varint
    1: _parse_64_bit,  # 64-bit
    2: _parse_length_delimited,  # length-delimited
    # 3: 'start group',  # deprecated and unused
    # 4: 'end group',  # deprecated and unused
    5: _parse_32_bit  # 32-bit
}


def decode(byte_blob: bytes) -> dict[int, int | float | dict]:
    """
    Decode a byte blob into a dictionary.
    The byte blob should be a valid Protobuf message.

    Example:
    b'\x08\x96\x01' is a valid Protobuf message, which would be decoded into {1: 150}.

    :param byte_blob: The byte blob to decode.
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
            if wire_type_function:
                value, new_index = wire_type_function(byte_blob, index)
            else:
                raise Exception(f'Unsupported wire type {wire_type_function}')

            decoded_object[field_number] = value
            wire_type_function = None
            field_number = None

    return decoded_object
