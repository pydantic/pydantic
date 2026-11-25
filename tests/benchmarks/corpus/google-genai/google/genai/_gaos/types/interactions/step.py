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
from .codeexecutioncallstep import CodeExecutionCallStep, CodeExecutionCallStepParam
from .codeexecutionresultstep import CodeExecutionResultStep, CodeExecutionResultStepParam
from .filesearchcallstep import FileSearchCallStep, FileSearchCallStepParam
from .filesearchresultstep import FileSearchResultStep, FileSearchResultStepParam
from .functioncallstep import FunctionCallStep, FunctionCallStepParam
from .functionresultstep import FunctionResultStep, FunctionResultStepParam
from .googlemapscallstep import GoogleMapsCallStep, GoogleMapsCallStepParam
from .googlemapsresultstep import GoogleMapsResultStep, GoogleMapsResultStepParam
from .googlesearchcallstep import GoogleSearchCallStep, GoogleSearchCallStepParam
from .googlesearchresultstep import GoogleSearchResultStep, GoogleSearchResultStepParam
from .mcpservertoolcallstep import MCPServerToolCallStep, MCPServerToolCallStepParam
from .mcpservertoolresultstep import MCPServerToolResultStep, MCPServerToolResultStepParam
from .modeloutputstep import ModelOutputStep, ModelOutputStepParam
from .processingcallstep import ProcessingCallStep, ProcessingCallStepParam
from .processingresultstep import ProcessingResultStep, ProcessingResultStepParam
from .retrievalcallstep import RetrievalCallStep, RetrievalCallStepParam
from .retrievalresultstep import RetrievalResultStep, RetrievalResultStepParam
from .thoughtstep import ThoughtStep, ThoughtStepParam
from .urlcontextcallstep import URLContextCallStep, URLContextCallStepParam
from .urlcontextresultstep import URLContextResultStep, URLContextResultStepParam
from .userinputstep import UserInputStep, UserInputStepParam
from functools import partial
from pydantic import ConfigDict
from pydantic.functional_validators import BeforeValidator
from typing import Any, Literal, Union
from typing_extensions import Annotated, TypeAliasType
StepParam = TypeAliasType('StepParam', Union[UserInputStepParam, ThoughtStepParam, FileSearchCallStepParam, FileSearchResultStepParam, ModelOutputStepParam, ProcessingResultStepParam, ProcessingCallStepParam, GoogleMapsCallStepParam, GoogleMapsResultStepParam, RetrievalResultStepParam, CodeExecutionCallStepParam, URLContextCallStepParam, FunctionCallStepParam, MCPServerToolCallStepParam, MCPServerToolResultStepParam, RetrievalCallStepParam, GoogleSearchResultStepParam, GoogleSearchCallStepParam, FunctionResultStepParam, URLContextResultStepParam, CodeExecutionResultStepParam])

class UnknownStep(BaseModel):
    """A Step variant the SDK doesn't recognize. Preserves the raw payload."""
    type: Literal['UNKNOWN'] = 'UNKNOWN'
    raw: Any
    is_unknown: Literal[True] = True
    model_config = ConfigDict(frozen=True)
_STEP_VARIANTS: dict[str, Any] = {'code_execution_call': CodeExecutionCallStep, 'code_execution_result': CodeExecutionResultStep, 'file_search_call': FileSearchCallStep, 'file_search_result': FileSearchResultStep, 'function_call': FunctionCallStep, 'function_result': FunctionResultStep, 'google_maps_call': GoogleMapsCallStep, 'google_maps_result': GoogleMapsResultStep, 'google_search_call': GoogleSearchCallStep, 'google_search_result': GoogleSearchResultStep, 'mcp_server_tool_call': MCPServerToolCallStep, 'mcp_server_tool_result': MCPServerToolResultStep, 'model_output': ModelOutputStep, 'processing_call': ProcessingCallStep, 'processing_result': ProcessingResultStep, 'retrieval_call': RetrievalCallStep, 'retrieval_result': RetrievalResultStep, 'thought': ThoughtStep, 'url_context_call': URLContextCallStep, 'url_context_result': URLContextResultStep, 'user_input': UserInputStep}
Step = Annotated[Union[CodeExecutionCallStep, CodeExecutionResultStep, FileSearchCallStep, FileSearchResultStep, FunctionCallStep, FunctionResultStep, GoogleMapsCallStep, GoogleMapsResultStep, GoogleSearchCallStep, GoogleSearchResultStep, MCPServerToolCallStep, MCPServerToolResultStep, ModelOutputStep, ProcessingCallStep, ProcessingResultStep, RetrievalCallStep, RetrievalResultStep, ThoughtStep, URLContextCallStep, URLContextResultStep, UserInputStep, UnknownStep], BeforeValidator(partial(parse_open_union, disc_key='type', variants=_STEP_VARIANTS, unknown_cls=UnknownStep, union_name='Step', lenient=True))]
