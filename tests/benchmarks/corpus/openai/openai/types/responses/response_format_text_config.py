# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..shared.response_format_text import ResponseFormatText
from ..shared.response_format_json_object import ResponseFormatJSONObject
from .response_format_text_json_schema_config import ResponseFormatTextJSONSchemaConfig
ResponseFormatTextConfig: TypeAlias = Annotated[Union[ResponseFormatText, ResponseFormatTextJSONSchemaConfig, ResponseFormatJSONObject], PropertyInfo(discriminator='type')]
