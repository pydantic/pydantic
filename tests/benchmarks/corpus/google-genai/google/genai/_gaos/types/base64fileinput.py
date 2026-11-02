# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# pyformat: disable
# pylint: skip-file

# Frozen model corpus; modified from google-genai 2.34.0; see README.md and LICENSE.
from __future__ import annotations
import base64
import io
from os import PathLike
from typing import IO, Union
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated
Base64FileInput = Union[IO[bytes], PathLike[str]]

def encode_base64_file_input(value: Any) -> Any:
    if isinstance(value, (PathLike, io.IOBase)):
        if isinstance(value, PathLike):
            with open(value, 'rb') as fh:
                binary = fh.read()
        else:
            position = value.tell() if value.seekable() else None
            binary = value.read()
            if position is not None:
                value.seek(position)
            if isinstance(binary, str):
                binary = binary.encode()
        if not isinstance(binary, (bytes, bytearray)):
            raise TypeError(f'Base64FileInput expected binary IO returning bytes; got {type(binary).__name__}')
        return base64.b64encode(binary).decode('ascii')
    return value
Base64EncodedString = Annotated[str, BeforeValidator(encode_base64_file_input)]
