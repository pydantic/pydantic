from typing_extensions import Annotated, TypedDict

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from pydantic.dataclasses import dataclass as pydantic_dataclass


def test_model_no_docs_extraction():
    class ModelNoDocs(BaseModel):
        a: int = 1
        """A docs"""

        b: str = '1'

        """B docs"""

    assert ModelNoDocs.model_fields['a'].description is None
    assert ModelNoDocs.model_fields['b'].description is None


def test_model_docs_extraction():
    class ModelDocs(BaseModel):
        a: int
        """A docs"""
        b: int = 1

        """B docs"""
        c: int = 1
        # This isn't used as a description.

        d: int

        def dummy_method(self) -> None:
            """Docs for dummy that won't be used for d"""

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

    assert ModelDocs.model_fields['a'].description == 'A docs'
    assert ModelDocs.model_fields['b'].description == 'B docs'
    assert ModelDocs.model_fields['c'].description is None
    assert ModelDocs.model_fields['d'].description is None
    assert ModelDocs.model_fields['e'].description == 'Real description'
    assert ModelDocs.model_fields['g'].description == 'G docs'


def test_dataclass_no_docs_extraction():
    @pydantic_dataclass
    class ModelDCNoDocs:
        a: int = 1
        """A docs"""

        b: str = '1'

        """B docs"""

    assert ModelDCNoDocs.__pydantic_fields__['a'].description is None
    assert ModelDCNoDocs.__pydantic_fields__['b'].description is None


def test_dataclass_docs_extraction():
    @pydantic_dataclass(config=ConfigDict(use_attributes_docstring=True))
    class ModelDCDocs:
        a: int
        """A docs"""
        b: int = 1

        """B docs"""
        c: int = 1
        # This isn't used as a description.

        d: int = 1

        def dummy_method(self) -> None:
            """Docs for dummy_method that won't be used for d"""

        e: int = Field(1, description='Real description')
        """Won't be used"""

        f: int = 1
        """F docs"""

        """Useless docs"""

        g: int = 1
        """G docs"""

        h = 1
        """H docs"""

        i: Annotated[int, Field(description='Real description')] = 1
        """Won't be used"""

    assert ModelDCDocs.__pydantic_fields__['a'].description == 'A docs'
    assert ModelDCDocs.__pydantic_fields__['b'].description == 'B docs'
    assert ModelDCDocs.__pydantic_fields__['c'].description is None
    assert ModelDCDocs.__pydantic_fields__['d'].description is None
    assert ModelDCDocs.__pydantic_fields__['e'].description == 'Real description'
    assert ModelDCDocs.__pydantic_fields__['g'].description == 'G docs'
    assert ModelDCDocs.__pydantic_fields__['i'].description == 'Real description'


def test_typeddict():
    class ModelTDNoDocs(TypedDict):
        a: int
        """A docs"""

    ta = TypeAdapter(ModelTDNoDocs)
    assert ta.json_schema() == {
        'properties': {'a': {'title': 'A', 'type': 'integer'}},
        'required': ['a'],
        'title': 'ModelTDNoDocs',
        'type': 'object',
    }

    class ModelTDDocs(TypedDict):
        a: int
        """A docs"""

        __pydantic_config__ = ConfigDict(use_attributes_docstring=True)

    ta = TypeAdapter(ModelTDDocs)

    assert ta.json_schema() == {
        'properties': {'a': {'title': 'A', 'type': 'integer', 'description': 'A docs'}},
        'required': ['a'],
        'title': 'ModelTDDocs',
        'type': 'object',
    }


def test_typeddict_as_field():
    class ModelTDAsField(TypedDict):
        a: int
        """A docs"""

        __pydantic_config__ = ConfigDict(use_attributes_docstring=True)

    class ModelWithTDField(BaseModel):
        td: ModelTDAsField

    a_property = ModelWithTDField.model_json_schema()['$defs']['ModelTDAsField']['properties']['a']
    assert a_property['description'] == 'A docs'
