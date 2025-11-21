from pydantic import BaseModel, computed_field, field_validator


def test_validators_build(benchmark) -> None:
    class Base1(BaseModel):
        a: int

        @field_validator('a', mode='after')
        @classmethod
        def val_a(cls, value: int) -> int: ...

        @computed_field
        def prop(self) -> int: ...

    class Bare:
        @computed_field
        def prop_bare(self) -> int: ...

    class Sub1(Base1):
        @computed_field
        def prop_2(self) -> int: ...

        @computed_field
        def prop_3(self) -> int: ...

        @computed_field
        def prop_4(self) -> int: ...

    @benchmark
    def bench() -> None:
        class SubS(Sub1, Bare, defer_build=True):
            @computed_field
            def prop_5(self) -> int: ...

            @computed_field
            def prop_6(self) -> int: ...

            @computed_field
            def prop_7(self) -> int: ...
