# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from .admin_api_key import AdminAPIKey

class AdminAPIKeyCreateResponse(AdminAPIKey):
    """Represents an individual Admin API key in an org."""
    value: str
