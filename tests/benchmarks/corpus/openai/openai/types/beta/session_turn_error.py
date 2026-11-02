# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class SessionTurnError(BaseModel):
    """A customer-safe error describing why a session request failed."""
    code: Literal['context_length_exceeded', 'session_budget_exceeded', 'usage_limit_exceeded', 'project_spend_limit_exceeded', 'organization_spend_limit_exceeded', 'organization_usage_limit_exceeded', 'billing_not_active', 'credit_balance_exhausted', 'rate_limit_exceeded', 'flex_unavailable', 'server_overloaded', 'cyber_policy', 'misalignment_policy_violation', 'connection_failed', 'server_error', 'authentication_error', 'invalid_request', 'resource_not_found', 'sandbox_error', 'executor_version_incompatible', 'active_turn_not_steerable', 'request_timeout', 'internal_error']
    message: str
