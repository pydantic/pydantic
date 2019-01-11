import warnings
from enum import IntEnum
from typing import Any, Dict, List, Mapping, Optional, Pattern, Set, Tuple, Type, Union

from . import errors as errors_
from .class_validators import Validator, ValidatorSignature, get_validator_signature
from .error_wrappers import ErrorWrapper
from .types import Json, JsonWrapper
from .utils import ForwardRef, display_as_type, lenient_issubclass, list_like
from .validators import NoneType, dict_validator, find_validators, is_none_validator

Required: Any = Ellipsis


class Shape(IntEnum):
    SINGLETON = 1
    LIST = 2
    SET = 3
    MAPPING = 4
    TUPLE = 5


class Field:
    __slots__ = (
        'type_',
        'sub_fields',
        'key_field',
        'validators',
        'whole_pre_validators',
        'whole_post_validators',
        'default',
        'required',
        'model_config',
        'name',
        'alias',
        'has_alias',
        'schema',
        'validate_always',
        'allow_none',
        'shape',
        'class_validators',
        'parse_json',
    )

    def __init__(
        self,
        *,
        name: str,
        type_: Type,
        class_validators: Optional[Dict[str, Validator]],
        model_config: Any,
        default: Any = None,
        required: bool = True,
        alias: str = None,
        schema=None,
    ):

        self.name: str = name
        self.has_alias: bool = bool(alias)
        self.alias: str = alias or name
        self.type_: type = type_
        self.class_validators = class_validators or {}
        self.default: Any = default
        self.required: bool = required
        self.model_config = model_config
        self.schema: 'schema.Schema' = schema

        self.allow_none: bool = False
        self.validate_always: bool = False
        self.sub_fields: List[Field] = None
        self.key_field: Field = None
        self.validators = []
        self.whole_pre_validators = None
        self.whole_post_validators = None
        self.parse_json: bool = False
        self.shape: Shape = Shape.SINGLETON
        self.prepare()

    @classmethod
    def infer(cls, *, name, value, annotation, class_validators, config):
        schema_from_config = config.get_field_schema(name)
        from .schema import Schema, get_annotation_from_schema

        if isinstance(value, Schema):
            schema = value
            value = schema.default
        else:
            schema = Schema(value, **schema_from_config)
        schema.alias = schema.alias or schema_from_config.get('alias')
        required = value == Required
        annotation = get_annotation_from_schema(annotation, schema)
        return cls(
            name=name,
            type_=annotation,
            alias=schema.alias,
            class_validators=class_validators,
            default=None if required else value,
            required=required,
            model_config=config,
            schema=schema,
        )

    def set_config(self, config):
        self.model_config = config
        schema_from_config = config.get_field_schema(self.name)
        if schema_from_config:
            self.schema.alias = self.schema.alias or schema_from_config.get('alias')
            self.alias = self.schema.alias

    @property
    def alt_alias(self):
        return self.name != self.alias

    def prepare(self):
        if self.default is not None and self.type_ is None:
            self.type_ = type(self.default)

        if self.type_ is None:
            raise errors_.ConfigError(f'unable to infer type for attribute "{self.name}"')

        if type(self.type_) == ForwardRef:
            # self.type_ is currently a ForwardRef and there's nothing we can do now,
            # user will need to call model.update_forward_refs()
            return

        self.validate_always: bool = (
            getattr(self.type_, 'validate_always', False) or any(v.always for v in self.class_validators.values())
        )

        if not self.required and self.default is None:
            self.allow_none = True

        self._populate_sub_fields()
        self._populate_validators()

    def _populate_sub_fields(self):
        # typing interface is horrible, we have to do some ugly checks
        if lenient_issubclass(self.type_, JsonWrapper):
            self.type_ = self.type_.inner_type
            self.parse_json = True

        if self.type_ is Pattern:
            # python 3.7 only, Pattern is a typing object but without sub fields
            return
        origin = getattr(self.type_, '__origin__', None)
        if origin is None:
            # field is not "typing" object eg. Union, Dict, List etc.
            return
        if origin is Union:
            types_ = []
            for type_ in self.type_.__args__:
                if type_ is NoneType:
                    self.allow_none = True
                    self.required = False
                types_.append(type_)
            self.sub_fields = [self._create_sub_type(t, f'{self.name}_{display_as_type(t)}') for t in types_]
            return

        if issubclass(origin, Tuple):
            self.shape = Shape.TUPLE
            self.sub_fields = [self._create_sub_type(t, f'{self.name}_{i}') for i, t in enumerate(self.type_.__args__)]
            return

        if issubclass(origin, List):
            self.type_ = self.type_.__args__[0]
            self.shape = Shape.LIST
        elif issubclass(origin, Set):
            self.type_ = self.type_.__args__[0]
            self.shape = Shape.SET
        else:
            assert issubclass(origin, Mapping)
            self.key_field = self._create_sub_type(self.type_.__args__[0], 'key_' + self.name, for_keys=True)
            self.type_ = self.type_.__args__[1]
            self.shape = Shape.MAPPING

        if getattr(self.type_, '__origin__', None):
            # type_ has been refined eg. as the type of a List and sub_fields needs to be populated
            self.sub_fields = [self._create_sub_type(self.type_, '_' + self.name)]

    def _create_sub_type(self, type_, name, *, for_keys=False):
        return self.__class__(
            type_=type_,
            name=name,
            class_validators=None if for_keys else {k: v for k, v in self.class_validators.items() if not v.whole},
            model_config=self.model_config,
        )

    def _populate_validators(self):
        class_validators_ = self.class_validators.values()
        if not self.sub_fields:
            get_validators = getattr(self.type_, '__get_validators__', None)
            if not get_validators:
                get_validators = getattr(self.type_, 'get_validators', None)
                if get_validators:
                    warnings.warn(
                        f'get_validators has been replaced by __get_validators__ (on {self.name})', DeprecationWarning
                    )
            v_funcs = (
                *tuple(v.func for v in class_validators_ if not v.whole and v.pre),
                *(
                    get_validators()
                    if get_validators
                    else find_validators(self.type_, self.model_config.arbitrary_types_allowed)
                ),
                *tuple(v.func for v in class_validators_ if not v.whole and not v.pre),
            )
            self.validators = self._prep_vals(v_funcs)

        if class_validators_:
            self.whole_pre_validators = self._prep_vals(v.func for v in class_validators_ if v.whole and v.pre)
            self.whole_post_validators = self._prep_vals(v.func for v in class_validators_ if v.whole and not v.pre)

    @staticmethod
    def _prep_vals(v_funcs):
        return tuple((get_validator_signature(f), f) for f in v_funcs if f)

    def validate(self, v, values, *, loc, cls=None):
        if self.allow_none and not self.validate_always and v is None:
            return None, None

        loc = loc if isinstance(loc, tuple) else (loc,)

        if v is not None and self.parse_json:
            v, error = self._validate_json(v, loc)
            if error:
                return v, error

        if self.whole_pre_validators:
            v, errors = self._apply_validators(v, values, loc, cls, self.whole_pre_validators)
            if errors:
                return v, errors

        if self.shape is Shape.SINGLETON:
            v, errors = self._validate_singleton(v, values, loc, cls)
        elif self.shape is Shape.MAPPING:
            v, errors = self._validate_mapping(v, values, loc, cls)
        elif self.shape is Shape.TUPLE:
            v, errors = self._validate_tuple(v, values, loc, cls)
        else:
            # list or set
            v, errors = self._validate_list_set(v, values, loc, cls)
            if not errors and self.shape is Shape.SET:
                v = set(v)

        if not errors and self.whole_post_validators:
            v, errors = self._apply_validators(v, values, loc, cls, self.whole_post_validators)
        return v, errors

    def _validate_json(self, v, loc):
        try:
            return Json.validate(v), None
        except (ValueError, TypeError) as exc:
            return v, ErrorWrapper(exc, loc=loc, config=self.model_config)

    def _validate_list_set(self, v, values, loc, cls):
        if not list_like(v):
            e = errors_.ListError() if self.shape is Shape.LIST else errors_.SetError()
            return v, ErrorWrapper(e, loc=loc, config=self.model_config)

        result, errors = [], []
        for i, v_ in enumerate(v):
            v_loc = *loc, i
            r, e = self._validate_singleton(v_, values, v_loc, cls)
            if e:
                errors.append(e)
            else:
                result.append(r)

        if errors:
            return v, errors
        else:
            return result, None

    def _validate_tuple(self, v, values, loc, cls):
        e = None
        if not list_like(v):
            e = errors_.TupleError()
        else:
            actual_length, expected_length = len(v), len(self.sub_fields)
            if actual_length != expected_length:
                e = errors_.TupleLengthError(actual_length=actual_length, expected_length=expected_length)

        if e:
            return v, ErrorWrapper(e, loc=loc, config=self.model_config)

        result, errors = [], []
        for i, (v_, field) in enumerate(zip(v, self.sub_fields)):
            v_loc = *loc, i
            r, e = field.validate(v_, values, loc=v_loc, cls=cls)
            if e:
                errors.append(e)
            else:
                result.append(r)

        if errors:
            return v, errors
        else:
            return tuple(result), None

    def _validate_mapping(self, v, values, loc, cls):
        try:
            v_iter = dict_validator(v)
        except TypeError as exc:
            return v, ErrorWrapper(exc, loc=loc, config=self.model_config)

        result, errors = {}, []
        for k, v_ in v_iter.items():
            v_loc = *loc, '__key__'
            key_result, key_errors = self.key_field.validate(k, values, loc=v_loc, cls=cls)
            if key_errors:
                errors.append(key_errors)
                continue

            v_loc = *loc, k
            value_result, value_errors = self._validate_singleton(v_, values, v_loc, cls)
            if value_errors:
                errors.append(value_errors)
                continue

            result[key_result] = value_result
        if errors:
            return v, errors
        else:
            return result, None

    def _validate_singleton(self, v, values, loc, cls):
        if self.sub_fields:
            errors = []
            for field in self.sub_fields:
                value, error = field.validate(v, values, loc=loc, cls=cls)
                if error:
                    errors.append(error)
                else:
                    return value, None
            return v, errors
        else:
            return self._apply_validators(v, values, loc, cls, self.validators)

    def _apply_validators(self, v, values, loc, cls, validators):
        for signature, validator in validators:
            try:
                if signature is ValidatorSignature.JUST_VALUE:
                    v = validator(v)
                elif signature is ValidatorSignature.VALUE_KWARGS:
                    v = validator(v, values=values, config=self.model_config, field=self)
                elif signature is ValidatorSignature.CLS_JUST_VALUE:
                    v = validator(cls, v)
                else:
                    # ValidatorSignature.CLS_VALUE_KWARGS
                    v = validator(cls, v, values=values, config=self.model_config, field=self)
            except (ValueError, TypeError) as exc:
                return v, ErrorWrapper(exc, loc=loc, config=self.model_config)
        return v, None

    def include_in_schema(self) -> bool:
        """
        False if this is a simple field just allowing None as used in Unions/Optional.
        """
        return len(self.validators) > 1 or self.validators[0][1] != is_none_validator

    def is_complex(self):
        """
        Whether the field is "complex" eg. env variables should be parsed as JSON.
        """
        from .main import BaseModel

        return (
            self.shape != Shape.SINGLETON
            or lenient_issubclass(self.type_, (BaseModel, list, set, dict))
            or hasattr(self.type_, '__pydantic_model__')  # pydantic dataclass
        )

    def __repr__(self):
        return f'<Field({self})>'

    def __str__(self):
        parts = [self.name, 'type=' + display_as_type(self.type_)]

        if self.required:
            parts.append('required')
        else:
            parts.append(f'default={self.default!r}')

        if self.alt_alias:
            parts.append('alias=' + self.alias)
        return ' '.join(parts)
