## v1.8.2 (2021-05-11)

!!! warning
    A security vulnerability, level "moderate" is fixed in v1.8.2. Please upgrade **ASAP**.
    See security advisory [CVE-2021-29510](https://github.com/samuelcolvin/pydantic/security/advisories/GHSA-5jqp-qgf6-3pvh)

* **Security fix:** Fix `date` and `datetime` parsing so passing either `'infinity'` or `float('inf')` 
  (or their negative values) does not cause an infinite loop, 
  see security advisory [CVE-2021-29510](https://github.com/samuelcolvin/pydantic/security/advisories/GHSA-5jqp-qgf6-3pvh)
* fix schema generation with Enum by generating a valid name, #2575 by @PrettyWood
* fix JSON schema generation with a `Literal` of an enum member, #2536 by @PrettyWood
* Fix bug with configurations declarations that are passed as
  keyword arguments during class creation, #2532 by @uriyyo
* Allow passing `json_encoders` in class kwargs, #2521 by @layday
* support arbitrary types with custom `__eq__`, #2483 by @PrettyWood
* support `Annotated` in `validate_arguments` and in generic models with python 3.9, #2483 by @PrettyWood
* Support user defined generic field types in generic models, #2465 by @daviskirk

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

* [Hypothesis plugin](https://pydantic-docs.helpmanual.io/hypothesis_plugin/) for testing, #2097 by @Zac-HD
* support for [`NamedTuple` and `TypedDict`](https://pydantic-docs.helpmanual.io/usage/types/#annotated-types), #2216 by @PrettyWood
* Support [`Annotated` hints on model fields](https://pydantic-docs.helpmanual.io/usage/schema/#typingannotated-fields), #2147 by @JacobHayes
* [`frozen` parameter on `Config`](https://pydantic-docs.helpmanual.io/usage/model_config/) to allow models to be hashed, #1880 by @rhuille

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
* fix: allow `utils.lenient_issubclass` to handle `typing.GenericAlias` objects like `list[str]` in python >= 3.9, #2399 by @daviskirk
* Improve field declaration for _pydantic_ `dataclass` by allowing the usage of _pydantic_ `Field` or `'metadata'` kwarg of `dataclasses.field`, #2384 by @PrettyWood
* Making `typing-extensions` a required dependency, #2368 by @samuelcolvin
* Make `resolve_annotations` more lenient, allowing for missing modules, #2363 by @samuelcolvin
* Allow configuring models through class kwargs, #2356 by @MrMrRobat
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
* Add a [Hypothesis](https://hypothesis.readthedocs.io/) plugin for easier [property-based testing](https://increment.com/testing/in-praise-of-property-based-testing/) with Pydantic's custom types - [usage details here](https://pydantic-docs.helpmanual.io/hypothesis_plugin/), #2097 by @Zac-HD
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
  See security advisory [CVE-2021-29510](https://github.com/samuelcolvin/pydantic/security/advisories/GHSA-5jqp-qgf6-3pvh)

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

* fix slow `GenericModel` concrete model creation, allow `GenericModel` concrete name reusing in module, #2078 by @MrMrRobat
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

* python 3.9 support, thanks @PrettyWood
* [Private model attributes](https://pydantic-docs.helpmanual.io/usage/models/#private-model-attributes), thanks @MrMrRobat
* ["secrets files" support in `BaseSettings`](https://pydantic-docs.helpmanual.io/usage/settings/#secret-support), thanks @mdgilene
* [convert stdlib dataclasses to pydantic dataclasses and use stdlib dataclasses in models](https://pydantic-docs.helpmanual.io/usage/dataclasses/#stdlib-dataclasses-and-pydantic-dataclasses), thanks @PrettyWood

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
* add basic support for python 3.9, #1832 by @PrettyWood
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
* Add stub `__init__` with python 3.6 signature for `ForwardRef`, #1738 by @sirtelemak
* Fix behaviour with forward refs and optional fields in nested models, #1736 by @PrettyWood
* add `Enum` and `IntEnum` as valid types for fields, #1735 by @PrettyWood
* Change default value of `__module__` argument of `create_model` from `None` to `'pydantic.main'`. 
  Set reference of created concrete model to it's module to allow pickling (not applied to models created in 
  functions), #1686 by @MrMrRobat
* Add private attributes support, #1679 by @MrMrRobat
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
  See security advisory [CVE-2021-29510](https://github.com/samuelcolvin/pydantic/security/advisories/GHSA-5jqp-qgf6-3pvh)

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
* Make `BaseModel.__signature__` class-only, so getting `__signature__` from model instance will raise `AttributeError`, #1466 by @MrMrRobat
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
* Remove `typing_extensions` dependency for python 3.8, #1342 by @prettywood
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
* Add `__signature__` to models, #1034 by @MrMrRobat
* Refactor `._iter()` method, 10x speed boost for `dict(model)`, #1017 by @MrMrRobat

## v1.4 (2020-01-24)

* **Breaking Change:** alias precedence logic changed so aliases on a field always take priority over
  an alias from `alias_generator` to avoid buggy/unexpected behaviour,
  see [here](https://pydantic-docs.helpmanual.io/usage/model_config/#alias-precedence) for details, #1178 by @samuelcolvin
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
  see [here](https://pydantic-docs.helpmanual.io/usage/models/#required-optional-fields) for details
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
* Add manylinux binaries for python 3.8 to pypi, also support manylinux2010, #994 by @samuelcolvin
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
  deprecation warning on use `__values__` attr, attributes access speed increased up to 14 times, #712 by @MrMrRobat
* support `ForwardRef` (without self-referencing annotations) in Python 3.6, #706 by @koxudaxi
* implement `schema_extra` in `Config` sub-class, #663 by @tiangolo

## v0.31.1 (2019-07-31)

* fix json generation for `EnumError`, #697 by @dmontagu
* update numerous dependencies

## v0.31 (2019-07-24)

* better support for floating point `multiple_of` values, #652 by @justindujardin
* fix schema generation for `NewType` and `Literal`, #649 by @dmontagu
* fix `alias_generator` and field config conflict, #645 by @gmetzker and #658 by @MrMrRobat
* more detailed message for `EnumError`, #673 by @dmontagu
* add advanced exclude support for `dict`, `json` and `copy`, #648 by @MrMrRobat
* fix bug in `GenericModel` for models with concrete parameterized fields, #672 by @dmontagu
* add documentation for `Literal` type, #651 by @dmontagu
* add `Config.keep_untouched` for custom descriptors support, #679 by @MrMrRobat
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
* clarify that self-referencing models require python 3.7+, #616 by @vlcinsky
* fix truncate for types, #611 by @dmontagu
* add `alias_generator` support, #622 by @MrMrRobat
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

* fix tests for python 3.8, #396 by @samuelcolvin
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

* allow python date and times objects #122

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
