from pydantic import BaseModel, create_model

ModelNoExtra = create_model(
    'ModelNoExtra',
    __config__={'extra': 'forbid'},
    **{f'f{i}': (int, i) for i in range(30)},  # pyright: ignore
)

ModelExtra = create_model(
    'ModelNoExtra',
    __config__={'extra': 'allow'},
    **{f'f{i}': (int, i) for i in range(30)},  # pyright: ignore
)


def model_eq(m1: BaseModel, m2: BaseModel) -> bool:
    return m1 == m2


def test_model_eq_extra_forbid(benchmark) -> None:
    m1 = ModelNoExtra()
    m2 = ModelNoExtra()

    benchmark(model_eq, m1, m2)


def test_model_eq_extra_allow_no_extra(benchmark) -> None:
    m1 = ModelExtra()
    m2 = ModelExtra()

    benchmark(model_eq, m1, m2)


def test_model_eq_extra_allow_extra(benchmark) -> None:
    m1 = ModelExtra(extra1='test', extra2='other', extra3=2)
    m2 = ModelExtra(extra1='test', extra2='other', extra3=2)

    benchmark(model_eq, m1, m2)
