# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .beta_response_format_text_json_schema_config import BetaResponseFormatTextJSONSchemaConfig

class Text(BaseModel):
    """Default response format. Used to generate text responses."""
    type: Literal['text']

class JSONObject(BaseModel):
    """JSON object response format.

    An older method of generating JSON responses.
    Using `json_schema` is recommended for models that support it. Note that the
    model will not generate JSON without a system or user message instructing it
    to do so.
    """
    type: Literal['json_object']
BetaResponseFormatTextConfig: TypeAlias = Annotated[Union[Text, BetaResponseFormatTextJSONSchemaConfig, JSONObject], PropertyInfo(discriminator='type')]
