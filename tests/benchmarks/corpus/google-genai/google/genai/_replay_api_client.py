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
from typing import Any, Optional
from ._common import BaseModel

def pop_undeterministic_headers(headers: dict[str, str]) -> None:
    headers.pop('Date', None)
    headers.pop('Server-Timing', None)

class ReplayRequest(BaseModel):
    """Represents a single request in a replay."""
    method: str
    url: str
    headers: dict[str, str]
    body_segments: list[dict[str, object]]

class ReplayResponse(BaseModel):
    """Represents a single response in a replay."""
    status_code: int = 200
    headers: dict[str, str]
    body_segments: list[dict[str, object]]
    byte_segments: Optional[list[bytes]] = None
    sdk_response_segments: list[dict[str, object]]

    def model_post_init(self, __context: Any) -> None:
        pop_undeterministic_headers(self.headers)

class ReplayInteraction(BaseModel):
    """Represents a single interaction, request and response in a replay."""
    request: ReplayRequest
    response: ReplayResponse

class ReplayFile(BaseModel):
    """Represents a recorded session."""
    replay_id: str
    interactions: list[ReplayInteraction]
