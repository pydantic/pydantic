# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ToolChoiceTypes(BaseModel):
    """
    Indicates that the model should use a built-in tool to generate a response.
    [Learn more about built-in tools](https://developers.openai.com/api/docs/guides/tools).
    """
    type: Literal['file_search', 'web_search_preview', 'computer', 'computer_use_preview', 'computer_use', 'web_search_preview_2025_03_11', 'image_generation', 'code_interpreter']
