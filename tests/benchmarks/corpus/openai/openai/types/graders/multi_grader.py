# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel
from .python_grader import PythonGrader
from .label_model_grader import LabelModelGrader
from .score_model_grader import ScoreModelGrader
from .string_check_grader import StringCheckGrader
from .text_similarity_grader import TextSimilarityGrader
Graders: TypeAlias = Union[StringCheckGrader, TextSimilarityGrader, PythonGrader, ScoreModelGrader, LabelModelGrader]

class MultiGrader(BaseModel):
    """
    A MultiGrader object combines the output of multiple graders to produce a single score.
    """
    calculate_output: str
    graders: Graders
    name: str
    type: Literal['multi']
