import os


class ProtobufImporter:

    def __init__(self, protobuf_definition: 'ProtobufDefinition', import_path: str | None, import_level: int):
        self.protobuf_definition = protobuf_definition
        self.import_path = import_path
        self._remote_file_cache: dict[str, bytes] = {}
        self.import_level = import_level

    def load_import(self, importable: str, public_import: bool) -> None:
        if self.import_path:
            self._load_local_import(importable, public_import)
        else:
            self._load_remote_default_import(importable, public_import)

    def _load_local_import(self, importable: str, public_import: bool) -> None:
        filename = f'{self.import_path}/{importable}'
        absolute_path = os.path.abspath(filename)
        try:
            file_content: bytes = open(absolute_path, 'rb').read()
        except FileNotFoundError:
            print(f'Warning: Could not find file {absolute_path}, '
                  f'Trying to retrieve from the Github Protobuf repository.')
            self._load_remote_default_import(importable, public_import)
            return

        if not file_content:
            raise Exception(f'Could import {absolute_path}')

        file_content_string: str = file_content.decode('utf-8')
        self._parse_import_content(importable, file_content_string, public_import)

    def _load_remote_default_import(self, importable: str, public_import: bool) -> None:
        if importable in self._remote_file_cache:
            file_content: bytes = self._remote_file_cache[importable]
        else:
            import urllib.request

            print('WARNING: Remote imports are very slow, '
                  'consider downloading the protobuf files locally and set the imports_path variable.')

            url = f'https://raw.githubusercontent.com/protocolbuffers/protobuf/master/src/{importable}'
            file_content: bytes = urllib.request.urlopen(url).read()

        file_content_string: str = file_content.decode('utf-8')
        self._parse_import_content(importable, file_content_string, public_import)

    def _parse_import_content(self, importable: str, file_content: str, public_import: bool) -> None:
        if not public_import and self.import_level > 0:
            return

        from dynamic_protobuf import parse
        from parser_classes import ProtobufDefinition

        import_folder: str = os.path.dirname(importable).replace('/', '.')
        import_protobuf_definition = parse(file_content, self.import_path, import_level=self.import_level + 1)
        for imported_message_name, imported_message in import_protobuf_definition.messages.items():
            imported_message_name_with_path = f'{import_folder}.{imported_message_name}' \
                if import_folder else imported_message_name
            folder_parts = import_folder.split('.')

            part = None
            previous_part_definition = self.protobuf_definition
            for folder_part in folder_parts:
                if folder_part and folder_part not in self.protobuf_definition.messages:
                    part = ProtobufDefinition()
                    previous_part_definition.messages[folder_part] = part
                    previous_part_definition = part

            if not part:
                part = previous_part_definition
            part.messages[imported_message_name] = imported_message
            self.protobuf_definition.messages[imported_message_name_with_path] = imported_message
