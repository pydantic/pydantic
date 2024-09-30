from pydantic.dataclasses import dataclass


@dataclass
# MYPY: error: Expression type contains "Any" (has type overloaded function)  [misc]
class Foo:
    foo: int


@dataclass(config={'title': 'Bar Title'})
# MYPY: error: No overload variant of "dataclass" matches argument type "Dict[str, str]"  [call-overload]
# MYPY: note: Possible overload variants:
# MYPY: note:     def dataclass(*, init: Literal[False] = ..., repr: bool = ..., eq: bool = ..., order: bool = ..., unsafe_hash: bool = ..., frozen: bool = ..., config: Union[ConfigDict, Type[object], None] = ..., validate_on_init: Optional[bool] = ..., kw_only: bool = ..., slots: bool = ...) -> Callable[[Type[_T]], Type[PydanticDataclass]]
# MYPY: note:     def [_T] dataclass(_cls: Type[_T], *, init: Literal[False] = ..., repr: bool = ..., eq: bool = ..., order: bool = ..., unsafe_hash: bool = ..., frozen: Optional[bool] = ..., config: Union[ConfigDict, Type[object], None] = ..., validate_on_init: Optional[bool] = ..., kw_only: bool = ..., slots: bool = ...) -> Type[PydanticDataclass]
# MYPY: error: Expression has type "Any"  [misc]
class Bar:
    bar: str
