from functools import wraps
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Tuple, TypeVar, cast, get_type_hints

from . import validator
from .errors import ConfigError
from .main import BaseModel, Extra, create_model
from .utils import to_camel

__all__ = ('validate_arguments',)

if TYPE_CHECKING:
    from .typing import AnyCallable

    Callable = TypeVar('Callable', bound=AnyCallable)


def validate_arguments(function: 'Callable') -> 'Callable':
    """
    Decorator to validate the arguments passed to a function.
    """
    vd = ValidatedFunction(function)

    @wraps(function)
    def wrapper_function(*args: Any, **kwargs: Any) -> Any:
        return vd.call(*args, **kwargs)

    wrapper_function.vd = vd  # type: ignore
    wrapper_function.raw_function = vd.raw_function  # type: ignore
    wrapper_function.model = vd.model  # type: ignore
    return cast('Callable', wrapper_function)


ALT_V_ARGS = 'v__args'
ALT_V_KWARGS = 'v__kwargs'
V_POSITIONAL_ONLY_NAME = 'v__positional_only'


class ValidatedFunction:
    def __init__(self, function: 'Callable'):
        from inspect import signature, Parameter

        parameters: Mapping[str, Parameter] = signature(function).parameters

        if parameters.keys() & {ALT_V_ARGS, ALT_V_KWARGS, V_POSITIONAL_ONLY_NAME}:
            raise ConfigError(
                f'"{ALT_V_ARGS}", "{ALT_V_KWARGS}" and "{V_POSITIONAL_ONLY_NAME}" are not permitted as argument '
                f'names when using the "{validate_arguments.__name__}" decorator'
            )

        self.raw_function = function
        self.arg_mapping: Dict[int, str] = {}
        self.positional_only_args = set()
        self.v_args_name = 'args'
        self.v_kwargs_name = 'kwargs'

        type_hints = get_type_hints(function)
        takes_args = False
        takes_kwargs = False
        fields: Dict[str, Tuple[Any, Any]] = {}
        for i, (name, p) in enumerate(parameters.items()):
            if p.annotation == p.empty:
                annotation = Any
            else:
                annotation = type_hints[name]

            default = ... if p.default == p.empty else p.default
            if p.kind == Parameter.POSITIONAL_ONLY:
                self.arg_mapping[i] = name
                fields[name] = annotation, default
                fields[V_POSITIONAL_ONLY_NAME] = List[str], None
                self.positional_only_args.add(name)
            elif p.kind == Parameter.POSITIONAL_OR_KEYWORD:
                self.arg_mapping[i] = name
                fields[name] = annotation, default
            elif p.kind == Parameter.KEYWORD_ONLY:
                fields[name] = annotation, default
            elif p.kind == Parameter.VAR_POSITIONAL:
                self.v_args_name = name
                fields[name] = Tuple[annotation, ...], None
                takes_args = True
            else:
                assert p.kind == Parameter.VAR_KEYWORD, p.kind
                self.v_kwargs_name = name
                fields[name] = Dict[str, annotation], None  # type: ignore
                takes_kwargs = True

        # these checks avoid a clash between "args" and a field with that name
        if not takes_args and self.v_args_name in fields:
            self.v_args_name = ALT_V_ARGS

        # same with "kwargs"
        if not takes_kwargs and self.v_kwargs_name in fields:
            self.v_kwargs_name = ALT_V_KWARGS

        if not takes_args:
            # we add the field so validation below can raise the correct exception
            fields[self.v_args_name] = List[Any], None

        if not takes_kwargs:
            # same with kwargs
            fields[self.v_kwargs_name] = Dict[Any, Any], None

        self.create_model(fields, takes_args, takes_kwargs)

    def call(self, *args: Any, **kwargs: Any) -> Any:
        values = self.build_values(args, kwargs)
        m = self.model(**values)
        return self.execute(m)

    def build_values(self, args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> Dict[str, Any]:
        values: Dict[str, Any] = {}
        if args:
            arg_iter = enumerate(args)
            while True:
                try:
                    i, a = next(arg_iter)
                except StopIteration:
                    break
                arg_name = self.arg_mapping.get(i)
                if arg_name is not None:
                    values[arg_name] = a
                else:
                    values[self.v_args_name] = [a] + [a for _, a in arg_iter]
                    break

        var_kwargs = {}
        wrong_positional_args = []
        for k, v in kwargs.items():
            if k in self.model.__fields__:
                if k in self.positional_only_args:
                    wrong_positional_args.append(k)
                values[k] = v
            else:
                var_kwargs[k] = v

        if var_kwargs:
            values[self.v_kwargs_name] = var_kwargs
        if wrong_positional_args:
            values[V_POSITIONAL_ONLY_NAME] = wrong_positional_args
        return values

    def execute(self, m: BaseModel) -> Any:
        d = {k: v for k, v in m._iter() if k in m.__fields_set__}
        kwargs = d.pop(self.v_kwargs_name, None)
        if kwargs:
            d.update(kwargs)

        if self.v_args_name in d:
            args_: List[Any] = []
            in_kwargs = False
            kwargs = {}
            for name, value in d.items():
                if in_kwargs:
                    kwargs[name] = value
                elif name == self.v_args_name:
                    args_ += value
                    in_kwargs = True
                else:
                    args_.append(value)
            return self.raw_function(*args_, **kwargs)
        elif self.positional_only_args:
            args_ = []
            kwargs = {}
            for name, value in d.items():
                if name in self.positional_only_args:
                    args_.append(value)
                else:
                    kwargs[name] = value
            return self.raw_function(*args_, **kwargs)
        else:
            return self.raw_function(**d)

    def create_model(self, fields: Dict[str, Any], takes_args: bool, takes_kwargs: bool) -> None:
        pos_args = len(self.arg_mapping)

        class DecoratorBaseModel(BaseModel):
            @validator(self.v_args_name, check_fields=False, allow_reuse=True)
            def check_args(cls, v: List[Any]) -> List[Any]:
                if takes_args:
                    return v

                raise TypeError(f'{pos_args} positional arguments expected but {pos_args + len(v)} given')

            @validator(self.v_kwargs_name, check_fields=False, allow_reuse=True)
            def check_kwargs(cls, v: Dict[str, Any]) -> Dict[str, Any]:
                if takes_kwargs:
                    return v

                plural = '' if len(v) == 1 else 's'
                keys = ', '.join(map(repr, v.keys()))
                raise TypeError(f'unexpected keyword argument{plural}: {keys}')

            @validator(V_POSITIONAL_ONLY_NAME, check_fields=False, allow_reuse=True)
            def check_positional_only(cls, v: List[str]) -> None:
                plural = '' if len(v) == 1 else 's'
                keys = ', '.join(map(repr, v))
                raise TypeError(f'positional-only argument{plural} passed as keyword argument{plural}: {keys}')

            class Config:
                extra = Extra.forbid

        self.model = create_model(to_camel(self.raw_function.__name__), __base__=DecoratorBaseModel, **fields)
