from functools import update_wrapper
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Tuple, TypeVar, cast

from . import validator
from .main import BaseModel, Extra, create_model
from .utils import to_camel

__all__ = 'validate_arguments', 'DecoratorSetupError'

if TYPE_CHECKING:
    from .typing import AnyCallable

    Callable = TypeVar('Callable', bound=AnyCallable)


def validate_arguments(function: 'Callable') -> 'Callable':
    """
    Decorator to validate the arguments to a function.
    """
    vd = ValidatedFunction(function)
    vd = update_wrapper(vd, function)  # type: ignore
    return cast('Callable', vd)


class DecoratorSetupError(TypeError):
    pass


V_ARGS = 'v_args'
V_KWARGS = 'v_kwargs'
V_POSITIONAL_ONLY = 'v_positional_only'


class ValidatedFunction:
    def __init__(self, function: 'Callable'):
        from inspect import signature, Parameter

        self.raw_function = function
        self.arg_mapping: Dict[int, str] = {}
        self.positional_only_args = set()

        parameters: Mapping[str, Parameter] = signature(function).parameters

        if parameters.keys() & {V_ARGS, V_KWARGS, V_POSITIONAL_ONLY}:
            raise DecoratorSetupError(
                f'"{V_ARGS}", "{V_KWARGS}" and "{V_POSITIONAL_ONLY}" are not permitted as argument names when '
                f'using the "validate_arguments" decorator'
            )

        fields: Dict[str, Any] = {}
        for i, (name, p) in enumerate(parameters.items()):
            if p.annotation == p.empty:
                annotation = Any
            else:
                # TODO if str update forward ref
                annotation = p.annotation

            default = ... if p.default == p.empty else p.default
            if p.kind == Parameter.POSITIONAL_ONLY:
                self.arg_mapping[i] = name
                fields[name] = annotation, default
                fields[V_POSITIONAL_ONLY] = List[str], None
                self.positional_only_args.add(name)
            elif p.kind == Parameter.POSITIONAL_OR_KEYWORD:
                self.arg_mapping[i] = name
                fields[name] = annotation, default
            elif p.kind == Parameter.KEYWORD_ONLY:
                fields[name] = annotation, default
            elif p.kind == Parameter.VAR_POSITIONAL:
                fields[V_ARGS] = Tuple[annotation, ...], None
            else:
                assert p.kind == Parameter.VAR_KEYWORD, p.kind
                fields[V_KWARGS] = Dict[str, annotation], None  # type: ignore

        self.create_model(fields)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
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
                    values[V_ARGS] = [a] + [a for _, a in arg_iter]
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
            values[V_KWARGS] = var_kwargs
        if wrong_positional_args:
            values[V_POSITIONAL_ONLY] = wrong_positional_args
        return values

    def execute(self, m: BaseModel) -> Any:
        d = {k: v for k, v in m._iter() if k in m.__fields_set__}
        kwargs = d.pop(V_KWARGS, None)
        if kwargs:
            d.update(kwargs)

        if V_ARGS in d:
            args_: List[Any] = []
            in_kwargs = False
            kwargs = {}
            for name, value in d.items():
                if in_kwargs:
                    kwargs[name] = value
                elif name == V_ARGS:
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

    def create_model(self, fields: Dict[str, Any]) -> None:
        takes_args = V_ARGS in fields
        if not takes_args:
            # we add the field so validation below can raise the correct exception
            fields[V_ARGS] = List[Any], None
        takes_kwargs = V_KWARGS in fields
        if not takes_kwargs:
            # we add the field so validation below can raise the correct exception
            fields[V_KWARGS] = Dict[Any, Any], None

        pos_args = len(self.arg_mapping)

        class DecoratorBaseModel(BaseModel):
            @validator(V_ARGS, check_fields=False, allow_reuse=True)
            def check_args(cls, v: List[Any]) -> List[Any]:
                if takes_args:
                    return v

                raise TypeError(f'{pos_args} positional arguments taken but {pos_args + len(v)} given')

            @validator(V_KWARGS, check_fields=False, allow_reuse=True)
            def check_kwargs(cls, v: Dict[str, Any]) -> Dict[str, Any]:
                if takes_kwargs:
                    return v

                plural = '' if len(v) == 1 else 's'
                keys = ', '.join(map(repr, v.keys()))
                raise TypeError(f'unexpected keyword argument{plural}: {keys}')

            @validator(V_POSITIONAL_ONLY, check_fields=False, allow_reuse=True)
            def check_positional_only(cls, v: List[str]) -> None:
                plural = '' if len(v) == 1 else 's'
                keys = ', '.join(map(repr, v))
                raise TypeError(f'positional-only argument{plural} passed as keyword argument{plural}: {keys}')

            class Config:
                extra = Extra.forbid

        self.model = create_model(to_camel(self.raw_function.__name__), __base__=DecoratorBaseModel, **fields)
