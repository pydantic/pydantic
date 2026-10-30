
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Generic, TypeVar, Optional
from ._base_client import BasePage, BaseSyncPage, BaseAsyncPage
_T = TypeVar('_T')

class SyncPage(BaseSyncPage[_T], BasePage[_T], Generic[_T]):
    """Note: no pagination actually occurs yet, this is for forwards-compatibility."""
    data: List[_T]
    object: str

class AsyncPage(BaseAsyncPage[_T], BasePage[_T], Generic[_T]):
    """Note: no pagination actually occurs yet, this is for forwards-compatibility."""
    data: List[_T]
    object: str

class SyncCursorPage(BaseSyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    has_more: Optional[bool] = None

class AsyncCursorPage(BaseAsyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    has_more: Optional[bool] = None

class SyncConversationCursorPage(BaseSyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    has_more: Optional[bool] = None
    last_id: Optional[str] = None

class AsyncConversationCursorPage(BaseAsyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    has_more: Optional[bool] = None
    last_id: Optional[str] = None

class SyncNextCursorPage(BaseSyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    has_more: Optional[bool] = None
    next: Optional[str] = None

class AsyncNextCursorPage(BaseAsyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    has_more: Optional[bool] = None
    next: Optional[str] = None

class SyncTokenPage(BaseSyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    has_more: Optional[bool] = None
    next: Optional[str] = None

class AsyncTokenPage(BaseAsyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    has_more: Optional[bool] = None
    next: Optional[str] = None
