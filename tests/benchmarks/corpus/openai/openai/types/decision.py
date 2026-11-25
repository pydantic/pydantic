# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from pydantic import StrictStr, StrictBool
from .._utils import PropertyInfo
from .._models import BaseModel

class AnswerAnswerResourcePredicate(BaseModel):
    name: Optional[str] = None
    probability: float
    type: Literal['predicate']

class AnswerAnswerResourceChoiceProbability(BaseModel):
    probability: float
    value: Union[StrictStr, StrictBool]

class AnswerAnswerResourceChoice(BaseModel):
    choice: Union[StrictStr, StrictBool]
    confidence: float
    name: Optional[str] = None
    probabilities: List[AnswerAnswerResourceChoiceProbability]
    type: Literal['choice']

class AnswerAnswerResourceScoreProbability(BaseModel):
    label: str
    probability: float
    value: int

class AnswerAnswerResourceScore(BaseModel):
    confidence: float
    name: Optional[str] = None
    probabilities: List[AnswerAnswerResourceScoreProbability]
    score: float
    type: Literal['score']

class AnswerAnswerResourceRefusal(BaseModel):
    """The model declined to answer this question.

    Other questions in the same request can still receive answers.
    """
    name: Optional[str] = None
    type: Literal['refusal']
Answer: TypeAlias = Annotated[Union[AnswerAnswerResourcePredicate, AnswerAnswerResourceChoice, AnswerAnswerResourceScore, AnswerAnswerResourceRefusal], PropertyInfo(discriminator='type')]

class UsageInputTokensDetails(BaseModel):
    cache_write_tokens: int
    cached_tokens: int

class UsageOutputTokensDetails(BaseModel):
    reasoning_tokens: int

class Usage(BaseModel):
    """Token usage for the request."""
    input_tokens: int
    input_tokens_details: UsageInputTokensDetails
    output_tokens: int
    output_tokens_details: UsageOutputTokensDetails
    total_tokens: int

class Decision(BaseModel):
    answers: List[Answer]
    model: str
    usage: Usage
