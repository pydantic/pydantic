from __future__ import annotations as _annotations

import warnings
from typing import Any

from typing_extensions import deprecated

from .._internal import _config

__all__ = ('BaseConfig',)


class _ConfigMetaclass(type):
    def __getattr__(self, item: str) -> Any:
        warnings.warn(_config.DEPRECATION_MESSAGE, DeprecationWarning)

        try:
            return _config.config_defaults[item]
        except KeyError as exc:
            raise AttributeError(f"type object '{self.__name__}' has no attribute {exc}") from exc


@deprecated('BaseConfig is deprecated. Use the `pydantic.ConfigDict` instead.')
class BaseConfig(metaclass=_ConfigMetaclass):
    """
    This class is only retained for backwards compatibility.

    The preferred approach going forward is to assign a ConfigDict to the `model_config` attribute of the Model class.
    """

    def __getattr__(self, item: str) -> Any:
        warnings.warn(_config.DEPRECATION_MESSAGE, DeprecationWarning)
        try:
            return super().__getattribute__(item)
        except AttributeError as exc:
            try:
                return getattr(type(self), item)
            except AttributeError:
                # re-raising changes the displayed text to reflect that `self` is not a type
                raise AttributeError(str(exc)) from exc

    def __init_subclass__(cls, **kwargs: Any) -> None:
        warnings.warn(_config.DEPRECATION_MESSAGE, DeprecationWarning)
        return super().__init_subclass__(**kwargs)
