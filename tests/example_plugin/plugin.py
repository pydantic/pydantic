from __future__ import annotations

from typing import Any

import pydantic.plugin
from pydantic import ValidationError


class OnValidatePython(pydantic.plugin.OnValidatePython):
    def on_enter(
        self,
        input: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, Any] | None = None,
        self_instance: Any | None = None,
    ) -> None:
        from . import example_func

        example_func()

    def on_success(self, result: Any) -> None:
        from . import example_func

        example_func()

    def on_error(self, error: ValidationError) -> None:
        from . import example_func

        example_func()


plugin = pydantic.plugin.Plugin(on_validate_python=OnValidatePython)
