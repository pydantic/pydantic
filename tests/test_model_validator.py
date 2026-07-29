from __future__ import annotations

from typing import Any, cast

import pytest

from pydantic import (
    BaseModel,
    PydanticDeprecatedSince212,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    model_validator,
)


def test_model_validator_wrap() -> None:
    class Model(BaseModel):
        x: int
        y: int

        @model_validator(mode='wrap')
        @classmethod
        def val_model(cls, values: dict[str, Any] | Model, handler: ValidatorFunctionWrapHandler) -> Model:
            if isinstance(values, dict):
                assert values == {'x': 1, 'y': 2}
                model = handler({'x': 2, 'y': 3})
            else:
                assert values.x == 1
                assert values.y == 2
                model = handler(Model.model_construct(x=2, y=3))
            assert model.x == 2
            assert model.y == 3
            model.x = 20
            model.y = 30
            return model

    assert Model(x=1, y=2).model_dump() == {'x': 20, 'y': 30}
    assert Model.model_validate(Model.model_construct(x=1, y=2)).model_dump() == {'x': 20, 'y': 30}


@pytest.mark.parametrize('classmethod_decorator', [classmethod, lambda x: x])
def test_model_validator_before(classmethod_decorator: Any) -> None:
    class Model(BaseModel):
        x: int
        y: int

        @model_validator(mode='before')
        @classmethod_decorator
        def val_model(cls, values: Any, info: ValidationInfo) -> dict[str, Any] | Model:
            assert not info.context
            if isinstance(values, dict):
                values = cast(dict[str, Any], values)
                values['x'] += 1
                values['y'] += 1
            else:
                assert isinstance(values, Model)
                values.x += 1
                values.y += 1
            return values

    m = Model(x=1, y=2)
    assert m.model_dump() == {'x': 2, 'y': 3}
    # model not changed because we don't revalidate m
    assert Model.model_validate(m).model_dump() == {'x': 2, 'y': 3}


@pytest.mark.parametrize('classmethod_decorator', [classmethod, lambda x: x])
def test_model_validator_before_revalidate_always(classmethod_decorator: Any) -> None:
    class Model(BaseModel, revalidate_instances='always'):
        x: int
        y: int

        @model_validator(mode='before')
        @classmethod_decorator
        def val_model(cls, values: Any, info: ValidationInfo) -> dict[str, Any] | Model:
            assert not info.context
            if isinstance(values, dict):
                values = cast(dict[str, Any], values)
                values['x'] += 1
                values['y'] += 1
            else:
                assert isinstance(values, Model)
                values.x += 1
                values.y += 1
            return values

    assert Model(x=1, y=2).model_dump() == {'x': 2, 'y': 3}
    assert Model.model_validate(Model(x=1, y=2)).model_dump() == {'x': 3, 'y': 4}


def test_model_validator_after() -> None:
    class Model(BaseModel):
        x: int
        y: int

        @model_validator(mode='after')
        def val_model(self, info: ValidationInfo) -> Model:
            assert not info.context
            self.x += 1
            self.y += 1
            return self

    assert Model(x=1, y=2).model_dump() == {'x': 2, 'y': 3}
    assert Model.model_validate(Model(x=1, y=2)).model_dump() == {'x': 3, 'y': 4}


def test_subclass() -> None:
    class Human(BaseModel):
        @model_validator(mode='before')
        @classmethod
        def run_model_validator(cls, values: dict[str, Any]) -> dict[str, Any]:
            values['age'] *= 2
            return values

    class Person(Human):
        age: int

    assert Person(age=28).age == 56


def test_nested_models() -> None:
    calls: list[str] = []

    class Model(BaseModel):
        inner: Model | None

        @model_validator(mode='before')
        @classmethod
        def validate_model_before(cls, values: dict[str, Any]) -> dict[str, Any]:
            calls.append('before')
            return values

        @model_validator(mode='after')
        def validate_model_after(self) -> Model:
            calls.append('after')
            return self

    Model.model_validate({'inner': None})
    assert calls == ['before', 'after']
    calls.clear()

    Model.model_validate({'inner': {'inner': {'inner': None}}})
    assert calls == ['before'] * 3 + ['after'] * 3
    calls.clear()


def test_after_validator_wrong_signature() -> None:
    with pytest.warns(PydanticDeprecatedSince212):

        class Model1(BaseModel):
            @model_validator(mode='after')
            # This is converted into a class method, but deprecated
            # as it should be an instance method:
            def validator(cls, model, info: ValidationInfo):
                assert isinstance(model, cls)
                assert info.mode == 'python'
                return model

    with pytest.warns(PydanticDeprecatedSince212):

        class Model2(BaseModel):
            @model_validator(mode='after')
            # This is accepted as a class method, but deprecated
            # as it should be an instance method:
            @classmethod
            def validator(cls, model, info: ValidationInfo):
                assert isinstance(model, cls)
                assert info.mode == 'python'
                return model

    with pytest.warns(PydanticDeprecatedSince212):

        class Model3(BaseModel):
            @model_validator(mode='after')
            # This is converted into a class method, but deprecated
            # as it should be an instance method:
            def validator(cls, model):
                assert isinstance(model, cls)
                return model

    with pytest.warns(PydanticDeprecatedSince212):

        class Model4(BaseModel):
            @model_validator(mode='after')
            # This is accepted as a class method, but deprecated
            # as it should be an instance method:
            @classmethod
            def validator(cls, model):
                assert isinstance(model, cls)
                return model

    Model1()
    Model2()
    Model3()
    Model4()


def test_after_and_wrap_model_validators_run_once_when_reused_as_prebuilt() -> None:
    """`pydantic-core` reuses the already built ("prebuilt") validator of a completed model when other
    models reference it. `'after'`/`'wrap'` model validators are applied outside of the `model` core
    schema, and are compiled inline by the referencing model, so the prebuilt validator is stripped
    down to the inner `model` validator to avoid running the function validators twice.
    """
    after_calls: list[Any] = []
    wrap_calls: list[Any] = []

    class InnerAfter(BaseModel):
        x: int

        @model_validator(mode='after')
        def after_validator(self) -> InnerAfter:
            after_calls.append(self.x)
            return self

    class InnerWrap(BaseModel):
        x: int

        @model_validator(mode='wrap')
        @classmethod
        def wrap_validator(cls, data: Any, handler: ValidatorFunctionWrapHandler) -> InnerWrap:
            wrap_calls.append(data)
            return cast(InnerWrap, handler(data))

    class Outer(BaseModel):
        after: InnerAfter
        wrap: InnerWrap

    # the inner models' validators are reused, stripped of the model validators:
    assert repr(Outer.__pydantic_validator__).count('PrebuiltValidator') == 2

    Outer.model_validate({'after': {'x': 1}, 'wrap': {'x': 2}})
    assert after_calls == [1]
    assert wrap_calls == [{'x': 2}]


def test_model_config_isolated_when_validator_reused_as_prebuilt() -> None:
    """Nested validation delegating to a referenced model's prebuilt validator must apply the
    referenced model's own config, not the referencing model's (the `'model'` core schema carries
    its own `'config'`, so this also holds for inline compilation)."""
    from pydantic import ConfigDict, ValidationError

    class StrictChild(BaseModel):
        model_config = ConfigDict(strict=True)

        x: int

        @model_validator(mode='after')
        def validate_model(self) -> StrictChild:
            return self

    class LaxParent(BaseModel):
        model_config = ConfigDict(strict=False)

        child: StrictChild
        y: int

    assert 'PrebuiltValidator' in repr(LaxParent.__pydantic_validator__)

    # The parent's lax config still applies to its own fields:
    validated = LaxParent.model_validate({'child': {'x': 1}, 'y': '2'})
    assert validated.y == 2

    # The child's strict config applies to the child, even when nested in a lax parent:
    with pytest.raises(ValidationError, match='int_type'):
        LaxParent.model_validate({'child': {'x': '1'}, 'y': 2})

    class LaxChild(BaseModel):
        model_config = ConfigDict(strict=False)

        x: int

        @model_validator(mode='after')
        def validate_model(self) -> LaxChild:
            return self

    class StrictParent(BaseModel):
        model_config = ConfigDict(strict=True)

        child: LaxChild

    assert 'PrebuiltValidator' in repr(StrictParent.__pydantic_validator__)

    # The child's lax config applies to the child, even when nested in a strict parent:
    assert StrictParent.model_validate({'child': {'x': '1'}}).child.x == 1


def test_after_and_wrap_model_validators_run_once_when_recursive_model_reused_as_prebuilt() -> None:
    """A recursive model stores its schema in a core schema definition, making the root of its own
    validator a reference to that definition, with the `'after'`/`'wrap'` model validators inside
    the definition. The validator reused by a referencing model must still be the inner `model`
    validator, so that the model validators (compiled inline by the referencing model) run exactly
    once.

    This was broken before the reuse logic resolved definition references: the full prebuilt
    validator, including the model validators, was reused, running them a second time.
    """
    after_calls: list[Any] = []
    wrap_calls: list[Any] = []

    class NodeAfter(BaseModel):
        child: NodeAfter | None = None

        @model_validator(mode='after')
        def after_validator(self) -> NodeAfter:
            after_calls.append(None)
            return self

    class NodeWrap(BaseModel):
        child: NodeWrap | None = None

        @model_validator(mode='wrap')
        @classmethod
        def wrap_validator(cls, data: Any, handler: ValidatorFunctionWrapHandler) -> NodeWrap:
            wrap_calls.append(None)
            return cast(NodeWrap, handler(data))

    class Outer(BaseModel):
        after: NodeAfter
        wrap: NodeWrap

    # the recursive models' validators are still reused, stripped of the model validators:
    assert repr(Outer.__pydantic_validator__).count('PrebuiltValidator') == 2

    Outer.model_validate({'after': {}, 'wrap': {}})
    assert after_calls == [None]
    assert wrap_calls == [None]

    # the model validators also run exactly once per node of a nested input:
    after_calls.clear()
    wrap_calls.clear()
    Outer.model_validate({'after': {'child': {'child': {}}}, 'wrap': {'child': {}}})
    assert after_calls == [None] * 3
    assert wrap_calls == [None] * 2
