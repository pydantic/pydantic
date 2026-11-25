# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Optional
from typing_extensions import Literal
from ...._models import BaseModel
from ..eval_api_error import EvalAPIError

class Result(BaseModel):
    """A single grader result for an evaluation run output item."""
    name: str
    passed: bool
    score: float
    sample: Optional[Dict[str, object]] = None
    type: Optional[str] = None
    __pydantic_extra__: Dict[str, object]

class SampleInput(BaseModel):
    """An input message."""
    content: str
    role: str

class SampleOutput(BaseModel):
    content: Optional[str] = None
    role: Optional[str] = None

class SampleUsage(BaseModel):
    """Token usage details for the sample."""
    cached_tokens: int
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int

class Sample(BaseModel):
    """A sample containing the input and output of the evaluation run."""
    error: EvalAPIError
    finish_reason: str
    input: List[SampleInput]
    max_completion_tokens: int
    model: str
    output: List[SampleOutput]
    seed: int
    temperature: float
    top_p: float
    usage: SampleUsage

class OutputItemRetrieveResponse(BaseModel):
    """A schema representing an evaluation run output item."""
    id: str
    created_at: int
    datasource_item: Dict[str, object]
    datasource_item_id: int
    eval_id: str
    object: Literal['eval.run.output_item']
    results: List[Result]
    run_id: str
    sample: Sample
    status: str
