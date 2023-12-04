import os
from typing import Any

from dynamic_protobuf import encode, WireType, decode
from protobuf_instance import ProtobufMessage


class AnyMessage(ProtobufMessage):

    def __init__(self, **kwargs):
        if self.definition:
            super().__init__(**kwargs)
        else:
            self.__dict__.update(**kwargs)

    def _pickle_pack(self, obj) -> bytes:
        if hasattr(obj, '__dict__') or isinstance(obj, dict):
            if isinstance(obj, dict):
                proto_dict = obj
            else:
                inner_dict = obj.__dict__

                proto_dict = {
                    1: (WireType.LENGTH_DELIMITED, [])
                }
                import pickle
                for key, value in sorted(inner_dict.items()):
                    _type = type(value).__name__
                    typed_value: bytes = f'{len(_type)}'.encode()
                    typed_value += _type.encode()
                    typed_value += pickle.dumps(value)
                    proto_dict[1][1].append({1: (WireType.LENGTH_DELIMITED, key), 2: (WireType.LENGTH_DELIMITED, typed_value)})
            packed_value = encode(proto_dict, determine_wire_types=True)
            return packed_value
        else:
            raise ValueError(f'Object of type {type(obj)} is not packable.')

    def _jsonpickle_pack(self, obj) -> bytes:
        import jsonpickle
        packed_value = jsonpickle.encode(obj).encode()
        return packed_value

    @classmethod
    def pack(cls, obj):
        from constants import PACKING_BACKEND
        packing_backend = PACKING_BACKEND
        pack_function = getattr(cls, f'_{packing_backend}_pack')
        if not pack_function:
            raise ValueError(f'Packing backend {packing_backend} not supported.')

        packed_value = pack_function(cls, obj)
        return cls(
            # type url is only known after rendering the value in the message.
            type_url=None,
            value=packed_value
        )

    def _pickle_unpack(self, clazz):
        import pickle
        instance = clazz.__new__(clazz)
        decoded_map: dict[int: list[dict[int, dict[str, Any]]]] = decode(self.value)
        for map_entry in decoded_map[1]:
            key = map_entry[1]
            typed_value = bytes.fromhex(map_entry[2])
            length_chars = []
            for char in typed_value:
                # find if char is a number between 0 and 9
                if 48 <= char <= 57:
                    length_chars.append(char)
                else:
                    break

            length = int(bytes(length_chars).decode())
            _type = typed_value[len(length_chars):len(length_chars) + length].decode()
            value = typed_value[len(length_chars) + length:]
            value = pickle.loads(value)
            setattr(instance, key, value)
        return instance

    def _jsonpickle_unpack(self, clazz):
        import jsonpickle
        instance = jsonpickle.decode(self.value.decode())
        return instance

    def unpack(self, clazz):
        from constants import PACKING_BACKEND
        packing_backend = PACKING_BACKEND
        unpack_function = getattr(self, f'_{packing_backend}_unpack')
        if not unpack_function:
            raise ValueError(f'Packing backend {packing_backend} not supported.')

        instance = unpack_function(clazz)
        return instance

    @classmethod
    def prepare_decode(cls, value):
        return cls(value=value)

