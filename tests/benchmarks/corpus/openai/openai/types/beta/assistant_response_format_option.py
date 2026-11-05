# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, TypeAlias
from ..shared.response_format_text import ResponseFormatText
from ..shared.response_format_json_object import ResponseFormatJSONObject
from ..shared.response_format_json_schema import ResponseFormatJSONSchema
AssistantResponseFormatOption: TypeAlias = Union[Literal['auto'], ResponseFormatText, ResponseFormatJSONObject, ResponseFormatJSONSchema]
