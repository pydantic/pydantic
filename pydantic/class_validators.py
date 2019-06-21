from collections import ChainMap
from functools import wraps
from inspect import Signature, signature
from itertools import chain
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set, Type

from .errors import ConfigError
from .utils import AnyCallable, in_ipython

if TYPE_CHECKING:  # pragma: no cover
    from .main import BaseConfig
    from .fields import Field
    from .types import ModelOrDc

    ValidatorCallable = Callable[[Optional[ModelOrDc], Any, Dict[str, Any], Field, Type[BaseConfig]], Any]


class Validator:
    def __init__(self, func: AnyCallable, pre: bool, whole: bool, always: bool, check_fields: bool):
        self.func = func
        self.pre = pre
        self.whole = whole
        self.always = always
        self.check_fields = check_fields


_FUNCS: Set[str] = set()


def validator(
    *fields: str, pre: bool = False, whole: bool = False, always: bool = False, check_fields: bool = True
) -> Callable[[AnyCallable], classmethod]:
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
            "validators should be used with fields and keyword arguments, not bare. "  # noqa: Q000
            "E.g. usage should be `@validator('<field_name>', ...)`"
        )

    def dec(f: AnyCallable) -> classmethod:
        # avoid validators with duplicated names since without this validators can be overwritten silently
        # which generally isn't the intended behaviour, don't run in ipython - see #312
        if not in_ipython():  # pragma: no branch
            ref = f.__module__ + '.' + f.__qualname__
            if ref in _FUNCS:
                raise ConfigError(f'duplicate validator function "{ref}"')
            _FUNCS.add(ref)
        f_cls = classmethod(f)
        f_cls.__validator_config = (  # type: ignore
            fields,
            Validator(func=f, pre=pre, whole=whole, always=always, check_fields=check_fields),
        )
        return f_cls

    return dec


ValidatorListDict = Dict[str, List[Validator]]


class ValidatorGroup:
    def __init__(self, validators: ValidatorListDict) -> None:
        self.validators = validators
        self.used_validators = {'*'}

    def get_validators(self, name: str) -> Optional[Dict[str, Validator]]:
        self.used_validators.add(name)
        specific_validators = self.validators.get(name)
        wildcard_validators = self.validators.get('*')
        if specific_validators or wildcard_validators:
            validators = (specific_validators or []) + (wildcard_validators or [])
            return {v.func.__name__: v for v in validators}
        return None

    def check_for_unused(self) -> None:
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
                f"Validators defined with incorrect fields: {fn} "  # noqa: Q000
                f"(use check_fields=False if you're inheriting from the model and intended this)"
            )


def extract_validators(namespace: Dict[str, Any]) -> Dict[str, List[Validator]]:
    validators: Dict[str, List[Validator]] = {}
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


def inherit_validators(base_validators: ValidatorListDict, validators: ValidatorListDict) -> ValidatorListDict:
    for field, field_validators in base_validators.items():
        if field not in validators:
            validators[field] = []
        validators[field] += field_validators
    return validators


def make_generic_validator(validator: AnyCallable) -> 'ValidatorCallable':
    """
    Make a generic function which calls a validator with the right arguments.

    Unfortunately other approaches (eg. return a partial of a function that builds the arguments) is slow,
    hence this laborious way of doing things.

    It's done like this so validators don't all need **kwargs in their signature, eg. any combination of
    the arguments "values", "fields" and/or "config" are permitted.
    """
    sig = signature(validator)
    args = list(sig.parameters.keys())
    first_arg = args.pop(0)
    if first_arg == 'self':
        raise ConfigError(
            f'Invalid signature for validator {validator}: {sig}, "self" not permitted as first argument, '
            f'should be: (cls, value, values, config, field), "values", "config" and "field" are all optional.'
        )
    elif first_arg == 'cls':
        # assume the second argument is value
        return wraps(validator)(_generic_validator_cls(validator, sig, set(args[1:])))
    else:
        # assume the first argument was value which has already been removed
        return wraps(validator)(_generic_validator_basic(validator, sig, set(args)))


all_kwargs = {'values', 'field', 'config'}


def _generic_validator_cls(validator: AnyCallable, sig: Signature, args: Set[str]) -> 'ValidatorCallable':
    # assume the first argument is value
    has_kwargs = False
    if 'kwargs' in args:
        has_kwargs = True
        args -= {'kwargs'}

    if not args.issubset(all_kwargs):
        raise ConfigError(
            f'Invalid signature for validator {validator}: {sig}, should be: '
            f'(cls, value, values, config, field), "values", "config" and "field" are all optional.'
        )

    if has_kwargs:
        return lambda cls, v, values, field, config: validator(cls, v, values=values, field=field, config=config)
    elif args == set():
        return lambda cls, v, values, field, config: validator(cls, v)
    elif args == {'values'}:
        return lambda cls, v, values, field, config: validator(cls, v, values=values)
    elif args == {'field'}:
        return lambda cls, v, values, field, config: validator(cls, v, field=field)
    elif args == {'config'}:
        return lambda cls, v, values, field, config: validator(cls, v, config=config)
    elif args == {'values', 'field'}:
        return lambda cls, v, values, field, config: validator(cls, v, values=values, field=field)
    elif args == {'values', 'config'}:
        return lambda cls, v, values, field, config: validator(cls, v, values=values, config=config)
    elif args == {'field', 'config'}:
        return lambda cls, v, values, field, config: validator(cls, v, field=field, config=config)
    else:
        # args == {'values', 'field', 'config'}
        return lambda cls, v, values, field, config: validator(cls, v, values=values, field=field, config=config)


def _generic_validator_basic(validator: AnyCallable, sig: Signature, args: Set[str]) -> 'ValidatorCallable':
    has_kwargs = False
    if 'kwargs' in args:
        has_kwargs = True
        args -= {'kwargs'}

    if not args.issubset(all_kwargs):
        raise ConfigError(
            f'Invalid signature for validator {validator}: {sig}, should be: '
            f'(value, values, config, field), "values", "config" and "field" are all optional.'
        )

    if has_kwargs:
        return lambda cls, v, values, field, config: validator(v, values=values, field=field, config=config)
    elif args == set():
        return lambda cls, v, values, field, config: validator(v)
    elif args == {'values'}:
        return lambda cls, v, values, field, config: validator(v, values=values)
    elif args == {'field'}:
        return lambda cls, v, values, field, config: validator(v, field=field)
    elif args == {'config'}:
        return lambda cls, v, values, field, config: validator(v, config=config)
    elif args == {'values', 'field'}:
        return lambda cls, v, values, field, config: validator(v, values=values, field=field)
    elif args == {'values', 'config'}:
        return lambda cls, v, values, field, config: validator(v, values=values, config=config)
    elif args == {'field', 'config'}:
        return lambda cls, v, values, field, config: validator(v, field=field, config=config)
    else:
        # args == {'values', 'field', 'config'}
        return lambda cls, v, values, field, config: validator(v, values=values, field=field, config=config)


def gather_validators(type_: 'ModelOrDc') -> Dict[str, classmethod]:
    all_attributes = ChainMap(*[cls.__dict__ for cls in type_.__mro__])
    return {k: v for k, v in all_attributes.items() if hasattr(v, '__validator_config')}
