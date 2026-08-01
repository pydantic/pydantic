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


def test_model_validator_outer_ordering() -> None:
    calls: list[str] = []

    class Model(BaseModel):
        x: int

        @model_validator(mode='before')
        @classmethod
        def val_before(cls, values: Any) -> Any:
            calls.append('before')
            return values

        @model_validator(mode='wrap')
        @classmethod
        def val_wrap(cls, values: Any, handler: ValidatorFunctionWrapHandler) -> Any:
            calls.append('wrap_enter')
            res = handler(values)
            calls.append('wrap_exit')
            return res

        @model_validator(mode='after')
        def val_after(self) -> Model:
            calls.append('after')
            return self

        @model_validator(mode='outer')
        @classmethod
        def val_outer(cls, values: Any, handler: ValidatorFunctionWrapHandler) -> Any:
            calls.append('outer_enter')
            res = handler(values)
            calls.append('outer_exit')
            return res

    Model(x=1)
    assert calls == ['outer_enter', 'wrap_enter', 'before', 'wrap_exit', 'after', 'outer_exit']


def test_model_validator_outer_catches_after_error() -> None:
    from pydantic import ValidationError

    caught_errors: list[str] = []

    class Model(BaseModel):
        x: int

        @model_validator(mode='after')
        def val_after(self) -> Model:
            if self.x < 0:
                raise ValueError('x must be non-negative')
            return self

        @model_validator(mode='outer')
        @classmethod
        def val_outer(cls, values: Any, handler: ValidatorFunctionWrapHandler) -> Any:
            try:
                return handler(values)
            except ValidationError as e:
                caught_errors.append(e.errors()[0]['msg'])
                raise

    with pytest.raises(ValidationError):
        Model(x=-1)

    assert caught_errors == ['Value error, x must be non-negative']


def test_model_validator_outer_inheritance() -> None:
    calls: list[str] = []

    class Base(BaseModel):
        @model_validator(mode='outer')
        @classmethod
        def base_outer(cls, values: Any, handler: ValidatorFunctionWrapHandler) -> Any:
            calls.append('base_outer_enter')
            res = handler(values)
            calls.append('base_outer_exit')
            return res

    class Child(Base):
        x: int

        @model_validator(mode='after')
        def child_after(self) -> Child:
            calls.append('child_after')
            return self

    Child(x=1)
    assert calls == ['base_outer_enter', 'child_after', 'base_outer_exit']


def test_model_validator_outer_nested() -> None:
    from pydantic import ValidationError

    error_locs: list[tuple[str | int, ...]] = []

    class Inner(BaseModel):
        val: int

    class Outer(BaseModel):
        inner: Inner

        @model_validator(mode='outer')
        @classmethod
        def outer_val(cls, values: Any, handler: ValidatorFunctionWrapHandler) -> Any:
            try:
                return handler(values)
            except ValidationError as e:
                error_locs.extend(err['loc'] for err in e.errors())
                raise

    with pytest.raises(ValidationError):
        Outer(inner={'val': 'invalid'})

    assert error_locs == [('inner', 'val')]


def test_model_validator_outer_root_model() -> None:
    from pydantic import RootModel

    calls: list[str] = []

    class MyRoot(RootModel[int]):
        @model_validator(mode='after')
        def root_after(self) -> MyRoot:
            calls.append('root_after')
            return self

        @model_validator(mode='outer')
        @classmethod
        def root_outer(cls, values: Any, handler: ValidatorFunctionWrapHandler) -> Any:
            calls.append('root_outer_enter')
            res = handler(values)
            calls.append('root_outer_exit')
            return res

    r = MyRoot(42)
    assert r.root == 42
    assert calls == ['root_outer_enter', 'root_after', 'root_outer_exit']


def test_model_validator_outer_generic_model() -> None:
    from typing import Generic, TypeVar

    T = TypeVar('T')
    calls: list[str] = []

    class GenericModel(BaseModel, Generic[T]):
        value: T

        @model_validator(mode='after')
        def generic_after(self) -> GenericModel[T]:
            calls.append('generic_after')
            return self

        @model_validator(mode='outer')
        @classmethod
        def generic_outer(cls, values: Any, handler: ValidatorFunctionWrapHandler) -> Any:
            calls.append('generic_outer_enter')
            res = handler(values)
            calls.append('generic_outer_exit')
            return res

    m = GenericModel[int](value=10)
    assert m.value == 10
    assert calls == ['generic_outer_enter', 'generic_after', 'generic_outer_exit']


def test_model_validator_outer_multiple() -> None:
    calls: list[str] = []

    class Model(BaseModel):
        x: int

        @model_validator(mode='outer')
        @classmethod
        def outer1(cls, values: Any, handler: ValidatorFunctionWrapHandler) -> Any:
            calls.append('outer1_enter')
            res = handler(values)
            calls.append('outer1_exit')
            return res

        @model_validator(mode='outer')
        @classmethod
        def outer2(cls, values: Any, handler: ValidatorFunctionWrapHandler) -> Any:
            calls.append('outer2_enter')
            res = handler(values)
            calls.append('outer2_exit')
            return res

    Model(x=1)
    assert calls == ['outer2_enter', 'outer1_enter', 'outer1_exit', 'outer2_exit']


def test_model_validator_outer_validation_info() -> None:
    info_received: list[dict[str, Any]] = []

    class Model(BaseModel):
        x: int

        @model_validator(mode='outer')
        @classmethod
        def val_outer(cls, values: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> Any:
            info_received.append({'mode': info.mode, 'context': info.context})
            return handler(values)

    Model.model_validate({'x': 1}, context={'foo': 'bar'})
    assert info_received == [{'mode': 'python', 'context': {'foo': 'bar'}}]


def test_model_validator_outer_serializer_interaction() -> None:
    from pydantic import model_serializer

    calls: list[str] = []

    class Model(BaseModel):
        x: int

        @model_validator(mode='outer')
        @classmethod
        def val_outer(cls, values: Any, handler: ValidatorFunctionWrapHandler) -> Any:
            calls.append('outer')
            return handler(values)

        @model_serializer
        def ser(self) -> dict[str, int]:
            calls.append('serializer')
            return {'x': self.x * 2}

    m = Model(x=5)
    assert calls == ['outer']
    dumped = m.model_dump()
    assert dumped == {'x': 10}
    assert calls == ['outer', 'serializer']
