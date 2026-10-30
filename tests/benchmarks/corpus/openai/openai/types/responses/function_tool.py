# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Optional
from typing_extensions import Literal
from pydantic import Field as FieldInfo
from ..._models import BaseModel

class FunctionTool(BaseModel):
    """Defines a function in your own code the model can choose to call.

    Learn more about [function calling](https://developers.openai.com/api/docs/guides/function-calling).
    """
    name: str
    parameters: Optional[Dict[str, object]] = None
    strict: Optional[bool] = None
    type: Literal['function']
    allowed_callers: Optional[List[Literal['direct', 'programmatic']]] = None
    async_: Optional[bool] = FieldInfo(alias='async', default=None)
    defer_loading: Optional[bool] = None
    description: Optional[str] = None
    output_schema: Optional[Dict[str, object]] = None
