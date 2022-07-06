# Pydantic V2

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

I think I owe people a proper explanation of the plan for V2:

* What will be added
* What will be removed
* What will change
* How I'm intending to go about completing it and getting it released
* Some idea of timeframe :fearful:

Here goes...

# Plan & Timeframe

I'm currently taking a kind of sabbatical after leaving my last job to get pydantic V2 released.
Why? Well I ask myself that question quite often.
I'm very proud of how much pydantic is used, but I'm less proud of its internals.
Since it's something people seem to care about and use quite a lot 
(26M downloads a month, used by 72K public repos on GitHub).
I want it to be as good as possible.

While I'm on the subject of why, how and my odd sabbatical: if you work for a large company who use pydantic a lot,
you should encourage the company to **sponsor me a meaningful amount**, 
like [Salesforce did](https://twitter.com/samuel_colvin/status/1501288247670063104).
This is not charity, recruitment or marketing - the argument should be about how much the company will save if
pydantic is 10x faster, more stable and more powerful - it would be worth paying me 10% of that to make it happen.

The plan is to have pydantic V2 released within 3 months of full-time work 
(again, that'll be sooner if I can continue to work on it full-time :face_with_raised_eyebrow:).

Before pydantic V2 can be released, we need to released pydantic v1.10 - there are lots of changes in the main
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
6. Rename `master` to `main`, seems like a good time to do this
7. Change the main branch of pydantic to target v2
8. Start tearing pydantic code apart and see how many existing tests can be made to pass
9. Rinse, repeat
10. Release pydantic V2 :tada:

# Introduction

Pydantic began life as an experiment in some code in a long dead project.
I ended up making the code into a package and releasing it.
It got a bit of attention on hacker news when it was first released, but started to get really popular when
Sebastian Ramirez used it in FastAPI.
Since then the package and its usage have grown enormously.
The core logic however has remained relatively unchanged since the initial experiment.
It's old, it smells, it needs to be rebuilt.
The release of version 2 is an opportunity to rebuild pydantic and correct many things that don't make sense.

Much of the work on V2 is already done, but there's still a lot to do.
Now seems a good opportunity to explain what V2 is going to look like and get feedback from uses.

## Headlines

For good and bad, here are some of the biggest changes expected in V2.

The core validation logic of pydantic V2 will be performed by a separate package 
[pydantic-core](https://github.com/samuelcolvin/pydantic-core) which I've been building over the last few months.

*pydantic-core* is written in Rust using the excellent [pyo3](https://pyo3.rs/) library which provides rust bindings
for python.

!!! note
    The python interface to pydantic shouldn't change as a result of using pydantic-core, instead
    pydantic will use type annotations to build a schema for pydantic-core to use.

pydantic-core is usable now, albeit with a fairly unintuitive API, if you're interested, please give it a try.

pydantic-core provides validators for all common data types, 
[see a list here](https://github.com/samuelcolvin/pydantic-core/blob/main/pydantic_core/_types.py#L291).
Other, less commonly used data types will be supported via validator functions.

### Performance :smiley:

As a result of the move to rust for the validation logic 
(and significant improvements in how validation objects are structured) pydantic V2 will be significantly faster
than pydantic V1.X.

Looking at the pydantic-core [benchmarks](https://github.com/samuelcolvin/pydantic-core/tree/main/tests/benchmarks),
pydantic V2 is between 4x and 50x faster than pydantic V1.X.

In general, pydantic V2 is about 17x faster than V1.X when validating a representative model containing a range
of common fields.

### Strict Mode :smiley:

People have long complained about pydantic preference for coercing data instead of throwing an error.
E.g. input to an `int` field could be `123` or the string `"123"` which would be converted to `123`.

pydantic-core comes with "strict mode" built in. With this only the exact data type is allowed, e.g. passing
`"123"` to an `int` field would result in a validation error.

Strictness can be defined on a per-field basis, or whole model.

#### IsInstance checks :smiley:

Strict mode also means it makes sense to provide an `is_instance` method on validators which effectively run
validation then throw away the result while avoiding the (admittedly small) overhead of creating and raising
and error or returning the validation result.

### Formalised Conversion Table :smiley:

As well as complaints about coercion, another (legitimate) complaint was inconsistency around data conversion.

In pydantic V2, the following principle will govern when data should be converted in "lax mode" (`strict=False`):

> If the input data has a SINGLE and INTUITIVE representation, in the field's type, AND no data is lost
> during the conversion, then the data will be converted, Otherwise a validation error is raised.
> There is one exception to this rule: string fields -
> virtually all data has an intuitive representation as a string (e.g. `repr()` and `str()`), therefore
> a custom rule is required: only `str`, `bytes` and `bytearray` are valid as inputs to string fields.

| Field Type | Input                   | Single & Intuitive R. | data Loss        | Result  |
|------------|-------------------------|-----------------------|------------------|---------|
| `int`      | `"123"`                 | :material-check:      | :material-close: | Convert |
| `int`      | `123.0`                 | :material-check:      | :material-close: | Convert |
| `int`      | `123.1`                 | :material-check:      | :material-check: | Error   |
| `date`     | `"2020-01-01"`          | :material-check:      | :material-close: | Convert |
| `date`     | `"2020-01-01T12:00:00"` | :material-check:      | :material-check: | Error   |

In addition to the general rule, we'll provide a conversion table which defines exactly what data will be allowed 
to which field types. See [the table below](TODO) for a start on this.

### Built in JSON support :smiley:

pydantic-core can parse JSON directly into a model or output type, this both improves performance and avoids
issue with strictness - e.g. if you have a "strict" model with a `datetime` field, the input must be a 
`datetime` object, but clearly that makes no sense when parsing JSON which has no `datatime` type.
Same with `bytes` and many other types.

Pydantic v2 will therefore allow some conversion when validating JSON directly, even in strict mode 
(e.g. `ISO8601 string -> datetime`, `str -> bytes`) even though this would not be allowed when validating
a python object.

In future direct validation of JSON will also allow:
* parsing in a separate thread while starting validation in the main thread
* line numbers from JSON to be included in the validation errors

!!! note
    Pydantic has always had special support for JSON, that is not going to change. While in theory other formats
    could be specifically supported, the overheads are significant and I don't think there's another format that's
    used widely enough to be worth specific logic. Other formats can be parsed to python then validated, similarly
    when serialising, data can be exported to a python object, then serialised, see below.

### Validation without a Model :smiley:

In pydantic v1 the core of all validation was a pydantic model, this led to significant overheads and complexity
when the output data type was not a model.

pydantic-core operates on a tree of validators with no "model" type required at the base of the tree.
It can therefore validate a single `string` or `datetime` value, a `TypeDict` or `Model` equally easily.

This feature will provide significant addition performance improvements in scenarios like:

* adding validation to `dataclass`
* validating URL arguments, query strings, headers, etc. in FastAPI
* adding validation to `TypedDict`
* function argument validation

Basically anywhere were you don't care about a traditional model class.

We'll need to add standalone methods for generating json schema and dumping these objects to JSON etc.

### Validator Function Improvements :smiley: :smiley: :smiley:

This is one of the changes in pydantic V2 that I'm most excited about, I've been talking about something
like this for a long time, see [#1984](https://github.com/samuelcolvin/pydantic/issues/1984), but couldn't
find a way to do this until now.

Fields which use a function for validation can be any of the following types:

* **function before mode** - where the function is called before the inner validator is called
* **function after mode** - where the function is called after the inner validator is called
* **plan mode** - where there's no inner validator
* **wrap mode** - where the function takes a reference to a function which calls the inner validator,
  and can therefore modify the input before inner validation, modify the output after inner validation, conditionally
  not call the inner validator or catch errors from the inner validator and return a default value

An example how a wrap validator might look:

```py title="Wrap mode validator function"
from datetime import datetime
from pydantic import BaseModel, ValidationError, validator

class MyModel(BaseModel):
    timestamp: datetime

    @validator('timestamp', mode='wrap')
    def validate_timestamp(cls, v, handler):
        if v == 'now':
            # we don't want to bother with further validation, so we just return the value
            return datetime.now()
        try:
            return handler(v)
        except ValidationError:
            # validation failed, in this case we want to return a default value
            return datetime(2000, 1, 1)
```

### Improvements to Dumping/Serialization/Export :smiley: :confused:

(I haven't worked on this yet, so these ideas are only provisional)

There has long been a debate about how to handle converting data when extracting it from a model.
One of the features people have long requested is the ability to convert data to JSON compliant types while 
converting a model to a dict.

My plan is to move data export into pydantic-core, with that one implementation can support all export modes without
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

The current `include` and `exclude` logic is extremely complicated, hopefully it won't be too hard to
translate it to rust.

We should also add support for `validate_alias` and `dump_alias` to allow for customising field keys.

### Model namespace cleanup :smiley:

For years I've wanted to clean up the model namespace,
see [#1001](https://github.com/samuelcolvin/pydantic/issues/1001). This would avoid confusing gotchas when field
names clash with methods on a model, it would also make it safer to add more methods to a model without risking
new clashes.

After much deliberation (and even giving a lightning talk at the python language submit about alternatives, see 
[here](https://discuss.python.org/t/better-fields-access-and-allowing-a-new-character-at-the-start-of-identifiers/14529))
I've decided to go with the simplest and clearest approach, the expense of a bit more typing:

All methods on models with start with `model_`, fields names will not be allowed to start with `"model"`,
aliases can be used if required.

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
* `._model_validator` attribute holding the internal pydantic `SchemaValidator`
* `.model_fields` (currently `.__fields__`) - although the format will have to change a lot, might be an alias of
  `._model_validator.schema`
* `ModelConfig` (currently `Config`) - configuration class for models

The following methods will be removed:

* `.parse_file()`
* `.parse_raw()`
* `.from_orm()` - the functionality has been configured as a `Config` property call `from_attributes` which can be set
  either on `ModelConfig` or on a specific `ModelClass` or `TypedDict` field

### Strict API & API documentation :smiley:

When preparing a pydantic V2, we'll make a strict distinction between the public API and private functions & classes.
Private objects clearly identified as private via `_internal` sub package to discourage use.

The public API will have API documentation. I've recently been working with the wonderful
[mkdocstrings](https://github.com/mkdocstrings/mkdocstrings) for both 
[dirty-equals](https://dirty-equals.helpmanual.io/) and
[watchfiles](https:://watchfiles.helpmanual.io/) documentation. I intend to use `mkdocstrings` to generate complete
API documentation.

This wouldn't replace the current example-based somewhat informal documentation style byt instead will augment it.

### Error descriptions :smiley:

TODO

### No pure python implementation :frowning:

Since pydantic-core is written in Rust, and I have absolutely no intention of rewriting it in python,
pydantic V2 will only work where a binary package can be installed.

pydantic-core will provide binaries in PyPI for (at least):

* **Linux**: `x86_64`, `aarch64`, `i686`, `armv7l`, `musl-x86_64` & `musl-aarch64`
* **MacOS**: `x86_64` & `arm64` (except python 3.7)
* **Windows**: `amd64` & `win32`
* **Web Assembly**: `wasm32` (pydantic-core is already compiled for wasm32 using emscripten and unit tests pass, 
  except where cpython itself has [problems](https://github.com/pyodide/pyodide/issues/2841))

Other binaries can be added provided they can be (cross-)compiled on github actions.
If no binary is available from PyPI, pydantic-core can be compiled from source if Rust stable is available.

The only place where I know this will cause problems is Raspberry Pi, which is a bit of 
[mess](https://github.com/piwheels/packages/issues/254) when it comes to packages written in rust for python.
Effectively, until that's fixed you'll likely have to install pydantic-core with 
`pip install -i https://pypi.org/simple/ pydantic-core`.

### Pydantic becomes a pure python package :neutral_face:

Pydantic v1.X is a pure python code base but is compiled with cython to provide some performance improvements.
Since the "hot" code is moved to pydantic-core, pydantic itself can go back to being a pure python package.

This should significantly reduce the size of the pydantic package and make unit tests of pydantic much faster.
In addition, some constraints on pydantic code can be removed once it no-longer has to be compilable with cython.

Some pieces of edge logic could get a little slower as they're no longer compiled.

### I'm dropping the word "parse" and just using "validate" :neutral_face:

Partly due to the issues with the lack of strict mode. I've previously gone back and forth between using 
"parse" and "validate" for what pydantic does.

While pydantic is not simply a validation library (and I'm sure some would argue validation is not strictly what it does),
most people use the **validation**.

it's time to stop fighting that, use consistent names.

The word "parse" will no longer be used except when talking about JSON parsing.

## Changes to custom field types :neutral_face:

Since the core structure of validators has changed from "a list of validators to call on each field" to
"a tree of validators which call each other", the 
[`__get_validators__`](https://pydantic-docs.helpmanual.io/usage/types/#classes-with-__get_validators__)
way of defining custom field types no longer makes sense.

Instead we'll look for the attribute `__pydantic_schema__` which must be a 
pydantic-core compliant schema for validating data to this field type, except for the `function`
item which can be a string which should be the name of a class function - `validate` below.

Here's an example of how a custom field type could be defined:

```py title="New custom field types"
from pydantic import ValiationSchema

class Foobar:
    __pydantic_schema__: ValiationSchema = {
        'type': 'function',
        'mode': 'after',
        'function': 'validate',
        'schema': {'type': 'str'}
    }
    
    def __init__(self, value: str):
        self.value = value

    @classmethod
    def validate(cls, value):
        if 'foobar' in value:
            return Foobar(value)
        else:
            raise ValueError('expected foobar')
```

What's going on here: `__pydantic_schema__` defines a schema which effectively says:

> Validate input data as a string, then call the `validate` with that string, use the output of `validate`
> as the final result of validation.

`ValiationSchema` is just an alias to 
[`pydantic_core.Schema`](https://github.com/samuelcolvin/pydantic-core/blob/main/pydantic_core/_types.py#L291)
which is a type defining the schema for validation schemas.

!!! note
    pydantic-core schema has full type definitions although since the type is recursive, 
    mypy can't provide static type analysis, pyright however can.

## Other Improvements :smiley:

1. Recursive models with cyclic references - although recursive models were supported by pydantic V1,
   data with cyclic references cause recursion errors, in pydantic-core code is correctly detected
   and a validation error is raised
2. The reason I've been so keen to get pydantic-core to compile and run with wasm is that I want all examples
   in the docs of pydantic V2 to be editable and runnable in the browser
3. `from_orm` has become `from_attributes` and is now defined at schema generation time 
   (either via model config or field config)

## Removed Features :neutral_face:

1. `__root__` custom root models are no longer necessary since validation on any support data type is supported
   without a model
2. `parse_file` and `parse_raw`, partially replaced with `.model_validate_json()`
3. `TypeError` are no longer considered as validation errors, but rather as internal errors, this is to better
   catch errors in argument names in function validators.
4. Subclasses of builtin types like `str`, `bytes` and `int` are coerced to their parent builtin type,
   this is a limitation of how pydantic-core converts these types to rust types during validation, if you have a
   specific need to keep the type, you can use wrap validators (see above) or custom type validation

## Conversion Table

TODO
