from __future__ import annotations as _annotations

import sys
from functools import partial
from types import FunctionType
from typing import Any, Callable, ForwardRef, _eval_type as typing_eval_type

from pydantic_core import Schema as PydanticCoreSchema, SchemaValidator

from ..config import BaseConfig, ConfigDict, inherit_config, prepare_config
from ..fields import FieldInfo, ModelPrivateAttr, PrivateAttr
from ..json import custom_pydantic_encoder, pydantic_encoder
from .babelfish import model_fields_schema
from .typing_extra import is_classvar
from .valdation_functions import ValidationFunctions

CONFIG_PARAMS: set[str] = set(ConfigDict.__annotations__.keys())

# This is used to identify a reference to the current model class, e.g. in recursive classes
SelfType = object()


IGNORED_TYPES: tuple[Any, ...] = (FunctionType, property, type, classmethod, staticmethod)
DUNDER_ATTRIBUTES = {
    '__annotations__',
    '__classcell__',
    '__doc__',
    '__module__',
    '__orig_bases__',
    '__orig_class__',
    '__qualname__',
    '__slots__',
}
# attribute names to ignore off the bat, mostly to save time
IGNORED_ATTRIBUTES = DUNDER_ATTRIBUTES | {'Config'}


class NewModel:
    """
    Logic used in ModelMetaclass.__new__ to create a Model
    """

    __slots__ = (
        'metaclass_type',
        'cls_name',
        'bases',
        'namespace',
        'kwargs',
        'fields',
        'config',
        'validator_functions',
        'private_attributes',
        'base_private_attributes',
        'raw_slots',
        'slots',
        'class_vars',
        'hash_func',
        'base_globals',
    )

    def __init__(
        self,
        metaclass_type: type[Any],
        name: str,
        bases: tuple[type[Any], ...],
        namespace: dict[str, Any],
        kwargs: dict[str, Any],
    ):
        self.metaclass_type = metaclass_type
        self.cls_name = name
        self.bases = bases
        self.namespace = namespace
        self.kwargs = kwargs

        self.fields: dict[str, FieldInfo] = {}
        self.config = BaseConfig
        self.validator_functions = ValidationFunctions()
        self.private_attributes: dict[str, ModelPrivateAttr] = {}
        self.class_vars: set[str] = set()
        self.hash_func: Callable[[Any], int] | None = None

        self.base_globals: dict[str, Any] | None = None
        module_name = self.namespace.get('__module__')
        if module_name:
            try:
                module = sys.modules[module_name]
            except KeyError:
                # happens occasionally, see https://github.com/pydantic/pydantic/issues/2363
                pass
            else:
                self.base_globals = module.__dict__

    def inherit(self) -> None:
        """
        Process bases and take care of inheritance.
        """
        from ..main import BaseModel

        for base in reversed(self.bases):
            if issubclass(base, BaseModel) and base is not BaseModel:
                self.fields.update(base.__fields__)
                self.config = inherit_config(base.__config__, self.config)
                self.validator_functions.inherit(base.__validator_functions__)
                self.private_attributes.update(base.__private_attributes__)
                self.class_vars.update(base.__class_vars__)
                self.hash_func = base.__hash__

    def prepare_config(self) -> None:
        """
        Prepare model config from kwargs and self.config.
        """
        config_kwargs = {k: v for k, v in self.kwargs.items() if k in CONFIG_PARAMS}
        config_from_namespace = self.namespace.get('Config')
        if config_kwargs and config_from_namespace:
            raise TypeError('Specifying config in two places is ambiguous, use either Config attribute or class kwargs')

        self.config = inherit_config(config_from_namespace, self.config, **config_kwargs)
        prepare_config(self.config, self.cls_name)

    def inspect_annotations(self) -> None:
        """
        Inspect __annotations__ and populate class_vars and fields.
        """
        try:
            raw_annotations = self.namespace['__annotations__']
        except KeyError:
            return None

        for ann_name, raw_ann_type in raw_annotations.items():
            ann_type = self._resolve_annotation(raw_ann_type)
            if is_classvar(ann_type):
                self.class_vars.add(ann_name)
            # TODO???
            # elif is_finalvar_with_default_val(ann_type, namespace.get(ann_name, Undefined)):
            #     class_vars.add(ann_name)
            elif not ann_name.startswith('_'):
                self._check_clash(ann_name)

                try:
                    default = self.namespace[ann_name]
                except KeyError:
                    self.fields[ann_name] = FieldInfo.from_bare(ann_type)
                else:
                    self.fields[ann_name] = FieldInfo.from_default(ann_type, default)

    def inspect_namespace(self) -> None:
        """
        Inspect namespace
        :return:
        """
        raw_annotations = self.namespace.get('__annotations__', {})
        ignored_types = IGNORED_TYPES + self.config.keep_untouched
        for var_name, value in self.namespace.items():
            if var_name in IGNORED_ATTRIBUTES:
                continue
            elif isinstance(value, ModelPrivateAttr):
                if var_name in DUNDER_ATTRIBUTES:
                    raise NameError(
                        f'Private attributes "{var_name}" must not be a valid field name; '
                        f'Use sunder or dunder names, e. g. "_{var_name}" or "__{var_name}__"'
                    )
                self.private_attributes[var_name] = value
            elif self.validator_functions.extract_validator(value):
                continue
            elif var_name in self.class_vars or isinstance(value, ignored_types):
                continue
            elif var_name.startswith('_'):
                self.private_attributes[var_name] = PrivateAttr(default=value)
            elif var_name not in raw_annotations:
                raise TypeError(
                    f'All fields must include a type annotation; '
                    f'{var_name!r} looks like a field but has no type annotation.'
                )
        self.validator_functions.check_for_unused()

    def new_namespace(self) -> tuple[dict[str, Any], PydanticCoreSchema]:
        if self.config.json_encoders:
            json_encoder = partial(custom_pydantic_encoder, self.config.json_encoders)
        else:
            json_encoder = pydantic_encoder

        if self.hash_func is None and self.config.frozen:

            def hash_func(self_: Any) -> int:
                return hash(self_.__class__) + hash(tuple(self_.__dict__.values()))

            self.hash_func = hash_func

        inner_schema = model_fields_schema(self.fields, self.validator_functions)
        self.validator_functions.check_for_unused()
        validator = SchemaValidator(inner_schema)
        exclude_from_namespace = self.fields.keys() | self.private_attributes.keys() | {'__slots__'}
        slots: set[str] = set(self.namespace.get('__slots__', ()))

        new_namespace = {
            '__validator__': validator,
            '__config__': self.config,
            '__fields__': self.fields,
            '__validator_functions__': self.validator_functions,
            '__schema_cache__': {},
            '__json_encoder__': staticmethod(json_encoder),
            '__private_attributes__': self.private_attributes,
            '__slots__': slots | self.private_attributes.keys(),
            '__hash__': self.hash_func,
            '__class_vars__': self.class_vars,
            **{n: v for n, v in self.namespace.items() if n not in exclude_from_namespace},
        }

        return new_namespace, inner_schema

    def complete_class(self, cls: type[Any], inner_schema: PydanticCoreSchema) -> None:
        cls.__pydantic_validation_schema__ = {
            'type': 'new-class',
            'class_type': cls,
            'schema': inner_schema,
        }

        # set __signature__ attr only for model class, but not for its instances
        # TODO:
        # cls.__signature__ = ClassAttribute('__signature__', generate_model_signature(cls.__init__, fields, config))

        for name, private_attr in self.private_attributes.items():
            private_attr.__set_name__(cls, name)

    def _resolve_annotation(self, raw_annotation: type[Any] | str) -> type[Any] | ForwardRef | SelfType:
        """
        Partially taken from typing.get_type_hints.

        Resolve string or ForwardRef annotations into type objects if possible.
        """
        if isinstance(raw_annotation, str):
            if raw_annotation == self.cls_name:
                return SelfType
            if (3, 10) > sys.version_info >= (3, 9, 8) or sys.version_info >= (3, 10, 1):
                raw_annotation = ForwardRef(raw_annotation, is_argument=False, is_class=True)
            else:
                raw_annotation = ForwardRef(raw_annotation, is_argument=False)

        try:
            return typing_eval_type(raw_annotation, self.base_globals, None)
        except NameError:
            # this is ok, it can be fixed with update_forward_refs
            return raw_annotation

    def _check_clash(self, field_name: str) -> None:
        """
        Ensure that the field's name does not shadow an existing attribute of the model.
        """
        for base in self.bases:
            if hasattr(base, field_name):
                raise NameError(
                    f'Field name "{field_name}" shadows an attribute in parent {base.__qualname__}; '
                    f'use a different field name with "alias=\'{field_name}\'".'
                )
