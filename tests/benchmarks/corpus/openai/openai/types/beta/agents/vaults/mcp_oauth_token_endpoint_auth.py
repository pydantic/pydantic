# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ....._utils import PropertyInfo
from ....._models import BaseModel

class McpOauthTokenEndpointAuthResourceNone(BaseModel):
    """Sends the client ID without a client secret."""
    type: Literal['none']

class McpOauthTokenEndpointAuthResourceClientSecretBasic(BaseModel):
    """Sends the client ID and secret using HTTP Basic authentication."""
    type: Literal['client_secret_basic']

class McpOauthTokenEndpointAuthResourceClientSecretPost(BaseModel):
    """Sends the client ID and secret in the token request body."""
    type: Literal['client_secret_post']
McpOauthTokenEndpointAuth: TypeAlias = Annotated[Union[McpOauthTokenEndpointAuthResourceNone, McpOauthTokenEndpointAuthResourceClientSecretBasic, McpOauthTokenEndpointAuthResourceClientSecretPost], PropertyInfo(discriminator='type')]
