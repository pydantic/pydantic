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
from .argumentsdelta import ArgumentsDelta
from .audiodelta import AudioDelta
from .codeexecutioncalldelta import CodeExecutionCallDelta
from .codeexecutionresultdelta import CodeExecutionResultDelta
from .documentdelta import DocumentDelta
from .filesearchcalldelta import FileSearchCallDelta
from .filesearchresultdelta import FileSearchResultDelta
from .functionresultdelta import FunctionResultDelta
from .googlemapscalldelta import GoogleMapsCallDelta
from .googlemapsresultdelta import GoogleMapsResultDelta
from .googlesearchcalldelta import GoogleSearchCallDelta
from .googlesearchresultdelta import GoogleSearchResultDelta
from .imagedelta import ImageDelta
from .mcpservertoolcalldelta import MCPServerToolCallDelta
from .mcpservertoolresultdelta import MCPServerToolResultDelta
from .processingcalldelta import ProcessingCallDelta
from .processingresultdelta import ProcessingResultDelta
from .retrievalcalldelta import RetrievalCallDelta
from .retrievalresultdelta import RetrievalResultDelta
from .textannotationdelta import TextAnnotationDelta
from .textdelta import TextDelta
from .thoughtsignaturedelta import ThoughtSignatureDelta
from .thoughtsummarydelta import ThoughtSummaryDelta
from .urlcontextcalldelta import URLContextCallDelta
from .urlcontextresultdelta import URLContextResultDelta
from .videodelta import VideoDelta
from functools import partial
from pydantic import ConfigDict
from pydantic.functional_validators import BeforeValidator
from typing import Any, Literal, Union
from typing_extensions import Annotated

class UnknownStepDeltaData(BaseModel):
    """A StepDeltaData variant the SDK doesn't recognize. Preserves the raw payload."""
    type: Literal['UNKNOWN'] = 'UNKNOWN'
    raw: Any
    is_unknown: Literal[True] = True
    model_config = ConfigDict(frozen=True)
_STEP_DELTA_DATA_VARIANTS: dict[str, Any] = {'arguments_delta': ArgumentsDelta, 'audio': AudioDelta, 'code_execution_call': CodeExecutionCallDelta, 'code_execution_result': CodeExecutionResultDelta, 'document': DocumentDelta, 'file_search_call': FileSearchCallDelta, 'file_search_result': FileSearchResultDelta, 'function_result': FunctionResultDelta, 'google_maps_call': GoogleMapsCallDelta, 'google_maps_result': GoogleMapsResultDelta, 'google_search_call': GoogleSearchCallDelta, 'google_search_result': GoogleSearchResultDelta, 'image': ImageDelta, 'mcp_server_tool_call': MCPServerToolCallDelta, 'mcp_server_tool_result': MCPServerToolResultDelta, 'processing_call': ProcessingCallDelta, 'processing_result': ProcessingResultDelta, 'retrieval_call': RetrievalCallDelta, 'retrieval_result': RetrievalResultDelta, 'text_annotation_delta': TextAnnotationDelta, 'text': TextDelta, 'thought_signature': ThoughtSignatureDelta, 'thought_summary': ThoughtSummaryDelta, 'url_context_call': URLContextCallDelta, 'url_context_result': URLContextResultDelta, 'video': VideoDelta}
StepDeltaData = Annotated[Union[ArgumentsDelta, AudioDelta, CodeExecutionCallDelta, CodeExecutionResultDelta, DocumentDelta, FileSearchCallDelta, FileSearchResultDelta, FunctionResultDelta, GoogleMapsCallDelta, GoogleMapsResultDelta, GoogleSearchCallDelta, GoogleSearchResultDelta, ImageDelta, MCPServerToolCallDelta, MCPServerToolResultDelta, ProcessingCallDelta, ProcessingResultDelta, RetrievalCallDelta, RetrievalResultDelta, TextAnnotationDelta, TextDelta, ThoughtSignatureDelta, ThoughtSummaryDelta, URLContextCallDelta, URLContextResultDelta, VideoDelta, UnknownStepDeltaData], BeforeValidator(partial(parse_open_union, disc_key='type', variants=_STEP_DELTA_DATA_VARIANTS, unknown_cls=UnknownStepDeltaData, union_name='StepDeltaData', lenient=True))]
