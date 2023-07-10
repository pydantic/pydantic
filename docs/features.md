
## Why use Pydantic?

Built-in Python type annotations are a useful way to hint about the expected type of data, improving code clarity and supporting development tools. However, Python's type annotations are optional and don't affect the runtime behavior of the program.

Static type checkers like [mypy](https://mypy-lang.org/) use type annotations to catch potential type-related errors before running the program. But static type checkers can't catch all errors, and they don't affect the runtime behavior of the program.

Pydantic, on the other hand, uses type annotations to perform [data validation](usage/validators.md) and [type coercion](usage/conversion_table.md) at runtime, which is particularly useful for ensuring the correctness of user or external data.

Pydantic enables you to convert input data to Python [standard library types and custom types](usage/types/types.md) in a controlled manner, ensuring they meet the specifications you've provided. This eliminates a significant amount of manual data validation and transformation code, making your program more robust and less prone to errors. It's particularly helpful when dealing with untrusted user input such as form data, [JSON documents](usage/json_schema.md), and other data types.

By providing a simple, declarative way of defining how data should be shaped, Pydantic helps you write cleaner, safer, and more reliable code.

## Features of Pydantic

Some of the main features of Pydantic include:

- [**Data validation**](usage/validators.md): Pydantic validates data as it is assigned to ensure it meets the requirements. It automatically handles a broad range of data types, including custom types and custom validators.
- [**Standard library and custom data types**](usage/types/types.md): Pydantic supports all of the Python standard library types, and you can define custom data types and specify how they should be validated and converted.
- [**Conversion types**](usage/conversion_table.md): Pydantic will not only validate data, but also convert it to the appropriate type if possible. For instance, a string containing a number will be converted to the proper numerical type.
- [**Custom and nested models**](usage/models.md): You can define models (similar to classes) that contain other models, allowing for complex data structures to be neatly and efficiently represented.
- [**Generic models**](usage/models.md#generic-models): Pydantic supports generic models, which allow the declaration of models that are "parameterized" on one or more fields.
- [**Dataclasses**](usage/dataclasses.md): Pydantic supports `dataclasses.dataclass`, offering same data validation as using `BaseModel`.
- [**Model schema generation**](usage/json_schema.md): Pydantic models can be converted to and from a JSON Schema, which can be useful for documentation, code generation, or other purposes.
- [**Error handling**](errors/errors.md): Pydantic models raise informative errors when invalid data is provided, with the option to create your own [custom errors](errors/errors.md#custom-errors).
- [**Settings management**](api/pydantic_settings.md): The `BaseSettings` class from [pydantic-settings](https://github.com/pydantic/pydantic-settings) provides a way to validate, document, and provide default values for environment variables.

Pydantic is simple to use, even when doing complex things, and enables you to define and validate data in pure, canonical Python.
