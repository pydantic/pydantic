Where possible Pydantic uses [standard library types](standard_types.md) to define fields, thus smoothing
the learning curve. For many useful applications, however, no standard library type exists,
so Pydantic implements many commonly used types.

If no existing type suits your purpose you can also implement your [own Pydantic-compatible types](custom.md#custom-data-types) with custom properties and validation.

The following sections describe the types supported by Pydantic.


* [Standard Library Types](standard_types.md) &mdash; types from the Python standard library.
* [Booleans](booleans.md) &mdash; `bool` types.
* [ByteSize](bytesize.md) &mdash; a type that allows handling byte string representations in your model.
* [Callables](callables.md) &mdash; `Callable` types.
* [Color Types](color_types.md) &mdash; color validation types.
* [Datetimes](datetime.md) &mdash; `datetime`, `date`, `time`, and `timedelta` types.
* [Dicts and Mapping Types](dicts_mapping.md) &mdash; `dict` types and mapping types.
* [Enums and Choices](enums.md) &mdash; uses Python's standard `enum` classes to define choices.
* [File Types](file_types.md) &mdash; types for handling files and paths.
* [JSON](json.md) &mdash; a type that allows you to store JSON data in your model.
* [Lists and Tuples](list_types.md) &mdash; `list` and `tuple` types.
* [Number Types](number_types.md) &mdash; `int`, `float`, `Decimal`, and other number types.
* [Payment Card Numbers](payment_cards.md) &mdash; a type that allows you to store payment card numbers in your model.
* [Secret Types](secrets.md) &mdash; types for storing sensitive information that you do not want to be visible in logging or tracebacks.
* [Sequence, Iterable, & Iterator](sequence_iterable.md) &mdash; iterable types including `Sequence`, `Iterable`, and `Iterator`.
* [Sets and frozenset](set_types.md) &mdash; `set` and `frozenset` types.
* [String Types](string_types.md) &mdash; `str` types.
* [Type and TypeVar](typevars.md) &mdash; `Type` and `TypeVar` types.
* [Types with Fields](types_fields.md) &mdash; types that allow you to define fields.
* [Unions](unions.md) &mdash; allows a model attribute to accept different types.
* [URLs](urls.md) &mdash; URI/URL validation types.
* [UUIDs](uuids.md) &mdash; types that allow you to store UUIDs in your model.
* [Custom Data Types](custom.md) &mdash; create your own custom data types.
* [Field Type Conversions](../conversion_table.md) &mdash; strict and lax conversion between different field types.
