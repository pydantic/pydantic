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
from .audioresponseformat import AudioResponseFormat, AudioResponseFormatParam
from .imageresponseformat import ImageResponseFormat, ImageResponseFormatParam
from .textresponseformat import TextResponseFormat, TextResponseFormatParam
from .videoresponseformat import VideoResponseFormat, VideoResponseFormatParam
from typing import Any, Dict, Union
from typing_extensions import TypeAliasType
ResponseFormatParam = TypeAliasType('ResponseFormatParam', Union[TextResponseFormatParam, AudioResponseFormatParam, ImageResponseFormatParam, VideoResponseFormatParam, Dict[str, Any]])
ResponseFormat = TypeAliasType('ResponseFormat', Union[TextResponseFormat, AudioResponseFormat, ImageResponseFormat, VideoResponseFormat, Dict[str, Any]])
