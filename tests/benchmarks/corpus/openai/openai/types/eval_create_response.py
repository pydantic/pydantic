# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from pydantic import Field as FieldInfo
from .._utils import PropertyInfo
from .._models import BaseModel
from .shared.metadata import Metadata
from .graders.python_grader import PythonGrader
from .graders.label_model_grader import LabelModelGrader
from .graders.score_model_grader import ScoreModelGrader
from .graders.string_check_grader import StringCheckGrader
from .eval_custom_data_source_config import EvalCustomDataSourceConfig
from .graders.text_similarity_grader import TextSimilarityGrader
from .eval_stored_completions_data_source_config import EvalStoredCompletionsDataSourceConfig

class DataSourceConfigLogs(BaseModel):
    """
    A LogsDataSourceConfig which specifies the metadata property of your logs query.
    This is usually metadata like `usecase=chatbot` or `prompt-version=v2`, etc.
    The schema returned by this data source config is used to defined what variables are available in your evals.
    `item` and `sample` are both defined when using this data source config.
    """
    schema_: Dict[str, object] = FieldInfo(alias='schema')
    type: Literal['logs']
    metadata: Optional[Metadata] = None
DataSourceConfig: TypeAlias = Annotated[Union[EvalCustomDataSourceConfig, DataSourceConfigLogs, EvalStoredCompletionsDataSourceConfig], PropertyInfo(discriminator='type')]

class TestingCriterionEvalGraderTextSimilarity(TextSimilarityGrader):
    __test__ = False
    pass_threshold: float

class TestingCriterionEvalGraderPython(PythonGrader):
    __test__ = False
    pass_threshold: Optional[float] = None

class TestingCriterionEvalGraderScoreModel(ScoreModelGrader):
    __test__ = False
    pass_threshold: Optional[float] = None
TestingCriterion: TypeAlias = Union[LabelModelGrader, StringCheckGrader, TestingCriterionEvalGraderTextSimilarity, TestingCriterionEvalGraderPython, TestingCriterionEvalGraderScoreModel]

class EvalCreateResponse(BaseModel):
    """
    An Eval object with a data source config and testing criteria.
    An Eval represents a task to be done for your LLM integration.
    Like:
     - Improve the quality of my chatbot
     - See how well my chatbot handles customer support
     - Check if o4-mini is better at my usecase than gpt-6-astra
    """
    id: str
    created_at: int
    data_source_config: DataSourceConfig
    metadata: Optional[Metadata] = None
    name: str
    object: Literal['eval']
    testing_criteria: List[TestingCriterion]
