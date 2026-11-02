
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from __future__ import annotations
from typing import Generic, TypeVar
import pydantic
from pydantic import PrivateAttr
from ._models import GenericModel
_T = TypeVar('_T')

class BasePage(GenericModel, Generic[_T]):
    """
    Defines the core interface for pagination.

    Type Args:
        ModelT: The pydantic model that represents an item in the response.

    Methods:
        has_next_page(): Check if there is another page available
        next_page_info(): Get the necessary information to make a request for the next page
    """
    _options: FinalRequestOptions = PrivateAttr()
    _model: Type[_T] = PrivateAttr()

class BaseSyncPage(BasePage[_T], Generic[_T]):
    _client: SyncAPIClient = pydantic.PrivateAttr()

class BaseAsyncPage(BasePage[_T], Generic[_T]):
    _client: AsyncAPIClient = pydantic.PrivateAttr()
