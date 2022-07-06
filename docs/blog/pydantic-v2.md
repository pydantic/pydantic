# Pydantic V2

I've spoken to quite a few people about pydantic V2, and mention it in passing even more.

I think I owe people a proper explanation of the plan for V2:
* What will change
* What will be added
* What will be removed
* How I'm intending to go about completing it and getting it released
* Some idea of timeframe :fearful:

Here goes...

# Plan & Timeframe

I'm currently taking a kind of "sabbatical" after leaving my last job to get pydantic V2 released.
Why? Well I ask myself that quite often. I'm very proud of how much pydantic is used, but I'm less proud of its internals.
Since it's something people seem to use quite a lot (26m downloads a month, Used 72k public repos on GitHub),
I want it to be as good as possible.

While I'm on the subject of why, how and my odd sabbatical: if you work for a large company who use pydantic a lot,
you should encourage the company to **sponsor me a meaningful amount**, 
like [Salesforce did](https://twitter.com/samuel_colvin/status/1501288247670063104).
This is not charity, recruitment or marketing - the argument should be about how much the company will save if
pydantic is 10x faster, more stable and more powerful - it would be worth paying me 10% of that to make it happen.

The plan is to have pydantic V2 released within 3 months of full time work 
(again, that'll be sooner if I can continue to work on it full time).

Before pydantic V2 can be released, we need to released pydantic v1.10 - there are lots of changes in the main
branch of pydantic contributed by the community, it's only fair to provide a release including those changes,
many of them will remain unchanged for V2, the rest will act as a requirement to make sure pydantic V2 includes
the capabilities they implemented.

The basic road map for me is as follows:
1. implement a few more critical features in pydantic-core
2. release V0.1 of pydantic-core
3. work on getting pydantic V1.10 out - basically merge all open PRs that are finished
4. release pydantic V1.10
5. delete all stale PRs which didn't make it into V1.10, apologise profusely to their authors who put their valuable
  time into pydantic only to have their PRs closed :pray:
6. change the main branch of pydantic to target v2
7. start tearing pydantic code apart and see how many existing tests can be made to pass
8. rinse, repeat
9. release pydantic V2 :tada:

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

**Note:** the python interface to pydantic shouldn't change as a result of using pydantic-core, instead
pydantic will use type annotations to build a schema for pydantic-core to use.

pydantic-core is usable now, albeit with a fairly unintuitive API, if you're interested, please give it a try.

pydantic-core provides validators for all common data types, 
[see a list here](https://github.com/samuelcolvin/pydantic-core/blob/main/pydantic_core/_types.py#L291).
Other, less commonly used data types will be supported via validator functions.

### Performance :smile:

As a result of the move to rust for the validation logic 
(and significant improvements in how validation objects are structured) pydantic V2 will be significantly faster
than pydantic V1.X.

Looking at the pydantic-core [benchmarks](https://github.com/samuelcolvin/pydantic-core/tree/main/tests/benchmarks),
pydantic V2 is between 4x and 50x faster than pydantic V1.X.

In general, pydantic V2 is about 17x faster than V1.X when validating a representative model containing a range
of common fields.

### Strict Mode :smile:

People have long complained about pydantic preference for coercing data instead of throwing an error.
E.g. input to an `int` field could be `123` or the string `"123"` which would be converted to `123`.

pydantic-core comes with "strict mode" built in. With this only the exact data type is allowed, e.g. passing
`"123"` to an `int` field would result in a validation error.

Strictness can be defined on a per-field basis, or whole model.

#### IsInstance checks :smile:

Strict mode also means it makes sense to provide an `is_instance` method on validators which effectively run
validation then throw away the result while avoiding the (admittedly small) overhead of creating and raising
and error or returning the validation result.

### Formalised Conversion Table :smile:

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

### Built in JSON support :smile:

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

### Validation without a Model :smile:

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

### Strict API & API documentation :smile:

When preparing a pydantic V2, we'll make a strict distinction between the public API and private functions & classes.
Private objects clearly identified as private via `_internal` sub package to discourage use.

The public API will have API documentation. I've recently been working with the wonderful
[mkdocstrings](https://github.com/mkdocstrings/mkdocstrings) for both 
[dirty-equals](https://dirty-equals.helpmanual.io/) and
[watchfiles](https:://watchfiles.helpmanual.io/) documentation. I intend to use `mkdocstrings` to generate complete
API documentation.

This wouldn't replace the current example-based somewhat informal documentation style byt instead will augment it.

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

### Pydantic becomes a pure python package :confused:

Pydantic v1.X is a pure python code base but is compiled with cython to provide some performance improvements.
Since the "hot" code is moved to pydantic-core, pydantic itself can go back to being a pure python package.

This should significantly reduce the size of the pydantic package and make unit tests of pydantic much faster.
In addition, some constraints on pydantic code can be removed once it no-longer has to be compilable with cython.

Some pieces of edge logic could get a little slower as they're no longer compiled.

## Other Improvements :smile:

* Recursive models
* Documentation examples you can edit and run

TODO

## Removed Features :neutral_face:

* `__root__` models

TODO

## Conversion Table

TODO
