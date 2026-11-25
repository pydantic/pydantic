# Copyright 2025 Google LLC
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

# Frozen model corpus; modified from google-genai 2.34.0; see README.md and LICENSE.
from __future__ import annotations
import os
from typing import Optional
import pydantic

class DebugConfig(pydantic.BaseModel):
    """Configuration options that change client network behavior when testing."""
    client_mode: Optional[str] = pydantic.Field(default_factory=lambda: os.getenv('GOOGLE_GENAI_CLIENT_MODE', None))
    replays_directory: Optional[str] = pydantic.Field(default_factory=lambda: os.getenv('GOOGLE_GENAI_REPLAYS_DIRECTORY', None))
    replay_id: Optional[str] = pydantic.Field(default_factory=lambda: os.getenv('GOOGLE_GENAI_REPLAY_ID', None))
