from typing import Any, Dict, Generator, Set, Union, Optional, Type
import pathlib


class Required:
    pass


class BaseModel(object):
    fields: Dict
    config: type

    def __init__(self, **values: Any) -> None: ...

    def construct(self, **values: Any) -> 'BaseModel': ...

    def copy(self, include:Optional[Set[str]]=None,
             exclude:Optional[Set[str]]=None,
             update:Optional[Dict[str, Any]]=None) -> 'BaseModel': ...

    def dict(self, include:Optional[Set[str]]=None,
             exclude:Set[str]=set()) -> Dict[str, Any]: ...

    def get_validators(self) -> Generator: ...

    def parse_file(self, path:Union[str, pathlib.Path], *,
                   content_type:Optional[str]=None, encoding:str='utf8',
                   proto:Any=None,
                   allow_pickle:Optional[bool]=False) -> Any: ...

    def parse_obj(self, obj: Any) -> Any: ...

    def parse_raw(self, b:Union[str, bytes], content_type:Optional[str]=None,
                  encoding:str='utf8', proto:Any=None,
                  allow_pickle:bool=False) -> Any: ...

    def to_string(self, pretty:bool) -> str: ...

    def validate(self, value: Dict) -> 'BaseModel': ...

    def values(self, **kwargs: Any) -> Dict[str, Any]: ...


def validator(*fields, pre: bool=False, whole: bool=False,
              always: bool=False) -> Any: ...


def conint(*, gt=None, lt=None) -> Type[int]: ...
