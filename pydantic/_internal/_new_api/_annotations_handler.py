from collections.abc import Generator
from typing import Any

import annotated_types as at

from pydantic import AfterValidator, FailFast, Strict

ANNS_AS_VALIDATORS = {at.Gt, at.Ge, at.Lt, at.Le}


class AnnotationsHandler:
    def __init__(self, annotations: list[Any], known_metadata: set[type[Any]]) -> None:
        self._annotations = annotations
        self._known_metadata = known_metadata
        self._remaining_annotations: list[Any] = []

    def iter_annotations(self) -> Generator[Any]:
        anns_as_validators = False
        if not self._known_metadata:
            # Early return, no need to iterate over annotations
            self._remaining_annotations.extend(self._annotations)
            return

        for ann in self._annotations:
            if isinstance(ann, AfterValidator):
                # For backwards compatibility, some annotations (e.g. `Gt`) behave as validators
                # if defined after an *after* validator, and the order need to be kept. If we ever
                # encounter one, don't yield these annotations anymore.
                anns_as_validators = True
            # Some metadata can be used as bare classes (e.g. `Strict`). We shouldn't continue using this
            # pattern, but handle it here and special case when yielding annotation:
            ann_class = ann if isinstance(ann, type) else type(ann)
            if ann_class in self._known_metadata:
                if anns_as_validators and ann_class in ANNS_AS_VALIDATORS:
                    self._remaining_annotations.append(ann)
                    continue
                if ann is Strict or ann is FailFast:
                    yield ann()
                else:
                    yield ann
            else:
                self._remaining_annotations.append(ann)
