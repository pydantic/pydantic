# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, TypeAlias
ResponseSteerErrorCode: TypeAlias = Union[Literal['response_not_found', 'invalid_input', 'steering_not_supported', 'too_many_pending_steers', 'response_already_completed', 'response_not_active', 'successor_creation_failed'], str]
