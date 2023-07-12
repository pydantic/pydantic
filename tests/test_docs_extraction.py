from typing_extensions import Annotated, TypedDict

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from pydantic.dataclasses import dataclass as pydantic_dataclass


def test_model_no_docs_extraction():
    class Model(BaseModel):
        a: int = 1
        """A docs"""

        b: str = '1'

        """B docs"""

    assert Model.model_fields['a'].description is None
    assert Model.model_fields['b'].description is None


def test_model_docs_extraction():
    class Model(BaseModel):
        a: int
        """A docs"""
        b: int = 1

        """B docs"""
        c: int = 1
        # This isn't used as a description.

        d: int

        def dummy_method(self) -> None:
            """Docs for dummy that wont be used for d"""

        e: Annotated[int, Field(description='Real description')]
        """Won't be used"""

        f: int
        """F docs"""

        """Useless docs"""

        g: int
        """G docs"""

        model_config = ConfigDict(
            use_attributes_docstring=True,
        )

    assert Model.model_fields['a'].description == 'A docs'
    assert Model.model_fields['b'].description == 'B docs'
    assert Model.model_fields['c'].description is None
    assert Model.model_fields['d'].description is None
    assert Model.model_fields['e'].description == 'Real description'
    assert Model.model_fields['g'].description == 'G docs'


def test_dataclass_no_docs_extraction():
    @pydantic_dataclass
    class Model:
        a: int = 1
        """A docs"""

        b: str = '1'

        """B docs"""

    assert Model.__pydantic_fields__['a'].description is None
    assert Model.__pydantic_fields__['b'].description is None


def test_dataclass_docs_extraction():
    @pydantic_dataclass(config=ConfigDict(use_attributes_docstring=True))
    class Model:
        a: int
        """A docs"""
        b: int = 1

        """B docs"""
        c: int = 1
        # This isn't used as a description.

        d: int

        def dummy_method(self) -> None:
            """Docs for dummy that wont be used for d"""

        e: int = Field(1, description='Real description')
        """Won't be used"""

        f: int
        """F docs"""

        """Useless docs"""

        g: int
        """G docs"""

        h = 1
        """H docs"""

        i: Annotated[int, Field(description='Real description')]
        """Won't be used"""

    assert Model.__pydantic_fields__['a'].description == 'A docs'
    assert Model.__pydantic_fields__['b'].description == 'B docs'
    assert Model.__pydantic_fields__['c'].description is None
    assert Model.__pydantic_fields__['d'].description is None
    assert Model.__pydantic_fields__['e'].description == 'Real description'
    assert Model.__pydantic_fields__['g'].description == 'G docs'
    assert Model.__pydantic_fields__['i'].description == 'Real description'  # TODO What is happening here?
    # Annotated[..., Field(...)] doesn't seem to work for dataclasses


def test_typeddict():
    class Model(TypedDict):
        a: int
        """A docs"""

    ta = TypeAdapter(Model)
    assert ta.json_schema() == {
        'properties': {'a': {'title': 'A', 'type': 'integer'}},
        'required': ['a'],
        'title': 'Model',
        'type': 'object',
    }

    class Model(TypedDict):
        a: int
        """A docs"""

        __pydantic_config__ = ConfigDict(use_attributes_docstring=True)

    assert ta.json_schema() == {
        'properties': {'a': {'title': 'A', 'type': 'integer', 'description': 'A docs'}},
        'required': ['a'],
        'title': 'Model',
        'type': 'object',
    }
