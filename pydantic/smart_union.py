from typing import TYPE_CHECKING, Any, Final, Generic, TypeVar, Union

from pydantic.main import BaseModel

class SmartUnion:
    def __class_getitem__(cls, item):
        class _Model(BaseModel):
            __root__: Union[item]

            class Config:
                smart_union = True

        def _parse(**kwargs: Any) -> Any:
            return _Model(__root__=kwargs).__root__

        return _parse