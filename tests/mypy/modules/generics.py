from typing import Any, Generic, Optional, TypeVar

from typing_extensions import assert_type

from pydantic import BaseModel

Tbody = TypeVar('Tbody')


class Response(BaseModel, Generic[Tbody]):
    url: str
    body: Tbody


class JsonBody(BaseModel):
    raw: str
    data: dict[str, Any]


class HtmlBody(BaseModel):
    raw: str
    doctype: str


class JsonResponse(Response[JsonBody]):
    pass


class HtmlResponse(Response[HtmlBody]):
    def custom_method(self) -> None:
        doctype = self.body.doctype
        print(f'self: {doctype}')


example = {'url': 'foo.com', 'body': {'raw': '..<html>..', 'doctype': 'html'}}

resp = HtmlResponse.model_validate(example)
resp.custom_method()

assert_type(resp.body, HtmlBody)


T = TypeVar('T', int, str)


class HistoryField(BaseModel, Generic[T]):
    value: Optional[T]


class DomainType(HistoryField[int]):
    pass


thing = DomainType(value=None)
assert_type(thing.value, Optional[int])
