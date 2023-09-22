# Pydantic V2 Plan

<aside class="blog" markdown>
![Samuel Colvin](../img/samuelcolvin.jpg)
<div markdown>
  **Samuel Colvin** &bull;&nbsp;
  [:simple-github:](https://github.com/samuelcolvin) &bull;&nbsp;
  [:material-twitter:](https://twitter.com/samuel_colvin) &bull;&nbsp;
  :octicons-calendar-24: Jul 10, 2022 &bull;&nbsp;
  :octicons-clock-24: 25 min read
</div>
</aside>

---

Updated late 10 Jul 2022, see [pydantic#4226](https://github.com/pydantic/pydantic/pull/4226).

---

I've spoken to quite a few people about pydantic V2, and mention it in passing even more.

I owe people a proper explanation of the plan for V2:

* What we will add
* What we will remove
* What we will change
* How I'm intending to go about completing it and getting it released
* Some idea of timeframe :fearful:

Here goes...

---

Enormous thanks to
[Eric Jolibois](https://github.com/PrettyWood), [Laurence Watson](https://github.com/Rabscuttler),
[Sebastián Ramírez](https://github.com/tiangolo), [Adrian Garcia Badaracco](https://github.com/adriangb),
[Tom Hamilton Stubber](https://github.com/tomhamiltonstubber), [Zac Hatfield-Dodds](https://github.com/Zac-HD),
[Tom](https://github.com/czotomo) & [Hasan Ramezani](https://github.com/hramezani)
for reviewing this blog post, putting up with (and correcting) my horrible typos and making great suggestions
that have made this post and Pydantic V2 materially better.

---

## Plan & Timeframe

I'm currently taking a kind of sabbatical after leaving my last job to get pydantic V2 released.
Why? I ask myself that question quite often.
I'm very proud of how much pydantic is used, but I'm less proud of its internals.
Since it's something people seem to care about and use quite a lot
(26m downloads a month, used by 72k public repos, 10k stars).
I want it to be as good as possible.

While I'm on the subject of why, how and my odd sabbatical: if you work for a large company who use pydantic a lot,
you might encourage the company to **sponsor me a meaningful amount**,
like [Salesforce did](https://twitter.com/samuel_colvin/status/1501288247670063104)
(if your organisation is not open to donations, I can also offer consulting services).
This is not charity, recruitment or marketing - the argument should be about how much the company will save if
pydantic is 10x faster, more stable and more powerful - it would be worth paying me 10% of that to make it happen.

Before pydantic V2 can be released, we need to release pydantic V1.10 - there are lots of changes in the main
branch of pydantic contributed by the community, it's only fair to provide a release including those changes,
many of them will remain unchanged for V2, the rest will act as a requirement to make sure pydantic V2 includes
the capabilities they implemented.

The basic road map for me is as follows:

1. Implement a few more features in pydantic-core, and release a first version, see [below](#motivation-pydantic-core)
2. Work on getting pydantic V1.10 out - basically merge all open PRs that are finished
3. Release pydantic V1.10
4. Delete all stale PRs which didn't make it into V1.10, apologise profusely to their authors who put their valuable
   time into pydantic only to have their PRs closed :pray:
   (and explain when and how they can rebase and recreate the PR)
5. Rename `master` to `main`, seems like a good time to do this
6. Change the main branch of pydantic to target V2
7. Start tearing pydantic code apart and see how many existing tests can be made to pass
8. Rinse, repeat
9. Release pydantic V2 :tada:

Plan is to have all this done by the end of October, definitely by the end of the year.

### Breaking Changes & Compatibility :pray:

While we'll do our best to avoid breaking changes, some things will break.

As per the [greatest pun in modern TV history](https://youtu.be/ezAlySFluEk).

> You can't make a Tomelette without breaking some Greggs.

Where possible, if breaking changes are unavoidable, we'll try to provide warnings or errors to make sure those
changes are obvious to developers.

## Motivation & `pydantic-core`

Since pydantic's initial release, with the help of wonderful contributors
[Eric Jolibois](https://github.com/PrettyWood),
[Sebastián Ramírez](https://github.com/tiangolo),
[David Montague](https://github.com/dmontagu) and many others, the package and its usage have grown enormously.
The core logic however has remained mostly unchanged since the initial experiment.
It's old, it smells, it needs to be rebuilt.

The release of version 2 is an opportunity to rebuild pydantic and correct many things that don't make sense -
**to make pydantic amazing :rocket:**.

The core validation logic of pydantic V2 will be performed by a separate package
[pydantic-core](https://github.com/pydantic/pydantic-core) which I've been building over the last few months.
*pydantic-core* is written in Rust using the excellent [pyo3](https://pyo3.rs) library which provides rust bindings
for python.

The motivation for building pydantic-core in Rust is as follows:

1. **Performance**, see [below](#performance)
2. **Recursion and code separation** - with no stack and little-to-no overhead for extra function calls,
   Rust allows pydantic-core to be implemented as a tree of small validators which call each other,
   making code easier to understand and extend without harming performance
4. **Safety and complexity** - pydantic-core is a fairly complex piece of code which has to draw distinctions
   between many different errors, Rust is great in situations like this,
   it should minimise bugs (:fingers_crossed:) and allow the codebase to be extended for a long time to come

!!! note
    The python interface to pydantic shouldn't change as a result of using pydantic-core, instead
    pydantic will use type annotations to build a schema for pydantic-core to use.

pydantic-core is usable now, albeit with an unintuitive API, if you're interested, please give it a try.

pydantic-core provides validators for common data types,
[see a list here](https://github.com/pydantic/pydantic-core/blob/main/pydantic_core/schema_types.py#L314).
Other, less commonly used data types will be supported via validator functions implemented in pydantic, in Python.

See [pydantic-core#153](https://github.com/pydantic/pydantic-core/issues/153)
for a summary of what needs to be completed before its first release.

## Headlines

Here are some of the biggest changes expected in V2.

### Performance :thumbsup:

As a result of the move to Rust for the validation logic
(and significant improvements in how validation objects are structured) pydantic V2 will be significantly faster
than pydantic V1.

Looking at the pydantic-core [benchmarks](https://github.com/pydantic/pydantic-core/tree/main/tests/benchmarks)
today, pydantic V2 is between 4x and 50x faster than pydantic V1.9.1.

In general, pydantic V2 is about 17x faster than V1 when validating a model containing a range of common fields.

### Strict Mode :thumbsup:

People have long complained about pydantic for coercing data instead of throwing an error.
E.g. input to an `int` field could be `123` or the string `"123"` which would be converted to `123`
While this is very useful in many scenarios (think: URL parameters, environment variables, user input),
there are some situations where it's not desirable.

pydantic-core comes with "strict mode" built in. With this, only the exact data type is allowed, e.g. passing
`"123"` to an `int` field would result in a validation error.

This will allow pydantic V2 to offer a `strict` switch which can be set on either a model or a field.

### Formalised Conversion Table :thumbsup:

As well as complaints about coercion, another legitimate complaint was inconsistency around data conversion.

In pydantic V2, the following principle will govern when data should be converted in "lax mode" (`strict=False`):

> If the input data has a SINGLE and INTUITIVE representation, in the field's type, AND no data is lost
> during the conversion, then the data will be converted; otherwise a validation error is raised.
> There is one exception to this rule: string fields -
> virtually all data has an intuitive representation as a string (e.g. `repr()` and `str()`), therefore
> a custom rule is required: only `str`, `bytes` and `bytearray` are valid as inputs to string fields.

Some examples of what that means in practice:

| Field Type | Input                   | Single & Intuitive R. | All Data Preserved | Result  |
|------------|-------------------------|-----------------------|--------------------|---------|
| `int`      | `"123"`                 | :material-check:      | :material-check:   | Convert |
| `int`      | `123.0`                 | :material-check:      | :material-check:   | Convert |
| `int`      | `123.1`                 | :material-check:      | :material-close:   | Error   |
| `date`     | `"2020-01-01"`          | :material-check:      | :material-check:   | Convert |
| `date`     | `"2020-01-01T00:00:00"` | :material-check:      | :material-check:   | Convert |
| `date`     | `"2020-01-01T12:00:00"` | :material-check:      | :material-close:   | Error   |
| `int`      | `b"1"`                  | :material-close:      | :material-check:   | Error   |

(For the last case converting `bytes` to an `int` could reasonably mean `int(bytes_data.decode())` or
`int.from_bytes(b'1', 'big/little')`, hence an error)

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

(These features will not be included in V2, but instead will hopefully be added later.)

!!! note
    Pydantic has always had special support for JSON, that is not going to change.

    While in theory other formats could be specifically supported, the overheads and development time are
    significant and I don't think there's another format that's
    used widely enough to be worth specific logic. Other formats can be parsed to python then validated, similarly
    when serializing, data can be exported to a python object, then serialized,
    see [below](#improvements-to-dumpingserializationexport).

### Validation without a Model :thumbsup:

In pydantic V1 the core of all validation was a pydantic model, this led to a significant performance penalty
and extra complexity when the output data type was not a model.

pydantic-core operates on a tree of validators with no "model" type required at the base of that tree.
It can therefore validate a single `string` or `datetime` value, a `TypedDict` or a `Model` equally easily.

This feature will provide significant addition performance improvements in scenarios like:

* Adding validation to `dataclasses`
* Validating URL arguments, query strings, headers, etc. in FastAPI
* Adding validation to `TypedDict`
* Function argument validation
* Adding validation to your custom classes, decorators...

In effect - anywhere where you don't care about a traditional model class instance.

We'll need to add standalone methods for generating JSON Schema and dumping these objects to JSON, etc.

### Required vs. Nullable Cleanup :thumbsup:

Pydantic previously had a somewhat confused idea about "required" vs. "nullable". This mostly resulted from
my misgivings about marking a field as `Optional[int]` but requiring a value to be provided but allowing it to be
`None` - I didn't like using the word "optional" in relation to a field which was not optional.

In pydantic V2, pydantic will move to match dataclasses, thus:

```py title="Required vs. Nullable" test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Foo(BaseModel):
    f1: str  # required, cannot be None
    f2: str | None  # required, can be None - same as Optional[str] / Union[str, None]
    f3: str | None = None  # not required, can be None
    f4: str = 'Foobar'  # not required, but cannot be None
```

### Validator Function Improvements :thumbsup: :thumbsup: :thumbsup:

This is one of the changes in pydantic V2 that I'm most excited about, I've been talking about something
like this for a long time, see [pydantic#1984](https://github.com/pydantic/pydantic/issues/1984), but couldn't
find a way to do this until now.

Fields which use a function for validation can be any of the following types:

* **function before mode** - where the function is called before the inner validator is called
* **function after mode** - where the function is called after the inner validator is called
* **plain mode** - where there's no inner validator
* **wrap mode** - where the function takes a reference to a function which calls the inner validator,
  and can therefore modify the input before inner validation, modify the output after inner validation, conditionally
  not call the inner validator or catch errors from the inner validator and return a default value, or change the error

An example how a wrap validator might look:

```py title="Wrap mode validator function" test="skip" lint="skip" upgrade="skip"
from datetime import datetime
from pydantic import BaseModel, ValidationError, validator


class MyModel(BaseModel):
    timestamp: datetime

    @validator('timestamp', mode='wrap')
    def validate_timestamp(cls, v, handler):
        if v == 'now':
            # we don't want to bother with further validation,
            # just return the new value
            return datetime.now()
        try:
            return handler(v)
        except ValidationError:
            # validation failed, in this case we want to
            # return a default value
            return datetime(2000, 1, 1)
```

As well as being powerful, this provides a great "escape hatch" when pydantic validation doesn't do what you need.

### More powerful alias(es) :thumbsup:

pydantic-core can support alias "paths" as well as simple string aliases to flatten data as it's validated.

Best demonstrated with an example:

```py title="Alias paths" test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, Field


class Foo(BaseModel):
    bar: str = Field(aliases=[['baz', 2, 'qux']])


data = {
    'baz': [
        {'qux': 'a'},
        {'qux': 'b'},
        {'qux': 'c'},
        {'qux': 'd'},
    ]
}

foo = Foo(**data)
assert foo.bar == 'c'
```

`aliases` is a list of lists because multiple paths can be provided, if so they're tried in turn until a value is found.

Tagged unions will use the same logic as `aliases` meaning nested attributes can be used to select a schema
to validate against.

### Improvements to Dumping/Serialization/Export :thumbsup: :confused:

(I haven't worked on this yet, so these ideas are only provisional)

There has long been a debate about how to handle converting data when extracting it from a model.
One of the features people have long requested is the ability to convert data to JSON compliant types while
converting a model to a dict.

My plan is to move data export into pydantic-core, with that, one implementation can support all export modes without
compromising (and hopefully significantly improving) performance.

I see four different export/serialization scenarios:

1. Extracting the field values of a model with no conversion, effectively `model.__dict__` but with the current filtering
   logic provided by `.dict()`
2. Extracting the field values of a model recursively (effectively what `.dict()` does now) - sub-models are converted to
   dicts, but other fields remain unchanged.
3. Extracting data and converting at the same time (e.g. to JSON compliant types)
4. Serializing data straight to JSON

I think all 4 modes can be supported in a single implementation, with a kind of "3.5" mode where a python function
is used to convert the data as the user wishes.

The current `include` and `exclude` logic is extremely complicated, but hopefully it won't be too hard to
translate it to Rust.

We should also add support for `validate_alias` and `dump_alias` as well as the standard `alias`
to allow for customising field keys.

### Validation Context :thumbsup:

Pydantic V2 will add a new optional `context` argument to `model_validate` and `model_validate_json`
which will allow you to pass information not available when creating a model to validators.
See [pydantic#1549](https://github.com/pydantic/pydantic/issues/1549) for motivation.

Here's an example of `context` might be used:

```py title="Context during Validation" test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, EmailStr, validator


class User(BaseModel):
    email: EmailStr
    home_country: str

    @validator('home_country')
    def check_home_country(cls, v, context):
        if v not in context['countries']:
            raise ValueError('invalid country choice')
        return v


async def add_user(post_data: bytes):
    countries = set(await db_connection.fetch_all('select code from country'))
    user = User.model_validate_json(post_data, context={'countries': countries})
    ...
```

!!! note
    We (actually mostly Sebastián :wink:) will have to make some changes to FastAPI to fully leverage `context`
    as we'd need some kind of dependency injection to build context before validation so models can still be passed as
    arguments to views. I'm sure he'll be game.

!!! warning
    Although this will make it slightly easier to run synchronous IO (HTTP requests, DB. queries, etc.)
    from within validators, I strongly advise you keep IO separate from validation - do it before and use context,
    do it afterwards, avoid where possible making queries inside validation.

### Model Namespace Cleanup :thumbsup:

For years I've wanted to clean up the model namespace,
see [pydantic#1001](https://github.com/pydantic/pydantic/issues/1001). This would avoid confusing gotchas when field
names clash with methods on a model, it would also make it safer to add more methods to a model without risking
new clashes.

After much deliberation (and even giving a lightning talk at the python language submit about alternatives, see
[this discussion](https://discuss.python.org/t/better-fields-access-and-allowing-a-new-character-at-the-start-of-identifiers/14529)).
I've decided to go with the simplest and clearest approach, at the expense of a bit more typing:

All methods on models will start with `model_`, fields' names will not be allowed to start with `"model"`
(aliases can be used if required).

This will mean `BaseModel` will have roughly the following signature.

```{.py .annotate title="New BaseModel methods" test="skip" lint="skip" upgrade="skip"}
class BaseModel:
    model_fields: List[FieldInfo]
    """previously `__fields__`, although the format will change a lot"""
    @classmethod
    def model_validate(cls, data: Any, *, context=None) -> Self:  # (1)
        """
        previously `parse_obj()`, validate data
        """
    @classmethod
    def model_validate_json(
        cls,
        data: str | bytes | bytearray,
        *,
        context=None
    ) -> Self:
        """
        previously `parse_raw(..., content_type='application/json')`
        validate data from JSON
        """
    @classmethod
    def model_is_instance(cls, data: Any, *, context=None) -> bool: # (2)
        """
        new, check if data is value for the model
        """
    @classmethod
    def model_is_instance_json(
        cls,
        data: str | bytes | bytearray,
        *,
        context=None
    ) -> bool:
        """
        Same as `model_is_instance`, but from JSON
        """
    def model_dump(
        self,
        include: ... = None,
        exclude: ... = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        mode: Literal['unchanged', 'dicts', 'json-compliant'] = 'unchanged',
        converter: Callable[[Any], Any] | None = None
    ) -> Any:
        """
        previously `dict()`, as before
        with new `mode` argument
        """
    def model_dump_json(self, ...) -> str:
        """
        previously `json()`, arguments as above
        effectively equivalent to `json.dump(self.model_dump(..., mode='json'))`,
        but more performant
        """
    def model_json_schema(self, ...) -> dict[str, Any]:
        """
        previously `schema()`, arguments roughly as before
        JSON schema as a dict
        """
    def model_update_forward_refs(self) -> None:
        """
        previously `update_forward_refs()`, update forward references
        """
    @classmethod
    def model_construct(
        self,
        _fields_set: set[str] | None = None,
        **values: Any
    ) -> Self:
        """
        previously `construct()`, arguments roughly as before
        construct a model with no validation
        """
    @classmethod
    def model_customize_schema(cls, schema: dict[str, Any]) -> dict[str, Any]:
        """
        new, way to customize validation,
        e.g. if you wanted to alter how the model validates certain types,
        or add validation for a specific type without custom types or
        decorated validators
        """
    class ModelConfig:
        """
        previously `Config`, configuration class for models
        """
```

1. see [Validation Context](#validation-context) for more information on `context`
2. see [`is_instance` checks](#is_instance-like-checks)

The following methods will be removed:

* `.parse_file()` - was a mistake, should never have been in pydantic
* `.parse_raw()` - partially replaced by `.model_validate_json()`, the other functionality was a mistake
* `.from_orm()` - the functionality has been moved to config, see [other improvements](#other-improvements) below
* `.schema_json()` - mostly since it causes confusion between pydantic validation schema and JSON schema,
  and can be replaced with just `json.dumps(m.model_json_schema())`
* `.copy()` instead we'll implement `__copy__` and let people use the `copy` module
  (this removes some functionality) from `copy()` but there are bugs and ambiguities with the functionality anyway

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
[set of error codes and messages](https://github.com/pydantic/pydantic-core/blob/main/src/errors/kinds.rs).

More will be added when other types are validated via pure python validators in pydantic.

I would like to add a dedicated section to the documentation with extra information for each type of error.

This would be another key in a line error: `documentation`, which would link to the appropriate section in the
docs.

Thus, errors might look like:

```py title="Line Errors Example" test="skip" lint="skip" upgrade="skip"
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

I own the `pydantic.dev` domain and will use it for at least these errors so that even if the docs URL
changes, the error will still link to the correct documentation. If developers don't want to show these errors to users,
they can always process the errors list and filter out items from each error they don't need or want.

### No pure python implementation :frowning:

Since pydantic-core is written in Rust, and I have absolutely no intention of rewriting it in python,
pydantic V2 will only work where a binary package can be installed.

pydantic-core will provide binaries in PyPI for (at least):

* **Linux**: `x86_64`, `aarch64`, `i686`, `armv7l`, `musl-x86_64` & `musl-aarch64`
* **MacOS**: `x86_64` & `arm64` (except python 3.7)
* **Windows**: `amd64` & `win32`
* **Web Assembly**: `wasm32`
  (pydantic-core is [already](https://github.com/pydantic/pydantic-core/runs/7214195252?check_suite_focus=true)
  compiled for wasm32 using emscripten and unit tests pass, except where cpython itself has
  [problems](https://github.com/pyodide/pyodide/issues/2841))

Binaries for pypy are a work in progress and will be added if possible,
see [pydantic-core#154](https://github.com/pydantic/pydantic-core/issues/154).

Other binaries can be added provided they can be (cross-)compiled on github actions.
If no binary is available from PyPI, pydantic-core can be compiled from source if Rust stable is available.

The only place where I know this will cause problems is Raspberry Pi, which is a
[mess](https://github.com/piwheels/packages/issues/254) when it comes to packages written in Rust for Python.
Effectively, until that's fixed you'll likely have to install pydantic with
`pip install -i https://pypi.org/simple/ pydantic`.

### Pydantic becomes a pure python package :thumbsup:

Pydantic V1.X is a pure python code base but is compiled with cython to provide some performance improvements.
Since the "hot" code is moved to pydantic-core, pydantic itself can go back to being a pure python package.

This should significantly reduce the size of the pydantic package and make unit tests of pydantic much faster.
In addition:

* some constraints on pydantic code can be removed once it no-longer has to be compilable with cython
* debugging will be easier as you'll be able to drop straight into the pydantic codebase as you can with other,
  pure python packages

Some pieces of edge logic could get a little slower as they're no longer compiled.

### `is_instance` like checks :thumbsup:

Strict mode also means it makes sense to provide an `is_instance` method on models which effectively run
validation then throws away the result while avoiding the (admittedly small) overhead of creating and raising
an error or returning the validation result.

To be clear, this isn't a real `isinstance` call, rather it is equivalent to

```py title="is_instance" test="skip" lint="skip" upgrade="skip"
class BaseModel:
    ...

    @classmethod
    def model_is_instance(cls, data: Any) -> bool:
        try:
            cls(**data)
        except ValidationError:
            return False
        else:
            return True
```

### I'm dropping the word "parse" and just using "validate" :neutral_face:

Partly due to the issues with the lack of strict mode,
I've gone back and forth between using the terms "parse" and "validate" for what pydantic does.

While pydantic is not simply a validation library (and I'm sure some would argue validation is not strictly what it does),
most people use the word **"validation"**.

It's time to stop fighting that, and use consistent names.

The word "parse" will no longer be used except when talking about JSON parsing, see
[model methods](#model-namespace-cleanup) above.

### Changes to custom field types :neutral_face:

Since the core structure of validators has changed from "a list of validators to call one after another" to
"a tree of validators which call each other", the
[`__get_validators__`](https://docs.pydantic.dev/usage/types/#classes-with-__get_validators__)
way of defining custom field types no longer makes sense.

Instead, we'll look for the attribute `__pydantic_validation_schema__` which must be a
pydantic-core compliant schema for validating data to this field type (the `function`
item can be a string, if so a function of that name will be taken from the class, see `'validate'` below).

Here's an example of how a custom field type could be defined:

```py title="New custom field types" test="skip" lint="skip" upgrade="skip"
from pydantic import ValidationSchema


class Foobar:
    def __init__(self, value: str):
        self.value = value

    __pydantic_validation_schema__: ValidationSchema = {
        'type': 'function',
        'mode': 'after',
        'function': 'validate',
        'schema': {'type': 'str'},
    }

    @classmethod
    def validate(cls, value):
        if 'foobar' in value:
            return Foobar(value)
        else:
            raise ValueError('expected foobar')
```

What's going on here: `__pydantic_validation_schema__` defines a schema which effectively says:

> Validate input data as a string, then call the `validate` function with that string, use the returned value
> as the final result of validation.

`ValidationSchema` is just an alias to
[`pydantic_core.Schema`](https://github.com/pydantic/pydantic-core/blob/main/pydantic_core/_types.py#L291)
which is a type defining the schema for validation schemas.

!!! note
    pydantic-core schema has full type definitions although since the type is recursive,
    mypy can't provide static type analysis, pyright however can.

We can probably provide one or more helper functions to make `__pydantic_validation_schema__` easier to generate.

## Other Improvements :thumbsup:

Some other things which will also change, IMHO for the better:

1. Recursive models with cyclic references - although recursive models were supported by pydantic V1,
   data with cyclic references caused recursion errors, in pydantic-core cyclic references are correctly detected
   and a validation error is raised
2. The reason I've been so keen to get pydantic-core to compile and run with wasm is that I want all examples
   in the docs of pydantic V2 to be editable and runnable in the browser
3. Full support for `TypedDict`, including `total=False` - e.g. omitted keys,
   providing validation schema to a `TypedDict` field/item will use `Annotated`, e.g. `Annotated[str, Field(strict=True)]`
4. `from_orm` has become `from_attributes` and is now defined at schema generation time
   (either via model config or field config)
5. `input_value` has been added to each line error in a `ValidationError`, making errors easier to understand,
   and more comprehensive details of errors to be provided to end users,
   [pydantic#784](https://github.com/pydantic/pydantic/issues/784)
6. `on_error` logic in a schema which allows either a default value to be used in the event of an error,
   or that value to be omitted (in the case of a `total=False` `TypedDict`),
   [pydantic-core#151](https://github.com/pydantic/pydantic-core/issues/151)
7. `datetime`, `date`, `time` & `timedelta` validation is improved, see the
   [speedate] Rust library I built specifically for this purpose for more details
8. Powerful "priority" system for optionally merging or overriding config in sub-models for nested schemas
9. Pydantic will support [annotated-types](https://github.com/annotated-types/annotated-types),
   so you can do stuff like `Annotated[set[int], Len(0, 10)]` or `Name = Annotated[str, Len(1, 1024)]`
10. A single decorator for general usage - we should add a `validate` decorator which can be used:
  * on functions (replacing `validate_arguments`)
  * on dataclasses, `pydantic.dataclasses.dataclass` will become an alias of this
  * on `TypedDict`s
  * On any supported type, e.g. `Union[...]`, `Dict[str, Thing]`
  * On Custom field types - e.g. anything with a `__pydantic_schema__` attribute
11. Easier validation error creation, I've often found myself wanting to raise `ValidationError`s outside
    models, particularly in FastAPI
    ([here](https://github.com/samuelcolvin/foxglove/blob/a4aaacf372178f345e5ff1d569ee8fd9d10746a4/foxglove/exceptions.py#L137-L149)
    is one method I've used), we should provide utilities to generate these errors
12. Improve the performance of `__eq__` on models
13. Computed fields, these having been an idea for a long time in pydantic - we should get them right
14. Model validation that avoids instances of subclasses leaking data (particularly important for FastAPI),
    see [pydantic-core#155](https://github.com/pydantic/pydantic-core/issues/155)
15. We'll now follow [semvar](https://semver.org/) properly and avoid breaking changes between minor versions,
    as a result, major versions will become more common
16. Improve generics to use `M(Basemodel, Generic[T])` instead of `M(GenericModel, Generic[T])` - e.g. `GenericModel`
    can be removed; this results from no-longer needing to compile pydantic code with cython

## Removed Features & Limitations :frowning:

The emoji here is just for variation, I'm not frowning about any of this, these changes are either good IMHO
(will make pydantic cleaner, easier to learn and easier to maintain) or irrelevant to 99.9+% of users.

1. `__root__` custom root models are no longer necessary since validation on any supported data type is allowed
   without a model
2. `.parse_file()` and `.parse_raw()`, partially replaced with `.model_validate_json()`,
   see [model methods](#model-namespace-cleanup)
3. `.schema_json()` & `.copy()`, see [model methods](#model-namespace-cleanup)
4. `TypeError` are no longer considered as validation errors, but rather as internal errors, this is to better
   catch errors in argument names in function validators.
5. Subclasses of builtin types like `str`, `bytes` and `int` are coerced to their parent builtin type,
   this is a limitation of how pydantic-core converts these types to Rust types during validation, if you have a
   specific need to keep the type, you can use wrap validators or custom type validation as described above
6. integers are represented in rust code as `i64`, meaning if you want to use ints where `abs(v) > 2^63 − 1`
   (9,223,372,036,854,775,807), you'll need to use a [wrap validator](#validator-function-improvements) and your own logic
7. [Settings Management](https://docs.pydantic.dev/usage/settings/) ??? - I definitely don't want to
   remove the functionality, but it's something of a historical curiosity that it lives within pydantic,
   perhaps it should move to a separate package, perhaps installable alongside pydantic with
   `pip install pydantic[settings]`?
8. The following `Config` properties will be removed or deprecated:
   * `fields` - it's very old (it pre-dates `Field`), can be removed
   * `allow_mutation` will be removed, instead `frozen` will be used
   * `error_msg_templates`, it's not properly documented anyway, error messages can be customized with external logic if required
   * `getter_dict` - pydantic-core has hardcoded `from_attributes` logic
   * `json_loads` - again this is hard coded in pydantic-core
   * `json_dumps` - possibly
   * `json_encoders` - see the export "mode" discussion [above](#improvements-to-dumpingserializationexport)
   * `underscore_attrs_are_private` we should just choose a sensible default
   * `smart_union` - all unions are now "smart"
9. `dict(model)` functionality should be removed, there's a much clearer distinction now that in 2017 when I
   implemented this between a model and a dict

## Features Remaining :neutral_face:

The following features will remain (mostly) unchanged:

* JSONSchema, internally this will need to change a lot, but hopefully the external interface will remain unchanged
* `dataclass` support, again internals might change, but not the external interface
* `validate_arguments`, might be renamed, but otherwise remain
* hypothesis plugin, might be able to improve this as part of the general cleanup

## Questions :question:

I hope the explanation above is useful. I'm sure people will have questions and feedback; I'm aware
I've skipped over some features with limited detail (this post is already fairly long :sleeping:).

To allow feedback without being overwhelmed, I've created a "Pydantic V2" category for
[discussions on github](https://github.com/pydantic/pydantic/discussions/categories/pydantic-v2) - please
feel free to create a discussion if you have any questions or suggestions.
We will endeavour to read and respond to everyone.

---

## Implementation Details :nerd:

(This is yet to be built, so these are nascent ideas which might change)

At the center of pydantic v2 will be a `PydanticValidator` class which looks roughly like this
(note: this is just pseudo-code, it's not even valid python and is only supposed to be used to demonstrate the idea):

```py title="PydanticValidator" test="skip" lint="skip" upgrade="skip"
# type identifying data which has been validated,
# as per pydantic-core, this can include "fields_set" data
ValidData = ...

# any type we can perform validation for
AnyOutputType = ...

class PydanticValidator:
    def __init__(self, output_type: AnyOutputType, config: Config):
        ...
    def validate(self, input_data: Any) -> ValidData:
        ...
    def validate_json(self, input_data: str | bytes | bytearray) -> ValidData:
        ...
    def is_instance(self, input_data: Any) -> bool:
        ...
    def is_instance_json(self, input_data: str | bytes | bytearray) -> bool:
        ...
    def json_schema(self) -> dict:
        ...
    def dump(
        self,
        data: ValidData,
        include: ... = None,
        exclude: ... = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        mode: Literal['unchanged', 'dicts', 'json-compliant'] = 'unchanged',
        converter: Callable[[Any], Any] | None = None
    ) -> Any:
        ...
    def dump_json(self, ...) -> str:
        ...
```

This could be used directly, but more commonly will be used by the following:

* `BaseModel`
* the `validate` decorator described above
* `pydantic.dataclasses.dataclass` (which might be an alias of `validate`)
* generics

The aim will be to get pydantic V2 to a place were the vast majority of tests continue to pass unchanged.

Thereby guaranteeing (as much as possible) that the external interface to pydantic and its behaviour are unchanged.

## Conversion Table :material-table:

The table below provisionally defines what input value types are allowed to which field types.

**An updated and complete version of this table is available in [V2 conversion table](../concepts/conversion_table.md)**.

!!!note
    Some type conversion shown here is a significant departure from existing behavior, we may have to provide a config
    flag for backwards compatibility for a few of them, however pydantic V2 cannot be entirely backward compatible,
    see [pydantic-core#152](https://github.com/pydantic/pydantic-core/issues/152).

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
| `TypedDict`    | `dict`      | both   | python       | -                                                                           |
| `TypedDict`    | `Object`    | both   | JSON         | -                                                                           |
| `TypedDict`    | `Any`       | both   | python       | builtins not allowed, uses `getattr`, requires `from_attributes=True`       |
| `TypedDict`    | `mapping`   | lax    | python       | must implement the mapping interface and have an `items()` method           |
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

The `ModelClass` validator (use to create instances of a class) uses the `TypedDict` validator, then creates an instance
with `__dict__` and `__fields_set__` set, so same rules apply as `TypedDict`.

[speedate]: https://docs.rs/speedate/latest/speedate/
