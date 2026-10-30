# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
import builtins
from typing import Dict
from typing_extensions import Literal
from ....._models import BaseModel

class SessionTrace(BaseModel):
    id: str
    created_at: int
    object: Literal['agent.session.trace']
    otlp: Dict[str, builtins.object]
    session_id: str
