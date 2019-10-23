After 2.5 years of development with contributions from over 80 people and 62 releases, *pydantic* has reached
version 1!

While the fundamentals of *pydantic* have remained unchanged since the previous release 
[v0.32](changelog.md#v0322-2019-08-17) (indeed, since *pydantic* began in early 2017); 
a number of things have changed which might be of note.

Below is a list of significant changes, for a full list of changes see release notes for 
[v1.0b1](changelog.md#v10b1-2019-10-01), [v1.0b2](changelog.md#v10b2-2019-10-07), and [v1.0](changelog.md).

## What's new in pydantic v1

### Root validators

A new decorator [`root_validator`](usage/validators.md#root-validators) has been added to allow validation of entire
models.

### Custom JSON encoding/decoding

There are new `Config` settings to allow 
[Custom JSON (de)serialisation](usage/exporting_models.md#custom-json-deserialisation). This can allow alternative
JSON implementations to be used with significantly improved performance.

### Boolean parsing

The logic for [parsing and validating boolean values](usage/types.md#booleans) has been overhauled to only allow
a defined set of values rather than allowing any value as it used to. 

### URL parsing

The logic for parsing URLs (and related objects like DSNs) has been completely re-written to provide more useful
error messages, greater simplicity and more flexibility.

### Performance improvements

Some less "clever" error handling and cleanup of how errors are wrapped (together with many other small changes)
has improved the performance of *pydantic* by ~25%, see 
[samuelcolvin/pydantic#819](https://github.com/samuelcolvin/pydantic/pull/819).

### ORM mode improvements

There are improvements to [`GetterDict`](usage/models.md#orm-mode-aka-arbitrary-class-instances) to make ORM mode
easier to use and work with root validators, see 
[samuelcolvin/pydantic#822](https://github.com/samuelcolvin/pydantic/pull/822).

### Settings improvements

There are a number of changes to how [`BaseSettings`](usage/settings.md) works:

* `case_insensitive` has been renamed to `case_sensitive` and the default has changed to `case_sensitive = False`
* the default for `env_prefix` has changed to an empty string, i.e. by default there's no prefix for environment
  variable lookups
* aliases are no longer used when looking up environment variables, instead there's a new `env` setting for `Field()` or 
  in `Config.fields`.

### Improvements to field ordering

There are some subtle changes to the ordering of fields, see [Model field ordering](usage/models.md#field-ordering)
for more details.

### Schema renamed to Field

The function used for providing extra information about fields has been renamed from `Schema` to `Field`. The
new name makes more sense since the method can be used to provide any sort of information and change the behaviour
of the field, as well as add attributes which are used while [generating a model schema](usage/schema.md).

### Improved repr methods and devtools integration 

The `__repr__` and `__str__` method of models as well as most other public classes in *pydantic* have been altered
to be consistent and informative. There's also new [integration with python-devtools](usage/devtools.md).

### Field constraints checks

Constraints added to `Field()` which are not enforced now cause an error when a model is created, see
[Unenforced Field constraints](usage/schema.md#unenforced-field-constraints) for more details and work-arounds.
