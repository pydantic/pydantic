
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
from typing import Optional
from typing_extensions import Literal, Required, TypedDict

class BetaBrowserStateChangeDownloadCompletedParam(TypedDict, total=False):
    """
    A file download that finished during this call, reported with the
    same `download_id` as its `download_started` — or without a prior
    `download_started`, when the download finished during the call that
    started it (at most one state change per `download_id` per result).
    """
    download_id: Required[str]
    type: Required[Literal['download_completed']]
    url: Required[str]
    path: Optional[str]
    size_bytes: Optional[int]
