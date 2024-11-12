from pydantic import BaseModel


class ModelV2(BaseModel):
    my_str: str


mv2 = ModelV2(my_str='hello')


def test_isinstance_basemodel(benchmark) -> None:
    @benchmark
    def run():
        for _ in range(10000):
            assert isinstance(mv2, BaseModel)
