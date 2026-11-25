# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, Optional
from typing_extensions import Literal
from pydantic import Field as FieldInfo
from ..._models import BaseModel

class ResponseFormatTextJSONSchemaConfig(BaseModel):
    """JSON Schema response format.

    Used to generate structured JSON responses.
    Learn more about [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
    """
    name: str
    schema_: Dict[str, object] = FieldInfo(alias='schema')
    type: Literal['json_schema']
    description: Optional[str] = None
    strict: Optional[bool] = None
