# Experimental API

## Pipeline API

Experimental pipeline API functionality. Be careful with this API, it's subject to change.

## \_Pipeline

```python
_Pipeline(_steps: tuple[_Step, ...])

```

Bases: `Generic[_InT, _OutT]`

Abstract representation of a chain of validation, transformation, and parsing steps.

### transform

```python
transform(
    func: Callable[[_OutT], _NewOutT]
) -> _Pipeline[_InT, _NewOutT]

```

Transform the output of the previous step.

If used as the first step in a pipeline, the type of the field is used. That is, the transformation is applied to after the value is parsed to the field's type.

Source code in `pydantic/experimental/pipeline.py`

```python
def transform(
    self,
    func: Callable[[_OutT], _NewOutT],
) -> _Pipeline[_InT, _NewOutT]:
    """Transform the output of the previous step.

    If used as the first step in a pipeline, the type of the field is used.
    That is, the transformation is applied to after the value is parsed to the field's type.
    """
    return _Pipeline[_InT, _NewOutT](self._steps + (_Transform(func),))

```

### validate_as

```python
validate_as(
    tp: type[_NewOutT], *, strict: bool = ...
) -> _Pipeline[_InT, _NewOutT]

```

```python
validate_as(
    tp: EllipsisType, *, strict: bool = ...
) -> _Pipeline[_InT, Any]

```

```python
validate_as(
    tp: type[_NewOutT] | EllipsisType,
    *,
    strict: bool = False
) -> _Pipeline[_InT, Any]

```

Validate / parse the input into a new type.

If no type is provided, the type of the field is used.

Types are parsed in Pydantic's `lax` mode by default, but you can enable `strict` mode by passing `strict=True`.

Source code in `pydantic/experimental/pipeline.py`

```python
def validate_as(self, tp: type[_NewOutT] | EllipsisType, *, strict: bool = False) -> _Pipeline[_InT, Any]:  # type: ignore
    """Validate / parse the input into a new type.

    If no type is provided, the type of the field is used.

    Types are parsed in Pydantic's `lax` mode by default,
    but you can enable `strict` mode by passing `strict=True`.
    """
    if isinstance(tp, EllipsisType):
        return _Pipeline[_InT, Any](self._steps + (_ValidateAs(_FieldTypeMarker, strict=strict),))
    return _Pipeline[_InT, _NewOutT](self._steps + (_ValidateAs(tp, strict=strict),))

```

### validate_as_deferred

```python
validate_as_deferred(
    func: Callable[[], type[_NewOutT]]
) -> _Pipeline[_InT, _NewOutT]

```

Parse the input into a new type, deferring resolution of the type until the current class is fully defined.

This is useful when you need to reference the class in it's own type annotations.

Source code in `pydantic/experimental/pipeline.py`

```python
def validate_as_deferred(self, func: Callable[[], type[_NewOutT]]) -> _Pipeline[_InT, _NewOutT]:
    """Parse the input into a new type, deferring resolution of the type until the current class
    is fully defined.

    This is useful when you need to reference the class in it's own type annotations.
    """
    return _Pipeline[_InT, _NewOutT](self._steps + (_ValidateAsDefer(func),))

```

### constrain

```python
constrain(constraint: Ge) -> _Pipeline[_InT, _NewOutGe]

```

```python
constrain(constraint: Gt) -> _Pipeline[_InT, _NewOutGt]

```

```python
constrain(constraint: Le) -> _Pipeline[_InT, _NewOutLe]

```

```python
constrain(constraint: Lt) -> _Pipeline[_InT, _NewOutLt]

```

```python
constrain(constraint: Len) -> _Pipeline[_InT, _NewOutLen]

```

```python
constrain(
    constraint: MultipleOf,
) -> _Pipeline[_InT, _NewOutT]

```

```python
constrain(
    constraint: Timezone,
) -> _Pipeline[_InT, _NewOutDatetime]

```

```python
constrain(constraint: Predicate) -> _Pipeline[_InT, _OutT]

```

```python
constrain(
    constraint: Interval,
) -> _Pipeline[_InT, _NewOutInterval]

```

```python
constrain(constraint: _Eq) -> _Pipeline[_InT, _OutT]

```

```python
constrain(constraint: _NotEq) -> _Pipeline[_InT, _OutT]

```

```python
constrain(constraint: _In) -> _Pipeline[_InT, _OutT]

```

```python
constrain(constraint: _NotIn) -> _Pipeline[_InT, _OutT]

```

```python
constrain(
    constraint: Pattern[str],
) -> _Pipeline[_InT, _NewOutT]

```

```python
constrain(constraint: _ConstraintAnnotation) -> Any

```

Constrain a value to meet a certain condition.

We support most conditions from `annotated_types`, as well as regular expressions.

Most of the time you'll be calling a shortcut method like `gt`, `lt`, `len`, etc so you don't need to call this directly.

Source code in `pydantic/experimental/pipeline.py`

```python
def constrain(self, constraint: _ConstraintAnnotation) -> Any:
    """Constrain a value to meet a certain condition.

    We support most conditions from `annotated_types`, as well as regular expressions.

    Most of the time you'll be calling a shortcut method like `gt`, `lt`, `len`, etc
    so you don't need to call this directly.
    """
    return _Pipeline[_InT, _OutT](self._steps + (_Constraint(constraint),))

```

### predicate

```python
predicate(
    func: Callable[[_NewOutT], bool]
) -> _Pipeline[_InT, _NewOutT]

```

Constrain a value to meet a certain predicate.

Source code in `pydantic/experimental/pipeline.py`

```python
def predicate(self: _Pipeline[_InT, _NewOutT], func: Callable[[_NewOutT], bool]) -> _Pipeline[_InT, _NewOutT]:
    """Constrain a value to meet a certain predicate."""
    return self.constrain(annotated_types.Predicate(func))

```

### gt

```python
gt(gt: _NewOutGt) -> _Pipeline[_InT, _NewOutGt]

```

Constrain a value to be greater than a certain value.

Source code in `pydantic/experimental/pipeline.py`

```python
def gt(self: _Pipeline[_InT, _NewOutGt], gt: _NewOutGt) -> _Pipeline[_InT, _NewOutGt]:
    """Constrain a value to be greater than a certain value."""
    return self.constrain(annotated_types.Gt(gt))

```

### lt

```python
lt(lt: _NewOutLt) -> _Pipeline[_InT, _NewOutLt]

```

Constrain a value to be less than a certain value.

Source code in `pydantic/experimental/pipeline.py`

```python
def lt(self: _Pipeline[_InT, _NewOutLt], lt: _NewOutLt) -> _Pipeline[_InT, _NewOutLt]:
    """Constrain a value to be less than a certain value."""
    return self.constrain(annotated_types.Lt(lt))

```

### ge

```python
ge(ge: _NewOutGe) -> _Pipeline[_InT, _NewOutGe]

```

Constrain a value to be greater than or equal to a certain value.

Source code in `pydantic/experimental/pipeline.py`

```python
def ge(self: _Pipeline[_InT, _NewOutGe], ge: _NewOutGe) -> _Pipeline[_InT, _NewOutGe]:
    """Constrain a value to be greater than or equal to a certain value."""
    return self.constrain(annotated_types.Ge(ge))

```

### le

```python
le(le: _NewOutLe) -> _Pipeline[_InT, _NewOutLe]

```

Constrain a value to be less than or equal to a certain value.

Source code in `pydantic/experimental/pipeline.py`

```python
def le(self: _Pipeline[_InT, _NewOutLe], le: _NewOutLe) -> _Pipeline[_InT, _NewOutLe]:
    """Constrain a value to be less than or equal to a certain value."""
    return self.constrain(annotated_types.Le(le))

```

### len

```python
len(
    min_len: int, max_len: int | None = None
) -> _Pipeline[_InT, _NewOutLen]

```

Constrain a value to have a certain length.

Source code in `pydantic/experimental/pipeline.py`

```python
def len(self: _Pipeline[_InT, _NewOutLen], min_len: int, max_len: int | None = None) -> _Pipeline[_InT, _NewOutLen]:
    """Constrain a value to have a certain length."""
    return self.constrain(annotated_types.Len(min_len, max_len))

```

### multiple_of

```python
multiple_of(
    multiple_of: _NewOutDiv,
) -> _Pipeline[_InT, _NewOutDiv]

```

```python
multiple_of(
    multiple_of: _NewOutMod,
) -> _Pipeline[_InT, _NewOutMod]

```

```python
multiple_of(multiple_of: Any) -> _Pipeline[_InT, Any]

```

Constrain a value to be a multiple of a certain number.

Source code in `pydantic/experimental/pipeline.py`

```python
def multiple_of(self: _Pipeline[_InT, Any], multiple_of: Any) -> _Pipeline[_InT, Any]:
    """Constrain a value to be a multiple of a certain number."""
    return self.constrain(annotated_types.MultipleOf(multiple_of))

```

### eq

```python
eq(value: _OutT) -> _Pipeline[_InT, _OutT]

```

Constrain a value to be equal to a certain value.

Source code in `pydantic/experimental/pipeline.py`

```python
def eq(self: _Pipeline[_InT, _OutT], value: _OutT) -> _Pipeline[_InT, _OutT]:
    """Constrain a value to be equal to a certain value."""
    return self.constrain(_Eq(value))

```

### not_eq

```python
not_eq(value: _OutT) -> _Pipeline[_InT, _OutT]

```

Constrain a value to not be equal to a certain value.

Source code in `pydantic/experimental/pipeline.py`

```python
def not_eq(self: _Pipeline[_InT, _OutT], value: _OutT) -> _Pipeline[_InT, _OutT]:
    """Constrain a value to not be equal to a certain value."""
    return self.constrain(_NotEq(value))

```

### in\_

```python
in_(values: Container[_OutT]) -> _Pipeline[_InT, _OutT]

```

Constrain a value to be in a certain set.

Source code in `pydantic/experimental/pipeline.py`

```python
def in_(self: _Pipeline[_InT, _OutT], values: Container[_OutT]) -> _Pipeline[_InT, _OutT]:
    """Constrain a value to be in a certain set."""
    return self.constrain(_In(values))

```

### not_in

```python
not_in(values: Container[_OutT]) -> _Pipeline[_InT, _OutT]

```

Constrain a value to not be in a certain set.

Source code in `pydantic/experimental/pipeline.py`

```python
def not_in(self: _Pipeline[_InT, _OutT], values: Container[_OutT]) -> _Pipeline[_InT, _OutT]:
    """Constrain a value to not be in a certain set."""
    return self.constrain(_NotIn(values))

```

### otherwise

```python
otherwise(
    other: _Pipeline[_OtherIn, _OtherOut]
) -> _Pipeline[_InT | _OtherIn, _OutT | _OtherOut]

```

Combine two validation chains, returning the result of the first chain if it succeeds, and the second chain if it fails.

Source code in `pydantic/experimental/pipeline.py`

```python
def otherwise(self, other: _Pipeline[_OtherIn, _OtherOut]) -> _Pipeline[_InT | _OtherIn, _OutT | _OtherOut]:
    """Combine two validation chains, returning the result of the first chain if it succeeds, and the second chain if it fails."""
    return _Pipeline((_PipelineOr(self, other),))

```

### then

```python
then(
    other: _Pipeline[_OutT, _OtherOut]
) -> _Pipeline[_InT, _OtherOut]

```

Pipe the result of one validation chain into another.

Source code in `pydantic/experimental/pipeline.py`

```python
def then(self, other: _Pipeline[_OutT, _OtherOut]) -> _Pipeline[_InT, _OtherOut]:
    """Pipe the result of one validation chain into another."""
    return _Pipeline((_PipelineAnd(self, other),))

```

## Arguments schema API

Experimental module exposing a function to generate a core schema that validates callable arguments.

## generate_arguments_schema

```python
generate_arguments_schema(
    func: Callable[..., Any],
    schema_type: Literal[
        "arguments", "arguments-v3"
    ] = "arguments-v3",
    parameters_callback: (
        Callable[[int, str, Any], Literal["skip"] | None]
        | None
    ) = None,
    config: ConfigDict | None = None,
) -> CoreSchema

```

Generate the schema for the arguments of a function.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `func` | `Callable[..., Any]` | The function to generate the schema for. | *required* | | `schema_type` | `Literal['arguments', 'arguments-v3']` | The type of schema to generate. | `'arguments-v3'` | | `parameters_callback` | `Callable[[int, str, Any], Literal['skip'] | None] | None` | A callable that will be invoked for each parameter. The callback should take three required arguments: the index, the name and the type annotation (or Parameter.empty if not annotated) of the parameter. The callback can optionally return 'skip', so that the parameter gets excluded from the resulting schema. | `None` | | `config` | `ConfigDict | None` | The configuration to use. | `None` |

Returns:

| Type | Description | | --- | --- | | `CoreSchema` | The generated schema. |

Source code in `pydantic/experimental/arguments_schema.py`

```python
def generate_arguments_schema(
    func: Callable[..., Any],
    schema_type: Literal['arguments', 'arguments-v3'] = 'arguments-v3',
    parameters_callback: Callable[[int, str, Any], Literal['skip'] | None] | None = None,
    config: ConfigDict | None = None,
) -> CoreSchema:
    """Generate the schema for the arguments of a function.

    Args:
        func: The function to generate the schema for.
        schema_type: The type of schema to generate.
        parameters_callback: A callable that will be invoked for each parameter. The callback
            should take three required arguments: the index, the name and the type annotation
            (or [`Parameter.empty`][inspect.Parameter.empty] if not annotated) of the parameter.
            The callback can optionally return `'skip'`, so that the parameter gets excluded
            from the resulting schema.
        config: The configuration to use.

    Returns:
        The generated schema.
    """
    generate_schema = _generate_schema.GenerateSchema(
        _config.ConfigWrapper(config),
        ns_resolver=_namespace_utils.NsResolver(namespaces_tuple=_namespace_utils.ns_for_function(func)),
    )

    if schema_type == 'arguments':
        schema = generate_schema._arguments_schema(func, parameters_callback)  # pyright: ignore[reportArgumentType]
    else:
        schema = generate_schema._arguments_v3_schema(func, parameters_callback)  # pyright: ignore[reportArgumentType]
    return generate_schema.clean_schema(schema)

```
