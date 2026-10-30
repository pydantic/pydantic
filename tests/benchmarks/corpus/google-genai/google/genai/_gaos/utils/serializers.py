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
from ..types.basemodel import Unset

def serialize_int(as_str: bool):

    def serialize(i):
        if i is None:
            return None
        if isinstance(i, Unset):
            return i
        if not isinstance(i, int):
            raise ValueError('Expected int')
        return str(i) if as_str else i
    return serialize

def validate_int(b):
    if b is None:
        return None
    if isinstance(b, (int, Unset)):
        return b
    if not isinstance(b, str):
        raise ValueError('Expected string')
    return int(b)

def validate_const(v):

    def validate(c):
        if c is None:
            return None
        if v != c:
            raise ValueError(f'Expected {v}')
        return c
    return validate
