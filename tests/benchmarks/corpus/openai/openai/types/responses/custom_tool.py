# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from pydantic import Field as FieldInfo
from ..._models import BaseModel
from ..shared.custom_tool_input_format import CustomToolInputFormat

class CustomTool(BaseModel):
    """A custom tool that processes input using a specified format.

    Learn more about   [custom tools](https://developers.openai.com/api/docs/guides/function-calling#custom-tools)
    """
    name: str
    type: Literal['custom']
    allowed_callers: Optional[List[Literal['direct', 'programmatic']]] = None
    async_: Optional[bool] = FieldInfo(alias='async', default=None)
    defer_loading: Optional[bool] = None
    description: Optional[str] = None
    format: Optional[CustomToolInputFormat] = None
