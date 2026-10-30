# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import TypeAlias
from .input_content import InputContent
AgentFunctionCallOutput: TypeAlias = Union[str, List[InputContent]]
