Models can be [created dynamically](../concepts/models.md#dynamic-model-creation) using the [`create_model()`][pydantic.create_model]
factory function.

In this example, we will show how to dynamically derive a model from an existing one, and making every field optional. To achieve this,
we will make use of the [`model_fields`][pydantic.main.BaseModel.model_fields] model class attribute, and derive new annotations
from the field definitions to be passed to the [`create_model()`][pydantic.create_model] factory. Of course, this example can apply
to any use case where you need to derive a new model from another (remove default values, add aliases, etc).

=== "Python 3.9"

    ```python {lint="skip" linenums="1"}
    from typing import Annotated, Union

    from pydantic import BaseModel, Field, create_model


    def make_fields_optional(model_cls: type[BaseModel]) -> type[BaseModel]:
        new_fields = {}

        for f_name, f_info in model_cls.model_fields.items():
            f_dct = f_info.asdict()
            new_fields[f_name] = (
                Annotated[(Union[f_dct['annotation'], None], *f_dct['metadata'], Field(**f_dct['attributes']))],
                None,
            )

        return create_model(
            f'{type.__name__}Optional',
            __base__=model_cls,  # (1)!
            **new_fields,
        )
    ```

    1. Using the original model as a base will inherit the [validators](../concepts/validators.md), [computed fields](../concepts/fields.md#the-computed_field-decorator), etc.
    The parent fields are overridden by the ones we define.

=== "Python 3.10"

    ```python {lint="skip" requires="3.10" linenums="1"}
    from typing import Annotated

    from pydantic import BaseModel, Field, create_model


    def make_fields_optional(model_cls: type[BaseModel]) -> type[BaseModel]:
        new_fields = {}

        for f_name, f_info in model_cls.model_fields.items():
            f_dct = f_info.asdict()
            new_fields[f_name] = (
                Annotated[(f_dct['annotation'] | None, *f_dct['metadata'], Field(**f_dct['attributes']))],
                None,
            )

        return create_model(
            f'{type.__name__}Optional',
            __base__=model_cls,  # (1)!
            **new_fields,
        )
    ```

    1. Using the original model as a base will inherit the [validators](../concepts/validators.md), [computed fields](../concepts/fields.md#the-computed_field-decorator), etc.
    The parent fields are overridden by the ones we define.

=== "Python 3.11 and above"

    ```python {lint="skip" requires="3.11" linenums="1"}
    from typing import Annotated

    from pydantic import BaseModel, Field, create_model


    def make_fields_optional(model_cls: type[BaseModel]) -> type[BaseModel]:
        new_fields = {}

        for f_name, f_info in model_cls.model_fields.items():
            f_dct = f_info.asdict()
            new_fields[f_name] = (
                Annotated[f_dct['annotation'] | None, *f_dct['metadata'], Field(**f_dct['attributes'])],
                None,
            )

        return create_model(
            f'{type.__name__}Optional',
            __base__=model_cls,  # (1)!
            **new_fields,
        )
    ```

    1. Using the original model as a base will inherit the [validators](../concepts/validators.md), [computed fields](../concepts/fields.md#the-computed_field-decorator), etc.
    The parent fields are overridden by the ones we define.

For each field, we generate a dictionary representation of the [`FieldInfo`][pydantic.fields.FieldInfo] instance
using the [`asdict()`][pydantic.fields.FieldInfo.asdict] method, containing the annotation, metadata and attributes.

With the following model:

```python {lint="skip" test="skip"}
class Model(BaseModel):
    f: Annotated[int, Field(gt=1), WithJsonSchema({'extra': 'data'}), Field(title='F')] = 1
```

The [`FieldInfo`][pydantic.fields.FieldInfo] instance of `f` will have three items in its dictionary representation:

* `annotation`: `int`.
* `metadata`: A list containing the type-specific constraints and other metadata: `[Gt(1), WithJsonSchema({'extra': 'data'})]`.
* `attributes`: The remaining field-specific attributes: `{'title': 'F'}`.

With that in mind, we can recreate an annotation that "simulates" the one from the original model:

=== "Python 3.9 and above"

    ```python {lint="skip" test="skip"}
    new_annotation = Annotated[(
        f_dct['annotation'] | None,  # (1)!
        *f_dct['metadata'],  # (2)!
        Field(**f_dct['attributes']),  # (3)!
    )]
    ```

    1. We create a new annotation from the existing one, but adding `None` as an allowed value
       (in our previous example, this is equivalent to `int | None`).

    2. We unpack the metadata to be reused (in our previous example, this is equivalent to
       specifying `Field(gt=1)` and `WithJsonSchema({'extra': 'data'})` as [`Annotated`][typing.Annotated]
       metadata).

    3. We specify the field-specific attributes by using the [`Field()`][pydantic.Field] function
       (in our previous example, this is equivalent to `Field(title='F')`).

=== "Python 3.11 and above"

    ```python {lint="skip" test="skip"}
    new_annotation = Annotated[
        f_dct['annotation'] | None,  # (1)!
        *f_dct['metadata'],  # (2)!
        Field(**f_dct['attributes']),  # (3)!
    ]
    ```

    1. We create a new annotation from the existing one, but adding `None` as an allowed value
       (in our previous example, this is equivalent to `int | None`).

    2. We unpack the metadata to be reused (in our previous example, this is equivalent to
       specifying `Field(gt=1)` and `WithJsonSchema({'extra': 'data'})` as [`Annotated`][typing.Annotated]
       metadata).

    3. We specify the field-specific attributes by using the [`Field()`][pydantic.Field] function
       (in our previous example, this is equivalent to `Field(title='F')`).

and specify `None` as a default value (the second element of the tuple for the field definition accepted by [`create_model()`][pydantic.create_model]).

Here is a demonstration of our factory function:

```python {lint="skip" test="skip"}
from pydantic import BaseModel, Field


class Model(BaseModel):
    a: Annotated[int, Field(gt=1)]


ModelOptional = make_fields_optional(Model)

m = ModelOptional()
print(m.a)
#> None
```

A couple notes on the implementation:

* Our `make_fields_optional()` function is defined as returning an arbitrary Pydantic model class (`-> type[BaseModel]`).
  An alternative solution can be to use a type variable to preserve the input class:

    === "Python 3.9 and above"

        ```python {lint="skip" test="skip"}
        ModelTypeT = TypeVar('ModelTypeT', bound=type[BaseModel])

        def make_fields_optional(model_cls: ModelTypeT) -> ModelTypeT:
            ...
        ```

    === "Python 3.12 and above"

        ```python {lint="skip" test="skip"}
        def make_fields_optional[ModelTypeT: type[BaseModel]](model_cls: ModelTypeT) -> ModelTypeT:
            ...
        ```

    However, note that static type checkers *won't* be able to understand that all fields are now optional.

* The experimental [`MISSING` sentinel](../concepts/experimental.md#missing-sentinel) can be used as an alternative to `None`
  for the default values. Simply replace `None` by `MISSING` in the new annotation and default value.

* You might be tempted to make a copy of the original [`FieldInfo`][pydantic.fields.FieldInfo] instances, add a
  default and/or perform other mutations, to then reuse it as [`Annotated`][typing.Annotated] metadata. While this
  may work in some cases, it is **not** a supported pattern, and could break or be deprecated at any point. We strongly
  encourage using the pattern from this example instead.
