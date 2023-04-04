Where possible *pydantic* uses [standard library types](/usage/standard_types/#standard-library-types) to define fields, thus smoothing
the learning curve. For many useful applications, however, no standard library type exists,
so *pydantic* implements [many commonly used types](/usage/pydantic_types/#pydantic-types).

If no existing type suits your purpose you can also implement your [own pydantic-compatible types](/usage/custom/#custom-data-types) with custom properties and validation.

The following sections describe the types supported by Pydantic.

* [Standard Library Types](/usage/standard_types/) &mdash; types from the Python standard library.
* [Typing Iterables](/usage/typing_iterables/) &mdash; iterable `typing` types including `Deque`, `Dict`, `FrozenSet`, `List`, `Optional`, `Sequence`, `Set`, and `Tuple`.
* [Unions](/usage/unions/) &mdash; allows a model attribute to accept different types.
* [Enums and Choices](/usage/enums/) &mdash; uses Python's standard `enum` classes to define choices.
* [Datetime Types](/usage/datetimes/) &mdash; `datetime`, `date`, `time`, and `timedelta` types.
* [Booleans](/usage/booleans/) &mdash; `bool` types.
* [Callable](/usage/callable/) &mdash; `Callable` types.
* [Type and TypeVar](/usage/typevars/) &mdash; `Type` and `TypeVar` types.
* [Literal](/usage/literals/) &mdash; `Literal` types.
* [Annotated Types](/usage/annotated_types/) &mdash; `Annotated` types, including `NamedTuple` and `TypedDict`.
* [Pydantic Types](/usage/pydantic_types/) &mdash; general types provided by Pydantic.
* [ImportString](/usage/importstring/) &mdash; a type that references a Python module or object by string name.
* [URLs](/usage/urls/) &mdash; URI/URL validation types.
* [Color Types](/usage/colors/) &mdash; color validation types.
* [Secret Types](/usage/secrets/) &mdash; types for storing sensitive information that you do not want to be visible in logging or tracebacks.
* [Json Type](/usage/json/) &mdash; a type that allows you to store JSON data in your model.
* [Payment Card Numbers](/usage/payment_cards/) &mdash; a type that allows you to store payment card numbers in your model.
* [Constrained Types](/usage/constrained/) &mdash; types that allow you to constrain the values of standard library types.
* [Strict Types](/usage/strict/) &mdash; types that prevent coercion from compatible types.
* [ByteSize](/usage/bytes/) &mdash; a type that allows handling byte string representations in your model.
* [Custom Data Types](/usage/custom/) &mdash; how to define your own custom data types.
* Field Type Conversions &mdash; strict and lax conversion between different field types.
