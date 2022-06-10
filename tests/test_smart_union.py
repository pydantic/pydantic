from typing import Literal

from pydantic.dataclasses import dataclass
from pydantic.smart_union import SmartUnion


@dataclass
class SuccessResponse:
    success: Literal[True]
 
@dataclass
class FailedResponse:
    success: Literal[False]
    failed_reason: str
 
 
Response = SmartUnion[SuccessResponse, FailedResponse]

def test_smart_union() -> None:
    assert isinstance(Response(**{"success": True}), SuccessResponse)
    assert isinstance(Response(**{"success": False, "failed_reason": "failed"}), FailedResponse)