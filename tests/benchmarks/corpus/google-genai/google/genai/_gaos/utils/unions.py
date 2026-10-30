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
from typing import Any, Mapping
from pydantic import BaseModel, TypeAdapter, ValidationError, ValidationInfo

def parse_open_union(v: Any, info: ValidationInfo, *, disc_key: str, variants: dict[str, Any], unknown_cls: type, union_name: str, lenient: bool=False) -> Any:
    from .serializers import ALLOW_UNKNOWN_UNION_VARIANTS
    if isinstance(v, BaseModel):
        return v
    if not isinstance(v, dict) or disc_key not in v:
        raise ValueError(f"{union_name}: expected object with '{disc_key}' field")
    context = info.context
    fallback_allowed = isinstance(context, Mapping) and bool(context.get(ALLOW_UNKNOWN_UNION_VARIANTS))
    disc = v[disc_key]
    variant_cls = variants.get(disc)
    if variant_cls is None:
        if fallback_allowed:
            return unknown_cls(raw=v)
        raise ValueError(f'{union_name}: unrecognized {disc_key} value {disc!r}')
    try:
        if isinstance(variant_cls, type) and issubclass(variant_cls, BaseModel):
            return variant_cls.model_validate(v, context=info.context)
        return TypeAdapter(variant_cls).validate_python(v, context=info.context)
    except ValidationError:
        if not fallback_allowed:
            raise
        if lenient:
            from .serializers import construct_unvalidated
            return construct_unvalidated(v, variant_cls)
        return unknown_cls(raw=v)
