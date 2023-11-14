from enum import Enum

# A mask for getting only the most significant bit (continuation bit).
most_significant_bit_mask = 0b10000000

# A mask for getting only the value bits.
value_mask = 0b01111111

# A mask for getting only the wire type bits.
wire_type_mask = 0b00000111

# The number of decimals to round to for 32-bit floats to get rid of floating point error.
seven_decimals = 10_000_000

# The number of decimals to round to for 64-bit floats to get rid of floating point error.
fifteen_decimals = 1_000_000_000_000_000


class WireType(Enum):
    VARINT = 0
    FIXED64 = 1
    LENGTH_DELIMITED = 2
    FIXED32 = 5
