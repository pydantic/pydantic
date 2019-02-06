import inspect
from dataclasses import dataclass
from functools import wraps
from itertools import chain
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set, Type

from .errors import ConfigError
from .utils import AnyCallable, in_ipython

if TYPE_CHECKING:
    from .main import BaseConfig, BaseModel
    from .fields import Field

    ValidatorCallable = Callable[[Optional[Type[BaseModel]], Any, Dict[str, Any], Field, Type[BaseConfig]], Any]


@dataclass
class Validator:
    func: AnyCallable
    pre: bool
    whole: bool
    always: bool
    check_fields: bool


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
            "validators should be used with fields and keyword arguments, not bare. "
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
        f_cls.__validator_config = fields, Validator(f, pre, whole, always, check_fields)  # type: ignore
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
                f"Validators defined with incorrect fields: {fn} "
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


all_kwargs = {'values', 'field', 'config'}


def _make_generic_validator(validator: AnyCallable) -> 'ValidatorCallable':  # noqa: C901 (ignore complexity)
    """
    Logic for building validators with a generic signature.

    Unfortunately other approaches eg. return a partial of a function that builds the arguments is slow than this,
    hence this laborious way of doing things.

    It's done like this so validators don't all need **kwargs in their signature, eg. any combination of
    the arguments "values", "fields" and/or "config" are permitted.
    """
    signature = inspect.signature(validator)
    args = list(signature.parameters.keys())
    # debug(validator, args)

    # bind here will raise a TypeError so:
    # 1. we can deal with it before validation begins
    # 2. (more importantly) it doesn't get confused with a TypeError when executing the validator
    if args[0] == 'cls':
        other_args = set(args[2:])
        has_kwargs = False
        if 'kwargs' in other_args:
            has_kwargs = True
            other_args -= {'kwargs'}
        if not other_args.issubset(all_kwargs):
            raise ConfigError(
                f'Invalid signature for validator {validator}: {signature}, should be: '
                f'(cls, value, *, values, config, field), "values", "config" and "field" are all optional.'
            )
        if has_kwargs:
            return lambda cls, v, values, field, config: validator(cls, v, values=values, field=field, config=config)
        elif other_args == set():
            return lambda cls, v, values, field, config: validator(cls, v)
        elif other_args == {'values'}:
            return lambda cls, v, values, field, config: validator(cls, v, values=values)
        elif other_args == {'field'}:
            return lambda cls, v, values, field, config: validator(cls, v, field=field)
        elif other_args == {'config'}:
            return lambda cls, v, values, field, config: validator(cls, v, config=config)
        elif other_args == {'values', 'field'}:
            return lambda cls, v, values, field, config: validator(cls, v, values=values, field=field)
        elif other_args == {'values', 'config'}:
            return lambda cls, v, values, field, config: validator(cls, v, values=values, config=config)
        elif other_args == {'field', 'config'}:
            return lambda cls, v, values, field, config: validator(cls, v, field=field, config=config)
        else:
            # other_args == {'values', 'field', 'config'}
            return lambda cls, v, values, field, config: validator(cls, v, values=values, field=field, config=config)
    elif args[0] == 'self':
        raise ConfigError(
            f'Invalid signature for validator {validator}: {signature}, should be: '
            f'(cls, value, *, values, config, field), "values", "config" and "field" are all optional.'
        )
    else:
        # assume the first argument is value
        other_args = set(args[1:])
        has_kwargs = False
        if 'kwargs' in other_args:
            has_kwargs = True
            other_args -= {'kwargs'}
        if not other_args.issubset(all_kwargs):
            raise ConfigError(
                f'Invalid signature for validator {validator}: {signature}, should be: '
                f'(value, *, values, config, field), "values", "config" and "field" are all optional.'
            )
        if has_kwargs:
            return lambda cls, v, values, field, config: validator(v, values=values, field=field, config=config)
        elif other_args == set():
            return lambda cls, v, values, field, config: validator(v)
        elif other_args == {'values'}:
            return lambda cls, v, values, field, config: validator(v, values=values)
        elif other_args == {'field'}:
            return lambda cls, v, values, field, config: validator(v, field=field)
        elif other_args == {'config'}:
            return lambda cls, v, values, field, config: validator(v, config=config)
        elif other_args == {'values', 'field'}:
            return lambda cls, v, values, field, config: validator(v, values=values, field=field)
        elif other_args == {'values', 'config'}:
            return lambda cls, v, values, field, config: validator(v, values=values, config=config)
        elif other_args == {'field', 'config'}:
            return lambda cls, v, values, field, config: validator(v, field=field, config=config)
        else:
            # other_args == {'values', 'field', 'config'}
            return lambda cls, v, values, field, config: validator(v, values=values, field=field, config=config)


def make_generic_validator(validator: AnyCallable) -> 'ValidatorCallable':
    """
    Make a generic function which calls a validator with the right arguments.

    make_generic_validator vs. _make_generic_validator is a bodge to avoid "E731 do not assign a lambda expression"
    errors.
    """
    return wraps(validator)(_make_generic_validator(validator))
