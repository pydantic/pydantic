import inspect
from dataclasses import dataclass
from enum import IntEnum
from itertools import chain
from types import FunctionType
from typing import Callable, Dict

from .errors import ConfigError
from .utils import in_ipython


class ValidatorSignature(IntEnum):
    JUST_VALUE = 1
    VALUE_KWARGS = 2
    CLS_JUST_VALUE = 3
    CLS_VALUE_KWARGS = 4


@dataclass
class Validator:
    func: Callable
    pre: bool
    whole: bool
    always: bool
    check_fields: bool


_FUNCS = set()


def validator(*fields, pre: bool = False, whole: bool = False, always: bool = False, check_fields: bool = True):
    """
    Decorate methods on the class indicating that they should be used to validate fields
    :param fields: which field(s) the method should be called on
    :param pre: whether or not this validator should be called before the standard validators (else after)
    :param whole: for complex objects (sets, lists etc.) whether to validate individual elements or the whole object
    :param always: whether this method and other validators should be called even if the value is missing
    :param check_fields: whether to check that the fields actually exist on the model
    """
    if not fields:
        raise ConfigError('validator with no fields specified')
    elif isinstance(fields[0], FunctionType):
        raise ConfigError(
            "validators should be used with fields and keyword arguments, not bare. "
            "E.g. usage should be `@validator('<field_name>', ...)`"
        )

    def dec(f):
        # avoid validators with duplicated names since without this validators can be overwritten silently
        # which generally isn't the intended behaviour, don't run in ipython - see #312
        if not in_ipython():  # pragma: no branch
            ref = f.__module__ + '.' + f.__qualname__
            if ref in _FUNCS:
                raise ConfigError(f'duplicate validator function "{ref}"')
            _FUNCS.add(ref)
        f_cls = classmethod(f)
        f_cls.__validator_config = fields, Validator(f, pre, whole, always, check_fields)
        return f_cls

    return dec


class ValidatorGroup:
    def __init__(self, validators):
        self.validators: Dict[str, Validator] = validators
        self.used_validators = {'*'}

    def get_validators(self, name):
        self.used_validators.add(name)
        specific_validators = self.validators.get(name)
        wildcard_validators = self.validators.get('*')
        if specific_validators or wildcard_validators:
            validators = (specific_validators or []) + (wildcard_validators or [])
            return {v.func.__name__: v for v in validators}

    def check_for_unused(self):
        unused_validators = set(
            chain(
                *[
                    (v.func.__name__ for v in self.validators[f] if v.check_fields)
                    for f in (self.validators.keys() - self.used_validators)
                ]
            )
        )
        if unused_validators:
            fn = ', '.join(unused_validators)
            raise ConfigError(
                f"Validators defined with incorrect fields: {fn} "
                f"(use check_fields=False if you're inheriting from the model and intended this)"
            )


def extract_validators(namespace):
    validators = {}
    for var_name, value in namespace.items():
        validator_config = getattr(value, '__validator_config', None)
        if validator_config:
            fields, v = validator_config
            for field in fields:
                if field in validators:
                    validators[field].append(v)
                else:
                    validators[field] = [v]
    return validators


def inherit_validators(base_validators, validators):
    for field, field_validators in base_validators.items():
        if field not in validators:
            validators[field] = []
        validators[field] += field_validators
    return validators


def get_validator_signature(validator):
    signature = inspect.signature(validator)

    # bind here will raise a TypeError so:
    # 1. we can deal with it before validation begins
    # 2. (more importantly) it doesn't get confused with a TypeError when executing the validator
    try:
        if 'cls' in signature._parameters:
            if len(signature.parameters) == 2:
                signature.bind(object(), 1)
                return ValidatorSignature.CLS_JUST_VALUE
            else:
                signature.bind(object(), 1, values=2, config=3, field=4)
                return ValidatorSignature.CLS_VALUE_KWARGS
        else:
            if len(signature.parameters) == 1:
                signature.bind(1)
                return ValidatorSignature.JUST_VALUE
            else:
                signature.bind(1, values=2, config=3, field=4)
                return ValidatorSignature.VALUE_KWARGS
    except TypeError as e:
        raise ConfigError(
            f'Invalid signature for validator {validator}: {signature}, should be: '
            f'(value) or (value, *, values, config, field) or for class validators '
            f'(cls, value) or (cls, value, *, values, config, field)'
        ) from e
