# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseFormatTextPython(BaseModel):
    """Configure the model to generate valid Python code.

    See the
    [custom grammars guide](https://developers.openai.com/api/docs/guides/function-calling#context-free-grammars) for more details.
    """
    type: Literal['python']
