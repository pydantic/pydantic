# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, Union
from typing_extensions import Literal, Annotated, TypeAlias
from pydantic import Field as FieldInfo
from ..._utils import PropertyInfo
from ..._models import BaseModel

class TextFormatResourceText(BaseModel):
    """Generates ordinary text without a structured-output constraint."""
    type: Literal['text']

class TextFormatResourceJSONSchema(BaseModel):
    """Constrains generated text to a JSON Schema."""
    schema_: Dict[str, object] = FieldInfo(alias='schema')
    type: Literal['json_schema']
TextFormat: TypeAlias = Annotated[Union[TextFormatResourceText, TextFormatResourceJSONSchema], PropertyInfo(discriminator='type')]
