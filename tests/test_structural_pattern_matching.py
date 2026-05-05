from pydantic import BaseModel


def test_match_kwargs():

    class Model(BaseModel):
        a: str
        b: str

    def main(model):
        match model:
            case Model(a='a', b=b):
                return b
            case Model(a='a2'):
                return 'b2'
            case _:
                return None

    assert main(Model(a='a', b='b')) == 'b'
    assert main(Model(a='a2', b='b')) == 'b2'
    assert main(Model(a='x', b='b')) is None
