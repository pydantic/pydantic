# Pydantic V2 Plan

<aside class="blog" markdown>
![Samuel Colvin](/img/samuelcolvin.jpg)
<div markdown>
  **Samuel Colvin** &bull;&nbsp;
  [@samuelcolvin](https://github.com/samuelcolvin) &bull;&nbsp;
  :octicons-calendar-24: Jul 6, 2022 &bull;&nbsp;
  :octicons-clock-24: 10 min read
</div>
</aside>

I've spoken to quite a few people about pydantic V2, and mention it in passing even more.

I owe people a proper explanation of the plan for V2:

* What we will add
* What we will remove
* What we will change
* How I'm intending to go about completing it and getting it released
* Some idea of timeframe :fearful:

Here goes...

## Plan & Timeframe

I'm currently taking a kind of sabbatical after leaving my last job to get pydantic V2 released.
Why? I ask myself that question quite often.
I'm very proud of how much pydantic is used, but I'm less proud of its internals.
Since it's something people seem to care about and use quite a lot 
(26m downloads a month, used by 72k public repos, 10k stars).
I want it to be as good as possible.

While I'm on the subject of why, how and my odd sabbatical: if you work for a large company who use pydantic a lot,
you might encourage the company to **sponsor me a meaningful amount**, 
like [Salesforce did](https://twitter.com/samuel_colvin/status/1501288247670063104).
This is not charity, recruitment or marketing - the argument should be about how much the company will save if
pydantic is 10x faster, more stable and more powerful - it would be worth paying me 10% of that to make it happen.

The plan is to have pydantic V2 released within 3 months of full-time work 
(again, that'll be sooner if I can continue to work on it full-time :face_with_raised_eyebrow:).

Before pydantic V2 can be released, we need to release pydantic V1.10 - there are lots of changes in the main
branch of pydantic contributed by the community, it's only fair to provide a release including those changes,
many of them will remain unchanged for V2, the rest will act as a requirement to make sure pydantic V2 includes
the capabilities they implemented.

The basic road map for me is as follows:

1. Implement a few more critical features in pydantic-core
2. Release V0.1 of pydantic-core
3. Work on getting pydantic V1.10 out - basically merge all open PRs that are finished
4. Release pydantic V1.10
5. Delete all stale PRs which didn't make it into V1.10, apologise profusely to their authors who put their valuable
   time into pydantic only to have their PRs closed :pray: 
   (and explain when and how they can rebase and recreate their PR)
7. Rename `master` to `main`, seems like a good time to do this
8. Change the main branch of pydantic to target V2
9. Start tearing pydantic code apart and see how many existing tests can be made to pass
10. Rinse, repeat
11. Release pydantic V2 :tada:

Plan is to have all this done by the end of October, definitely by the end of the year.

## Introduction

Pydantic began life as an experiment in some code in a long dead project.
I ended up making the code into a package and releasing it.
It got a bit of attention on hacker news when it was first released, but started to get really popular when
Sebastián Ramírez used it in [FastAPI](https://fastapi.tiangolo.com/).

Since then, with the help of wonderful contributors like 
[Eric Jolibois](https://github.com/PrettyWood),
[Sebastián](https://github.com/tiangolo),
and [David Montague](https://github.com/dmontagu) the package and its usage have grown enormously.
The core logic however has remained relatively unchanged since the initial experiment.
It's old, it smells, it needs to be rebuilt.

The release of version 2 is an opportunity to rebuild pydantic and correct many things that don't make sense - 
**to make pydantic amazing :rocket:**.

Much of the work on V2 is already done, but there's still a lot to do.
Now seems a good opportunity to explain what V2 is going to look like and get feedback from users.

## Headlines

For good and bad, here are some of the biggest changes expected in V2.

The core validation logic of pydantic V2 will be performed by a separate package 
[pydantic-core](https://github.com/samuelcolvin/pydantic-core) which I've been building over the last few months.

*pydantic-core* is written in Rust using the excellent [pyo3](https://pyo3.rs) library which provides rust bindings
for python.

!!! note
    The python interface to pydantic shouldn't change as a result of using pydantic-core, instead
    pydantic will use type annotations to build a schema for pydantic-core to use.

pydantic-core is usable now, albeit with a fairly unintuitive API, if you're interested, please give it a try.

pydantic-core provides validators for all common data types, 
[see a list here](https://github.com/samuelcolvin/pydantic-core/blob/main/pydantic_core/_types.py#L291).
Other, less commonly used data types will be supported via validator functions.

### Performance :thumbsup:

As a result of the move to rust for the validation logic 
(and significant improvements in how validation objects are structured) pydantic V2 will be significantly faster
than pydantic V1.

Looking at the pydantic-core [benchmarks](https://github.com/samuelcolvin/pydantic-core/tree/main/tests/benchmarks)
today, pydantic V2 is between 4x and 50x faster than pydantic V1.9.1.

In general, pydantic V2 is about 17x faster than V1 when validating a model containing a range
of common fields.

### Strict Mode :thumbsup:

People have long complained about pydantic for coercing data instead of throwing an error.
E.g. input to an `int` field could be `123` or the string `"123"` which would be converted to `123`.

pydantic-core comes with "strict mode" built in. With this only the exact data type is allowed, e.g. passing
`"123"` to an `int` field would result in a validation error.

This will allow pydantic V2 to offer a `strict` switch which can be set on either a model or a field.

#### `IsInstance` checks :thumbsup:

Strict mode also means it makes sense to provide an `is_instance` method on validators which effectively run
validation then throw away the result while avoiding the (admittedly small) overhead of creating and raising
and error or returning the validation result.

### Formalised Conversion Table :thumbsup:

As well as complaints about coercion, another (legitimate) complaint was inconsistency around data conversion.

In pydantic V2, the following principle will govern when data should be converted in "lax mode" (`strict=False`):

> If the input data has a SINGLE and INTUITIVE representation, in the field's type, AND no data is lost
> during the conversion, then the data will be converted, Otherwise a validation error is raised.
> There is one exception to this rule: string fields -
> virtually all data has an intuitive representation as a string (e.g. `repr()` and `str()`), therefore
> a custom rule is required: only `str`, `bytes` and `bytearray` are valid as inputs to string fields.

Some examples of what that means in practice:

| Field Type | Input                   | Single & Intuitive R. | data Loss        | Result  |
|------------|-------------------------|-----------------------|------------------|---------|
| `int`      | `"123"`                 | :material-check:      | :material-close: | Convert |
| `int`      | `123.0`                 | :material-check:      | :material-close: | Convert |
| `int`      | `123.1`                 | :material-check:      | :material-check: | Error   |
| `date`     | `"2020-01-01"`          | :material-check:      | :material-close: | Convert |
| `date`     | `"2020-01-01T12:00:00"` | :material-check:      | :material-check: | Error   |
| `int`      | `b"1"`                  | :material-close:      | :material-close: | Error   |

(For the last case converting `bytes` to an `int` could reasonably mean `int(bytes_data.decode())` or 
`int.from_bytes(b'1', 'big')`, hence an error)

In addition to the general rule, we'll provide a conversion table which defines exactly what data will be allowed 
to which field types. See [the table below](#conversion-table) for a start on this.

### Built in JSON support :thumbsup:

pydantic-core can parse JSON directly into a model or output type, this both improves performance and avoids
issue with strictness - e.g. if you have a strict model with a `datetime` field, the input must be a 
`datetime` object, but clearly that makes no sense when parsing JSON which has no `datatime` type.
Same with `bytes` and many other types.

Pydantic V2 will therefore allow some conversion when validating JSON directly, even in strict mode 
(e.g. `ISO8601 string -> datetime`, `str -> bytes`) even though this would not be allowed when validating
a python object.

In future direct validation of JSON will also allow:

* parsing in a separate thread while starting validation in the main thread
* line numbers from JSON to be included in the validation errors

!!! note
    Pydantic has always had special support for JSON, that is not going to change.

    While in theory other formats
    could be specifically supported, the overheads are significant and I don't think there's another format that's
    used widely enough to be worth specific logic. Other formats can be parsed to python then validated, similarly
    when serialising, data can be exported to a python object, then serialised, 
    see [below](#improvements-to-dumpingserializationexport).

### Validation without a Model :thumbsup:

In pydantic V1 the core of all validation was a pydantic model, this led to significant overheads and complexity
when the output data type was not a model.

pydantic-core operates on a tree of validators with no "model" type required at the base of that tree.
It can therefore validate a single `string` or `datetime` value, a `TypeDict` or a `Model` equally easily.

This feature will provide significant addition performance improvements in scenarios like:

* Adding validation to `dataclasses`
* Validating URL arguments, query strings, headers, etc. in FastAPI
* Adding validation to `TypedDict`
* Function argument validation
* Adding validation to your custom classes, decorators...

In effect - anywhere where you don't care about a traditional model class instance.

We'll need to add standalone methods for generating json schema and dumping these objects to JSON etc.

### Required vs. Nullable Cleanup :thumbsup:

Pydantic previously had a somewhat confused idea about "required" vs. "nullable". This mostly resulted from
my misgivings about marking a field as `Optional[int]` but requiring a value to be provided but allowing it to be 
`None`.

In pydantic V2, pydantic will move to match dataclasses, thus:

```py title="Required vs. Nullable"
from pydantic import BaseModel

class Foo(BaseModel):
    f1: str  # required, cannot be None
    f2: str | None  # required, can be None - same as Optional[str] / Union[str, None]
    f3: str | None = None  # optional, can be None
    f4: str = 'Foobar'  # optional, but cannot be None  
```

### Validator Function Improvements :thumbsup: :thumbsup: :thumbsup:

This is one of the changes in pydantic V2 that I'm most excited about, I've been talking about something
like this for a long time, see [#1984](https://github.com/samuelcolvin/pydantic/issues/1984), but couldn't
find a way to do this until now.

Fields which use a function for validation can be any of the following types:

* **function before mode** - where the function is called before the inner validator is called
* **function after mode** - where the function is called after the inner validator is called
* **plan mode** - where there's no inner validator
* **wrap mode** - where the function takes a reference to a function which calls the inner validator,
  and can therefore modify the input before inner validation, modify the output after inner validation, conditionally
  not call the inner validator or catch errors from the inner validator and return a default value, or change the error

An example how a wrap validator might look:

```py title="Wrap mode validator function"
from datetime import datetime
from pydantic import BaseModel, ValidationError, validator

class MyModel(BaseModel):
    timestamp: datetime

    @validator('timestamp', mode='wrap')
    def validate_timestamp(cls, v, handler):
        if v == 'now':
            # we don't want to bother with further validation, just return the value
            return datetime.now()
        try:
            return handler(v)
        except ValidationError:
            # validation failed, in this case we want to return a default value
            return datetime(2000, 1, 1)
```

As well as being powerful, this provides a great "escape hatch" when pydantic validation doesn't do what you want.

### More powerful alias(es) :thumbsup:

pydantic-core can support alias "paths" as well as simple string aliases to flatten data as it's validated.

Best demonstrated with an example:

```py title="Alias paths"
from pydantic import BaseModel, Field


class Foo(BaseModel):
    bar: str = Field(aliases=[['baz', 2, 'qux']])


data = {
    'baz': [{'qux': 'a'}, {'qux': 'b'}, {'qux': 'c'}, {'qux': 'd'}]
}

foo = Foo(**data)
assert foo.bar == 'c'
```

`aliases` is a list of lists because multiple paths can be provided, if so they're tried in turn until a value is found.

### Improvements to Dumping/Serialization/Export :thumbsup: :confused:

(I haven't worked on this yet, so these ideas are only provisional)

There has long been a debate about how to handle converting data when extracting it from a model.
One of the features people have long requested is the ability to convert data to JSON compliant types while 
converting a model to a dict.

My plan is to move data export into pydantic-core, with that, one implementation can support all export modes without
compromising (and hopefully significantly improving) performance.

I see four different export/serialisation scenarios:

1. Extracting the field values of a model with no conversion, effectively `model.__dict__` but with the current filtering
   logic provided by `.dict()`
2. Extracting the field values of a model recursively (effectively what `.dict()` does now) - sub-models are converted to
   dicts, but other fields remain unchanged.
3. Extracting data and converting at the same time (e.g. to JSON compliant types)
4. Serialising data straight to JSON

I think all 4 modes can be supported in a single implementation, with a kind of "3.5" mode where a python function
is used to convert the data as the use wishes.

The current `include` and `exclude` logic is extremely complicated, but hopefully it won't be too hard to
translate it to rust.

We should also add support for `validate_alias` and `dump_alias` as well as the standard `alias`
to allow for customising field keys.

### Model namespace cleanup :thumbsup:

For years I've wanted to clean up the model namespace,
see [#1001](https://github.com/samuelcolvin/pydantic/issues/1001). This would avoid confusing gotchas when field
names clash with methods on a model, it would also make it safer to add more methods to a model without risking
new clashes.

After much deliberation (and even giving a lightning talk at the python language submit about alternatives, see 
[here](https://discuss.python.org/t/better-fields-access-and-allowing-a-new-character-at-the-start-of-identifiers/14529))
I've decided to go with the simplest and clearest approach, at the expense of a bit more typing:

All methods on models will start with `model_`, fields' names will not be allowed to start with `"model"`
(aliases can be used if required).

This will mean the following methods and attributes on a model:

* `.__dict__` as currently, holds a dict of validated data
* `.__fields_set__` as currently, set containing which fields were set (vs. populated from defaults)
* `.model_validate()` (currently `.parse_obj()`) - validate data
* `.model_validate_json()` (currently `parse_raw(j..., content_type='application/json')`) - validate data from JSON
* `.model_dump()` (currently `.dict()`) - as above, with new `mode` argument
* `.model_json()` (currently `.json()`) - alias of `.model_dump(mode='json')`
* `.model_schema()` (currently `.schema()`)
* `.model_schema_json()` (currently `.schema_json()`)
* `.model_update_forward_refs()` (currently `.update_forward_refs()`) - update forward references
* `.model_copy()` (currently `.copy()`) - copy a model
* `.model_construct()` (currently `.construct()`) - construct a model with no validation
* `.__model_validator__` attribute holding the internal pydantic `SchemaValidator`
* `.model_fields` (currently `.__fields__`) - although the format will have to change a lot, might be an alias of
  `.__model_validator__.schema`
* `ModelConfig` (currently `Config`) - configuration class for models

The following methods will be removed:

* `.parse_file()`
* `.parse_raw()`
* `.from_orm()` - the functionality has been moved to config, see [other improvements](#other-improvements) below

### Strict API & API documentation :thumbsup:

When preparing for pydantic V2, we'll make a strict distinction between the public API and private functions & classes.
Private objects will be clearly identified as private via a `_internal` sub package to discourage use.

The public API will have API documentation. I've recently been working with the wonderful
[mkdocstrings](https://github.com/mkdocstrings/mkdocstrings) package for both 
[dirty-equals](https://dirty-equals.helpmanual.io/) and
[watchfiles](https://watchfiles.helpmanual.io/) documentation. I intend to use `mkdocstrings` to generate complete
API documentation for V2.

This wouldn't replace the current example-based somewhat informal documentation style but instead will augment it.

### Error descriptions :thumbsup:

The way line errors (the individual errors within a `ValidationError`) are built has become much more sophisticated
in pydantic-core.

There's a well-defined 
[set of error codes and messages](https://github.com/samuelcolvin/pydantic-core/blob/main/src/errors/kinds.rs).

More will be added when other type are validated via pure python validators in pydantic.

I would like to add a dedicated section to the documentation with extra information for each type of error.

This would be another key in a line error: `documentation`, which would link to the appropriate section in the
docs.

Thus, errors might look like:

```py title="Line Errors Example"
[
    {
        'kind': 'greater_than_equal',
        'loc': ['age'],
        'message': 'Value must be greater than or equal to 18',
        'input_value': 11,
        'context': {'ge': 18},
        'documentation': 'https://pydantic.dev/errors/#greater_than_equal',
    },
    {
        'kind': 'bool_parsing',
        'loc': ['is_developer'],
        'message': 'Value must be a valid boolean, unable to interpret input',
        'input_value': 'foobar',
        'documentation': 'https://pydantic.dev/errors/#bool_parsing',
    },
]
```

(I own the `pydantic.dev` domain and will use it for at least these errors so that even if the docs URL
changes, the error will still link to the correct documentation.)

### No pure python implementation :frowning:

Since pydantic-core is written in Rust, and I have absolutely no intention of rewriting it in python,
pydantic V2 will only work where a binary package can be installed.

pydantic-core will provide binaries in PyPI for (at least):

* **Linux**: `x86_64`, `aarch64`, `i686`, `armv7l`, `musl-x86_64` & `musl-aarch64`
* **MacOS**: `x86_64` & `arm64` (except python 3.7)
* **Windows**: `amd64` & `win32`
* **Web Assembly**: `wasm32` 
  (pydantic-core is [already](https://github.com/samuelcolvin/pydantic-core/runs/7214195252?check_suite_focus=true) 
  compiled for wasm32 using emscripten and unit tests pass, except where cpython itself has 
  [problems](https://github.com/pyodide/pyodide/issues/2841))

Other binaries can be added provided they can be (cross-)compiled on github actions.
If no binary is available from PyPI, pydantic-core can be compiled from source if Rust stable is available.

The only place where I know this will cause problems is Raspberry Pi, which is a 
[mess](https://github.com/piwheels/packages/issues/254) when it comes to packages written in rust for python.
Effectively, until that's fixed you'll likely have to install pydantic with 
`pip install -i https://pypi.org/simple/ pydantic`.

### Pydantic becomes a pure python package :thumbsup:

Pydantic V1.X is a pure python code base but is compiled with cython to provide some performance improvements.
Since the "hot" code is moved to pydantic-core, pydantic itself can go back to being a pure python package.

This should significantly reduce the size of the pydantic package and make unit tests of pydantic much faster.
In addition, some constraints on pydantic code can be removed once it no-longer has to be compilable with cython.

Some pieces of edge logic could get a little slower as they're no longer compiled.

### I'm dropping the word "parse" and just using "validate" :neutral_face:

Partly due to the issues with the lack of strict mode. I've previously gone back and forth between using 
the terms "parse" and "validate" for what pydantic does.

While pydantic is not simply a validation library (and I'm sure some would argue validation is not strictly what it does),
most people use the word **"validation"**.

It's time to stop fighting that, and use consistent names.

The word "parse" will no longer be used except when talking about JSON parsing, see
[model methods](#model-namespace-cleanup) above.

## Changes to custom field types :neutral_face:

Since the core structure of validators has changed from "a list of validators to call one after another" to
"a tree of validators which call each other", the 
[`__get_validators__`](https://pydantic-docs.helpmanual.io/usage/types/#classes-with-__get_validators__)
way of defining custom field types no longer makes sense.

Instead we'll look for the attribute `__pydantic_schema__` which must be a 
pydantic-core compliant schema for validating data to this field type (the `function`
item can be a string, if so a function of that name will be taken from the class, see `'validate'` below).

Here's an example of how a custom field type could be defined:

```py title="New custom field types"
from pydantic import ValidationSchema

class Foobar:
    def __init__(self, value: str):
        self.value = value

    __pydantic_schema__: ValidationSchema = {
        'type': 'function',
        'mode': 'after',
        'function': 'validate',
        'schema': {'type': 'str'}
    }

    @classmethod
    def validate(cls, value):
        if 'foobar' in value:
            return Foobar(value)
        else:
            raise ValueError('expected foobar')
```

What's going on here: `__pydantic_schema__` defines a schema which effectively says:

> Validate input data as a string, then call the `validate` function with that string, use the returned value
> as the final result of validation.

`ValidationSchema` is just an alias to 
[`pydantic_core.Schema`](https://github.com/samuelcolvin/pydantic-core/blob/main/pydantic_core/_types.py#L291)
which is a type defining the schema for validation schemas.

!!! note
    pydantic-core schema has full type definitions although since the type is recursive, 
    mypy can't provide static type analysis, pyright however can.

## Other Improvements :thumbsup:

Some other things which will also change, IMHO for the better:

1. Recursive models with cyclic references - although recursive models were supported by pydantic V1,
   data with cyclic references caused recursion errors, in pydantic-core cyclic references are correctly detected
   and a validation error is raised
2. The reason I've been so keen to get pydantic-core to compile and run with wasm is that I want all examples
   in the docs of pydantic V2 to be editable and runnable in the browser
3. Full (pun intended) support for `TypedDict`, including `full=False` - e.g. omitted keys
4. `from_orm` has become `from_attributes` and is now defined at schema generation time 
   (either via model config or field config)
5. `input_value` has been added to each line error in a `ValidationError`, making errors easier to understand,
   and more comprehensive details of errors to be provided to end users, 
   [#784](https://github.com/samuelcolvin/pydantic/issues/784)
7. `on_error` logic in a schema which allows either a default value to be used in the event of an error,
   or that value to be omitted (in the case of a `full=False` `TypeDict`),
   [#151](https://github.com/samuelcolvin/pydantic-core/issues/151)
8. `datetime`, `date`, `time` & `timedelta` validation is improved, see the 
   [speedate] rust library I built specifically for this purpose for more details
9. Powerful "priority" system for optionally merging or overriding config in sub-models for nested schemas

## Removed Features :neutral_face:

1. `__root__` custom root models are no longer necessary since validation on any supported data type is allowed
   without a model
2. `parse_file` and `parse_raw`, partially replaced with `.model_validate_json()`
3. `TypeError` are no longer considered as validation errors, but rather as internal errors, this is to better
   catch errors in argument names in function validators.
4. Subclasses of builtin types like `str`, `bytes` and `int` are coerced to their parent builtin type,
   this is a limitation of how pydantic-core converts these types to rust types during validation, if you have a
   specific need to keep the type, you can use wrap validators or custom type validation as described above
5. [Settings Management](https://pydantic-docs.helpmanual.io/usage/settings/) ??? - I definitely don't want to
   remove the functionality, but it's something of a historical curiosity that it lives within pydantic,
   perhaps it should move to a separate package, perhaps installable alongside pydantic with 
   `pip install pydantic[settings]`?

## Conversion Table :material-table:

The table below provisionally defines what input value types are allowed to which field types.

An updated and complete version of this table will be included in the docs for V2.

!!!note
    Some type conversion shown here are a significant departure from existing behavior, we may have to provide a config
    flag for backwards compatibility for a few of them, however pydantic V2 cannot be entirely backward compatible,
    see [#152](https://github.com/samuelcolvin/pydantic-core/issues/152).

| Field Type    | Input       | Mode   | Input Source | Conditions                                                                  |
|---------------|-------------|--------|--------------|-----------------------------------------------------------------------------|
| `str`         | `str`       | both   | python, JSON | -                                                                           |
| `str`         | `bytes`     | lax    | python       | assumes UTF-8, error on unicode decoding error                              |
| `str`         | `bytearray` | lax    | python       | assumes UTF-8, error on unicode decoding error                              |
| `bytes`       | `bytes`     | both   | python       | -                                                                           |
| `bytes`       | `str`       | both   | JSON         | -                                                                           |
| `bytes`       | `str`       | lax    | python       | -                                                                           |
| `bytes`       | `bytearray` | lax    | python       | -                                                                           |
| `int`         | `int`       | strict | python, JSON | max abs value 2^64 - `i64` is used internally, `bool` explicitly forbidden  |
| `int`         | `int`       | lax    | python, JSON | `i64`                                                                       |
| `int`         | `float`     | lax    | python, JSON | `i64`, must be exact int, e.g. `f % 1 == 0`, `nan`, `inf` raise errors      |
| `int`         | `Decimal`   | lax    | python, JSON | `i64`, must be exact int, e.g. `f % 1 == 0`                                 |
| `int`         | `bool`      | lax    | python, JSON | -                                                                           |
| `int`         | `str`       | lax    | python, JSON | `i64`, must be numeric only, e.g. `[0-9]+`                                  |
| `float`       | `float`     | strict | python, JSON | `bool` explicitly forbidden                                                 |
| `float`       | `float`     | lax    | python, JSON | -                                                                           |
| `float`       | `int`       | lax    | python, JSON | -                                                                           |
| `float`       | `str`       | lax    | python, JSON | must match `[0-9]+(\.[0-9]+)?`                                              |
| `float`       | `Decimal`   | lax    | python       | -                                                                           |
| `float`       | `bool`      | lax    | python, JSON | -                                                                           |
| `bool`        | `bool`      | both   | python, JSON | -                                                                           |
| `bool`        | `int`       | lax    | python, JSON | allowed: `0, 1`                                                             |
| `bool`        | `float`     | lax    | python, JSON | allowed: `0, 1`                                                             |
| `bool`        | `Decimal`   | lax    | python, JSON | allowed: `0, 1`                                                             |
| `bool`        | `str`       | lax    | python, JSON | allowed: `'f', 'n', 'no', 'off', 'false', 't', 'y', 'on', 'yes', 'true'`    |
| `None`        | `None`      | both   | python, JSON | -                                                                           |
| `date`        | `date`      | both   | python       | -                                                                           |
| `date`        | `datetime`  | lax    | python       | must be exact date, eg. no H, M, S, f                                       |
| `date`        | `str`       | both   | JSON         | format `YYYY-MM-DD`                                                         |
| `date`        | `str`       | lax    | python       | format `YYYY-MM-DD`                                                         |
| `date`        | `bytes`     | lax    | python       | format `YYYY-MM-DD` (UTF-8)                                                 |
| `date`        | `int`       | lax    | python, JSON | interpreted as seconds or ms from epoch, see [speedate], must be exact date |
| `date`        | `float`     | lax    | python, JSON | interpreted as seconds or ms from epoch, see [speedate], must be exact date |
| `datetime`    | `datetime`  | both   | python       | -                                                                           |
| `datetime`    | `date`      | lax    | python       | -                                                                           |
| `datetime`    | `str`       | both   | JSON         | format `YYYY-MM-DDTHH:MM:SS.f` etc. see [speedate]                          |
| `datetime`    | `str`       | lax    | python       | format `YYYY-MM-DDTHH:MM:SS.f` etc. see [speedate]                          |
| `datetime`    | `bytes`     | lax    | python       | format `YYYY-MM-DDTHH:MM:SS.f` etc. see [speedate], (UTF-8)                 |
| `datetime`    | `int`       | lax    | python, JSON | interpreted as seconds or ms from epoch, see [speedate]                     |
| `datetime`    | `float`     | lax    | python, JSON | interpreted as seconds or ms from epoch, see [speedate]                     |
| `time`        | `time`      | both   | python       | -                                                                           |
| `time`        | `str`       | both   | JSON         | format `HH:MM:SS.FFFFFF` etc. see [speedate]                                |
| `time`        | `str`       | lax    | python       | format `HH:MM:SS.FFFFFF` etc. see [speedate]                                |
| `time`        | `bytes`     | lax    | python       | format `HH:MM:SS.FFFFFF` etc. see [speedate], (UTF-8)                       |
| `time`        | `int`       | lax    | python, JSON | interpreted as seconds, range 0 - 86399                                     |
| `time`        | `float`     | lax    | python, JSON | interpreted as seconds, range 0 - 86399.9*                                  |
| `time`        | `Decimal`   | lax    | python, JSON | interpreted as seconds, range 0 - 86399.9*                                  |
| `timedelta`   | `timedelta` | both   | python       | -                                                                           |
| `timedelta`   | `str`       | both   | JSON         | format ISO8601 etc. see [speedate]                                          |
| `timedelta`   | `str`       | lax    | python       | format ISO8601 etc. see [speedate]                                          |
| `timedelta`   | `bytes`     | lax    | python       | format ISO8601 etc. see [speedate], (UTF-8)                                 |
| `timedelta`   | `int`       | lax    | python, JSON | interpreted as seconds                                                      |
| `timedelta`   | `float`     | lax    | python, JSON | interpreted as seconds                                                      |
| `timedelta`   | `Decimal`   | lax    | python, JSON | interpreted as seconds                                                      |
| `dict`        | `dict`      | both   | python       | -                                                                           |
| `dict`        | `Object`    | both   | JSON         | -                                                                           |
| `dict`        | `mapping`   | lax    | python       | must implement the mapping interface and have an `items()` method           | 
| `TypeDict`    | `dict`      | both   | python       | -                                                                           |
| `TypeDict`    | `Object`    | both   | JSON         | -                                                                           |
| `TypeDict`    | `Any`       | both   | python       | builtins not allowed, uses `getattr`, requires `from_attributes=True`       | 
| `TypeDict`    | `mapping`   | lax    | python       | must implement the mapping interface and have an `items()` method           | 
| `list`        | `list`      | both   | python       | -                                                                           |
| `list`        | `Array`     | both   | JSON         | -                                                                           |
| `list`        | `tuple`     | lax    | python       | -                                                                           |
| `list`        | `set`       | lax    | python       | -                                                                           |
| `list`        | `frozenset` | lax    | python       | -                                                                           |
| `list`        | `dict_keys` | lax    | python       | -                                                                           |
| `tuple`       | `tuple`     | both   | python       | -                                                                           |
| `tuple`       | `Array`     | both   | JSON         | -                                                                           |
| `tuple`       | `list`      | lax    | python       | -                                                                           |
| `tuple`       | `set`       | lax    | python       | -                                                                           |
| `tuple`       | `frozenset` | lax    | python       | -                                                                           |
| `tuple`       | `dict_keys` | lax    | python       | -                                                                           |
| `set`         | `set`       | both   | python       | -                                                                           |
| `set`         | `Array`     | both   | JSON         | -                                                                           |
| `set`         | `list`      | lax    | python       | -                                                                           |
| `set`         | `tuple`     | lax    | python       | -                                                                           |
| `set`         | `frozenset` | lax    | python       | -                                                                           |
| `set`         | `dict_keys` | lax    | python       | -                                                                           |
| `frozenset`   | `frozenset` | both   | python       | -                                                                           |
| `frozenset`   | `Array`     | both   | JSON         | -                                                                           |
| `frozenset`   | `list`      | lax    | python       | -                                                                           |
| `frozenset`   | `tuple`     | lax    | python       | -                                                                           |
| `frozenset`   | `set`       | lax    | python       | -                                                                           |
| `frozenset`   | `dict_keys` | lax    | python       | -                                                                           |
| `is_instance` | `Any`       | both   | python       | `isinstance()` check returns `True`                                         |
| `is_instance` | -           | both   | JSON         | never valid                                                                 |
| `callable`    | `Any`       | both   | python       | `callable()` check returns `True`                                           |
| `callable`    | -           | both   | JSON         | never valid                                                                 |

The `ModelClass` validator (use to create instances of a class) uses the `TypeDict` validator, then creates an instance
with `__dict__` and `__fields_set__` set, so same rules apply as `TypeDict`.

[speedate]: https://docs.rs/speedate/latest/speedate/
