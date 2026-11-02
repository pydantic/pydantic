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
from .. import BaseModel
from ...utils.unions import parse_open_union
from .audiocontent import AudioContent, AudioContentParam
from .documentcontent import DocumentContent, DocumentContentParam
from .imagecontent import ImageContent, ImageContentParam
from .textcontent import TextContent, TextContentParam
from .videocontent import VideoContent, VideoContentParam
from functools import partial
from pydantic import ConfigDict
from pydantic.functional_validators import BeforeValidator
from typing import Any, Literal, Union
from typing_extensions import Annotated, TypeAliasType
ContentParam = TypeAliasType('ContentParam', Union[TextContentParam, DocumentContentParam, ImageContentParam, AudioContentParam, VideoContentParam])

class UnknownContent(BaseModel):
    """A Content variant the SDK doesn't recognize. Preserves the raw payload."""
    type: Literal['UNKNOWN'] = 'UNKNOWN'
    raw: Any
    is_unknown: Literal[True] = True
    model_config = ConfigDict(frozen=True)
_CONTENT_VARIANTS: dict[str, Any] = {'audio': AudioContent, 'document': DocumentContent, 'image': ImageContent, 'text': TextContent, 'video': VideoContent}
Content = Annotated[Union[AudioContent, DocumentContent, ImageContent, TextContent, VideoContent, UnknownContent], BeforeValidator(partial(parse_open_union, disc_key='type', variants=_CONTENT_VARIANTS, unknown_cls=UnknownContent, union_name='Content', lenient=True))]
