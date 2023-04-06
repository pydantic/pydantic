Where possible *pydantic* uses [standard library types](/usage/standard_types/) to define fields, thus smoothing
the learning curve. For many useful applications, however, no standard library type exists,
so *pydantic* implements [many commonly used types](/usage/pydantic_types/#pydantic-types).

If no existing type suits your purpose you can also implement your [own pydantic-compatible types](/usage/custom/#custom-data-types) with custom properties and validation.

The following sections describe the types supported by Pydantic.

* [Standard Library Types](/usage/standard_types/) &mdash; types from the Python standard library.
* [Booleans](/usage/booleans/) &mdash; `bool` types.
* [ByteSize](/usage/bytesize/) &mdash; a type that allows handling byte string representations in your model.
* [Callable](/usage/callable/) &mdash; `Callable` types.
* [Color Types](/usage/color_types/) &mdash; color validation types.
* [Custom Data Types](/usage/custom/) &mdash; how to define your own custom data types.
* [Datetime Types](/usage/datetimes/) &mdash; `datetime`, `date`, `time`, and `timedelta` types.
* [Enums and Choices](/usage/enums/) &mdash; uses Python's standard `enum` classes to define choices.
* [File Types](/usage/filetypes/) &mdash; types for handling files and paths.
* [Json Type](/usage/json/) &mdash; a type that allows you to store JSON data in your model.
* [Payment Card Numbers](/usage/payment_cards/) &mdash; a type that allows you to store payment card numbers in your model.
* [Pydantic Types](/usage/pydantic_types/) &mdash; general types provided by Pydantic.
* [Secret Types](/usage/secrets/) &mdash; types for storing sensitive information that you do not want to be visible in logging or tracebacks.
* [Special String Types](/usage/string_types/) &mdash; types that handle specialized uses of strings such as email addresses and module references.
* [Type and TypeVar](/usage/typevars/) &mdash; `Type` and `TypeVar` types.
* [Types with Fields](/usage/types_fields/) &mdash; `Annotated` types, including `NamedTuple` and `TypedDict`.
* [Typing Iterables](/usage/typing_iterables/) &mdash; iterable `typing` types including `Deque`, `Dict`, `FrozenSet`, `List`, `Optional`, `Sequence`, `Set`, and `Tuple`.
* [Unions](/usage/unions/) &mdash; allows a model attribute to accept different types.
* [URLs](/usage/urls/) &mdash; URI/URL validation types.
* [UUIDs](/usage/uuids/) &mdash; types that allow you to store UUIDs in your model.
* Field Type Conversions &mdash; strict and lax conversion between different field types.
