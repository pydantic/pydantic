## v1.10.12 (2023-07-24)

* Fixes the `maxlen` property being dropped on `deque` validation. Happened only if the deque item has been typed. Changes the `_validate_sequence_like` func, #6581 by @maciekglowka

## v1.10.11 (2023-07-04)

* Importing create_model in tools.py through relative path instead of absolute path - so that it doesn't import V2 code when copied over to V2 branch, #6361 by @SharathHuddar

## v2.0b3 (2023-06-16)

Third beta pre-release of Pydantic V2

See the full changelog [here](https://github.com/pydantic/pydantic/releases/tag/v2.0b3)

## v2.0b2 (2023-06-03)

Add `from_attributes` runtime flag to `TypeAdapter.validate_python` and `BaseModel.model_validate`.

See the full changelog [here](https://github.com/pydantic/pydantic/releases/tag/v2.0b2)

## v2.0b1 (2023-06-01)

First beta pre-release of Pydantic V2

See the full changelog [here](https://github.com/pydantic/pydantic/releases/tag/v2.0b1)

## v2.0a4 (2023-05-05)

Fourth pre-release of Pydantic V2

See the full changelog [here](https://github.com/pydantic/pydantic/releases/tag/v2.0a4)

## v2.0a3 (2023-04-20)

Third pre-release of Pydantic V2

See the full changelog [here](https://github.com/pydantic/pydantic/releases/tag/v2.0a3)

## v2.0a2 (2023-04-12)

Second pre-release of Pydantic V2

See the full changelog [here](https://github.com/pydantic/pydantic/releases/tag/v2.0a2)

## v2.0a1 (2023-04-03)

First pre-release of Pydantic V2!

See [this post](https://docs.pydantic.dev/blog/pydantic-v2-alpha/) for more details.

## v1.10.10 (2023-06-30)

* Add Pydantic `Json` field support to settings management, #6250 by @hramezani
* Fixed literal validator errors for unhashable values, #6188 by @markus1978
* Fixed bug with generics receiving forward refs, #6130 by @mark-todd
* Update install method of FastAPI for internal tests in CI, #6117 by @Kludex

## v1.10.9 (2023-06-07)

* Fix trailing zeros not ignored in Decimal validation, #5968 by @hramezani
* Fix mypy plugin for v1.4.0, #5928 by @cdce8p
* Add future and past date hypothesis strategies, #5850 by @bschoenmaeckers
* Discourage usage of Cython 3 with Pydantic 1.x, #5845 by @lig

## v1.10.8 (2023-05-23)

* Fix a bug in `Literal` usage with `typing-extension==4.6.0`, #5826 by @hramezani
* This solves the (closed) issue #3849 where aliased fields that use discriminated union fail to validate when the data contains the non-aliased field name, #5736 by @benwah
* Update email-validator dependency to >=2.0.0post2, #5627 by @adriangb
* update `AnyClassMethod` for changes in [python/typeshed#9771](https://github.com/python/typeshed/issues/9771), #5505 by @ITProKyle

## v1.10.7 (2023-03-22)

* Fix creating schema from model using `ConstrainedStr` with `regex` as dict key, #5223 by @matejetz
* Address bug in mypy plugin caused by explicit_package_bases=True, #5191 by @dmontagu
* Add implicit defaults in the mypy plugin for Field with no default argument, #5190 by @dmontagu
* Fix schema generated for Enum values used as Literals in discriminated unions, #5188 by @javibookline
* Fix mypy failures caused by the pydantic mypy plugin when users define `from_orm` in their own classes, #5187 by @dmontagu
* Fix `InitVar` usage with pydantic dataclasses, mypy version `1.1.1` and the custom mypy plugin, #5162 by @cdce8p

## v1.10.6 (2023-03-08)

* Implement logic to support creating validators from non standard callables by using defaults to identify them and unwrapping `functools.partial` and `functools.partialmethod` when checking the signature, #5126 by @JensHeinrich
* Fix mypy plugin for v1.1.1, and fix `dataclass_transform` decorator for pydantic dataclasses, #5111 by @cdce8p
* Raise `ValidationError`, not `ConfigError`, when a discriminator value is unhashable, #4773 by @kurtmckee

## v1.10.5 (2023-02-15)

* Fix broken parametrized bases handling with `GenericModel`s with complex sets of models, #5052 by @MarkusSintonen
* Invalidate mypy cache if plugin config changes, #5007 by @cdce8p
* Fix `RecursionError` when deep-copying dataclass types wrapped by pydantic, #4949 by @mbillingr
* Fix `X | Y` union syntax breaking `GenericModel`, #4146 by @thenx
* Switch coverage badge to show coverage for this branch/release, #5060 by @samuelcolvin

## v1.10.4 (2022-12-30)

* Change dependency to `typing-extensions>=4.2.0`, #4885 by @samuelcolvin

## v1.10.3 (2022-12-29)

**NOTE: v1.10.3 was ["yanked"](https://pypi.org/help/#yanked) from PyPI due to #4885 which is fixed in v1.10.4**

* fix parsing of custom root models, #4883 by @gou177
* fix: use dataclass proxy for frozen or empty dataclasses, #4878 by @PrettyWood
* Fix `schema` and `schema_json` on models where a model instance is a one of default values, #4781 by @Bobronium
* Add Jina AI to sponsors on docs index page, #4767 by @samuelcolvin
* fix: support assignment on `DataclassProxy`, #4695 by @PrettyWood
* Add `postgresql+psycopg` as allowed scheme for `PostgreDsn` to make it usable with SQLAlchemy 2, #4689 by @morian
* Allow dict schemas to have both `patternProperties` and `additionalProperties`, #4641 by @jparise
* Fixes error passing None for optional lists with `unique_items`, #4568 by @mfulgo
* Fix `GenericModel` with `Callable` param raising a `TypeError`, #4551 by @mfulgo
* Fix field regex with `StrictStr` type annotation, #4538 by @sisp
* Correct `dataclass_transform` keyword argument name from `field_descriptors` to `field_specifiers`, #4500 by @samuelcolvin
* fix: avoid multiple calls of `__post_init__` when dataclasses are inherited, #4487 by @PrettyWood
* Reduce the size of binary wheels, #2276 by @samuelcolvin

## v1.10.2 (2022-09-05)

* **Revert Change:** Revert percent encoding of URL parts which was originally added in #4224, #4470 by @samuelcolvin
* Prevent long (length > `4_300`) strings/bytes as input to int fields, see 
  [python/cpython#95778](https://github.com/python/cpython/issues/95778) and 
  [CVE-2020-10735](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-10735), #1477 by @samuelcolvin
* fix: dataclass wrapper was not always called, #4477 by @PrettyWood
* Use `tomllib` on Python 3.11 when parsing `mypy` configuration, #4476 by @hauntsaninja
* Basic fix of `GenericModel` cache to detect order of arguments in `Union` models, #4474 by @sveinugu
* Fix mypy plugin when using bare types like `list` and `dict` as `default_factory`, #4457 by @samuelcolvin

## v1.10.1 (2022-08-31)

* Add `__hash__` method to `pydancic.color.Color` class, #4454 by @czaki

## v1.10.0 (2022-08-30)

* Refactor the whole _pydantic_ `dataclass` decorator to really act like its standard lib equivalent.
  It hence keeps `__eq__`, `__hash__`, ... and makes comparison with its non-validated version possible.
  It also fixes usage of `frozen` dataclasses in fields and usage of `default_factory` in nested dataclasses.
  The support of `Config.extra` has been added.
  Finally, config customization directly via a `dict` is now possible, #2557 by @PrettyWood
  <br/><br/>
  **BREAKING CHANGES:**
  - The `compiled` boolean (whether _pydantic_ is compiled with cython) has been moved from `main.py` to `version.py`
  - Now that `Config.extra` is supported, `dataclass` ignores by default extra arguments (like `BaseModel`)
* Fix PEP487 `__set_name__` protocol in `BaseModel` for PrivateAttrs, #4407 by @tlambert03
* Allow for custom parsing of environment variables via `parse_env_var` in `Config`, #4406 by @acmiyaguchi
* Rename `master` to `main`, #4405 by @hramezani
* Fix `StrictStr` does not raise `ValidationError` when `max_length` is present in `Field`, #4388 by @hramezani
* Make `SecretStr` and `SecretBytes` hashable, #4387 by @chbndrhnns
* Fix `StrictBytes` does not raise `ValidationError` when `max_length` is present in `Field`, #4380 by @JeanArhancet
* Add support for bare `type`, #4375 by @hramezani
* Support Python 3.11, including binaries for 3.11 in PyPI, #4374 by @samuelcolvin
* Add support for `re.Pattern`, #4366 by @hramezani
* Fix `__post_init_post_parse__` is incorrectly passed keyword arguments when no `__post_init__` is defined, #4361 by @hramezani
* Fix implicitly importing `ForwardRef` and `Callable` from `pydantic.typing` instead of `typing` and also expose `MappingIntStrAny`, #4358 by @aminalaee
* remove `Any` types from the `dataclass` decorator so it can be used with the `disallow_any_expr` mypy option, #4356 by @DetachHead
* moved repo to `pydantic/pydantic`, #4348 by @yezz123
* fix "extra fields not permitted" error when dataclass with `Extra.forbid` is validated multiple times, #4343 by @detachhead
* Add Python 3.9 and 3.10 examples to docs, #4339 by @Bobronium
* Discriminated union models now use `oneOf` instead of `anyOf` when generating OpenAPI schema definitions, #4335 by @MaxwellPayne
* Allow type checkers to infer inner type of `Json` type. `Json[list[str]]` will be now inferred as `list[str]`, 
  `Json[Any]` should be used instead of plain `Json`.
  Runtime behaviour is not changed, #4332 by @Bobronium
* Allow empty string aliases by using a `alias is not None` check, rather than `bool(alias)`, #4253 by @sergeytsaplin
* Update `ForwardRef`s in `Field.outer_type_`, #4249 by @JacobHayes
* The use of `__dataclass_transform__` has been replaced by `typing_extensions.dataclass_transform`, which is the preferred way to mark pydantic models as a dataclass under [PEP 681](https://peps.python.org/pep-0681/), #4241 by @multimeric
* Use parent model's `Config` when validating nested `NamedTuple` fields, #4219 by @synek
* Update `BaseModel.construct` to work with aliased Fields, #4192 by @kylebamos
* Catch certain raised errors in `smart_deepcopy` and revert to `deepcopy` if so, #4184 by @coneybeare
* Add `Config.anystr_upper` and `to_upper` kwarg to constr and conbytes, #4165 by @satheler
* Fix JSON schema for `set` and `frozenset` when they include default values, #4155 by @aminalaee
* Teach the mypy plugin that methods decorated by `@validator` are classmethods, #4102 by @DMRobertson
* Improve mypy plugin's ability to detect required fields, #4086 by @richardxia
* Support fields of type `Type[]` in schema, #4051 by @aminalaee
* Add `default` value in JSON Schema when `const=True`, #4031 by @aminalaee
* Adds reserved word check to signature generation logic, #4011 by @strue36
* Fix Json strategy failure for the complex nested field, #4005 by @sergiosim
* Add JSON-compatible float constraint `allow_inf_nan`, #3994 by @tiangolo
* Remove undefined behaviour when `env_prefix` had characters in common with `env_nested_delimiter`, #3975 by @arsenron
* Support generics model with `create_model`, #3945 by @hot123s
* allow submodels to overwrite extra field info, #3934 by @PrettyWood
* Document and test structural pattern matching ([PEP 636](https://peps.python.org/pep-0636/)) on `BaseModel`, #3920 by @irgolic
* Fix incorrect deserialization of python timedelta object to ISO 8601 for negative time deltas.
  Minus was serialized in incorrect place ("P-1DT23H59M59.888735S" instead of correct "-P1DT23H59M59.888735S"), #3899 by @07pepa
* Fix validation of discriminated union fields with an alias when passing a model instance, #3846 by @chornsby
* Add a CockroachDsn type to validate CockroachDB connection strings. The type
  supports the following schemes: `cockroachdb`, `cockroachdb+psycopg2` and `cockroachdb+asyncpg`, #3839 by @blubber
* Fix MyPy plugin to not override pre-existing `__init__` method in models, #3824 by @patrick91
* Fix mypy version checking, #3783 by @KotlinIsland
* support overwriting dunder attributes of `BaseModel` instances, #3777 by @PrettyWood
* Added `ConstrainedDate` and `condate`, #3740 by @hottwaj
* Support `kw_only` in dataclasses, #3670 by @detachhead
* Add comparison method for `Color` class, #3646 by @aminalaee
* Drop support for python3.6, associated cleanup, #3605 by @samuelcolvin
* created new function `to_lower_camel()` for "non pascal case" camel case, #3463 by @schlerp
* Add checks to `default` and `default_factory` arguments in Mypy plugin, #3430 by @klaa97
* fix mangling of `inspect.signature` for `BaseModel`, #3413 by @fix-inspect-signature
* Adds the `SecretField` abstract class so that all the current and future secret fields like `SecretStr` and `SecretBytes` will derive from it, #3409 by @expobrain
* Support multi hosts validation in `PostgresDsn`, #3337 by @rglsk
* Fix parsing of very small numeric timedelta values, #3315 by @samuelcolvin
* Update `SecretsSettingsSource` to respect `config.case_sensitive`, #3273 by @JeanArhancet
* Add MongoDB network data source name (DSN) schema, #3229 by @snosratiershad
* Add support for multiple dotenv files, #3222 by @rekyungmin
* Raise an explicit `ConfigError` when multiple fields are incorrectly set for a single validator, #3215 by @SunsetOrange
* Allow ellipsis on `Field`s inside `Annotated` for `TypedDicts` required, #3133 by @ezegomez
* Catch overflow errors in `int_validator`, #3112 by @ojii
* Adds a `__rich_repr__` method to `Representation` class which enables pretty printing with [Rich](https://github.com/willmcgugan/rich), #3099 by @willmcgugan
* Add percent encoding in `AnyUrl` and descendent types, #3061 by @FaresAhmedb
* `validate_arguments` decorator now supports `alias`, #3019 by @MAD-py
* Avoid `__dict__` and `__weakref__` attributes in `AnyUrl` and IP address fields, #2890 by @nuno-andre
* Add ability to use `Final` in a field type annotation, #2766 by @uriyyo
* Update requirement to `typing_extensions>=4.1.0` to guarantee `dataclass_transform` is available, #4424 by @commonism
* Add Explosion and AWS to main sponsors, #4413 by @samuelcolvin
* Update documentation for `copy_on_model_validation` to reflect recent changes, #4369 by @samuelcolvin
* Runtime warning if `__slots__` is passed to `create_model`, `__slots__` is then ignored, #4432 by @samuelcolvin
* Add type hints to `BaseSettings.Config` to avoid mypy errors, also correct mypy version compatibility notice in docs, #4450 by @samuelcolvin

## v1.10.0b1 (2022-08-24)

Pre-release, see [the GitHub release](https://github.com/pydantic/pydantic/releases/tag/v1.10.0b1) for details.

## v1.10.0a2 (2022-08-24)

Pre-release, see [the GitHub release](https://github.com/pydantic/pydantic/releases/tag/v1.10.0a2) for details.

## v1.10.0a1 (2022-08-22)

Pre-release, see [the GitHub release](https://github.com/pydantic/pydantic/releases/tag/v1.10.0a1) for details.

## v1.9.2 (2022-08-11)

**Revert Breaking Change**: _v1.9.1_ introduced a breaking change where model fields were
deep copied by default, this release reverts the default behaviour to match _v1.9.0_ and before, 
while also allow deep-copy behaviour via `copy_on_model_validation = 'deep'`. See #4092 for more information.

* Allow for shallow copies of model fields, `Config.copy_on_model_validation` is now a str which must be
  `'none'`, `'deep'`, or `'shallow'` corresponding to not copying, deep copy & shallow copy; default `'shallow'`, 
  #4093 by @timkpaine

## v1.9.1 (2022-05-19)

Thank you to pydantic's sponsors:
@tiangolo, @stellargraph, @JonasKs, @grillazz, @Mazyod, @kevinalh, @chdsbd, @povilasb, @povilasb, @jina-ai, 
@mainframeindustries, @robusta-dev, @SendCloud, @rszamszur, @jodal, @hardbyte, @corleyma, @daddycocoaman, 
@Rehket, @jokull, @reillysiemens, @westonsteimel, @primer-io, @koxudaxi, @browniebroke, @stradivari96, 
@adriangb, @kamalgill, @jqueguiner, @dev-zero, @datarootsio, @RedCarpetUp
for their kind support.

* Limit the size of `generics._generic_types_cache` and `generics._assigned_parameters` 
  to avoid unlimited increase in memory usage, #4083 by @samuelcolvin
* Add Jupyverse and FPS as Jupyter projects using pydantic, #4082 by @davidbrochart
* Speedup `__isinstancecheck__` on pydantic models when the type is not a model, may also avoid memory "leaks", #4081 by @samuelcolvin
* Fix in-place modification of `FieldInfo` that caused problems with PEP 593 type aliases, #4067 by @adriangb
* Add support for autocomplete in VS Code via `__dataclass_transform__` when using `pydantic.dataclasses.dataclass`, #4006 by @giuliano-oliveira
* Remove benchmarks from codebase and docs, #3973 by @samuelcolvin
* Typing checking with pyright in CI, improve docs on vscode/pylance/pyright, #3972 by @samuelcolvin
* Fix nested Python dataclass schema regression, #3819 by @himbeles
* Update documentation about lazy evaluation of sources for Settings, #3806 by @garyd203
* Prevent subclasses of bytes being converted to bytes, #3706 by @samuelcolvin
* Fixed "error checking inheritance of" when using PEP585 and PEP604 type hints, #3681 by @aleksul
* Allow self referencing `ClassVar`s in models, #3679 by @samuelcolvin
* **Breaking Change, see #4106**: Fix issue with self-referencing dataclass, #3675 by @uriyyo
* Include non-standard port numbers in rendered URLs, #3652 by @dolfinus
* `Config.copy_on_model_validation` does a deep copy and not a shallow one, #3641 by @PrettyWood
* fix: clarify that discriminated unions do not support singletons, #3636 by @tommilligan
* Add `read_text(encoding='utf-8')` for `setup.py`, #3625 by @hswong3i
* Fix JSON Schema generation for Discriminated Unions within lists, #3608 by @samuelcolvin

## v1.9.0 (2021-12-31)

Thank you to pydantic's sponsors:
@sthagen, @timdrijvers, @toinbis, @koxudaxi, @ginomempin, @primer-io, @and-semakin, @westonsteimel, @reillysiemens,
@es3n1n, @jokull, @JonasKs, @Rehket, @corleyma, @daddycocoaman, @hardbyte, @datarootsio, @jodal, @aminalaee, @rafsaf, 
@jqueguiner, @chdsbd, @kevinalh, @Mazyod, @grillazz, @JonasKs, @simw, @leynier, @xfenix
for their kind support.

### Highlights

* add Python 3.10 support, #2885 by @PrettyWood
* [Discriminated unions](https://docs.pydantic.dev/usage/types/#discriminated-unions-aka-tagged-unions), #619 by @PrettyWood
* [`Config.smart_union` for better union logic](https://docs.pydantic.dev/usage/model_config/#smart-union), #2092 by @PrettyWood
* Binaries for Macos M1 CPUs, #3498 by @samuelcolvin
* Complex types can be set via [nested environment variables](https://docs.pydantic.dev/usage/settings/#parsing-environment-variable-values), e.g. `foo___bar`, #3159 by @Air-Mark
* add a dark mode to _pydantic_ documentation, #2913 by @gbdlin
* Add support for autocomplete in VS Code via `__dataclass_transform__`, #2721 by @tiangolo
* Add "exclude" as a field parameter so that it can be configured using model config, #660 by @daviskirk

### v1.9.0 (2021-12-31) Changes

* Apply `update_forward_refs` to `Config.json_encodes` prevent name clashes in types defined via strings, #3583 by @samuelcolvin
* Extend pydantic's mypy plugin to support mypy versions `0.910`, `0.920`, `0.921` & `0.930`, #3573 & #3594 by @PrettyWood, @christianbundy, @samuelcolvin

### v1.9.0a2 (2021-12-24) Changes

* support generic models with discriminated union, #3551 by @PrettyWood
* keep old behaviour of `json()` by default, #3542 by @PrettyWood
* Removed typing-only `__root__` attribute from `BaseModel`, #3540 by @layday
* Build Python 3.10 wheels, #3539 by @mbachry
* Fix display of `extra` fields with model `__repr__`, #3234 by @cocolman
* models copied via `Config.copy_on_model_validation` always have all fields, #3201 by @PrettyWood
* nested ORM from nested dictionaries, #3182 by @PrettyWood
* fix link to discriminated union section by @PrettyWood

### v1.9.0a1 (2021-12-18) Changes

* Add support for `Decimal`-specific validation configurations in `Field()`, additionally to using `condecimal()`, 
  to allow better support from editors and tooling, #3507 by @tiangolo
* Add `arm64` binaries suitable for MacOS with an M1 CPU to PyPI, #3498 by @samuelcolvin
* Fix issue where `None` was considered invalid when using a `Union` type containing `Any` or `object`, #3444 by @tharradine
* When generating field schema, pass optional `field` argument (of type
  `pydantic.fields.ModelField`) to `__modify_schema__()` if present, #3434 by @jasujm
* Fix issue when pydantic fail to parse `typing.ClassVar` string type annotation, #3401 by @uriyyo
* Mention Python >= 3.9.2 as an alternative to `typing_extensions.TypedDict`, #3374 by @BvB93
* Changed the validator method name in the [Custom Errors example](https://docs.pydantic.dev/usage/models/#custom-errors) 
  to more accurately describe what the validator is doing; changed from `name_must_contain_space` to ` value_must_equal_bar`, #3327 by @michaelrios28
* Add `AmqpDsn` class, #3254 by @kludex
* Always use `Enum` value as default in generated JSON schema, #3190 by @joaommartins
* Add support for Mypy 0.920, #3175 by @christianbundy
* `validate_arguments` now supports `extra` customization (used to always be `Extra.forbid`), #3161 by @PrettyWood
* Complex types can be set by nested environment variables, #3159 by @Air-Mark
* Fix mypy plugin to collect fields based on `pydantic.utils.is_valid_field` so that it ignores untyped private variables, #3146 by @hi-ogawa
* fix `validate_arguments` issue with `Config.validate_all`, #3135 by @PrettyWood
* avoid dict coercion when using dict subclasses as field type, #3122 by @PrettyWood
* add support for `object` type, #3062 by @PrettyWood
* Updates pydantic dataclasses to keep `_special` properties on parent classes, #3043 by @zulrang
* Add a `TypedDict` class for error objects, #3038 by @matthewhughes934
* Fix support for using a subclass of an annotation as a default, #3018 by @JacobHayes
* make `create_model_from_typeddict` mypy compliant, #3008 by @PrettyWood
* Make multiple inheritance work when using `PrivateAttr`, #2989 by @hmvp
* Parse environment variables as JSON, if they have a `Union` type with a complex subfield, #2936 by @cbartz
* Prevent `StrictStr` permitting `Enum` values where the enum inherits from `str`, #2929 by @samuelcolvin
* Make `SecretsSettingsSource` parse values being assigned to fields of complex types when sourced from a secrets file, 
  just as when sourced from environment variables, #2917 by @davidmreed
* add a dark mode to _pydantic_ documentation, #2913 by @gbdlin
* Make `pydantic-mypy` plugin compatible with `pyproject.toml` configuration, consistent with `mypy` changes. 
  See the [doc](https://docs.pydantic.dev/mypy_plugin/#configuring-the-plugin) for more information, #2908 by @jrwalk
* add Python 3.10 support, #2885 by @PrettyWood
* Correctly parse generic models with `Json[T]`, #2860 by @geekingfrog
* Update contrib docs re: Python version to use for building docs, #2856 by @paxcodes
* Clarify documentation about _pydantic_'s support for custom validation and strict type checking, 
  despite _pydantic_ being primarily a parsing library, #2855 by @paxcodes
* Fix schema generation for `Deque` fields, #2810 by @sergejkozin
* fix an edge case when mixing constraints and `Literal`, #2794 by @PrettyWood
* Fix postponed annotation resolution for `NamedTuple` and `TypedDict` when they're used directly as the type of fields 
  within Pydantic models, #2760 by @jameysharp
* Fix bug when `mypy` plugin fails on `construct` method call for `BaseSettings` derived classes, #2753 by @uriyyo
* Add function overloading for a `pydantic.create_model` function, #2748 by @uriyyo
* Fix mypy plugin issue with self field declaration, #2743 by @uriyyo
* The colon at the end of the line "The fields which were supplied when user was initialised:" suggests that the code following it is related.
  Changed it to a period, #2733 by @krisaoe
* Renamed variable `schema` to `schema_` to avoid shadowing of global variable name, #2724 by @shahriyarr
* Add support for autocomplete in VS Code via `__dataclass_transform__`, #2721 by @tiangolo
* add missing type annotations in `BaseConfig` and handle `max_length = 0`, #2719 by @PrettyWood
* Change `orm_mode` checking to allow recursive ORM mode parsing with dicts, #2718 by @nuno-andre
* Add episode 313 of the *Talk Python To Me* podcast, where Michael Kennedy and Samuel Colvin discuss *pydantic*, to the docs, #2712 by @RatulMaharaj
* fix JSON schema generation when a field is of type `NamedTuple` and has a default value, #2707 by @PrettyWood
* `Enum` fields now properly support extra kwargs in schema generation, #2697 by @sammchardy
* **Breaking Change, see #3780**: Make serialization of referenced pydantic models possible, #2650 by @PrettyWood
* Add `uniqueItems` option to `ConstrainedList`, #2618 by @nuno-andre
* Try to evaluate forward refs automatically at model creation, #2588 by @uriyyo
* Switch docs preview and coverage display to use [smokeshow](https://smokeshow.helpmanual.io/), #2580 by @samuelcolvin
* Add `__version__` attribute to pydantic module, #2572 by @paxcodes
* Add `postgresql+asyncpg`, `postgresql+pg8000`, `postgresql+psycopg2`, `postgresql+psycopg2cffi`, `postgresql+py-postgresql`
  and `postgresql+pygresql` schemes for `PostgresDsn`, #2567 by @postgres-asyncpg
* Enable the Hypothesis plugin to generate a constrained decimal when the `decimal_places` argument is specified, #2524 by @cwe5590
* Allow `collections.abc.Callable` to be used as type in Python 3.9, #2519 by @daviskirk
* Documentation update how to custom compile pydantic when using pip install, small change in `setup.py` 
  to allow for custom CFLAGS when compiling, #2517 by @peterroelants
* remove side effect of `default_factory` to run it only once even if `Config.validate_all` is set, #2515 by @PrettyWood
* Add lookahead to ip regexes for `AnyUrl` hosts. This allows urls with DNS labels
  looking like IPs to validate as they are perfectly valid host names, #2512 by @sbv-csis
* Set `minItems` and `maxItems` in generated JSON schema for fixed-length tuples, #2497 by @PrettyWood
* Add `strict` argument to `conbytes`, #2489 by @koxudaxi
* Support user defined generic field types in generic models, #2465 by @daviskirk
* Add an example and a short explanation of subclassing `GetterDict` to docs, #2463 by @nuno-andre
* add `KafkaDsn` type, `HttpUrl` now has default port 80 for http and 443 for https, #2447 by @MihanixA
* Add `PastDate` and `FutureDate` types, #2425 by @Kludex
* Support generating schema for `Generic` fields with subtypes, #2375 by @maximberg
* fix(encoder): serialize `NameEmail` to str, #2341 by @alecgerona
* add `Config.smart_union` to prevent coercion in `Union` if possible, see 
 [the doc](https://docs.pydantic.dev/usage/model_config/#smart-union) for more information, #2092 by @PrettyWood
* Add ability to use `typing.Counter` as a model field type, #2060 by @uriyyo
* Add parameterised subclasses to `__bases__` when constructing new parameterised classes, so that `A <: B => A[int] <: B[int]`, #2007 by @diabolo-dan
* Create `FileUrl` type that allows URLs that conform to [RFC 8089](https://tools.ietf.org/html/rfc8089#section-2).
  Add `host_required` parameter, which is `True` by default (`AnyUrl` and subclasses), `False` in `RedisDsn`, `FileUrl`, #1983 by @vgerak
* add `confrozenset()`, analogous to `conset()` and `conlist()`, #1897 by @PrettyWood
* stop calling parent class `root_validator` if overridden, #1895 by @PrettyWood
* Add `repr` (defaults to `True`) parameter to `Field`, to hide it from the default representation of the `BaseModel`, #1831 by @fnep
* Accept empty query/fragment URL parts, #1807 by @xavier

## v1.8.2 (2021-05-11)

!!! warning
    A security vulnerability, level "moderate" is fixed in v1.8.2. Please upgrade **ASAP**.
    See security advisory [CVE-2021-29510](https://github.com/pydantic/pydantic/security/advisories/GHSA-5jqp-qgf6-3pvh)

* **Security fix:** Fix `date` and `datetime` parsing so passing either `'infinity'` or `float('inf')` 
  (or their negative values) does not cause an infinite loop, 
  see security advisory [CVE-2021-29510](https://github.com/pydantic/pydantic/security/advisories/GHSA-5jqp-qgf6-3pvh)
* fix schema generation with Enum by generating a valid name, #2575 by @PrettyWood
* fix JSON schema generation with a `Literal` of an enum member, #2536 by @PrettyWood
* Fix bug with configurations declarations that are passed as
  keyword arguments during class creation, #2532 by @uriyyo
* Allow passing `json_encoders` in class kwargs, #2521 by @layday
* support arbitrary types with custom `__eq__`, #2483 by @PrettyWood
* support `Annotated` in `validate_arguments` and in generic models with Python 3.9, #2483 by @PrettyWood

## v1.8.1 (2021-03-03)

Bug fixes for regressions and new features from `v1.8` 

* allow elements of `Config.field` to update elements of a `Field`, #2461 by @samuelcolvin
* fix validation with a `BaseModel` field and a custom root type, #2449 by @PrettyWood
* expose `Pattern` encoder to `fastapi`, #2444 by @PrettyWood
* enable the Hypothesis plugin to generate a constrained float when the `multiple_of` argument is specified, #2442 by @tobi-lipede-oodle
* Avoid `RecursionError` when using some types like `Enum` or `Literal` with generic models, #2436 by @PrettyWood
* do not overwrite declared `__hash__` in subclasses of a model, #2422 by @PrettyWood
* fix `mypy` complaints on `Path` and `UUID` related custom types, #2418 by @PrettyWood
* Support properly variable length tuples of compound types, #2416 by @PrettyWood

## v1.8 (2021-02-26)

Thank you to pydantic's sponsors:
@jorgecarleitao, @BCarley, @chdsbd, @tiangolo, @matin, @linusg, @kevinalh, @koxudaxi, @timdrijvers, @mkeen, @meadsteve, 
@ginomempin, @primer-io, @and-semakin, @tomthorogood, @AjitZK, @westonsteimel, @Mazyod, @christippett, @CarlosDomingues, 
@Kludex, @r-m-n
for their kind support.

### Highlights

* [Hypothesis plugin](https://docs.pydantic.dev/hypothesis_plugin/) for testing, #2097 by @Zac-HD
* support for [`NamedTuple` and `TypedDict`](https://docs.pydantic.dev/usage/types/#annotated-types), #2216 by @PrettyWood
* Support [`Annotated` hints on model fields](https://docs.pydantic.dev/usage/schema/#typingannotated-fields), #2147 by @JacobHayes
* [`frozen` parameter on `Config`](https://docs.pydantic.dev/usage/model_config/) to allow models to be hashed, #1880 by @rhuille

### Changes

* **Breaking Change**, remove old deprecation aliases from v1, #2415 by @samuelcolvin:
  * remove notes on migrating to v1 in docs
  * remove `Schema` which was replaced by `Field`
  * remove `Config.case_insensitive` which was replaced by `Config.case_sensitive` (default `False`)
  * remove `Config.allow_population_by_alias` which was replaced by `Config.allow_population_by_field_name`
  * remove `model.fields` which was replaced by `model.__fields__`
  * remove `model.to_string()` which was replaced by `str(model)`
  * remove `model.__values__` which was replaced by `model.__dict__`
* **Breaking Change:** always validate only first sublevel items with `each_item`.
  There were indeed some edge cases with some compound types where the validated items were the last sublevel ones, #1933 by @PrettyWood
* Update docs extensions to fix local syntax highlighting, #2400 by @daviskirk
* fix: allow `utils.lenient_issubclass` to handle `typing.GenericAlias` objects like `list[str]` in Python >= 3.9, #2399 by @daviskirk
* Improve field declaration for _pydantic_ `dataclass` by allowing the usage of _pydantic_ `Field` or `'metadata'` kwarg of `dataclasses.field`, #2384 by @PrettyWood
* Making `typing-extensions` a required dependency, #2368 by @samuelcolvin
* Make `resolve_annotations` more lenient, allowing for missing modules, #2363 by @samuelcolvin
* Allow configuring models through class kwargs, #2356 by @Bobronium
* Prevent `Mapping` subclasses from always being coerced to `dict`, #2325 by @ofek
* fix: allow `None` for type `Optional[conset / conlist]`, #2320 by @PrettyWood
* Support empty tuple type, #2318 by @PrettyWood
* fix: `python_requires` metadata to require >=3.6.1, #2306 by @hukkinj1
* Properly encode `Decimal` with, or without any decimal places, #2293 by @hultner
* fix: update `__fields_set__` in `BaseModel.copy(update=…)`, #2290 by @PrettyWood
* fix: keep order of fields with `BaseModel.construct()`, #2281 by @PrettyWood
* Support generating schema for Generic fields, #2262 by @maximberg
* Fix `validate_decorator` so `**kwargs` doesn't exclude values when the keyword
  has the same name as the `*args` or `**kwargs` names, #2251 by @cybojenix
* Prevent overriding positional arguments with keyword arguments in
  `validate_arguments`, as per behaviour with native functions, #2249 by @cybojenix
* add documentation for `con*` type functions, #2242 by @tayoogunbiyi
* Support custom root type (aka `__root__`) when using `parse_obj()` with nested models, #2238 by @PrettyWood
* Support custom root type (aka `__root__`) with `from_orm()`, #2237 by @PrettyWood
* ensure cythonized functions are left untouched when creating models, based on #1944 by @kollmats, #2228 by @samuelcolvin
* Resolve forward refs for stdlib dataclasses converted into _pydantic_ ones, #2220 by @PrettyWood
* Add support for `NamedTuple` and `TypedDict` types.
  Those two types are now handled and validated when used inside `BaseModel` or _pydantic_ `dataclass`.
  Two utils are also added `create_model_from_namedtuple` and `create_model_from_typeddict`, #2216 by @PrettyWood
* Do not ignore annotated fields when type is `Union[Type[...], ...]`, #2213 by @PrettyWood
* Raise a user-friendly `TypeError` when a `root_validator` does not return a `dict` (e.g. `None`), #2209 by @masalim2
* Add a `FrozenSet[str]` type annotation to the `allowed_schemes` argument on the `strict_url` field type, #2198 by @Midnighter
* add `allow_mutation` constraint to `Field`, #2195 by @sblack-usu
* Allow `Field` with a `default_factory` to be used as an argument to a function
  decorated with `validate_arguments`, #2176 by @thomascobb
* Allow non-existent secrets directory by only issuing a warning, #2175 by @davidolrik
* fix URL regex to parse fragment without query string, #2168 by @andrewmwhite
* fix: ensure to always return one of the values in `Literal` field type, #2166 by @PrettyWood
* Support `typing.Annotated` hints on model fields. A `Field` may now be set in the type hint with `Annotated[..., Field(...)`; all other annotations are ignored but still visible with `get_type_hints(..., include_extras=True)`, #2147 by @JacobHayes
* Added `StrictBytes` type as well as `strict=False` option to `ConstrainedBytes`, #2136 by @rlizzo
* added `Config.anystr_lower` and `to_lower` kwarg to `constr` and `conbytes`, #2134 by @tayoogunbiyi
* Support plain `typing.Tuple` type, #2132 by @PrettyWood
* Add a bound method `validate` to functions decorated with `validate_arguments`
  to validate parameters without actually calling the function, #2127 by @PrettyWood
* Add the ability to customize settings sources (add / disable / change priority order), #2107 by @kozlek
* Fix mypy complaints about most custom _pydantic_ types, #2098 by @PrettyWood
* Add a [Hypothesis](https://hypothesis.readthedocs.io/) plugin for easier [property-based testing](https://increment.com/testing/in-praise-of-property-based-testing/) with Pydantic's custom types - [usage details here](https://docs.pydantic.dev/hypothesis_plugin/), #2097 by @Zac-HD
* add validator for `None`, `NoneType` or `Literal[None]`, #2095 by @PrettyWood
* Handle properly fields of type `Callable` with a default value, #2094 by @PrettyWood
* Updated `create_model` return type annotation to return type which inherits from `__base__` argument, #2071 by @uriyyo
* Add merged `json_encoders` inheritance, #2064 by @art049
* allow overwriting `ClassVar`s in sub-models without having to re-annotate them, #2061 by @layday
* add default encoder for `Pattern` type, #2045 by @PrettyWood
* Add `NonNegativeInt`, `NonPositiveInt`, `NonNegativeFloat`, `NonPositiveFloat`, #1975 by @mdavis-xyz
* Use % for percentage in string format of colors, #1960 by @EdwardBetts
* Fixed issue causing `KeyError` to be raised when building schema from multiple `BaseModel` with the same names declared in separate classes, #1912 by @JSextonn
* Add `rediss` (Redis over SSL) protocol to `RedisDsn`
  Allow URLs without `user` part (e.g., `rediss://:pass@localhost`), #1911 by @TrDex
* Add a new `frozen` boolean parameter to `Config` (default: `False`).
  Setting `frozen=True` does everything that `allow_mutation=False` does, and also generates a `__hash__()` method for the model. This makes instances of the model potentially hashable if all the attributes are hashable, #1880 by @rhuille
* fix schema generation with multiple Enums having the same name, #1857 by @PrettyWood
* Added support for 13/19 digits VISA credit cards in `PaymentCardNumber` type, #1416 by @AlexanderSov
* fix: prevent `RecursionError` while using recursive `GenericModel`s, #1370 by @xppt
* use `enum` for `typing.Literal` in JSON schema, #1350 by @PrettyWood
* Fix: some recursive models did not require `update_forward_refs` and silently behaved incorrectly, #1201 by @PrettyWood
* Fix bug where generic models with fields where the typevar is nested in another type `a: List[T]` are considered to be concrete. This allows these models to be subclassed and composed as expected, #947 by @daviskirk
* Add `Config.copy_on_model_validation` flag. When set to `False`, _pydantic_ will keep models used as fields
  untouched on validation instead of reconstructing (copying) them, #265 by @PrettyWood

## v1.7.4 (2021-05-11)

* **Security fix:** Fix `date` and `datetime` parsing so passing either `'infinity'` or `float('inf')` 
  (or their negative values) does not cause an infinite loop,
  See security advisory [CVE-2021-29510](https://github.com/pydantic/pydantic/security/advisories/GHSA-5jqp-qgf6-3pvh)

## v1.7.3 (2020-11-30)

Thank you to pydantic's sponsors:
@timdrijvers, @BCarley, @chdsbd, @tiangolo, @matin, @linusg, @kevinalh, @jorgecarleitao, @koxudaxi, @primer-api,
@mkeen, @meadsteve for their kind support.

* fix: set right default value for required (optional) fields, #2142 by @PrettyWood
* fix: support `underscore_attrs_are_private` with generic models, #2138 by @PrettyWood
* fix: update all modified field values in `root_validator` when `validate_assignment` is on, #2116 by @PrettyWood
* Allow pickling of `pydantic.dataclasses.dataclass` dynamically created from a built-in `dataclasses.dataclass`, #2111 by @aimestereo
* Fix a regression where Enum fields would not propagate keyword arguments to the schema, #2109 by @bm424
* Ignore `__doc__` as private attribute when `Config.underscore_attrs_are_private` is set, #2090 by @PrettyWood

## v1.7.2 (2020-11-01)

* fix slow `GenericModel` concrete model creation, allow `GenericModel` concrete name reusing in module, #2078 by @Bobronium
* keep the order of the fields when `validate_assignment` is set, #2073 by @PrettyWood
* forward all the params of the stdlib `dataclass` when converted into _pydantic_ `dataclass`, #2065 by @PrettyWood

## v1.7.1 (2020-10-28)

Thank you to pydantic's sponsors:
@timdrijvers, @BCarley, @chdsbd, @tiangolo, @matin, @linusg, @kevinalh, @jorgecarleitao, @koxudaxi, @primer-api, @mkeen
for their kind support.

* fix annotation of `validate_arguments` when passing configuration as argument, #2055 by @layday
* Fix mypy assignment error when using `PrivateAttr`, #2048 by @aphedges
* fix `underscore_attrs_are_private` causing `TypeError` when overriding `__init__`, #2047 by @samuelcolvin
* Fixed regression introduced in v1.7 involving exception handling in field validators when `validate_assignment=True`, #2044 by @johnsabath
* fix: _pydantic_ `dataclass` can inherit from stdlib `dataclass`
  and `Config.arbitrary_types_allowed` is supported, #2042 by @PrettyWood

## v1.7 (2020-10-26)

Thank you to pydantic's sponsors:
@timdrijvers, @BCarley, @chdsbd, @tiangolo, @matin, @linusg, @kevinalh, @jorgecarleitao, @koxudaxi, @primer-api 
for their kind support.

### Highlights

* Python 3.9 support, thanks @PrettyWood
* [Private model attributes](https://docs.pydantic.dev/usage/models/#private-model-attributes), thanks @Bobronium
* ["secrets files" support in `BaseSettings`](https://docs.pydantic.dev/usage/settings/#secret-support), thanks @mdgilene
* [convert stdlib dataclasses to pydantic dataclasses and use stdlib dataclasses in models](https://docs.pydantic.dev/usage/dataclasses/#stdlib-dataclasses-and-pydantic-dataclasses), thanks @PrettyWood

### Changes

* **Breaking Change:** remove `__field_defaults__`, add `default_factory` support with `BaseModel.construct`.
  Use `.get_default()` method on fields in `__fields__` attribute instead, #1732 by @PrettyWood
* Rearrange CI to run linting as a separate job, split install recipes for different tasks, #2020 by @samuelcolvin
* Allows subclasses of generic models to make some, or all, of the superclass's type parameters concrete, while 
  also defining new type parameters in the subclass, #2005 by @choogeboom
* Call validator with the correct `values` parameter type in `BaseModel.__setattr__`,
  when `validate_assignment = True` in model config, #1999 by @me-ransh
* Force `fields.Undefined` to be a singleton object, fixing inherited generic model schemas, #1981 by @daviskirk
* Include tests in source distributions, #1976 by @sbraz
* Add ability to use `min_length/max_length` constraints with secret types, #1974 by @uriyyo
* Also check `root_validators` when `validate_assignment` is on, #1971 by @PrettyWood
* Fix const validators not running when custom validators are present, #1957 by @hmvp
* add `deque` to field types, #1935 by @wozniakty
* add basic support for Python 3.9, #1832 by @PrettyWood
* Fix typo in the anchor of exporting_models.md#modelcopy and incorrect description, #1821 by @KimMachineGun
* Added ability for `BaseSettings` to read "secret files", #1820 by @mdgilene
* add `parse_raw_as` utility function, #1812 by @PrettyWood
* Support home directory relative paths for `dotenv` files (e.g. `~/.env`), #1803 by @PrettyWood
* Clarify documentation for `parse_file` to show that the argument
  should be a file *path* not a file-like object, #1794 by @mdavis-xyz
* Fix false positive from mypy plugin when a class nested within a `BaseModel` is named `Model`, #1770 by @selimb
* add basic support of Pattern type in schema generation, #1767 by @PrettyWood
* Support custom title, description and default in schema of enums, #1748 by @PrettyWood
* Properly represent `Literal` Enums when `use_enum_values` is True, #1747 by @noelevans
* Allows timezone information to be added to strings to be formatted as time objects. Permitted formats are `Z` for UTC 
  or an offset for absolute positive or negative time shifts. Or the timezone data can be omitted, #1744 by @noelevans
* Add stub `__init__` with Python 3.6 signature for `ForwardRef`, #1738 by @sirtelemak
* Fix behaviour with forward refs and optional fields in nested models, #1736 by @PrettyWood
* add `Enum` and `IntEnum` as valid types for fields, #1735 by @PrettyWood
* Change default value of `__module__` argument of `create_model` from `None` to `'pydantic.main'`. 
  Set reference of created concrete model to it's module to allow pickling (not applied to models created in 
  functions), #1686 by @Bobronium
* Add private attributes support, #1679 by @Bobronium
* add `config` to `@validate_arguments`, #1663 by @samuelcolvin
* Allow descendant Settings models to override env variable names for the fields defined in parent Settings models with 
  `env` in their `Config`. Previously only `env_prefix` configuration option was applicable, #1561 by @ojomio
* Support `ref_template` when creating schema `$ref`s, #1479 by @kilo59
* Add a `__call__` stub to `PyObject` so that mypy will know that it is callable, #1352 by @brianmaissy
* `pydantic.dataclasses.dataclass` decorator now supports built-in `dataclasses.dataclass`.
  It is hence possible to convert an existing `dataclass` easily to add *pydantic* validation.
  Moreover nested dataclasses are also supported, #744 by @PrettyWood

## v1.6.2 (2021-05-11)

* **Security fix:** Fix `date` and `datetime` parsing so passing either `'infinity'` or `float('inf')` 
  (or their negative values) does not cause an infinite loop,
  See security advisory [CVE-2021-29510](https://github.com/pydantic/pydantic/security/advisories/GHSA-5jqp-qgf6-3pvh)

## v1.6.1 (2020-07-15)

* fix validation and parsing of nested models with `default_factory`, #1710 by @PrettyWood

## v1.6 (2020-07-11)

Thank you to pydantic's sponsors: @matin, @tiangolo, @chdsbd, @jorgecarleitao, and 1 anonymous sponsor for their kind support.

* Modify validators for `conlist` and `conset` to not have `always=True`, #1682 by @samuelcolvin
* add port check to `AnyUrl` (can't exceed 65536) ports are 16 insigned bits: `0 <= port <= 2**16-1` src: [rfc793 header format](https://tools.ietf.org/html/rfc793#section-3.1), #1654 by @flapili
* Document default `regex` anchoring semantics, #1648 by @yurikhan
* Use `chain.from_iterable` in class_validators.py. This is a faster and more idiomatic way of using `itertools.chain`.
  Instead of computing all the items in the iterable and storing them in memory, they are computed one-by-one and never
  stored as a huge list. This can save on both runtime and memory space, #1642 by @cool-RR
* Add `conset()`, analogous to `conlist()`, #1623 by @patrickkwang
* make *pydantic* errors (un)pickable, #1616 by @PrettyWood
* Allow custom encoding for `dotenv` files, #1615 by @PrettyWood
* Ensure `SchemaExtraCallable` is always defined to get type hints on BaseConfig, #1614 by @PrettyWood
* Update datetime parser to support negative timestamps, #1600 by @mlbiche
* Update mypy, remove `AnyType` alias for `Type[Any]`, #1598 by @samuelcolvin
* Adjust handling of root validators so that errors are aggregated from _all_ failing root validators, instead of reporting on only the first root validator to fail, #1586 by @beezee
* Make `__modify_schema__` on Enums apply to the enum schema rather than fields that use the enum, #1581 by @therefromhere
* Fix behavior of `__all__` key when used in conjunction with index keys in advanced include/exclude of fields that are sequences, #1579 by @xspirus
* Subclass validators do not run when referencing a `List` field defined in a parent class when `each_item=True`. Added an example to the docs illustrating this, #1566 by @samueldeklund
* change `schema.field_class_to_schema` to support `frozenset` in schema, #1557 by @wangpeibao
* Call `__modify_schema__` only for the field schema, #1552 by @PrettyWood
* Move the assignment of `field.validate_always` in `fields.py` so the `always` parameter of validators work on inheritance, #1545 by @dcHHH
* Added support for UUID instantiation through 16 byte strings such as `b'\x12\x34\x56\x78' * 4`. This was done to support `BINARY(16)` columns in sqlalchemy, #1541 by @shawnwall
* Add a test assertion that `default_factory` can return a singleton, #1523 by @therefromhere
* Add `NameEmail.__eq__` so duplicate `NameEmail` instances are evaluated as equal, #1514 by @stephen-bunn
* Add datamodel-code-generator link in pydantic document site, #1500 by @koxudaxi
* Added a "Discussion of Pydantic" section to the documentation, with a link to "Pydantic Introduction" video by Alexander Hultnér, #1499 by @hultner
* Avoid some side effects of `default_factory` by calling it only once
  if possible and by not setting a default value in the schema, #1491 by @PrettyWood
* Added docs about dumping dataclasses to JSON, #1487 by @mikegrima
* Make `BaseModel.__signature__` class-only, so getting `__signature__` from model instance will raise `AttributeError`, #1466 by @Bobronium
* include `'format': 'password'` in the schema for secret types, #1424 by @atheuz
* Modify schema constraints on `ConstrainedFloat` so that `exclusiveMinimum` and
  minimum are not included in the schema if they are equal to `-math.inf` and
  `exclusiveMaximum` and `maximum` are not included if they are equal to `math.inf`, #1417 by @vdwees
* Squash internal `__root__` dicts in `.dict()` (and, by extension, in `.json()`), #1414 by @patrickkwang
* Move `const` validator to post-validators so it validates the parsed value, #1410 by @selimb
* Fix model validation to handle nested literals, e.g. `Literal['foo', Literal['bar']]`, #1364 by @DBCerigo
* Remove `user_required = True` from `RedisDsn`, neither user nor password are required, #1275 by @samuelcolvin
* Remove extra `allOf` from schema for fields with `Union` and custom `Field`, #1209 by @mostaphaRoudsari
* Updates OpenAPI schema generation to output all enums as separate models.
  Instead of inlining the enum values in the model schema, models now use a `$ref`
  property to point to the enum definition, #1173 by @calvinwyoung

## v1.5.1 (2020-04-23)

* Signature generation with `extra: allow` never uses a field name, #1418 by @prettywood
* Avoid mutating `Field` default value, #1412 by @prettywood

## v1.5 (2020-04-18)

* Make includes/excludes arguments for `.dict()`, `._iter()`, ..., immutable, #1404 by @AlexECX
* Always use a field's real name with includes/excludes in `model._iter()`, regardless of `by_alias`, #1397 by @AlexECX
* Update constr regex example to include start and end lines, #1396 by @lmcnearney
* Confirm that shallow `model.copy()` does make a shallow copy of attributes, #1383 by @samuelcolvin
* Renaming `model_name` argument of `main.create_model()` to `__model_name` to allow using `model_name` as a field name, #1367 by @kittipatv
* Replace raising of exception to silent passing  for non-Var attributes in mypy plugin, #1345 by @b0g3r
* Remove `typing_extensions` dependency for Python 3.8, #1342 by @prettywood
* Make `SecretStr` and `SecretBytes` initialization idempotent, #1330 by @atheuz
* document making secret types dumpable using the json method, #1328 by @atheuz
* Move all testing and build to github actions, add windows and macos binaries, 
  thank you @StephenBrown2 for much help, #1326 by @samuelcolvin
* fix card number length check in `PaymentCardNumber`, `PaymentCardBrand` now inherits from `str`, #1317 by @samuelcolvin
* Have `BaseModel` inherit from `Representation` to make mypy happy when overriding `__str__`, #1310 by @FuegoFro
* Allow `None` as input to all optional list fields, #1307 by @prettywood
* Add `datetime` field to `default_factory` example, #1301 by @StephenBrown2
* Allow subclasses of known types to be encoded with superclass encoder, #1291 by @StephenBrown2
* Exclude exported fields from all elements of a list/tuple of submodels/dicts with `'__all__'`, #1286 by @masalim2
* Add pydantic.color.Color objects as available input for Color fields, #1258 by @leosussan
* In examples, type nullable fields as `Optional`, so that these are valid mypy annotations, #1248 by @kokes
* Make `pattern_validator()` accept pre-compiled `Pattern` objects. Fix `str_validator()` return type to `str`, #1237 by @adamgreg
* Document how to manage Generics and inheritance, #1229 by @esadruhn
* `update_forward_refs()` method of BaseModel now copies `__dict__` of class module instead of modyfying it, #1228 by @paul-ilyin
* Support instance methods and class methods with `@validate_arguments`, #1222 by @samuelcolvin
* Add `default_factory` argument to `Field` to create a dynamic default value by passing a zero-argument callable, #1210 by @prettywood
* add support for `NewType` of `List`, `Optional`, etc, #1207 by @Kazy
* fix mypy signature for `root_validator`, #1192 by @samuelcolvin
* Fixed parsing of nested 'custom root type' models, #1190 by @Shados
* Add `validate_arguments` function decorator which checks the arguments to a function matches type annotations, #1179 by @samuelcolvin
* Add `__signature__` to models, #1034 by @Bobronium
* Refactor `._iter()` method, 10x speed boost for `dict(model)`, #1017 by @Bobronium

## v1.4 (2020-01-24)

* **Breaking Change:** alias precedence logic changed so aliases on a field always take priority over
  an alias from `alias_generator` to avoid buggy/unexpected behaviour,
  see [here](https://docs.pydantic.dev/usage/model_config/#alias-precedence) for details, #1178 by @samuelcolvin
* Add support for unicode and punycode in TLDs, #1182 by @jamescurtin
* Fix `cls` argument in validators during assignment, #1172 by @samuelcolvin
* completing Luhn algorithm for `PaymentCardNumber`, #1166 by @cuencandres
* add support for generics that implement `__get_validators__` like a custom data type, #1159 by @tiangolo
* add support for infinite generators with `Iterable`, #1152 by @tiangolo
* fix `url_regex` to accept schemas with `+`, `-` and `.` after the first character, #1142 by @samuelcolvin
* move `version_info()` to `version.py`, suggest its use in issues, #1138 by @samuelcolvin
* Improve pydantic import time by roughly 50% by deferring some module loading and regex compilation, #1127 by @samuelcolvin
* Fix `EmailStr` and `NameEmail` to accept instances of themselves in cython, #1126 by @koxudaxi
* Pass model class to the `Config.schema_extra` callable, #1125 by @therefromhere
* Fix regex for username and password in URLs, #1115 by @samuelcolvin
* Add support for nested generic models, #1104 by @dmontagu
* add `__all__` to `__init__.py` to prevent "implicit reexport" errors from mypy, #1072 by @samuelcolvin
* Add support for using "dotenv" files with `BaseSettings`, #1011 by @acnebs

## v1.3 (2019-12-21)

* Change `schema` and `schema_model` to handle dataclasses by using their `__pydantic_model__` feature, #792 by @aviramha
* Added option for `root_validator` to be skipped if values validation fails using keyword `skip_on_failure=True`, #1049 by @aviramha
* Allow `Config.schema_extra` to be a callable so that the generated schema can be post-processed, #1054 by @selimb
* Update mypy to version 0.750, #1057 by @dmontagu
* Trick Cython into allowing str subclassing, #1061 by @skewty
* Prevent type attributes being added to schema unless the attribute `__schema_attributes__` is `True`, #1064 by @samuelcolvin
* Change `BaseModel.parse_file` to use `Config.json_loads`, #1067 by @kierandarcy
* Fix for optional `Json` fields, #1073 by @volker48
* Change the default number of threads used when compiling with cython to one,
  allow override via the `CYTHON_NTHREADS` environment variable, #1074 by @samuelcolvin
* Run FastAPI tests during Pydantic's CI tests, #1075 by @tiangolo
* My mypy strictness constraints, and associated tweaks to type annotations, #1077 by @samuelcolvin
* Add `__eq__` to SecretStr and SecretBytes to allow "value equals", #1079 by @sbv-trueenergy
* Fix schema generation for nested None case, #1088 by @lutostag
* Consistent checks for sequence like objects, #1090 by @samuelcolvin
* Fix `Config` inheritance on `BaseSettings` when used with `env_prefix`, #1091 by @samuelcolvin
* Fix for `__modify_schema__` when it conflicted with `field_class_to_schema*`, #1102 by @samuelcolvin
* docs: Fix explanation of case sensitive environment variable names when populating `BaseSettings` subclass attributes, #1105 by @tribals
* Rename django-rest-framework benchmark in documentation, #1119 by @frankie567

## v1.2 (2019-11-28)

* **Possible Breaking Change:** Add support for required `Optional` with `name: Optional[AnyType] = Field(...)`
  and refactor `ModelField` creation to preserve `required` parameter value, #1031 by @tiangolo;
  see [here](https://docs.pydantic.dev/usage/models/#required-optional-fields) for details
* Add benchmarks for `cattrs`, #513 by @sebastianmika
* Add `exclude_none` option to `dict()` and friends, #587 by @niknetniko
* Add benchmarks for `valideer`, #670 by @gsakkis
* Add `parse_obj_as` and `parse_file_as` functions for ad-hoc parsing of data into arbitrary pydantic-compatible types, #934 by @dmontagu
* Add `allow_reuse` argument to validators, thus allowing validator reuse, #940 by @dmontagu
* Add support for mapping types for custom root models, #958 by @dmontagu
* Mypy plugin support for dataclasses, #966 by @koxudaxi
* Add support for dataclasses default factory, #968 by @ahirner
* Add a `ByteSize` type for converting byte string (`1GB`) to plain bytes, #977 by @dgasmith
* Fix mypy complaint about `@root_validator(pre=True)`, #984 by @samuelcolvin
* Add manylinux binaries for Python 3.8 to pypi, also support manylinux2010, #994 by @samuelcolvin
* Adds ByteSize conversion to another unit, #995 by @dgasmith
* Fix `__str__` and `__repr__` inheritance for models, #1022 by @samuelcolvin
* add testimonials section to docs, #1025 by @sullivancolin
* Add support for `typing.Literal` for Python 3.8, #1026 by @dmontagu

## v1.1.1 (2019-11-20)

* Fix bug where use of complex fields on sub-models could cause fields to be incorrectly configured, #1015 by @samuelcolvin

## v1.1 (2019-11-07)

* Add a mypy plugin for type checking `BaseModel.__init__` and more, #722 by @dmontagu
* Change return type typehint for `GenericModel.__class_getitem__` to prevent PyCharm warnings, #936 by @dmontagu
* Fix usage of `Any` to allow `None`, also support `TypeVar` thus allowing use of un-parameterised collection types
  e.g. `Dict` and `List`, #962 by @samuelcolvin
* Set `FieldInfo` on subfields to fix schema generation for complex nested types, #965 by @samuelcolvin

## v1.0 (2019-10-23)

* **Breaking Change:** deprecate the `Model.fields` property, use `Model.__fields__` instead, #883 by @samuelcolvin
* **Breaking Change:** Change the precedence of aliases so child model aliases override parent aliases,
  including using `alias_generator`, #904 by @samuelcolvin
* **Breaking change:** Rename `skip_defaults` to `exclude_unset`, and add ability to exclude actual defaults, #915 by @dmontagu
* Add `**kwargs` to `pydantic.main.ModelMetaclass.__new__` so `__init_subclass__` can take custom parameters on extended
  `BaseModel` classes, #867 by @retnikt
* Fix field of a type that has a default value, #880 by @koxudaxi
* Use `FutureWarning` instead of `DeprecationWarning` when `alias` instead of `env` is used for settings models, #881 by @samuelcolvin
* Fix issue with `BaseSettings` inheritance and `alias` getting set to `None`, #882 by @samuelcolvin
* Modify `__repr__` and `__str__` methods to be consistent across all public classes, add `__pretty__` to support
  python-devtools, #884 by @samuelcolvin
* deprecation warning for `case_insensitive` on `BaseSettings` config, #885 by @samuelcolvin
* For `BaseSettings` merge environment variables and in-code values recursively, as long as they create a valid object
  when merged together, to allow splitting init arguments, #888 by @idmitrievsky
* change secret types example, #890 by @ashears
* Change the signature of `Model.construct()` to be more user-friendly, document `construct()` usage, #898 by @samuelcolvin
* Add example for the `construct()` method, #907 by @ashears
* Improve use of `Field` constraints on complex types, raise an error if constraints are not enforceable,
  also support tuples with an ellipsis `Tuple[X, ...]`, `Sequence` and `FrozenSet` in schema, #909 by @samuelcolvin
* update docs for bool missing valid value, #911 by @trim21
* Better `str`/`repr` logic for `ModelField`, #912 by @samuelcolvin
* Fix `ConstrainedList`, update schema generation to reflect `min_items` and `max_items` `Field()` arguments, #917 by @samuelcolvin
* Allow abstracts sets (eg. dict keys) in the `include` and `exclude` arguments of `dict()`, #921 by @samuelcolvin
* Fix JSON serialization errors on `ValidationError.json()` by using `pydantic_encoder`, #922 by @samuelcolvin
* Clarify usage of `remove_untouched`, improve error message for types with no validators, #926 by @retnikt

## v1.0b2 (2019-10-07)

* Mark `StrictBool` typecheck as `bool` to allow for default values without mypy errors, #690 by @dmontagu
* Transfer the documentation build from sphinx to mkdocs, re-write much of the documentation, #856 by @samuelcolvin
* Add support for custom naming schemes for `GenericModel` subclasses, #859 by @dmontagu
* Add `if TYPE_CHECKING:` to the excluded lines for test coverage, #874 by @dmontagu
* Rename `allow_population_by_alias` to `allow_population_by_field_name`, remove unnecessary warning about it, #875 by @samuelcolvin

## v1.0b1 (2019-10-01)

* **Breaking Change:** rename `Schema` to `Field`, make it a function to placate mypy, #577 by @samuelcolvin
* **Breaking Change:** modify parsing behavior for `bool`, #617 by @dmontagu
* **Breaking Change:** `get_validators` is no longer recognised, use `__get_validators__`.
  `Config.ignore_extra` and `Config.allow_extra` are no longer recognised, use `Config.extra`, #720 by @samuelcolvin
* **Breaking Change:** modify default config settings for `BaseSettings`; `case_insensitive` renamed to `case_sensitive`,
  default changed to `case_sensitive = False`, `env_prefix` default changed to `''` - e.g. no prefix, #721 by @dmontagu
* **Breaking change:** Implement `root_validator` and rename root errors from `__obj__` to `__root__`, #729 by @samuelcolvin
* **Breaking Change:** alter the behaviour of `dict(model)` so that sub-models are nolonger
  converted to dictionaries, #733 by @samuelcolvin
* **Breaking change:** Added `initvars` support to `post_init_post_parse`, #748 by @Raphael-C-Almeida
* **Breaking Change:** Make `BaseModel.json()` only serialize the `__root__` key for models with custom root, #752 by @dmontagu
* **Breaking Change:** complete rewrite of `URL` parsing logic, #755 by @samuelcolvin
* **Breaking Change:** preserve superclass annotations for field-determination when not provided in subclass, #757 by @dmontagu
* **Breaking Change:** `BaseSettings` now uses the special `env` settings to define which environment variables to
  read, not aliases, #847 by @samuelcolvin
* add support for `assert` statements inside validators, #653 by @abdusco
* Update documentation to specify the use of `pydantic.dataclasses.dataclass` and subclassing `pydantic.BaseModel`, #710 by @maddosaurus
* Allow custom JSON decoding and encoding via `json_loads` and `json_dumps` `Config` properties, #714 by @samuelcolvin
* make all annotated fields occur in the order declared, #715 by @dmontagu
* use pytest to test `mypy` integration, #735 by @dmontagu
* add `__repr__` method to `ErrorWrapper`, #738 by @samuelcolvin
* Added support for `FrozenSet` members in dataclasses, and a better error when attempting to use types from the `typing` module that are not supported by Pydantic, #745 by @djpetti
* add documentation for Pycharm Plugin, #750 by @koxudaxi
* fix broken examples in the docs, #753 by @dmontagu
* moving typing related objects into `pydantic.typing`, #761 by @samuelcolvin
* Minor performance improvements to `ErrorWrapper`, `ValidationError` and datetime parsing, #763 by @samuelcolvin
* Improvements to `datetime`/`date`/`time`/`timedelta` types: more descriptive errors,
  change errors to `value_error` not `type_error`, support bytes, #766 by @samuelcolvin
* fix error messages for `Literal` types with multiple allowed values, #770 by @dmontagu
* Improved auto-generated `title` field in JSON schema by converting underscore to space, #772 by @skewty
* support `mypy --no-implicit-reexport` for dataclasses, also respect `--no-implicit-reexport` in pydantic itself, #783 by @samuelcolvin
* add the `PaymentCardNumber` type, #790 by @matin
* Fix const validations for lists, #794 by @hmvp
* Set `additionalProperties` to false in schema for models with extra fields disallowed, #796 by @Code0x58
* `EmailStr` validation method now returns local part case-sensitive per RFC 5321, #798 by @henriklindgren
* Added ability to validate strictness to `ConstrainedFloat`, `ConstrainedInt` and `ConstrainedStr` and added
  `StrictFloat` and `StrictInt` classes, #799 by @DerRidda
* Improve handling of `None` and `Optional`, replace `whole` with `each_item` (inverse meaning, default `False`)
  on validators, #803 by @samuelcolvin
* add support for `Type[T]` type hints, #807 by @timonbimon
* Performance improvements from removing `change_exceptions`, change how pydantic error are constructed, #819 by @samuelcolvin
* Fix the error message arising when a `BaseModel`-type model field causes a `ValidationError` during parsing, #820 by @dmontagu
* allow `getter_dict` on `Config`, modify `GetterDict` to be more like a `Mapping` object and thus easier to work with, #821 by @samuelcolvin
* Only check `TypeVar` param on base `GenericModel` class, #842 by @zpencerq
* rename `Model._schema_cache` -> `Model.__schema_cache__`, `Model._json_encoder` -> `Model.__json_encoder__`,
  `Model._custom_root_type` -> `Model.__custom_root_type__`, #851 by @samuelcolvin

## v0.32.2 (2019-08-17)

(Docs are available [here](https://5d584fcca7c9b70007d1c997--pydantic-docs.netlify.com))

* fix `__post_init__` usage with dataclass inheritance, fix #739 by @samuelcolvin
* fix required fields validation on GenericModels classes, #742 by @amitbl
* fix defining custom `Schema` on `GenericModel` fields, #754 by @amitbl

## v0.32.1 (2019-08-08)

* do not validate extra fields when `validate_assignment` is on, #724 by @YaraslauZhylko

## v0.32 (2019-08-06)

* add model name to `ValidationError` error message, #676 by @dmontagu
* **breaking change**: remove `__getattr__` and rename `__values__` to `__dict__` on `BaseModel`,
  deprecation warning on use `__values__` attr, attributes access speed increased up to 14 times, #712 by @Bobronium
* support `ForwardRef` (without self-referencing annotations) in Python 3.6, #706 by @koxudaxi
* implement `schema_extra` in `Config` sub-class, #663 by @tiangolo

## v0.31.1 (2019-07-31)

* fix json generation for `EnumError`, #697 by @dmontagu
* update numerous dependencies

## v0.31 (2019-07-24)

* better support for floating point `multiple_of` values, #652 by @justindujardin
* fix schema generation for `NewType` and `Literal`, #649 by @dmontagu
* fix `alias_generator` and field config conflict, #645 by @gmetzker and #658 by @Bobronium
* more detailed message for `EnumError`, #673 by @dmontagu
* add advanced exclude support for `dict`, `json` and `copy`, #648 by @Bobronium
* fix bug in `GenericModel` for models with concrete parameterized fields, #672 by @dmontagu
* add documentation for `Literal` type, #651 by @dmontagu
* add `Config.keep_untouched` for custom descriptors support, #679 by @Bobronium
* use `inspect.cleandoc` internally to get model description, #657 by @tiangolo
* add `Color` to schema generation, by @euri10
* add documentation for Literal type, #651 by @dmontagu

## v0.30.1 (2019-07-15)

* fix so nested classes which inherit and change `__init__` are correctly processed while still allowing `self` as a
  parameter, #644 by @lnaden and @dgasmith

## v0.30 (2019-07-07)

* enforce single quotes in code, #612 by @samuelcolvin
* fix infinite recursion with dataclass inheritance and `__post_init__`, #606 by @Hanaasagi
* fix default values for `GenericModel`, #610 by @dmontagu
* clarify that self-referencing models require Python 3.7+, #616 by @vlcinsky
* fix truncate for types, #611 by @dmontagu
* add `alias_generator` support, #622 by @Bobronium
* fix unparameterized generic type schema generation, #625 by @dmontagu
* fix schema generation with multiple/circular references to the same model, #621 by @tiangolo and @wongpat
* support custom root types, #628 by @koxudaxi
* support `self` as a field name in `parse_obj`, #632 by @samuelcolvin

## v0.29 (2019-06-19)

* support dataclasses.InitVar, #592 by @pfrederiks
* Updated documentation to elucidate the usage of `Union` when defining multiple types under an attribute's
  annotation and showcase how the type-order can affect marshalling of provided values, #594 by @somada141
* add `conlist` type, #583 by @hmvp
* add support for generics, #595 by @dmontagu

## v0.28 (2019-06-06)

* fix support for JSON Schema generation when using models with circular references in Python 3.7, #572 by @tiangolo
* support `__post_init_post_parse__` on dataclasses, #567 by @sevaho
* allow dumping dataclasses to JSON, #575 by @samuelcolvin and @DanielOberg
* ORM mode, #562 by @samuelcolvin
* fix `pydantic.compiled` on ipython, #573 by @dmontagu and @samuelcolvin
* add `StrictBool` type, #579 by @cazgp

## v0.27 (2019-05-30)

* **breaking change**  `_pydantic_post_init` to execute dataclass' original `__post_init__` before
  validation, #560 by @HeavenVolkoff
* fix handling of generic types without specified parameters, #550 by @dmontagu
* **breaking change** (maybe): this is the first release compiled with **cython**, see the docs and please
  submit an issue if you run into problems

## v0.27.0a1 (2019-05-26)

* fix JSON Schema for `list`, `tuple`, and `set`, #540 by @tiangolo
* compiling with cython, `manylinux` binaries, some other performance improvements, #548 by @samuelcolvin

## v0.26 (2019-05-22)

* fix to schema generation for `IPvAnyAddress`, `IPvAnyInterface`, `IPvAnyNetwork` #498 by @pilosus
* fix variable length tuples support, #495 by @pilosus
* fix return type hint for `create_model`, #526 by @dmontagu
* **Breaking Change:** fix `.dict(skip_keys=True)` skipping values set via alias (this involves changing
  `validate_model()` to always returns `Tuple[Dict[str, Any], Set[str], Optional[ValidationError]]`), #517 by @sommd
* fix to schema generation for `IPv4Address`, `IPv6Address`, `IPv4Interface`,
  `IPv6Interface`, `IPv4Network`, `IPv6Network` #532 by @euri10
* add `Color` type, #504 by @pilosus and @samuelcolvin

## v0.25 (2019-05-05)

* Improve documentation on self-referencing models and annotations, #487 by @theenglishway
* fix `.dict()` with extra keys, #490 by @JaewonKim
* support `const` keyword in `Schema`, #434 by @Sean1708

## v0.24 (2019-04-23)

* fix handling `ForwardRef` in sub-types, like `Union`, #464 by @tiangolo
* fix secret serialization, #465 by @atheuz
* Support custom validators for dataclasses, #454 by @primal100
* fix `parse_obj` to cope with dict-like objects, #472 by @samuelcolvin
* fix to schema generation in nested dataclass-based models, #474 by @NoAnyLove
* fix `json` for `Path`, `FilePath`, and `DirectoryPath` objects, #473 by @mikegoodspeed

## v0.23 (2019-04-04)

* improve documentation for contributing section, #441 by @pilosus
* improve README.rst to include essential information about the package, #446 by @pilosus
* `IntEnum` support, #444 by @potykion
* fix PyObject callable value, #409 by @pilosus
* fix `black` deprecation warnings after update, #451 by @pilosus
* fix `ForwardRef` collection bug, #450 by @tigerwings
* Support specialized `ClassVars`, #455 by @tyrylu
* fix JSON serialization for `ipaddress` types, #333 by @pilosus
* add `SecretStr` and `SecretBytes` types, #452 by @atheuz

## v0.22 (2019-03-29)

* add `IPv{4,6,Any}Network` and `IPv{4,6,Any}Interface` types from `ipaddress` stdlib, #333 by @pilosus
* add docs for `datetime` types, #386 by @pilosus
* fix to schema generation in dataclass-based models, #408 by @pilosus
* fix path in nested models, #437 by @kataev
* add `Sequence` support, #304 by @pilosus

## v0.21.0 (2019-03-15)

* fix typo in `NoneIsNotAllowedError` message, #414 by @YaraslauZhylko
* add `IPvAnyAddress`, `IPv4Address` and `IPv6Address` types, #333 by @pilosus

## v0.20.1 (2019-02-26)

* fix type hints of `parse_obj` and similar methods, #405 by @erosennin
* fix submodel validation, #403 by @samuelcolvin
* correct type hints for `ValidationError.json`, #406 by @layday

## v0.20.0 (2019-02-18)

* fix tests for Python 3.8, #396 by @samuelcolvin
* Adds fields to the `dir` method for autocompletion in interactive sessions, #398 by @dgasmith
* support `ForwardRef` (and therefore `from __future__ import annotations`) with dataclasses, #397 by @samuelcolvin

## v0.20.0a1 (2019-02-13)

* **breaking change** (maybe): more sophisticated argument parsing for validators, any subset of
  `values`, `config` and `field` is now permitted, eg. `(cls, value, field)`,
  however the variadic key word argument ("`**kwargs`") **must** be called `kwargs`, #388 by @samuelcolvin
* **breaking change**: Adds `skip_defaults` argument to `BaseModel.dict()` to allow skipping of fields that
  were not explicitly set, signature of `Model.construct()` changed, #389 by @dgasmith
* add `py.typed` marker file for PEP-561 support, #391 by @je-l
* Fix `extra` behaviour for multiple inheritance/mix-ins, #394 by @YaraslauZhylko

## v0.19.0 (2019-02-04)

* Support `Callable` type hint, fix #279 by @proofit404
* Fix schema for fields with `validator` decorator, fix #375 by @tiangolo
* Add `multiple_of` constraint to `ConstrainedDecimal`, `ConstrainedFloat`, `ConstrainedInt`
  and their related types `condecimal`, `confloat`, and `conint` #371, thanks @StephenBrown2
* Deprecated `ignore_extra` and `allow_extra` Config fields in favor of `extra`, #352 by @liiight
* Add type annotations to all functions, test fully with mypy, #373 by @samuelcolvin
* fix for 'missing' error with `validate_all` or `validate_always`, #381 by @samuelcolvin
* Change the second/millisecond watershed for date/datetime parsing to `2e10`, #385 by @samuelcolvin

## v0.18.2 (2019-01-22)

* Fix to schema generation with `Optional` fields, fix #361 by @samuelcolvin

## v0.18.1 (2019-01-17)

* add `ConstrainedBytes` and `conbytes` types, #315 @Gr1N
* adding `MANIFEST.in` to include license in package `.tar.gz`, #358 by @samuelcolvin

## v0.18.0 (2019-01-13)

* **breaking change**: don't call validators on keys of dictionaries, #254 by @samuelcolvin
* Fix validators with `always=True` when the default is `None` or the type is optional, also prevent
  `whole` validators being called for sub-fields, fix #132 by @samuelcolvin
* improve documentation for settings priority and allow it to be easily changed, #343 by @samuelcolvin
* fix `ignore_extra=False` and `allow_population_by_alias=True`, fix #257 by @samuelcolvin
* **breaking change**: Set `BaseConfig` attributes `min_anystr_length` and `max_anystr_length` to
  `None` by default, fix #349 in #350 by @tiangolo
* add support for postponed annotations, #348 by @samuelcolvin

## v0.17.0 (2018-12-27)

* fix schema for `timedelta` as number, #325 by @tiangolo
* prevent validators being called repeatedly after inheritance, #327 by @samuelcolvin
* prevent duplicate validator check in ipython, fix #312 by @samuelcolvin
* add "Using Pydantic" section to docs, #323 by @tiangolo & #326 by @samuelcolvin
* fix schema generation for fields annotated as `: dict`, `: list`,
  `: tuple` and `: set`, #330 & #335 by @nkonin
* add support for constrained strings as dict keys in schema, #332 by @tiangolo
* support for passing Config class in dataclasses decorator, #276 by @jarekkar
  (**breaking change**: this supersedes the `validate_assignment` argument with `config`)
* support for nested dataclasses, #334 by @samuelcolvin
* better errors when getting an `ImportError` with `PyObject`, #309 by @samuelcolvin
* rename `get_validators` to `__get_validators__`, deprecation warning on use of old name, #338 by @samuelcolvin
* support `ClassVar` by excluding such attributes from fields, #184 by @samuelcolvin

## v0.16.1 (2018-12-10)

* fix `create_model` to correctly use the passed `__config__`, #320 by @hugoduncan

## v0.16.0 (2018-12-03)

* **breaking change**: refactor schema generation to be compatible with JSON Schema and OpenAPI specs, #308 by @tiangolo
* add `schema` to `schema` module to generate top-level schemas from base models, #308 by @tiangolo
* add additional fields to `Schema` class to declare validation for `str` and numeric values, #311 by @tiangolo
* rename `_schema` to `schema` on fields, #318 by @samuelcolvin
* add `case_insensitive` option to `BaseSettings` `Config`, #277 by @jasonkuhrt

## v0.15.0 (2018-11-18)

* move codebase to use black, #287 by @samuelcolvin
* fix alias use in settings, #286 by @jasonkuhrt and @samuelcolvin
* fix datetime parsing in `parse_date`, #298 by @samuelcolvin
* allow dataclass inheritance, fix #293 by @samuelcolvin
* fix `PyObject = None`, fix #305 by @samuelcolvin
* allow `Pattern` type, fix #303 by @samuelcolvin

## v0.14.0 (2018-10-02)

* dataclasses decorator, #269 by @Gaunt and @samuelcolvin

## v0.13.1 (2018-09-21)

* fix issue where int_validator doesn't cast a `bool` to an `int` #264 by @nphyatt
* add deep copy support for `BaseModel.copy()` #249, @gangefors

## v0.13.0 (2018-08-25)

* raise an exception if a field's name shadows an existing `BaseModel` attribute #242
* add `UrlStr` and `urlstr` types #236
* timedelta json encoding ISO8601 and total seconds, custom json encoders #247, by @cfkanesan and @samuelcolvin
* allow `timedelta` objects as values for properties of type `timedelta` (matches `datetime` etc. behavior) #247

## v0.12.1 (2018-07-31)

* fix schema generation for fields defined using `typing.Any` #237

## v0.12.0 (2018-07-31)

* add `by_alias` argument in `.dict()` and `.json()` model methods #205
* add Json type support #214
* support tuples #227
* major improvements and changes to schema #213

## v0.11.2 (2018-07-05)

* add `NewType` support #115
* fix `list`, `set` & `tuple` validation #225
* separate out `validate_model` method, allow errors to be returned along with valid values #221

## v0.11.1 (2018-07-02)

* support Python 3.7 #216, thanks @layday
* Allow arbitrary types in model #209, thanks @oldPadavan

## v0.11.0 (2018-06-28)

* make `list`, `tuple` and `set` types stricter #86
* **breaking change**: remove msgpack parsing #201
* add `FilePath` and `DirectoryPath` types #10
* model schema generation #190
* JSON serialisation of models and schemas #133

## v0.10.0 (2018-06-11)

* add `Config.allow_population_by_alias` #160, thanks @bendemaree
* **breaking change**: new errors format #179, thanks @Gr1N
* **breaking change**: removed `Config.min_number_size` and `Config.max_number_size` #183, thanks @Gr1N
* **breaking change**: correct behaviour of `lt` and `gt` arguments to `conint` etc. #188
  for the old behaviour use `le` and `ge` #194, thanks @jaheba
* added error context and ability to redefine error message templates using `Config.error_msg_templates` #183,
  thanks @Gr1N
* fix typo in validator exception #150
* copy defaults to model values, so different models don't share objects #154

## v0.9.1 (2018-05-10)

* allow custom `get_field_config` on config classes #159
* add `UUID1`, `UUID3`, `UUID4` and `UUID5` types #167, thanks @Gr1N
* modify some inconsistent docstrings and annotations #173, thanks @YannLuo
* fix type annotations for exotic types #171, thanks @Gr1N
* re-use type validators in exotic types #171
* scheduled monthly requirements updates #168
* add `Decimal`, `ConstrainedDecimal` and `condecimal` types #170, thanks @Gr1N

## v0.9.0 (2018-04-28)

* tweak email-validator import error message #145
* fix parse error of `parse_date()` and `parse_datetime()` when input is 0 #144, thanks @YannLuo
* add `Config.anystr_strip_whitespace` and `strip_whitespace` kwarg to `constr`,
  by default values is `False` #163, thanks @Gr1N
* add `ConstrainedFloat`, `confloat`, `PositiveFloat` and `NegativeFloat` types #166, thanks @Gr1N

## v0.8.0 (2018-03-25)

* fix type annotation for `inherit_config` #139
* **breaking change**: check for invalid field names in validators #140
* validate attributes of parent models #141
* **breaking change**: email validation now uses
  [email-validator](https://github.com/JoshData/python-email-validator) #142

## v0.7.1 (2018-02-07)

* fix bug with `create_model` modifying the base class

## v0.7.0 (2018-02-06)

* added compatibility with abstract base classes (ABCs) #123
* add `create_model` method #113 #125
* **breaking change**: rename `.config` to `.__config__` on a model
* **breaking change**: remove deprecated `.values()` on a model, use `.dict()` instead
* remove use of `OrderedDict` and use simple dict #126
* add `Config.use_enum_values` #127
* add wildcard validators of the form `@validate('*')` #128

## v0.6.4 (2018-02-01)

* allow Python date and times objects #122

## v0.6.3 (2017-11-26)

* fix direct install without `README.rst` present

## v0.6.2 (2017-11-13)

* errors for invalid validator use
* safer check for complex models in `Settings`

## v0.6.1 (2017-11-08)

* prevent duplicate validators, #101
* add `always` kwarg to validators, #102

## v0.6.0 (2017-11-07)

* assignment validation #94, thanks petroswork!
* JSON in environment variables for complex types, #96
* add `validator` decorators for complex validation, #97
* depreciate `values(...)` and replace with `.dict(...)`, #99

## v0.5.0 (2017-10-23)

* add `UUID` validation #89
* remove `index` and `track` from error object (json) if they're null #90
* improve the error text when a list is provided rather than a dict #90
* add benchmarks table to docs #91

## v0.4.0 (2017-07-08)

* show length in string validation error
* fix aliases in config during inheritance #55
* simplify error display
* use unicode ellipsis in `truncate`
* add `parse_obj`, `parse_raw` and `parse_file` helper functions #58
* switch annotation only fields to come first in fields list not last

## v0.3.0 (2017-06-21)

* immutable models via `config.allow_mutation = False`, associated cleanup and performance improvement #44
* immutable helper methods `construct()` and `copy()` #53
* allow pickling of models #53
* `setattr` is removed as `__setattr__` is now intelligent #44
* `raise_exception` removed, Models now always raise exceptions #44
* instance method validators removed
* django-restful-framework benchmarks added #47
* fix inheritance bug #49
* make str type stricter so list, dict etc are not coerced to strings. #52
* add `StrictStr` which only always strings as input #52

## v0.2.1 (2017-06-07)

* pypi and travis together messed up the deploy of `v0.2` this should fix it

## v0.2.0 (2017-06-07)

* **breaking change**: `values()` on a model is now a method not a property,
  takes `include` and `exclude` arguments
* allow annotation only fields to support mypy
* add pretty `to_string(pretty=True)` method for models

## v0.1.0 (2017-06-03)

* add docs
* add history
