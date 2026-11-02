
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
from typing import Optional
from typing_extensions import Literal, Required, TypedDict

class BetaBrowserStateChangeDownloadFailedParam(TypedDict, total=False):
    """A file download that failed — or was cancelled — during this call."""
    download_id: Required[str]
    type: Required[Literal['download_failed']]
    url: Required[str]
    error: Optional[str]
