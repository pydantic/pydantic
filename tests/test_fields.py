from typing import Annotated, Any, Final, Union

import pytest
from annotated_types import Gt
from pydantic_core import PydanticUndefined
from typing_extensions import TypeAliasType

import pydantic.dataclasses
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    PydanticUserError,
    RootModel,
    ValidationError,
    computed_field,
    create_model,
    validate_call,
)
from pydantic.fields import FieldInfo
from pydantic.warnings import UnsupportedFieldAttributeWarning


def test_field_info_annotation_keyword_argument():
    """This tests that `FieldInfo.from_field` raises an error if passed the `annotation` kwarg.

    At the time of writing this test there is no way `FieldInfo.from_field` could receive the `annotation` kwarg from
    anywhere inside Pydantic code. However, it is possible that this API is still being in use by applications and
    third-party tools.
    """
    with pytest.raises(TypeError) as e:
        FieldInfo.from_field(annotation=())

    assert e.value.args == ('"annotation" is not permitted as a Field keyword argument',)


def test_field_info_annotated_attribute_name_clashing():
    """This tests that `FieldInfo.from_annotated_attribute` will raise a `PydanticUserError` if attribute names clashes
    with a type.
    """

    with pytest.raises(PydanticUserError):

        class SubModel(BaseModel):
            a: int = 1

        class Model(BaseModel):
            SubModel: SubModel = Field()


def test_init_var_field():
    @pydantic.dataclasses.dataclass
    class Foo:
        bar: str
        baz: str = Field(init_var=True)

    class Model(BaseModel):
        foo: Foo

    model = Model(foo=Foo('bar', baz='baz'))
    assert 'bar' in model.foo.__pydantic_fields__
    assert 'baz' not in model.foo.__pydantic_fields__


def test_root_model_arbitrary_field_name_error():
    with pytest.raises(
        NameError, match="Unexpected field with name 'a_field'; only 'root' is allowed as a field of a `RootModel`"
    ):

        class Model(RootModel[int]):
            a_field: str


def test_root_model_arbitrary_private_field_works():
    class Model(RootModel[int]):
        _a_field: str = 'value 1'

    m = Model(1)
    assert m._a_field == 'value 1'

    m._a_field = 'value 2'
    assert m._a_field == 'value 2'


def test_root_model_field_override():
    # Weird as this is, I think it's probably best to allow it to ensure it is possible to override
    # the annotation in subclasses of RootModel subclasses. Basically, I think retaining the flexibility
    # is worth the increased potential for weird/confusing "accidental" overrides.

    # I'm mostly including this test now to document the behavior
    class Model(RootModel[int]):
        root: str

    assert Model.model_validate('abc').root == 'abc'
    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate(1)
    assert exc_info.value.errors(include_url=False) == [
        {'input': 1, 'loc': (), 'msg': 'Input should be a valid string', 'type': 'string_type'}
    ]

    class SubModel(Model):
        root: float

    with pytest.raises(ValidationError) as exc_info:
        SubModel.model_validate('abc')
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'abc',
            'loc': (),
            'msg': 'Input should be a valid number, unable to parse string as a number',
            'type': 'float_parsing',
        }
    ]

    validated = SubModel.model_validate_json('1').root
    assert validated == 1.0
    assert isinstance(validated, float)


def test_frozen_field_repr():
    class Model(BaseModel):
        non_frozen_field: int = Field(frozen=False)
        frozen_field: int = Field(frozen=True)

    assert repr(Model.model_fields['non_frozen_field']) == 'FieldInfo(annotation=int, required=True)'
    assert repr(Model.model_fields['frozen_field']) == 'FieldInfo(annotation=int, required=True, frozen=True)'


def test_model_field_default_info():
    """Test that __repr_args__ of FieldInfo includes the default value when it's set to None."""

    class Model(BaseModel):
        a: Union[int, None] = Field(default=None)
        b: Union[int, None] = None

    assert str(Model.model_fields) == (
        "{'a': FieldInfo(annotation=Union[int, NoneType], required=False, default=None), "
        "'b': FieldInfo(annotation=Union[int, NoneType], required=False, default=None)}"
    )


def test_computed_field_raises_correct_attribute_error():
    class Model(BaseModel):
        model_config = ConfigDict(extra='allow')

        @computed_field
        def comp_field(self) -> str:
            raise AttributeError('Computed field attribute error')

        @property
        def prop_field(self):
            raise AttributeError('Property attribute error')

    with pytest.raises(AttributeError, match='Computed field attribute error'):
        Model().comp_field

    with pytest.raises(AttributeError, match='Property attribute error'):
        Model().prop_field

    with pytest.raises(AttributeError, match='Property attribute error'):
        Model(some_extra_field='some value').prop_field

    with pytest.raises(AttributeError, match=f"'{Model.__name__}' object has no attribute 'invalid_field'"):
        Model().invalid_field


@pytest.mark.parametrize('number', (1, 42, 443, 11.11, 0.553))
def test_coerce_numbers_to_str_field_option(number):
    class Model(BaseModel):
        field: str = Field(coerce_numbers_to_str=True, max_length=10)

    assert Model(field=number).field == str(number)


@pytest.mark.parametrize('number', (1, 42, 443, 11.11, 0.553))
def test_coerce_numbers_to_str_field_precedence(number):
    class Model(BaseModel):
        model_config = ConfigDict(coerce_numbers_to_str=True)

        field: str = Field(coerce_numbers_to_str=False)

    with pytest.raises(ValidationError):
        Model(field=number)

    class Model(BaseModel):
        model_config = ConfigDict(coerce_numbers_to_str=False)

        field: str = Field(coerce_numbers_to_str=True)

    assert Model(field=number).field == str(number)


def test_rebuild_model_fields_preserves_description() -> None:
    """https://github.com/pydantic/pydantic/issues/11696"""

    class Model(BaseModel):
        model_config = ConfigDict(use_attribute_docstrings=True)

        f: 'Int'
        """test doc"""

    assert Model.model_fields['f'].description == 'test doc'

    Int = int

    Model.model_rebuild()

    assert Model.model_fields['f'].description == 'test doc'


def test_final_to_frozen_with_assignment() -> None:
    class Model(BaseModel):
        # A buggy implementation made it so that `frozen` wouldn't
        # be set on the `FieldInfo`:
        b: Annotated[Final[int], ...] = Field(alias='test')

    assert Model.model_fields['b'].frozen


def test_metadata_preserved_with_assignment() -> None:
    def func1(v):
        pass

    def func2(v):
        pass

    class Model(BaseModel):
        # A buggy implementation made it so that the first validator
        # would be dropped:
        a: Annotated[int, AfterValidator(func1), Field(gt=1), AfterValidator(func2)] = Field(...)

    metadata = Model.model_fields['a'].metadata

    assert isinstance(metadata[0], AfterValidator)
    assert isinstance(metadata[1], Gt)
    assert isinstance(metadata[2], AfterValidator)


def test_reused_field_not_mutated() -> None:
    """https://github.com/pydantic/pydantic/issues/11876"""

    Ann = Annotated[int, Field()]

    class Foo(BaseModel):
        f: Ann = 50

    class Bar(BaseModel):
        f: Annotated[Ann, Field()]

    assert Bar.model_fields['f'].default is PydanticUndefined


def test_no_duplicate_metadata_with_assignment_and_rebuild() -> None:
    """https://github.com/pydantic/pydantic/issues/11870"""

    class Model(BaseModel):
        f: Annotated['Int', Gt(1)] = Field()

    Int = int

    Model.model_rebuild()

    assert len(Model.model_fields['f'].metadata) == 1


def test_fastapi_compatibility_hack() -> None:
    class Body(FieldInfo):
        """A reproduction of the FastAPI's `Body` param."""

    field = Body()
    # Assigning after doesn't update `_attributes_set`, which is currently
    # relied on to merge `FieldInfo` instances during field creation.
    # This is also what the FastAPI code is doing in some places.
    # The FastAPI compatibility hack makes it so that it still works.
    field.default = 1

    Model = create_model('Model', f=(int, field))
    model_field = Model.model_fields['f']

    assert isinstance(model_field, Body)
    assert not model_field.is_required()


_unsupported_standalone_fieldinfo_attributes = (
    ('alias', 'alias'),
    ('validation_alias', 'alias'),
    ('serialization_alias', 'alias'),
    ('default', 1),
    ('default_factory', lambda: 1),
    ('exclude', True),
    ('deprecated', True),
    ('repr', False),
    ('validate_default', True),
    ('frozen', True),
    ('init', True),
    ('init_var', True),
    ('kw_only', True),
)


@pytest.mark.parametrize(
    ['attribute', 'value'],
    _unsupported_standalone_fieldinfo_attributes,
)
def test_unsupported_field_attribute_type_alias(attribute: str, value: Any) -> None:
    TestType = TypeAliasType('TestType', Annotated[int, Field(**{attribute: value})])

    with pytest.warns(UnsupportedFieldAttributeWarning):

        class Model(BaseModel):
            f: TestType


@pytest.mark.parametrize(
    ['attribute', 'value'],
    _unsupported_standalone_fieldinfo_attributes,
)
def test_unsupported_field_attribute_nested(attribute: str, value: Any) -> None:
    TestType = TypeAliasType('TestType', Annotated[int, Field(**{attribute: value})])

    with pytest.warns(UnsupportedFieldAttributeWarning):

        class Model(BaseModel):
            f: list[TestType]


@pytest.mark.parametrize(
    ['attribute', 'value'],
    [
        (attr, value)
        for attr, value in _unsupported_standalone_fieldinfo_attributes
        if attr not in ('default', 'default_factory')
    ],
)
def test_unsupported_field_attribute_nested_with_function(attribute: str, value: Any) -> None:
    TestType = TypeAliasType('TestType', Annotated[int, Field(**{attribute: value})])

    with pytest.warns(UnsupportedFieldAttributeWarning):

        @validate_call
        def func(a: list[TestType]) -> None:
            return None
