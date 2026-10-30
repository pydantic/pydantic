
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Generic, TypeVar, Optional
from datetime import datetime
from ._base_client import BasePage, BaseSyncPage, BaseAsyncPage
_T = TypeVar('_T')

class SyncPage(BaseSyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    has_more: Optional[bool] = None
    first_id: Optional[str] = None
    last_id: Optional[str] = None

class AsyncPage(BaseAsyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    has_more: Optional[bool] = None
    first_id: Optional[str] = None
    last_id: Optional[str] = None

class SyncTokenPage(BaseSyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    has_more: Optional[bool] = None
    next_page: Optional[str] = None

class AsyncTokenPage(BaseAsyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    has_more: Optional[bool] = None
    next_page: Optional[str] = None

class SyncPageCursor(BaseSyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    next_page: Optional[str] = None

class AsyncPageCursor(BaseAsyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    next_page: Optional[str] = None

class SyncBidirectionalPageCursor(BaseSyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    next_page: Optional[str] = None
    prev_page: Optional[str] = None

class AsyncBidirectionalPageCursor(BaseAsyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    next_page: Optional[str] = None
    prev_page: Optional[str] = None

class SyncReportPageCursor(BaseSyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    next_page: Optional[str] = None
    has_more: Optional[bool] = None
    data_refreshed_at: Optional[datetime] = None

class AsyncReportPageCursor(BaseAsyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    next_page: Optional[str] = None
    has_more: Optional[bool] = None
    data_refreshed_at: Optional[datetime] = None
