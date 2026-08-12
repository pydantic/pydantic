from pydantic import BaseModel, computed_field


def test_field_title_generator_inheritance():
    class Model(BaseModel, field_title_generator=lambda v, _: v + 'a'):
        a: int

        @computed_field
        def c(self) -> int:
            return 1

    class Sub(Model, field_title_generator=lambda v, _: v + 'b'):
        b: int

        @computed_field
        def d(self) -> int:
            return 2

    assert Sub.model_fields['a'].title == 'ab'
    assert Sub.model_fields['b'].title == 'bb'
    assert Sub.model_computed_fields['c'].title == 'cb'
    assert Sub.model_computed_fields['d'].title == 'db'
