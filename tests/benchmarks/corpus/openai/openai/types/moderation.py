# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from pydantic import Field as FieldInfo
from .._models import BaseModel

class Categories(BaseModel):
    """A list of the categories, and whether they are flagged or not."""
    harassment: bool
    harassment_threatening: bool = FieldInfo(alias='harassment/threatening')
    hate: bool
    hate_threatening: bool = FieldInfo(alias='hate/threatening')
    illicit: Optional[bool] = None
    illicit_violent: Optional[bool] = FieldInfo(alias='illicit/violent', default=None)
    self_harm: bool = FieldInfo(alias='self-harm')
    self_harm_instructions: bool = FieldInfo(alias='self-harm/instructions')
    self_harm_intent: bool = FieldInfo(alias='self-harm/intent')
    sexual: bool
    sexual_minors: bool = FieldInfo(alias='sexual/minors')
    violence: bool
    violence_graphic: bool = FieldInfo(alias='violence/graphic')

class CategoryAppliedInputTypes(BaseModel):
    """
    A list of the categories along with the input type(s) that the score applies to.
    """
    harassment: List[Literal['text']]
    harassment_threatening: List[Literal['text']] = FieldInfo(alias='harassment/threatening')
    hate: List[Literal['text']]
    hate_threatening: List[Literal['text']] = FieldInfo(alias='hate/threatening')
    illicit: List[Literal['text']]
    illicit_violent: List[Literal['text']] = FieldInfo(alias='illicit/violent')
    self_harm: List[Literal['text', 'image']] = FieldInfo(alias='self-harm')
    self_harm_instructions: List[Literal['text', 'image']] = FieldInfo(alias='self-harm/instructions')
    self_harm_intent: List[Literal['text', 'image']] = FieldInfo(alias='self-harm/intent')
    sexual: List[Literal['text', 'image']]
    sexual_minors: List[Literal['text']] = FieldInfo(alias='sexual/minors')
    violence: List[Literal['text', 'image']]
    violence_graphic: List[Literal['text', 'image']] = FieldInfo(alias='violence/graphic')

class CategoryScores(BaseModel):
    """A list of the categories along with their scores as predicted by model."""
    harassment: float
    harassment_threatening: float = FieldInfo(alias='harassment/threatening')
    hate: float
    hate_threatening: float = FieldInfo(alias='hate/threatening')
    illicit: float
    illicit_violent: float = FieldInfo(alias='illicit/violent')
    self_harm: float = FieldInfo(alias='self-harm')
    self_harm_instructions: float = FieldInfo(alias='self-harm/instructions')
    self_harm_intent: float = FieldInfo(alias='self-harm/intent')
    sexual: float
    sexual_minors: float = FieldInfo(alias='sexual/minors')
    violence: float
    violence_graphic: float = FieldInfo(alias='violence/graphic')

class Moderation(BaseModel):
    categories: Categories
    category_applied_input_types: CategoryAppliedInputTypes
    category_scores: CategoryScores
    flagged: bool
