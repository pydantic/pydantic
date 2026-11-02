"""Griffe extension documenting the `ModelMetaclass` properties as `BaseModel` attributes.

`BaseModel.model_fields` and `BaseModel.model_computed_fields` are properties of the
`ModelMetaclass` (so that they can only be accessed from the model class). Griffe documents
them on the metaclass, which isn't part of the API documentation.
"""

from __future__ import annotations

from typing import Any

import griffe


class ModelMetaclassProperties(griffe.Extension):
    def on_package_loaded(self, *, pkg: griffe.Module, **kwargs: Any) -> None:
        if pkg.name != 'pydantic':
            return
        base_model = pkg['main.BaseModel']
        metaclass = pkg['_internal._model_construction.ModelMetaclass']
        for name, member in metaclass.members.items():
            if name.startswith('_') or name in base_model.members or 'property' not in member.labels:
                continue
            docstring = member.docstring
            attribute = griffe.Attribute(
                name,
                annotation=member.annotation,
                docstring=docstring and griffe.Docstring(docstring.value, parser=docstring.parser),
            )
            attribute.labels.add('class-attribute')
            base_model.set_member(name, attribute)
