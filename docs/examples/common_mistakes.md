!!! warning "🚧 Work in Progress"
    This page is a work in progress.

# Common mistakes and questions

We created this section to address issues that are repeats of the same common mistakes or questions submitted on github.

## How to implement custom error messages?

You can customize error messages by creating a custom error handler.
See [here](https://docs.pydantic.dev/latest/errors/errors/#customize-error-messages) for more details.

## Cannot use v1 model as type parameter in v2 generic model

We have removed the `pydantic.generics.GenericModel` class and is no longer necessary. Therefore, mixing of V1 and
V2 models is not compatible. This implies that type parameters for a generic BaseModel (V2) cannot be V1 models.
See [here](https://docs.pydantic.dev/latest/migration/#changes-to-pydanticgenericsgenericmodel) for better explanation.

## AnyUrl adds trailing slash (/) in URL validation

Pydantic V2 uses the `rust` url crate for URL validation which followed RFCs. So the new `Url` types append slashes to
the validated version if no path is included, even if a slash is not specified in the argument to a `Url` type
constructor.
See [here](https://docs.pydantic.dev/latest/migration/#url-and-dsn-types-in-pydanticnetworks-no-longer-inherit-from-str)
for proof of concept and a solution on how to use the old behavior without the appended slash.

## `TypeError` occurs when using Pydantic's Constraint Types

This error occurs if you are using Python `3.9.7`. To prevent this, upgrade to Python `3.9.8` or higher as there is a
[bug](https://bugs.python.org/issue45081) in version `3.9.7`. Also, it is discouraged to use some of the
[**con**](https://docs.pydantic.dev/latest/api/types/#pydantic.types.conint) functions because they will be deprecated
in Pydantic **3.0**. So check out the **Discouraged** warning for alternative solution.

## validate_call decorator raises "AttributeError" when applied to an instance method of a class with `__slots__`

This issue has been addressed in the latest Pydantic update but the reason is that when you use the **@validate_call**
decorator on your method, Pydantic attempts to wrap that function in a `ValidateCallWrapper` and calls `setattr` on
the object to reassign the function name to be associated with the new, wrapped function.

So when you define `__slots__` as an empty set, that prevents access to `__dict__`, which is required for assigning
instance variables on object instances.

## Two validators consecutively do not report all errors

Pydantic does not currently support exhaustive validation so it stops after the first error on a given field and
reports that validation error. So this is a feature request we would look into.

## Can not use **ValidataionError** `__init__` method

There is no `__init__` method for **ValidationError** so you would have to use `from_exception_data` static method
with **ValidationError**. See [here](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.ValidationError)
for more details.

## Pydantic does not allow Literal enum value discriminator to be initialized by string

A simple solution to this is to allow your class to inherit from both `str` and `Enum`.
