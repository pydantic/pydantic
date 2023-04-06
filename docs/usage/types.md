Where possible *pydantic* uses [standard library types](/usage/standard_types/) to define fields, thus smoothing
the learning curve. For many useful applications, however, no standard library type exists,
so *pydantic* implements [many commonly used types](/usage/pydantic_types/#pydantic-types).

If no existing type suits your purpose you can also implement your [own pydantic-compatible types](/usage/custom/#custom-data-types) with custom properties and validation.

The following sections describe the types supported by Pydantic.


* [Standard Library Types](/usage/standard_types/) &mdash; types from the Python standard library.
* [Booleans](usage/booleans/) &mdash; `bool` types.
* [ByteSize](usage/bytesize/) &mdash; a type that allows handling byte string representations in your model.
* [Callables](usage/callables/) &mdash; `Callable` types.
* [Color Types](usage/color_types/) &mdash; color validation types.
* [Datetimes](usage/datetime/) &mdash; `datetime`, `date`, `time`, and `timedelta` types.
* [Dicts and Mapping](usage/dicts_mapping/) &mdash;
* [Enums and Choices](usage/enums/) &mdash; uses Python's standard `enum` classes to define choices.
* [File Types](usage/filetypes/) &mdash; types for handling files and paths.
* [JSON](usage/json/) &mdash; a type that allows you to store JSON data in your model.
* [Lists and Tuples](usage/list_types/) &mdash;
* [Number Types](usage/number_types/) &mdash;
* [Payment Card Numbers](usage/payment_cards/) &mdash; a type that allows you to store payment card numbers in your model.
* [Secret Types](usage/secrets/) &mdash; types for storing sensitive information that you do not want to be visible in logging or tracebacks.
* [Sequence, Iterable, & Iterator](usage/sequence_iterable/) &mdash; iterable types including `Sequence`, `Iterable`, and `Iterator`.
* [Sets and frozenset](usage/set_types/) &mdash;
* [String Types](usage/string_types/) &mdash;
* [Type and TypeVar](usage/typevars/) &mdash; `Type` and `TypeVar` types.
* [Types with Fields](usage/types_fields/) &mdash;
* [Unions](usage/unions/) &mdash; allows a model attribute to accept different types.
* [URLs](usage/urls/) &mdash; URI/URL validation types.
* [UUIDs](usage/uuids/) &mdash; types that allow you to store UUIDs in your model.
* [Custom Data Types](usage/custom/) &mdash;
* Field Type Conversions &mdash; strict and lax conversion between different field types.
