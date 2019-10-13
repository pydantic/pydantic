from contextlib import contextmanager
import time
from datetime import datetime
from typing import List, Dict, Iterator

from pydantic import BaseModel


class DoubleNestedModel(BaseModel):
    number: int
    message: str


class SubDoubleNestedModel(DoubleNestedModel):
    timestamps: List[datetime]


class NestedModel(BaseModel):
    number: int
    message: str
    double_nested: DoubleNestedModel


class SubNestedModel(NestedModel):
    timestamps: List[datetime]


class Model(BaseModel):
    nested: List[Dict[str, NestedModel]]


class SubModel(Model):
    other_nested: Dict[str, List[NestedModel]]
    timestamps: List[datetime]


# "Secure cloned field" -- as currently implemented with FastAPI

class DoubleNestedModel2(BaseModel):
    number: int
    message: str


class NestedModel2(BaseModel):
    number: int
    message: str
    double_nested: DoubleNestedModel2


class Model2(BaseModel):
    nested: List[Dict[str, NestedModel2]]


def get_sub_model() -> SubModel:
    timestamp = datetime.utcnow()
    timestamps = [timestamp] * 5
    sub_double_nested = SubDoubleNestedModel(number=1, message="a", timestamps=timestamps)
    sub_nested = SubNestedModel(number=2, message="b", double_nested=sub_double_nested, timestamps=timestamps)

    nested = [{letter: sub_nested for letter in 'abcdefg'}]
    other_nested = {letter: [sub_nested] * 5 for letter in 'abcdefg'}
    return SubModel(nested=nested, other_nested=other_nested, timestamps=timestamps)


@contextmanager
def basic_profile(label: str) -> Iterator[None]:
    t0 = time.time()
    yield
    t1 = time.time()
    print(f"{label}: {(t1 - t0):,.3f}s")


def run():
    n_warmup_runs = 1000
    n_runs = 10000
    sub_model = get_sub_model()

    for _ in range(n_warmup_runs):
        sub_model.dict()

    with basic_profile("regular .dict()"):
        for _ in range(n_runs):
            sub_model.dict()

    with basic_profile("as_type .dict()"):
        for _ in range(n_runs):
            sub_model.dict(as_type=Model)

    with basic_profile("cloned field .dict()"):
        for _ in range(n_runs):
            Model2.parse_obj(sub_model).dict()


run()
