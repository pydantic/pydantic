
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from __future__ import annotations
import base64
from typing_extensions import Literal
PropertyFormat = Literal['iso8601', 'base64', 'custom']

class PropertyInfo:
    """Metadata class to be used in Annotated types to provide information about a given type.

    For example:

    class MyParams(TypedDict):
        account_holder_name: Annotated[str, PropertyInfo(alias='accountHolderName')]

    This means that {'account_holder_name': 'Robert'} will be transformed to {'accountHolderName': 'Robert'} before being sent to the API.
    """
    alias: str | None
    format: PropertyFormat | None
    format_template: str | None
    discriminator: str | None

    def __init__(self, *, alias: str | None=None, format: PropertyFormat | None=None, format_template: str | None=None, discriminator: str | None=None) -> None:
        self.alias = alias
        self.format = format
        self.format_template = format_template
        self.discriminator = discriminator
