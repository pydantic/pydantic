import warnings
from collections import ChainMap
from functools import wraps
from itertools import chain
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Type, Union, overload

from .errors import ConfigError
from .typing import AnyCallable
from .utils import in_ipython


class Validator:
    __slots__ = 'func', 'pre', 'each_item', 'always', 'check_fields', 'skip_on_failure'

    def __init__(
        self,
        func: AnyCallable,
        pre: bool = False,
        each_item: bool = False,
        always: bool = False,
        check_fields: bool = False,
        skip_on_failure: bool = False,
    ):
        self.func = func
        self.pre = pre
        self.each_item = each_item
        self.always = always
        self.check_fields = check_fields
        self.skip_on_failure = skip_on_failure


if TYPE_CHECKING:
    from inspect import Signature

    from .fields import ModelField
    from .main import BaseConfig
    from .types import ModelOrDc

    ValidatorCallable = Callable[[Optional[ModelOrDc], Any, Dict[str, Any], ModelField, Type[BaseConfig]], Any]
    ValidatorsList = List[ValidatorCallable]
    ValidatorListDict = Dict[str, List[Validator]]

_FUNCS: Set[str] = set()
ROOT_KEY = '__root__'
VALIDATOR_CONFIG_KEY = '__validator_config__'
ROOT_VALIDATOR_CONFIG_KEY = '__root_validator_config__'


def validator(
    *fields: str,
    pre: bool = False,
    each_item: bool = False,
    always: bool = False,
    check_fields: bool = True,
    whole: bool = None,
    allow_reuse: bool = False,
) -> Callable[[AnyCallable], classmethod]:
    """
    Decorate methods on the class indicating that they should be used to validate fields
    :param fields: which field(s) the method should be called on
    :param pre: whether or not this validator should be called before the standard validators (else after)
    :param each_item: for complex objects (sets, lists etc.) whether to validate individual elements rather than the
      whole object
    :param always: whether this method and other validators should be called even if the value is missing
    :param check_fields: whether to check that the fields actually exist on the model
    :param allow_reuse: whether to track and raise an error if another validator refers to the decorated function
    """
    if not fields:
        raise ConfigError('validator with no fields specified')
    elif isinstance(fields[0], FunctionType):
        raise ConfigError(
            "validators should be used with fields and keyword arguments, not bare. "  # noqa: Q000
            "E.g. usage should be `@validator('<field_name>', ...)`"
        )

    if whole is not None:
        warnings.warn(
            'The "whole" keyword argument is deprecated, use "each_item" (inverse meaning, default False) instead',
            DeprecationWarning,
        )
        assert each_item is False, '"each_item" and "whole" conflict, remove "whole"'
        each_item = not whole

    def dec(f: AnyCallable) -> classmethod:
        f_cls = _prepare_validator(f, allow_reuse)
        setattr(
            f_cls,
            VALIDATOR_CONFIG_KEY,
            (
                fields,
                Validator(func=f_cls.__func__, pre=pre, each_item=each_item, always=always, check_fields=check_fields),
            ),
        )
        return f_cls

    return dec


@overload
def root_validator(_func: AnyCallable) -> classmethod:
    ...


@overload
def root_validator(
    *, pre: bool = False, allow_reuse: bool = False, skip_on_failure: bool = False
) -> Callable[[AnyCallable], classmethod]:
    ...


def root_validator(
    _func: Optional[AnyCallable] = None, *, pre: bool = False, allow_reuse: bool = False, skip_on_failure: bool = False
) -> Union[classmethod, Callable[[AnyCallable], classmethod]]:
    """
    Decorate methods on a model indicating that they should be used to validate (and perhaps modify) data either
    before or after standard model parsing/validation is performed.
    """
    if _func:
        f_cls = _prepare_validator(_func, allow_reuse)
        setattr(
            f_cls, ROOT_VALIDATOR_CONFIG_KEY, Validator(func=f_cls.__func__, pre=pre, skip_on_failure=skip_on_failure)
        )
        return f_cls

    def dec(f: AnyCallable) -> classmethod:
        f_cls = _prepare_validator(f, allow_reuse)
        setattr(
            f_cls, ROOT_VALIDATOR_CONFIG_KEY, Validator(func=f_cls.__func__, pre=pre, skip_on_failure=skip_on_failure)
        )
        return f_cls

    return dec


def _prepare_validator(function: AnyCallable, allow_reuse: bool) -> classmethod:
    """
    Avoid validators with duplicated names since without this, validators can be overwritten silently
    which generally isn't the intended behaviour, don't run in ipython (see #312) or if allow_reuse is False.
    """
    f_cls = function if isinstance(function, classmethod) else classmethod(function)
    if not in_ipython() and not allow_reuse:
        ref = f_cls.__func__.__module__ + '.' + f_cls.__func__.__qualname__
        if ref in _FUNCS:
            raise ConfigError(f'duplicate validator function "{ref}"; if this is intended, set `allow_reuse=True`')
        _FUNCS.add(ref)
    return f_cls


class ValidatorGroup:
    def __init__(self, validators: 'ValidatorListDict') -> None:
        self.validators = validators
        self.used_validators = {'*'}

    def get_validators(self, name: str) -> Optional[Dict[str, Validator]]:
        self.used_validators.add(name)
        validators = self.validators.get(name, [])
        if name != ROOT_KEY:
            validators += self.validators.get('*', [])
        if validators:
            return {v.func.__name__: v for v in validators}
        else:
            return None

    def check_for_unused(self) -> None:
        unused_validators = set(
            chain.from_iterable(
                (v.func.__name__ for v in self.validators[f] if v.check_fields)
                for f in (self.validators.keys() - self.used_validators)
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
        validator_config = getattr(value, VALIDATOR_CONFIG_KEY, None)
        if validator_config:
            fields, v = validator_config
            for field in fields:
                if field in validators:
                    validators[field].append(v)
                else:
                    validators[field] = [v]
    return validators


def extract_root_validators(namespace: Dict[str, Any]) -> Tuple[List[AnyCallable], List[Tuple[bool, AnyCallable]]]:
    from inspect import signature

    pre_validators: List[AnyCallable] = []
    post_validators: List[Tuple[bool, AnyCallable]] = []
    for name, value in namespace.items():
        validator_config: Optional[Validator] = getattr(value, ROOT_VALIDATOR_CONFIG_KEY, None)
        if validator_config:
            sig = signature(validator_config.func)
            args = list(sig.parameters.keys())
            if args[0] == 'self':
                raise ConfigError(
                    f'Invalid signature for root validator {name}: {sig}, "self" not permitted as first argument, '
                    f'should be: (cls, values).'
                )
            if len(args) != 2:
                raise ConfigError(f'Invalid signature for root validator {name}: {sig}, should be: (cls, values).')
            # check function signature
            if validator_config.pre:
                pre_validators.append(validator_config.func)
            else:
                post_validators.append((validator_config.skip_on_failure, validator_config.func))
    return pre_validators, post_validators


def inherit_validators(base_validators: 'ValidatorListDict', validators: 'ValidatorListDict') -> 'ValidatorListDict':
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
    from inspect import signature

    sig = signature(validator)
    args = list(sig.parameters.keys())
    first_arg = args.pop(0)
    if first_arg == 'self':
        raise ConfigError(
            f'Invalid signature for validator {validator}: {sig}, "self" not permitted as first argument, '
            f'should be: (cls, value, values, config, field), "values", "config" and "field" are all optional.'
        )
    else:
        if first_arg == 'cls':
            # assume the second argument is value
            args = args[1:]
            skip_first = False
        else:
            # assume the first argument was value which has already been removed
            skip_first = True

        return wraps(validator)(_generic_validator(validator, sig, set(args), skip_first))


def prep_validators(v_funcs: Iterable[AnyCallable]) -> 'ValidatorsList':
    return [make_generic_validator(f) for f in v_funcs if f]


args_order = ('values', 'field', 'config')
all_kwargs = {*args_order}
required_args = 2


def _generic_validator(
    validator: AnyCallable, sig: 'Signature', args: Set[str], skip_first: bool = False
) -> 'ValidatorCallable':
    if 'kwargs' in args:
        args = all_kwargs | args - {'kwargs'}

    if not args.issubset(all_kwargs):
        sig_args = ('cls', 'value', *args_order)[skip_first:]
        raise ConfigError(
            f'Invalid signature for validator {validator}: {sig}, should be: '
            f'({", ".join(sig_args)}), "values", "config" and "field" are all optional.'
        )

    def _fetch_args(args_: Tuple[Any, ...]) -> Dict[str, Any]:
        return {k: args_[args_order.index(k)] for k in args_order if k in args}

    # Actual signature is (cls, value, values, field, config)
    # cls and value is required, other args is optional
    @wraps(validator)
    def validator_wrapper(*args_: Any) -> Any:
        return validator(*args_[skip_first:required_args], **_fetch_args(args_[required_args:]))

    return validator_wrapper


def gather_all_validators(type_: 'ModelOrDc') -> Dict[str, classmethod]:
    all_attributes = ChainMap(*[cls.__dict__ for cls in type_.__mro__])
    return {
        k: v
        for k, v in all_attributes.items()
        if hasattr(v, VALIDATOR_CONFIG_KEY) or hasattr(v, ROOT_VALIDATOR_CONFIG_KEY)
    }
