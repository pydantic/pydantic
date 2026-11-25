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
from .errorevent import ErrorEvent
from .interactioncompletedevent import InteractionCompletedEvent
from .interactioncreatedevent import InteractionCreatedEvent
from .interactionstatusupdate import InteractionStatusUpdate
from .stepdelta import StepDelta
from .stepstart import StepStart
from .stepstop import StepStop
from functools import partial
from pydantic import ConfigDict
from pydantic.functional_validators import BeforeValidator
from typing import Any, Literal, Union
from typing_extensions import Annotated

class UnknownInteractionSSEEvent(BaseModel):
    """A InteractionSSEEvent variant the SDK doesn't recognize. Preserves the raw payload."""
    event_type: Literal['UNKNOWN'] = 'UNKNOWN'
    raw: Any
    is_unknown: Literal[True] = True
    model_config = ConfigDict(frozen=True)
_INTERACTION_SSE_EVENT_VARIANTS: dict[str, Any] = {'error': ErrorEvent, 'interaction.completed': InteractionCompletedEvent, 'interaction.created': InteractionCreatedEvent, 'interaction.status_update': InteractionStatusUpdate, 'step.delta': StepDelta, 'step.start': StepStart, 'step.stop': StepStop}
InteractionSSEEvent = Annotated[Union[ErrorEvent, InteractionCompletedEvent, InteractionCreatedEvent, InteractionStatusUpdate, StepDelta, StepStart, StepStop, UnknownInteractionSSEEvent], BeforeValidator(partial(parse_open_union, disc_key='event_type', variants=_INTERACTION_SSE_EVENT_VARIANTS, unknown_cls=UnknownInteractionSSEEvent, union_name='InteractionSSEEvent', lenient=True))]
