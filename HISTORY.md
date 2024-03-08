## v2.6.4 (2024-03-08)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.6.4)

### What's Changed

#### Fixes

* Fix usage of `AliasGenerator` with `computed_field` decorator by @sydney-runkle in [#8806](https://github.com/pydantic/pydantic/pull/8806)
* Fix nested discriminated union schema gen, pt 2 by @sydney-runkle in [#8932](https://github.com/pydantic/pydantic/pull/8932)
* Fix bug with no_strict_optional=True caused by API deferral by @dmontagu in [#8826](https://github.com/pydantic/pydantic/pull/8826)


## v2.6.3 (2024-02-27)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.6.3)

### What's Changed

#### Packaging

* Update `pydantic-settings` version in the docs by @hramezani in [#8906](https://github.com/pydantic/pydantic/pull/8906)

#### Fixes

* Fix discriminated union schema gen bug by @sydney-runkle in [#8904](https://github.com/pydantic/pydantic/pull/8904)


## v2.6.2 (2024-02-23)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.6.2)

### What's Changed

#### Packaging

* Upgrade to `pydantic-core` 2.16.3 by @sydney-runkle in [#8879](https://github.com/pydantic/pydantic/pull/8879)

#### Fixes

* 'YYYY-MM-DD' date string coerced to datetime shouldn't infer timezone by @sydney-runkle in [pydantic/pydantic-core#1193](https://github.com/pydantic/pydantic-core/pull/1193)


## v2.6.1 (2024-02-05)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.6.1)

### What's Changed

#### Packaging

* Upgrade to `pydantic-core` 2.16.2 by @sydney-runkle in [#8717](https://github.com/pydantic/pydantic/pull/8717)

#### Fixes

* Fix bug with `mypy` plugin and `no_strict_optional = True` by @dmontagu in [#8666](https://github.com/pydantic/pydantic/pull/8666)
* Fix `ByteSize` error `type` change by @sydney-runkle in [#8681](https://github.com/pydantic/pydantic/pull/8681)
* Fix inheriting `Field` annotations in dataclasses by @sydney-runkle in [#8679](https://github.com/pydantic/pydantic/pull/8679)
* Fix regression in core schema generation for indirect definition references by @dmontagu in [#8702](https://github.com/pydantic/pydantic/pull/8702)
* Fix unsupported types bug with `PlainValidator` by @sydney-runkle in [#8710](https://github.com/pydantic/pydantic/pull/8710)
* Reverting problematic fix from 2.6 release, fixing schema building bug by @sydney-runkle in [#8718](https://github.com/pydantic/pydantic/pull/8718)
* Fix warning for tuple of wrong size in `Union` by @davidhewitt in [pydantic/pydantic-core#1174](https://github.com/pydantic/pydantic-core/pull/1174)
* Fix `computed_field` JSON serializer `exclude_none` behavior by @sydney-runkle in [pydantic/pydantic-core#1187](https://github.com/pydantic/pydantic-core/pull/1187)


## v2.6.0 (2024-01-29)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.6.0)

The code released in v2.6.0 is practically identical to that of v2.6.0b1.

### What's Changed

#### Packaging

* Check for `email-validator` version >= 2.0 by @commonism in [#6033](https://github.com/pydantic/pydantic/pull/6033)
* Upgrade `ruff`` target version to Python 3.8 by @Elkiwa in [#8341](https://github.com/pydantic/pydantic/pull/8341)
* Update to `pydantic-extra-types==2.4.1` by @yezz123 in [#8478](https://github.com/pydantic/pydantic/pull/8478)
* Update to `pyright==1.1.345` by @Viicos in [#8453](https://github.com/pydantic/pydantic/pull/8453)
* Update pydantic-core from 2.14.6 to 2.16.1, significant changes from these updates are described below, full changelog [here](https://github.com/pydantic/pydantic-core/compare/v2.14.6...v2.16.1)

#### New Features

* Add `NatsDsn` by @ekeew in [#6874](https://github.com/pydantic/pydantic/pull/6874)
* Add `ConfigDict.ser_json_inf_nan` by @davidhewitt in [#8159](https://github.com/pydantic/pydantic/pull/8159)
* Add `types.OnErrorOmit` by @adriangb in [#8222](https://github.com/pydantic/pydantic/pull/8222)
* Support `AliasGenerator` usage by @sydney-runkle in [#8282](https://github.com/pydantic/pydantic/pull/8282)
* Add Pydantic People Page to docs by @sydney-runkle in [#8345](https://github.com/pydantic/pydantic/pull/8345)
* Support `yyyy-MM-DD` datetime parsing by @sydney-runkle in [#8404](https://github.com/pydantic/pydantic/pull/8404)
* Added bits conversions to the `ByteSize` class #8415 by @luca-matei in [#8507](https://github.com/pydantic/pydantic/pull/8507)
* Enable json schema creation with type `ByteSize` by @geospackle in [#8537](https://github.com/pydantic/pydantic/pull/8537)
* Add `eval_type_backport` to handle union operator and builtin generic subscripting in older Pythons by @alexmojaki in [#8209](https://github.com/pydantic/pydantic/pull/8209)
* Add support for `dataclass` fields `init` by @dmontagu in [#8552](https://github.com/pydantic/pydantic/pull/8552)
* Implement pickling for `ValidationError` by @davidhewitt in [pydantic/pydantic-core#1119](https://github.com/pydantic/pydantic-core/pull/1119)
* Add unified tuple validator that can handle "variadic" tuples via PEP-646 by @dmontagu in [pydantic/pydantic-core#865](https://github.com/pydantic/pydantic-core/pull/865)

#### Changes

* Drop Python3.7 support by @hramezani in [#7188](https://github.com/pydantic/pydantic/pull/7188)
* Drop Python 3.7, and PyPy 3.7 and 3.8 by @davidhewitt in [pydantic/pydantic-core#1129](https://github.com/pydantic/pydantic-core/pull/1129)
* Use positional-only `self` in `BaseModel` constructor, so no field name can ever conflict with it by @ariebovenberg in [#8072](https://github.com/pydantic/pydantic/pull/8072)
* Make `@validate_call` return a function instead of a custom descriptor - fixes binding issue with inheritance and adds `self/cls` argument to validation errors by @alexmojaki in [#8268](https://github.com/pydantic/pydantic/pull/8268)
* Exclude `BaseModel` docstring from JSON schema description by @sydney-runkle in [#8352](https://github.com/pydantic/pydantic/pull/8352)
* Introducing `classproperty` decorator for `model_computed_fields` by @Jocelyn-Gas in [#8437](https://github.com/pydantic/pydantic/pull/8437)
* Explicitly raise an error if field names clashes with types by @Viicos in [#8243](https://github.com/pydantic/pydantic/pull/8243)
* Use stricter serializer for unions of simple types by @alexdrydew [pydantic/pydantic-core#1132](https://github.com/pydantic/pydantic-core/pull/1132)

#### Performance

* Add Codspeed profiling Actions workflow  by @lambertsbennett in [#8054](https://github.com/pydantic/pydantic/pull/8054)
* Improve `int` extraction by @samuelcolvin in [pydantic/pydantic-core#1155](https://github.com/pydantic/pydantic-core/pull/1155)
* Improve performance of recursion guard by @samuelcolvin in [pydantic/pydantic-core#1156](https://github.com/pydantic/pydantic-core/pull/1156)
* `dataclass` serialization speedups by @samuelcolvin in [pydantic/pydantic-core#1162](https://github.com/pydantic/pydantic-core/pull/1162)
* Avoid `HashMap` creation when looking up small JSON objects in `LazyIndexMaps` by @samuelcolvin in [pydantic/jiter#55](https://github.com/pydantic/jiter/pull/55)
* use hashbrown to speedup python string caching by @davidhewitt in [pydantic/jiter#51](https://github.com/pydantic/jiter/pull/51)
* Replace `Peak` with more efficient `Peek` by @davidhewitt in [pydantic/jiter#48](https://github.com/pydantic/jiter/pull/48)

#### Fixes

* Move `getattr` warning in deprecated `BaseConfig` by @tlambert03 in [#7183](https://github.com/pydantic/pydantic/pull/7183)
* Only hash `model_fields`, not whole `__dict__` by @alexmojaki in [#7786](https://github.com/pydantic/pydantic/pull/7786)
* Fix mishandling of unions while freezing types in the `mypy` plugin by @dmontagu in [#7411](https://github.com/pydantic/pydantic/pull/7411)
* Fix `mypy` error on untyped `ClassVar` by @vincent-hachin-wmx in [#8138](https://github.com/pydantic/pydantic/pull/8138)
* Only compare pydantic fields in `BaseModel.__eq__` instead of whole `__dict__` by @QuentinSoubeyranAqemia in [#7825](https://github.com/pydantic/pydantic/pull/7825)
* Update `strict` docstring in `model_validate` method. by @LukeTonin in [#8223](https://github.com/pydantic/pydantic/pull/8223)
* Fix overload position of `computed_field` by @Viicos in [#8227](https://github.com/pydantic/pydantic/pull/8227)
* Fix custom type type casting used in multiple attributes by @ianhfc in [#8066](https://github.com/pydantic/pydantic/pull/8066)
* Fix issue not allowing `validate_call` decorator to be dynamically assigned to a class method by @jusexton in [#8249](https://github.com/pydantic/pydantic/pull/8249)
* Fix issue `unittest.mock` deprecation warnings  by @ibleedicare in [#8262](https://github.com/pydantic/pydantic/pull/8262)
* Added tests for the case `JsonValue` contains subclassed primitive values by @jusexton in [#8286](https://github.com/pydantic/pydantic/pull/8286)
* Fix `mypy` error on free before validator (classmethod) by @sydney-runkle in [#8285](https://github.com/pydantic/pydantic/pull/8285)
* Fix `to_snake` conversion by @jevins09 in [#8316](https://github.com/pydantic/pydantic/pull/8316)
* Fix type annotation of `ModelMetaclass.__prepare__` by @slanzmich in [#8305](https://github.com/pydantic/pydantic/pull/8305)
* Disallow `config` specification when initializing a `TypeAdapter` when the annotated type has config already by @sydney-runkle in [#8365](https://github.com/pydantic/pydantic/pull/8365)
* Fix a naming issue with JSON schema for generics parametrized by recursive type aliases by @dmontagu in [#8389](https://github.com/pydantic/pydantic/pull/8389)
* Fix type annotation in pydantic people script by @shenxiangzhuang in [#8402](https://github.com/pydantic/pydantic/pull/8402)
* Add support for field `alias` in `dataclass` signature by @NeevCohen in [#8387](https://github.com/pydantic/pydantic/pull/8387)
* Fix bug with schema generation with `Field(...)` in a forward ref by @dmontagu in [#8494](https://github.com/pydantic/pydantic/pull/8494)
* Fix ordering of keys in `__dict__` with `model_construct` call by @sydney-runkle in [#8500](https://github.com/pydantic/pydantic/pull/8500)
* Fix module `path_type` creation when globals does not contain `__name__` by @hramezani in [#8470](https://github.com/pydantic/pydantic/pull/8470)
* Fix for namespace issue with dataclasses with `from __future__ import annotations` by @sydney-runkle in [#8513](https://github.com/pydantic/pydantic/pull/8513)
* Fix: make function validator types positional-only by @pmmmwh in [#8479](https://github.com/pydantic/pydantic/pull/8479)
* Fix usage of `@deprecated` by @Viicos in [#8294](https://github.com/pydantic/pydantic/pull/8294)
* Add more support for private attributes in `model_construct` call by @sydney-runkle in [#8525](https://github.com/pydantic/pydantic/pull/8525)
* Use a stack for the types namespace by @dmontagu in [#8378](https://github.com/pydantic/pydantic/pull/8378)
* Fix schema-building bug with `TypeAliasType` for types with refs by @dmontagu in [#8526](https://github.com/pydantic/pydantic/pull/8526)
* Support `pydantic.Field(repr=False)` in dataclasses by @tigeryy2 in [#8511](https://github.com/pydantic/pydantic/pull/8511)
* Override `dataclass_transform` behavior for `RootModel` by @Viicos in [#8163](https://github.com/pydantic/pydantic/pull/8163)
* Refactor signature generation for simplicity by @sydney-runkle in [#8572](https://github.com/pydantic/pydantic/pull/8572)
* Fix ordering bug of PlainValidator annotation by @Anvil in [#8567](https://github.com/pydantic/pydantic/pull/8567)
* Fix `exclude_none` for json serialization of `computed_field`s by @sydney-runkle in [pydantic/pydantic-core#1098](https://github.com/pydantic/pydantic-core/pull/1098)
* Support yyyy-MM-DD string for datetimes by @sydney-runkle in [pydantic/pydantic-core#1124](https://github.com/pydantic/pydantic-core/pull/1124)
* Tweak ordering of definitions in generated schemas by @StrawHatDrag0n in [#8583](https://github.com/pydantic/pydantic/pull/8583)


### New Contributors

#### `pydantic`
* @ekeew made their first contribution in [#6874](https://github.com/pydantic/pydantic/pull/6874)
* @lambertsbennett made their first contribution in [#8054](https://github.com/pydantic/pydantic/pull/8054)
* @vincent-hachin-wmx made their first contribution in [#8138](https://github.com/pydantic/pydantic/pull/8138)
* @QuentinSoubeyranAqemia made their first contribution in [#7825](https://github.com/pydantic/pydantic/pull/7825)
* @ariebovenberg made their first contribution in [#8072](https://github.com/pydantic/pydantic/pull/8072)
* @LukeTonin made their first contribution in [#8223](https://github.com/pydantic/pydantic/pull/8223)
* @denisart made their first contribution in [#8231](https://github.com/pydantic/pydantic/pull/8231)
* @ianhfc made their first contribution in [#8066](https://github.com/pydantic/pydantic/pull/8066)
* @eonu made their first contribution in [#8255](https://github.com/pydantic/pydantic/pull/8255)
* @amandahla made their first contribution in [#8263](https://github.com/pydantic/pydantic/pull/8263)
* @ibleedicare made their first contribution in [#8262](https://github.com/pydantic/pydantic/pull/8262)
* @jevins09 made their first contribution in [#8316](https://github.com/pydantic/pydantic/pull/8316)
* @cuu508 made their first contribution in [#8322](https://github.com/pydantic/pydantic/pull/8322)
* @slanzmich made their first contribution in [#8305](https://github.com/pydantic/pydantic/pull/8305)
* @jensenbox made their first contribution in [#8331](https://github.com/pydantic/pydantic/pull/8331)
* @szepeviktor made their first contribution in [#8356](https://github.com/pydantic/pydantic/pull/8356)
* @Elkiwa made their first contribution in [#8341](https://github.com/pydantic/pydantic/pull/8341)
* @parhamfh made their first contribution in [#8395](https://github.com/pydantic/pydantic/pull/8395)
* @shenxiangzhuang made their first contribution in [#8402](https://github.com/pydantic/pydantic/pull/8402)
* @NeevCohen made their first contribution in [#8387](https://github.com/pydantic/pydantic/pull/8387)
* @zby made their first contribution in [#8497](https://github.com/pydantic/pydantic/pull/8497)
* @patelnets made their first contribution in [#8491](https://github.com/pydantic/pydantic/pull/8491)
* @edwardwli made their first contribution in [#8503](https://github.com/pydantic/pydantic/pull/8503)
* @luca-matei made their first contribution in [#8507](https://github.com/pydantic/pydantic/pull/8507)
* @Jocelyn-Gas made their first contribution in [#8437](https://github.com/pydantic/pydantic/pull/8437)
* @bL34cHig0 made their first contribution in [#8501](https://github.com/pydantic/pydantic/pull/8501)
* @tigeryy2 made their first contribution in [#8511](https://github.com/pydantic/pydantic/pull/8511)
* @geospackle made their first contribution in [#8537](https://github.com/pydantic/pydantic/pull/8537)
* @Anvil made their first contribution in [#8567](https://github.com/pydantic/pydantic/pull/8567)
* @hungtsetse made their first contribution in [#8546](https://github.com/pydantic/pydantic/pull/8546)
* @StrawHatDrag0n made their first contribution in [#8583](https://github.com/pydantic/pydantic/pull/8583)

#### `pydantic-core`
* @mariuswinger made their first contribution in [pydantic/pydantic-core#1087](https://github.com/pydantic/pydantic-core/pull/1087)
* @adamchainz made their first contribution in [pydantic/pydantic-core#1090](https://github.com/pydantic/pydantic-core/pull/1090)
* @akx made their first contribution in [pydantic/pydantic-core#1123](https://github.com/pydantic/pydantic-core/pull/1123)

## v2.6.0b1 (2024-01-19)

Pre-release, see [the GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.6.0b1) for details.

## v2.5.3 (2023-12-22)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.5.3)

### What's Changed

#### Packaging

* uprev `pydantic-core` to 2.14.6

#### Fixes

* Fix memory leak with recursive definitions creating reference cycles by @davidhewitt in [pydantic/pydantic-core#1125](https://github.com/pydantic/pydantic-core/pull/1125)

## v2.5.2 (2023-11-22)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.5.2)

### What's Changed

#### Packaging

* uprev `pydantic-core` to 2.14.5

#### New Features

* Add `ConfigDict.ser_json_inf_nan` by @davidhewitt in [#8159](https://github.com/pydantic/pydantic/pull/8159)

#### Fixes

* Fix validation of `Literal` from JSON keys when used as `dict` key by @sydney-runkle in [pydantic/pydantic-core#1075](https://github.com/pydantic/pydantic-core/pull/1075)
* Fix bug re `custom_init` on members of `Union` by @sydney-runkle in [pydantic/pydantic-core#1076](https://github.com/pydantic/pydantic-core/pull/1076)
* Fix `JsonValue` `bool` serialization by @sydney-runkle in [#8190](https://github.com/pydantic/pydantic/pull/8159)
* Fix handling of unhashable inputs with `Literal` in `Union`s by @sydney-runkle in [pydantic/pydantic-core#1089](https://github.com/pydantic/pydantic-core/pull/1089)

## v2.5.1 (2023-11-15)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.5.1)

### What's Changed

#### Packaging

* uprev pydantic-core to 2.14.3 by @samuelcolvin in [#8120](https://github.com/pydantic/pydantic/pull/8120)

#### Fixes

* Fix package description limit by @dmontagu in [#8097](https://github.com/pydantic/pydantic/pull/8097)
* Fix `ValidateCallWrapper` error when creating a model which has a @validate_call wrapped field annotation by @sydney-runkle in [#8110](https://github.com/pydantic/pydantic/pull/8110)

## v2.5.0 (2023-11-13)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.5.0)

The code released in v2.5.0 is functionally identical to that of v2.5.0b1.

### What's Changed

#### Packaging

* Update pydantic-core from 2.10.1 to 2.14.1, significant changes from these updates are described below, full changelog [here](https://github.com/pydantic/pydantic-core/compare/v2.10.1...v2.14.1)
* Update to `pyright==1.1.335` by @Viicos in [#8075](https://github.com/pydantic/pydantic/pull/8075)

#### New Features

* Allow plugins to catch non `ValidationError` errors by @adriangb in [#7806](https://github.com/pydantic/pydantic/pull/7806)
* Support `__doc__` argument in `create_model()` by @chris-spann in [#7863](https://github.com/pydantic/pydantic/pull/7863)
* Expose `regex_engine` flag - meaning you can use with the Rust or Python regex libraries in constraints by @utkini in [#7768](https://github.com/pydantic/pydantic/pull/7768)
* Save return type generated from type annotation in `ComputedFieldInfo` by @alexmojaki in [#7889](https://github.com/pydantic/pydantic/pull/7889)
* Adopting `ruff` formatter by @Luca-Blight in [#7930](https://github.com/pydantic/pydantic/pull/7930)
* Added `validation_error_cause` to config by @zakstucke in [#7626](https://github.com/pydantic/pydantic/pull/7626)
* Make path of the item to validate available in plugin by @hramezani in [#7861](https://github.com/pydantic/pydantic/pull/7861)
* Add `CallableDiscriminator` and `Tag` by @dmontagu in [#7983](https://github.com/pydantic/pydantic/pull/7983)
  * `CallableDiscriminator` renamed to `Discriminator` by @dmontagu in [#8047](https://github.com/pydantic/pydantic/pull/8047)
* Make union case tags affect union error messages by @dmontagu in [#8001](https://github.com/pydantic/pydantic/pull/8001)
* Add `examples` and `json_schema_extra` to `@computed_field` by @alexmojaki in [#8013](https://github.com/pydantic/pydantic/pull/8013)
* Add `JsonValue` type by @dmontagu in [#7998](https://github.com/pydantic/pydantic/pull/7998)
* Allow `str` as argument to `Discriminator` by @dmontagu in [#8047](https://github.com/pydantic/pydantic/pull/8047)
* Add `SchemaSerializer.__reduce__` method to enable pickle serialization by @edoakes in [pydantic/pydantic-core#1006](https://github.com/pydantic/pydantic-core/pull/1006)

#### Changes

* **Significant Change:** replace `ultra_strict` with new smart union implementation, the way unions are validated has changed significantly to improve performance and correctness, we have worked hard to absolutely minimise the number of cases where behaviour has changed, see the PR for details - by @davidhewitt in [pydantic/pydantic-core#867](https://github.com/pydantic/pydantic-core/pull/867)
* Add support for instance method reassignment when `extra='allow'` by @sydney-runkle in [#7683](https://github.com/pydantic/pydantic/pull/7683)
* Support JSON schema generation for `Enum` types with no cases by @sydney-runkle in [#7927](https://github.com/pydantic/pydantic/pull/7927)
* Warn if a class inherits from `Generic` before `BaseModel` by @alexmojaki in [#7891](https://github.com/pydantic/pydantic/pull/7891)

#### Performance

* New custom JSON parser, `jiter` by @samuelcolvin in [pydantic/pydantic-core#974](https://github.com/pydantic/pydantic-core/pull/974)
* PGO build for MacOS M1 by @samuelcolvin in [pydantic/pydantic-core#1063](https://github.com/pydantic/pydantic-core/pull/1063)
* Use `__getattr__` for all package imports, improve import time by @samuelcolvin in [#7947](https://github.com/pydantic/pydantic/pull/7947)

#### Fixes

* Fix `mypy` issue with subclasses of `RootModel` by @sydney-runkle in [#7677](https://github.com/pydantic/pydantic/pull/7677)
* Properly rebuild the `FieldInfo` when a forward ref gets evaluated by @dmontagu in [#7698](https://github.com/pydantic/pydantic/pull/7698)
* Fix failure to load `SecretStr` from JSON (regression in v2.4) by @sydney-runkle in [#7729](https://github.com/pydantic/pydantic/pull/7729)
* Fix `defer_build` behavior with `TypeAdapter` by @sydney-runkle in [#7736](https://github.com/pydantic/pydantic/pull/7736)
* Improve compatibility with legacy `mypy` versions by @dmontagu in [#7742](https://github.com/pydantic/pydantic/pull/7742)
* Fix: update `TypeVar` handling when default is not set by @pmmmwh in [#7719](https://github.com/pydantic/pydantic/pull/7719)
* Support specification of `strict` on `Enum` type fields by @sydney-runkle in [#7761](https://github.com/pydantic/pydantic/pull/7761)
* Wrap `weakref.ref` instead of subclassing to fix `cloudpickle` serialization by @edoakes in [#7780](https://github.com/pydantic/pydantic/pull/7780)
* Keep values of private attributes set within `model_post_init` in subclasses by @alexmojaki in [#7775](https://github.com/pydantic/pydantic/pull/7775)
* Add more specific type for non-callable `json_schema_extra` by @alexmojaki in [#7803](https://github.com/pydantic/pydantic/pull/7803)
* Raise an error when deleting frozen (model) fields by @alexmojaki in [#7800](https://github.com/pydantic/pydantic/pull/7800)
* Fix schema sorting bug with default values by @sydney-runkle in [#7817](https://github.com/pydantic/pydantic/pull/7817)
* Use generated alias for aliases that are not specified otherwise by @alexmojaki in [#7802](https://github.com/pydantic/pydantic/pull/7802)
* Support `strict` specification for `UUID` types by @sydney-runkle in [#7865](https://github.com/pydantic/pydantic/pull/7865)
* JSON schema: fix extra parameter handling by @me-and in [#7810](https://github.com/pydantic/pydantic/pull/7810)
* Fix: support `pydantic.Field(kw_only=True)` with inherited dataclasses by @PrettyWood in [#7827](https://github.com/pydantic/pydantic/pull/7827)
* Support `validate_call` decorator for methods in classes with `__slots__` by @sydney-runkle in [#7883](https://github.com/pydantic/pydantic/pull/7883)
* Fix pydantic dataclass problem with `dataclasses.field` default by @hramezani in [#7898](https://github.com/pydantic/pydantic/pull/7898)
* Fix schema generation for generics with union type bounds by @sydney-runkle in [#7899](https://github.com/pydantic/pydantic/pull/7899)
* Fix version for `importlib_metadata` on python 3.7 by @sydney-runkle in [#7904](https://github.com/pydantic/pydantic/pull/7904)
* Support `|` operator (Union) in PydanticRecursiveRef by @alexmojaki in [#7892](https://github.com/pydantic/pydantic/pull/7892)
* Fix `display_as_type` for `TypeAliasType` in python 3.12 by @dmontagu in [#7929](https://github.com/pydantic/pydantic/pull/7929)
* Add support for `NotRequired` generics in `TypedDict` by @sydney-runkle in [#7932](https://github.com/pydantic/pydantic/pull/7932)
* Make generic `TypeAliasType` specifications produce different schema definitions by @alexdrydew in [#7893](https://github.com/pydantic/pydantic/pull/7893)
* Added fix for signature of inherited dataclass by @howsunjow in [#7925](https://github.com/pydantic/pydantic/pull/7925)
* Make the model name generation more robust in JSON schema by @joakimnordling in [#7881](https://github.com/pydantic/pydantic/pull/7881)
* Fix plurals in validation error messages (in tests) by @Iipin in [#7972](https://github.com/pydantic/pydantic/pull/7972)
* `PrivateAttr` is passed from `Annotated` default position by @tabassco in [#8004](https://github.com/pydantic/pydantic/pull/8004)
* Don't decode bytes (which may not be UTF8) when displaying SecretBytes by @alexmojaki in [#8012](https://github.com/pydantic/pydantic/pull/8012)
* Use `classmethod` instead of `classmethod[Any, Any, Any]` by @Mr-Pepe in [#7979](https://github.com/pydantic/pydantic/pull/7979)
* Clearer error on invalid Plugin by @samuelcolvin in [#8023](https://github.com/pydantic/pydantic/pull/8023)
* Correct pydantic dataclasses import by @samuelcolvin in [#8027](https://github.com/pydantic/pydantic/pull/8027)
* Fix misbehavior for models referencing redefined type aliases by @dmontagu in [#8050](https://github.com/pydantic/pydantic/pull/8050)
* Fix `Optional` field with `validate_default` only performing one field validation by @sydney-runkle in [pydantic/pydantic-core#1002](https://github.com/pydantic/pydantic-core/pull/1002)
* Fix `definition-ref` bug with `Dict` keys by @sydney-runkle in [pydantic/pydantic-core#1014](https://github.com/pydantic/pydantic-core/pull/1014)
* Fix bug allowing validation of `bool` types with `coerce_numbers_to_str=True` by @sydney-runkle in [pydantic/pydantic-core#1017](https://github.com/pydantic/pydantic-core/pull/1017)
* Don't accept `NaN` in float and decimal constraints by @davidhewitt in [pydantic/pydantic-core#1037](https://github.com/pydantic/pydantic-core/pull/1037)
* Add `lax_str` and `lax_int` support for enum values not inherited from str/int by @michaelhly in [pydantic/pydantic-core#1015](https://github.com/pydantic/pydantic-core/pull/1015)
* Support subclasses in lists in `Union` of `List` types by @sydney-runkle in [pydantic/pydantic-core#1039](https://github.com/pydantic/pydantic-core/pull/1039)
* Allow validation against `max_digits` and `decimals` to pass if normalized or non-normalized input is valid by @sydney-runkle in [pydantic/pydantic-core#1049](https://github.com/pydantic/pydantic-core/pull/1049)
* Fix: proper pluralization in `ValidationError` messages by @Iipin in [pydantic/pydantic-core#1050](https://github.com/pydantic/pydantic-core/pull/1050)
* Disallow the string `'-'` as `datetime` input by @davidhewitt in [pydantic/speedate#52](https://github.com/pydantic/speedate/pull/52) & [pydantic/pydantic-core#1060](https://github.com/pydantic/pydantic-core/pull/1060)
* Fix: NaN and Inf float serialization by @davidhewitt in [pydantic/pydantic-core#1062](https://github.com/pydantic/pydantic-core/pull/1062)
* Restore manylinux-compatible PGO builds by @davidhewitt in [pydantic/pydantic-core#1068](https://github.com/pydantic/pydantic-core/pull/1068)

### New Contributors

#### `pydantic`
* @schneebuzz made their first contribution in [#7699](https://github.com/pydantic/pydantic/pull/7699)
* @edoakes made their first contribution in [#7780](https://github.com/pydantic/pydantic/pull/7780)
* @alexmojaki made their first contribution in [#7775](https://github.com/pydantic/pydantic/pull/7775)
* @NickG123 made their first contribution in [#7751](https://github.com/pydantic/pydantic/pull/7751)
* @gowthamgts made their first contribution in [#7830](https://github.com/pydantic/pydantic/pull/7830)
* @jamesbraza made their first contribution in [#7848](https://github.com/pydantic/pydantic/pull/7848)
* @laundmo made their first contribution in [#7850](https://github.com/pydantic/pydantic/pull/7850)
* @rahmatnazali made their first contribution in [#7870](https://github.com/pydantic/pydantic/pull/7870)
* @waterfountain1996 made their first contribution in [#7878](https://github.com/pydantic/pydantic/pull/7878)
* @chris-spann made their first contribution in [#7863](https://github.com/pydantic/pydantic/pull/7863)
* @me-and made their first contribution in [#7810](https://github.com/pydantic/pydantic/pull/7810)
* @utkini made their first contribution in [#7768](https://github.com/pydantic/pydantic/pull/7768)
* @bn-l made their first contribution in [#7744](https://github.com/pydantic/pydantic/pull/7744)
* @alexdrydew made their first contribution in [#7893](https://github.com/pydantic/pydantic/pull/7893)
* @Luca-Blight made their first contribution in [#7930](https://github.com/pydantic/pydantic/pull/7930)
* @howsunjow made their first contribution in [#7925](https://github.com/pydantic/pydantic/pull/7925)
* @joakimnordling made their first contribution in [#7881](https://github.com/pydantic/pydantic/pull/7881)
* @icfly2 made their first contribution in [#7976](https://github.com/pydantic/pydantic/pull/7976)
* @Yummy-Yums made their first contribution in [#8003](https://github.com/pydantic/pydantic/pull/8003)
* @Iipin made their first contribution in [#7972](https://github.com/pydantic/pydantic/pull/7972)
* @tabassco made their first contribution in [#8004](https://github.com/pydantic/pydantic/pull/8004)
* @Mr-Pepe made their first contribution in [#7979](https://github.com/pydantic/pydantic/pull/7979)
* @0x00cl made their first contribution in [#8010](https://github.com/pydantic/pydantic/pull/8010)
* @barraponto made their first contribution in [#8032](https://github.com/pydantic/pydantic/pull/8032)

#### `pydantic-core`
* @sisp made their first contribution in [pydantic/pydantic-core#995](https://github.com/pydantic/pydantic-core/pull/995)
* @michaelhly made their first contribution in [pydantic/pydantic-core#1015](https://github.com/pydantic/pydantic-core/pull/1015)

## v2.5.0b1 (2023-11-09)

Pre-release, see [the GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.5.0b1) for details.

## v2.4.2 (2023-09-27)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.4.2)

### What's Changed

#### Fixes

* Fix bug with JSON schema for sequence of discriminated union by @dmontagu in [#7647](https://github.com/pydantic/pydantic/pull/7647)
* Fix schema references in discriminated unions by @adriangb in [#7646](https://github.com/pydantic/pydantic/pull/7646)
* Fix json schema generation for recursive models by @adriangb in [#7653](https://github.com/pydantic/pydantic/pull/7653)
* Fix `models_json_schema` for generic models by @adriangb in [#7654](https://github.com/pydantic/pydantic/pull/7654)
* Fix xfailed test for generic model signatures by @adriangb in [#7658](https://github.com/pydantic/pydantic/pull/7658)

### New Contributors

* @austinorr made their first contribution in [#7657](https://github.com/pydantic/pydantic/pull/7657)
* @peterHoburg made their first contribution in [#7670](https://github.com/pydantic/pydantic/pull/7670)

## v2.4.1 (2023-09-26)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.4.1)

### What's Changed

#### Packaging

* Update pydantic-core to 2.10.1 by @davidhewitt in [#7633](https://github.com/pydantic/pydantic/pull/7633)

#### Fixes

* Serialize unsubstituted type vars as `Any` by @adriangb in [#7606](https://github.com/pydantic/pydantic/pull/7606)
* Remove schema building caches by @adriangb in [#7624](https://github.com/pydantic/pydantic/pull/7624)
* Fix an issue where JSON schema extras weren't JSON encoded by @dmontagu in [#7625](https://github.com/pydantic/pydantic/pull/7625)

## v2.4.0 (2023-09-22)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.4.0)

### What's Changed

#### Packaging

* Update pydantic-core to 2.10.0 by @samuelcolvin in [#7542](https://github.com/pydantic/pydantic/pull/7542)

#### New Features

* Add `Base64Url` types by @dmontagu in [#7286](https://github.com/pydantic/pydantic/pull/7286)
* Implement optional `number` to `str` coercion by @lig in [#7508](https://github.com/pydantic/pydantic/pull/7508)
* Allow access to `field_name` and `data` in all validators if there is data and a field name by @samuelcolvin in [#7542](https://github.com/pydantic/pydantic/pull/7542)
* Add `BaseModel.model_validate_strings` and `TypeAdapter.validate_strings` by @hramezani in [#7552](https://github.com/pydantic/pydantic/pull/7552)
* Add Pydantic `plugins` experimental implementation by @lig @samuelcolvin and @Kludex in [#6820](https://github.com/pydantic/pydantic/pull/6820)

#### Changes

* Do not override `model_post_init` in subclass with private attrs by @Viicos in [#7302](https://github.com/pydantic/pydantic/pull/7302)
* Make fields with defaults not required in the serialization schema by default by @dmontagu in [#7275](https://github.com/pydantic/pydantic/pull/7275)
* Mark `Extra` as deprecated by @disrupted in [#7299](https://github.com/pydantic/pydantic/pull/7299)
* Make `EncodedStr` a dataclass by @Kludex in [#7396](https://github.com/pydantic/pydantic/pull/7396)
* Move `annotated_handlers` to be public by @samuelcolvin in [#7569](https://github.com/pydantic/pydantic/pull/7569)

#### Performance

* Simplify flattening and inlining of `CoreSchema` by @adriangb in [#7523](https://github.com/pydantic/pydantic/pull/7523)
* Remove unused copies in `CoreSchema` walking by @adriangb in [#7528](https://github.com/pydantic/pydantic/pull/7528)
* Add caches for collecting definitions and invalid schemas from a CoreSchema by @adriangb in [#7527](https://github.com/pydantic/pydantic/pull/7527)
* Eagerly resolve discriminated unions and cache cases where we can't by @adriangb in [#7529](https://github.com/pydantic/pydantic/pull/7529)
* Replace `dict.get` and `dict.setdefault` with more verbose versions in `CoreSchema` building hot paths by @adriangb in [#7536](https://github.com/pydantic/pydantic/pull/7536)
* Cache invalid `CoreSchema` discovery by @adriangb in [#7535](https://github.com/pydantic/pydantic/pull/7535)
* Allow disabling `CoreSchema` validation for faster startup times by @adriangb in [#7565](https://github.com/pydantic/pydantic/pull/7565)

#### Fixes

* Fix config detection for `TypedDict` from grandparent classes by @dmontagu in [#7272](https://github.com/pydantic/pydantic/pull/7272)
* Fix hash function generation for frozen models with unusual MRO by @dmontagu in [#7274](https://github.com/pydantic/pydantic/pull/7274)
* Make `strict` config overridable in field for Path by @hramezani in [#7281](https://github.com/pydantic/pydantic/pull/7281)
* Use `ser_json_<timedelta|bytes>` on default in `GenerateJsonSchema` by @Kludex in [#7269](https://github.com/pydantic/pydantic/pull/7269)
* Adding a check that alias is validated as an identifier for Python by @andree0 in [#7319](https://github.com/pydantic/pydantic/pull/7319)
* Raise an error when computed field overrides field by @sydney-runkle in [#7346](https://github.com/pydantic/pydantic/pull/7346)
* Fix applying `SkipValidation` to referenced schemas by @adriangb in [#7381](https://github.com/pydantic/pydantic/pull/7381)
* Enforce behavior of private attributes having double leading underscore by @lig in [#7265](https://github.com/pydantic/pydantic/pull/7265)
* Standardize `__get_pydantic_core_schema__` signature by @hramezani in [#7415](https://github.com/pydantic/pydantic/pull/7415)
* Fix generic dataclass fields mutation bug (when using `TypeAdapter`) by @sydney-runkle in [#7435](https://github.com/pydantic/pydantic/pull/7435)
* Fix `TypeError` on `model_validator` in `wrap` mode by @pmmmwh in [#7496](https://github.com/pydantic/pydantic/pull/7496)
* Improve enum error message by @hramezani in [#7506](https://github.com/pydantic/pydantic/pull/7506)
* Make `repr` work for instances that failed initialization when handling `ValidationError`s by @dmontagu in [#7439](https://github.com/pydantic/pydantic/pull/7439)
* Fixed a regular expression denial of service issue by limiting whitespaces by @prodigysml in [#7360](https://github.com/pydantic/pydantic/pull/7360)
* Fix handling of `UUID` values having `UUID.version=None` by @lig in [#7566](https://github.com/pydantic/pydantic/pull/7566)
* Fix `__iter__` returning private `cached_property` info by @sydney-runkle in [#7570](https://github.com/pydantic/pydantic/pull/7570)
* Improvements to version info message by @samuelcolvin in [#7594](https://github.com/pydantic/pydantic/pull/7594)

### New Contributors
* @15498th made their first contribution in [#7238](https://github.com/pydantic/pydantic/pull/7238)
* @GabrielCappelli made their first contribution in [#7213](https://github.com/pydantic/pydantic/pull/7213)
* @tobni made their first contribution in [#7184](https://github.com/pydantic/pydantic/pull/7184)
* @redruin1 made their first contribution in [#7282](https://github.com/pydantic/pydantic/pull/7282)
* @FacerAin made their first contribution in [#7288](https://github.com/pydantic/pydantic/pull/7288)
* @acdha made their first contribution in [#7297](https://github.com/pydantic/pydantic/pull/7297)
* @andree0 made their first contribution in [#7319](https://github.com/pydantic/pydantic/pull/7319)
* @gordonhart made their first contribution in [#7375](https://github.com/pydantic/pydantic/pull/7375)
* @pmmmwh made their first contribution in [#7496](https://github.com/pydantic/pydantic/pull/7496)
* @disrupted made their first contribution in [#7299](https://github.com/pydantic/pydantic/pull/7299)
* @prodigysml made their first contribution in [#7360](https://github.com/pydantic/pydantic/pull/7360)

## v2.3.0 (2023-08-23)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.3.0)

* 🔥 Remove orphaned changes file from repo by @lig in [#7168](https://github.com/pydantic/pydantic/pull/7168)
* Add copy button on documentation by @Kludex in [#7190](https://github.com/pydantic/pydantic/pull/7190)
* Fix docs on JSON type by @Kludex in [#7189](https://github.com/pydantic/pydantic/pull/7189)
* Update mypy 1.5.0 to 1.5.1 in CI by @hramezani in [#7191](https://github.com/pydantic/pydantic/pull/7191)
* fix download links badge by @samuelcolvin in [#7200](https://github.com/pydantic/pydantic/pull/7200)
* add 2.2.1 to changelog by @samuelcolvin in [#7212](https://github.com/pydantic/pydantic/pull/7212)
* Make ModelWrapValidator protocols generic by @dmontagu in [#7154](https://github.com/pydantic/pydantic/pull/7154)
* Correct `Field(..., exclude: bool)` docs by @samuelcolvin in [#7214](https://github.com/pydantic/pydantic/pull/7214)
* Make shadowing attributes a warning instead of an error by @adriangb in [#7193](https://github.com/pydantic/pydantic/pull/7193)
* Document `Base64Str` and `Base64Bytes` by @Kludex in [#7192](https://github.com/pydantic/pydantic/pull/7192)
* Fix `config.defer_build` for serialization first cases by @samuelcolvin in [#7024](https://github.com/pydantic/pydantic/pull/7024)
* clean Model docstrings in JSON Schema by @samuelcolvin in [#7210](https://github.com/pydantic/pydantic/pull/7210)
* fix [#7228](https://github.com/pydantic/pydantic/pull/7228) (typo): docs in `validators.md` to correct `validate_default` kwarg by @lmmx in [#7229](https://github.com/pydantic/pydantic/pull/7229)
* ✅ Implement `tzinfo.fromutc` method for `TzInfo` in `pydantic-core` by @lig in [#7019](https://github.com/pydantic/pydantic/pull/7019)
* Support `__get_validators__` by @hramezani in [#7197](https://github.com/pydantic/pydantic/pull/7197)

## v2.2.1 (2023-08-18)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.2.1)

* Make `xfail`ing test for root model extra stop `xfail`ing by @dmontagu in [#6937](https://github.com/pydantic/pydantic/pull/6937)
* Optimize recursion detection by stopping on the second visit for the same object by @mciucu in [#7160](https://github.com/pydantic/pydantic/pull/7160)
* fix link in docs by @tlambert03 in [#7166](https://github.com/pydantic/pydantic/pull/7166)
* Replace MiMalloc w/ default allocator by @adriangb in [pydantic/pydantic-core#900](https://github.com/pydantic/pydantic-core/pull/900)
* Bump pydantic-core to 2.6.1 and prepare 2.2.1 release by @adriangb in [#7176](https://github.com/pydantic/pydantic/pull/7176)

## v2.2.0 (2023-08-17)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.2.0)

* Split "pipx install" setup command into two commands on the documentation site by @nomadmtb in [#6869](https://github.com/pydantic/pydantic/pull/6869)
* Deprecate `Field.include` by @hramezani in [#6852](https://github.com/pydantic/pydantic/pull/6852)
* Fix typo in default factory error msg by @hramezani in [#6880](https://github.com/pydantic/pydantic/pull/6880)
* Simplify handling of typing.Annotated in GenerateSchema by @dmontagu in [#6887](https://github.com/pydantic/pydantic/pull/6887)
* Re-enable fastapi tests in CI by @dmontagu in [#6883](https://github.com/pydantic/pydantic/pull/6883)
* Make it harder to hit collisions with json schema defrefs by @dmontagu in [#6566](https://github.com/pydantic/pydantic/pull/6566)
* Cleaner error for invalid input to `Path` fields by @samuelcolvin in [#6903](https://github.com/pydantic/pydantic/pull/6903)
* :memo: support Coordinate Type by @yezz123 in [#6906](https://github.com/pydantic/pydantic/pull/6906)
* Fix `ForwardRef` wrapper for py 3.10.0 (shim until bpo-45166) by @randomir in [#6919](https://github.com/pydantic/pydantic/pull/6919)
* Fix misbehavior related to copying of RootModel by @dmontagu in [#6918](https://github.com/pydantic/pydantic/pull/6918)
* Fix issue with recursion error caused by ParamSpec by @dmontagu in [#6923](https://github.com/pydantic/pydantic/pull/6923)
* Add section about Constrained classes to the Migration Guide by @Kludex in [#6924](https://github.com/pydantic/pydantic/pull/6924)
* Use `main` branch for badge links by @Viicos in [#6925](https://github.com/pydantic/pydantic/pull/6925)
* Add test for v1/v2 Annotated discrepancy by @carlbordum in [#6926](https://github.com/pydantic/pydantic/pull/6926)
* Make the v1 mypy plugin work with both v1 and v2 by @dmontagu in [#6921](https://github.com/pydantic/pydantic/pull/6921)
* Fix issue where generic models couldn't be parametrized with BaseModel by @dmontagu in [#6933](https://github.com/pydantic/pydantic/pull/6933)
* Remove xfail for discriminated union with alias by @dmontagu in [#6938](https://github.com/pydantic/pydantic/pull/6938)
* add field_serializer to computed_field by @andresliszt in [#6965](https://github.com/pydantic/pydantic/pull/6965)
* Use union_schema with Type[Union[...]] by @JeanArhancet in [#6952](https://github.com/pydantic/pydantic/pull/6952)
* Fix inherited typeddict attributes / config by @adriangb in [#6981](https://github.com/pydantic/pydantic/pull/6981)
* fix dataclass annotated before validator called twice by @davidhewitt in [#6998](https://github.com/pydantic/pydantic/pull/6998)
* Update test-fastapi deselected tests by @hramezani in [#7014](https://github.com/pydantic/pydantic/pull/7014)
* Fix validator doc format by @hramezani in [#7015](https://github.com/pydantic/pydantic/pull/7015)
* Fix typo in docstring of model_json_schema by @AdamVinch-Federated in [#7032](https://github.com/pydantic/pydantic/pull/7032)
* remove unused "type ignores" with pyright by @samuelcolvin in [#7026](https://github.com/pydantic/pydantic/pull/7026)
* Add benchmark representing FastAPI startup time by @adriangb in [#7030](https://github.com/pydantic/pydantic/pull/7030)
* Fix json_encoders for Enum subclasses by @adriangb in [#7029](https://github.com/pydantic/pydantic/pull/7029)
* Update docstring of `ser_json_bytes` regarding base64 encoding by @Viicos in [#7052](https://github.com/pydantic/pydantic/pull/7052)
* Allow `@validate_call` to work on async methods by @adriangb in [#7046](https://github.com/pydantic/pydantic/pull/7046)
* Fix: mypy error with `Settings` and `SettingsConfigDict` by @JeanArhancet in [#7002](https://github.com/pydantic/pydantic/pull/7002)
* Fix some typos (repeated words and it's/its) by @eumiro in [#7063](https://github.com/pydantic/pydantic/pull/7063)
* Fix the typo in docstring by @harunyasar in [#7062](https://github.com/pydantic/pydantic/pull/7062)
* Docs: Fix broken URL in the pydantic-settings package recommendation by @swetjen in [#6995](https://github.com/pydantic/pydantic/pull/6995)
* Handle constraints being applied to schemas that don't accept it by @adriangb in [#6951](https://github.com/pydantic/pydantic/pull/6951)
* Replace almost_equal_floats with math.isclose by @eumiro in [#7082](https://github.com/pydantic/pydantic/pull/7082)
* bump pydantic-core to 2.5.0 by @davidhewitt in [#7077](https://github.com/pydantic/pydantic/pull/7077)
* Add `short_version` and use it in links by @hramezani in [#7115](https://github.com/pydantic/pydantic/pull/7115)
* 📝 Add usage link to `RootModel` by @Kludex in [#7113](https://github.com/pydantic/pydantic/pull/7113)
* Revert "Fix default port for mongosrv DSNs (#6827)" by @Kludex in [#7116](https://github.com/pydantic/pydantic/pull/7116)
* Clarify validate_default and _Unset handling in usage docs and migration guide by @benbenbang in [#6950](https://github.com/pydantic/pydantic/pull/6950)
* Tweak documentation of `Field.exclude` by @Viicos in [#7086](https://github.com/pydantic/pydantic/pull/7086)
* Do not require `validate_assignment` to use `Field.frozen` by @Viicos in [#7103](https://github.com/pydantic/pydantic/pull/7103)
* tweaks to `_core_utils` by @samuelcolvin in [#7040](https://github.com/pydantic/pydantic/pull/7040)
* Make DefaultDict working with set by @hramezani in [#7126](https://github.com/pydantic/pydantic/pull/7126)
* Don't always require typing.Generic as a base for partially parametrized models by @dmontagu in [#7119](https://github.com/pydantic/pydantic/pull/7119)
* Fix issue with JSON schema incorrectly using parent class core schema by @dmontagu in [#7020](https://github.com/pydantic/pydantic/pull/7020)
* Fix xfailed test related to TypedDict and alias_generator by @dmontagu in [#6940](https://github.com/pydantic/pydantic/pull/6940)
* Improve error message for NameEmail by @dmontagu in [#6939](https://github.com/pydantic/pydantic/pull/6939)
* Fix generic computed fields by @dmontagu in [#6988](https://github.com/pydantic/pydantic/pull/6988)
* Reflect namedtuple default values during validation by @dmontagu in [#7144](https://github.com/pydantic/pydantic/pull/7144)
* Update dependencies, fix pydantic-core usage, fix CI issues by @dmontagu in [#7150](https://github.com/pydantic/pydantic/pull/7150)
* Add mypy 1.5.0 by @hramezani in [#7118](https://github.com/pydantic/pydantic/pull/7118)
* Handle non-json native enum values by @adriangb in [#7056](https://github.com/pydantic/pydantic/pull/7056)
* document `round_trip` in Json type documentation  by @jc-louis in [#7137](https://github.com/pydantic/pydantic/pull/7137)
* Relax signature checks to better support builtins and C extension functions as validators by @adriangb in [#7101](https://github.com/pydantic/pydantic/pull/7101)
* add union_mode='left_to_right' by @davidhewitt in [#7151](https://github.com/pydantic/pydantic/pull/7151)
* Include an error message hint for inherited ordering by @yvalencia91 in [#7124](https://github.com/pydantic/pydantic/pull/7124)
* Fix one docs link and resolve some warnings for two others by @dmontagu in [#7153](https://github.com/pydantic/pydantic/pull/7153)
* Include Field extra keys name in warning by @hramezani in [#7136](https://github.com/pydantic/pydantic/pull/7136)

## v2.1.1 (2023-07-25)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.1.1)

* Skip FieldInfo merging when unnecessary by @dmontagu in [#6862](https://github.com/pydantic/pydantic/pull/6862)

## v2.1.0 (2023-07-25)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.1.0)

* Add `StringConstraints` for use as Annotated metadata by @adriangb in [#6605](https://github.com/pydantic/pydantic/pull/6605)
* Try to fix intermittently failing CI by @adriangb in [#6683](https://github.com/pydantic/pydantic/pull/6683)
* Remove redundant example of optional vs default. by @ehiggs-deliverect in [#6676](https://github.com/pydantic/pydantic/pull/6676)
* Docs update by @samuelcolvin in [#6692](https://github.com/pydantic/pydantic/pull/6692)
* Remove the Validate always section in validator docs by @adriangb in [#6679](https://github.com/pydantic/pydantic/pull/6679)
* Fix recursion error in json schema generation by @adriangb in [#6720](https://github.com/pydantic/pydantic/pull/6720)
* Fix incorrect subclass check for secretstr by @AlexVndnblcke in [#6730](https://github.com/pydantic/pydantic/pull/6730)
* update pdm / pdm lockfile to 2.8.0 by @davidhewitt in [#6714](https://github.com/pydantic/pydantic/pull/6714)
* unpin pdm on more CI jobs by @davidhewitt in [#6755](https://github.com/pydantic/pydantic/pull/6755)
* improve source locations for auxiliary packages in docs by @davidhewitt in [#6749](https://github.com/pydantic/pydantic/pull/6749)
* Assume builtins don't accept an info argument by @adriangb in [#6754](https://github.com/pydantic/pydantic/pull/6754)
* Fix bug where calling `help(BaseModelSubclass)` raises errors by @hramezani in [#6758](https://github.com/pydantic/pydantic/pull/6758)
* Fix mypy plugin handling of `@model_validator(mode="after")` by @ljodal in [#6753](https://github.com/pydantic/pydantic/pull/6753)
* update pydantic-core to 2.3.1 by @davidhewitt in [#6756](https://github.com/pydantic/pydantic/pull/6756)
* Mypy plugin for settings by @hramezani in [#6760](https://github.com/pydantic/pydantic/pull/6760)
* Use `contentSchema` keyword for JSON schema by @dmontagu in [#6715](https://github.com/pydantic/pydantic/pull/6715)
* fast-path checking finite decimals by @davidhewitt in [#6769](https://github.com/pydantic/pydantic/pull/6769)
* Docs update by @samuelcolvin in [#6771](https://github.com/pydantic/pydantic/pull/6771)
* Improve json schema doc by @hramezani in [#6772](https://github.com/pydantic/pydantic/pull/6772)
* Update validator docs by @adriangb in [#6695](https://github.com/pydantic/pydantic/pull/6695)
* Fix typehint for wrap validator by @dmontagu in [#6788](https://github.com/pydantic/pydantic/pull/6788)
* 🐛 Fix validation warning for unions of Literal and other type by @lig in [#6628](https://github.com/pydantic/pydantic/pull/6628)
* Update documentation for generics support in V2 by @tpdorsey in [#6685](https://github.com/pydantic/pydantic/pull/6685)
* add pydantic-core build info to `version_info()` by @samuelcolvin in [#6785](https://github.com/pydantic/pydantic/pull/6785)
* Fix pydantic dataclasses that use slots with default values by @dmontagu in [#6796](https://github.com/pydantic/pydantic/pull/6796)
* Fix inheritance of hash function for frozen models by @dmontagu in [#6789](https://github.com/pydantic/pydantic/pull/6789)
* ✨ Add `SkipJsonSchema` annotation by @Kludex in [#6653](https://github.com/pydantic/pydantic/pull/6653)
* Error if an invalid field name is used with Field by @dmontagu in [#6797](https://github.com/pydantic/pydantic/pull/6797)
* Add `GenericModel` to `MOVED_IN_V2` by @adriangb in [#6776](https://github.com/pydantic/pydantic/pull/6776)
* Remove unused code from `docs/usage/types/custom.md` by @hramezani in [#6803](https://github.com/pydantic/pydantic/pull/6803)
* Fix `float` -> `Decimal` coercion precision loss by @adriangb in [#6810](https://github.com/pydantic/pydantic/pull/6810)
* remove email validation from the north star benchmark by @davidhewitt in [#6816](https://github.com/pydantic/pydantic/pull/6816)
* Fix link to mypy by @progsmile in [#6824](https://github.com/pydantic/pydantic/pull/6824)
* Improve initialization hooks example by @hramezani in [#6822](https://github.com/pydantic/pydantic/pull/6822)
* Fix default port for mongosrv DSNs by @dmontagu in [#6827](https://github.com/pydantic/pydantic/pull/6827)
* Improve API documentation, in particular more links between usage and API docs by @samuelcolvin in [#6780](https://github.com/pydantic/pydantic/pull/6780)
* update pydantic-core to 2.4.0 by @davidhewitt in [#6831](https://github.com/pydantic/pydantic/pull/6831)
* Fix `annotated_types.MaxLen` validator for custom sequence types by @ImogenBits in [#6809](https://github.com/pydantic/pydantic/pull/6809)
* Update V1 by @hramezani in [#6833](https://github.com/pydantic/pydantic/pull/6833)
* Make it so callable JSON schema extra works by @dmontagu in [#6798](https://github.com/pydantic/pydantic/pull/6798)
* Fix serialization issue with `InstanceOf` by @dmontagu in [#6829](https://github.com/pydantic/pydantic/pull/6829)
* Add back support for `json_encoders` by @adriangb in [#6811](https://github.com/pydantic/pydantic/pull/6811)
* Update field annotations when building the schema by @dmontagu in [#6838](https://github.com/pydantic/pydantic/pull/6838)
* Use `WeakValueDictionary` to fix generic memory leak by @dmontagu in [#6681](https://github.com/pydantic/pydantic/pull/6681)
* Add `config.defer_build` to optionally make model building lazy by @samuelcolvin in [#6823](https://github.com/pydantic/pydantic/pull/6823)
* delegate `UUID` serialization to pydantic-core by @davidhewitt in [#6850](https://github.com/pydantic/pydantic/pull/6850)
* Update `json_encoders` docs by @adriangb in [#6848](https://github.com/pydantic/pydantic/pull/6848)
* Fix error message for `staticmethod`/`classmethod` order with validate_call by @dmontagu in [#6686](https://github.com/pydantic/pydantic/pull/6686)
* Improve documentation for `Config` by @samuelcolvin in [#6847](https://github.com/pydantic/pydantic/pull/6847)
* Update serialization doc to mention `Field.exclude` takes priority over call-time `include/exclude` by @hramezani in [#6851](https://github.com/pydantic/pydantic/pull/6851)
* Allow customizing core schema generation by making `GenerateSchema` public by @adriangb in [#6737](https://github.com/pydantic/pydantic/pull/6737)

## v2.0.3 (2023-07-05)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.0.3)

* Mention PyObject (v1) moving to ImportString (v2) in migration doc by @slafs in [#6456](https://github.com/pydantic/pydantic/pull/6456)
* Fix release-tweet CI by @Kludex in [#6461](https://github.com/pydantic/pydantic/pull/6461)
* Revise the section on required / optional / nullable fields. by @ybressler in [#6468](https://github.com/pydantic/pydantic/pull/6468)
* Warn if a type hint is not in fact a type by @adriangb in [#6479](https://github.com/pydantic/pydantic/pull/6479)
* Replace TransformSchema with GetPydanticSchema by @dmontagu in [#6484](https://github.com/pydantic/pydantic/pull/6484)
* Fix the un-hashability of various annotation types, for use in caching generic containers by @dmontagu in [#6480](https://github.com/pydantic/pydantic/pull/6480)
* PYD-164: Rework custom types docs by @adriangb in [#6490](https://github.com/pydantic/pydantic/pull/6490)
* Fix ci by @adriangb in [#6507](https://github.com/pydantic/pydantic/pull/6507)
* Fix forward ref in generic by @adriangb in [#6511](https://github.com/pydantic/pydantic/pull/6511)
* Fix generation of serialization JSON schemas for core_schema.ChainSchema by @dmontagu in [#6515](https://github.com/pydantic/pydantic/pull/6515)
* Document the change in `Field.alias` behavior in Pydantic V2 by @hramezani in [#6508](https://github.com/pydantic/pydantic/pull/6508)
* Give better error message attempting to compute the json schema of a model with undefined fields by @dmontagu in [#6519](https://github.com/pydantic/pydantic/pull/6519)
* Document `alias_priority` by @tpdorsey in [#6520](https://github.com/pydantic/pydantic/pull/6520)
* Add redirect for types documentation by @tpdorsey in [#6513](https://github.com/pydantic/pydantic/pull/6513)
* Allow updating docs without release by @samuelcolvin in [#6551](https://github.com/pydantic/pydantic/pull/6551)
* Ensure docs tests always run in the right folder by @dmontagu in [#6487](https://github.com/pydantic/pydantic/pull/6487)
* Defer evaluation of return type hints for serializer functions by @dmontagu in [#6516](https://github.com/pydantic/pydantic/pull/6516)
* Disable E501 from Ruff and rely on just Black by @adriangb in [#6552](https://github.com/pydantic/pydantic/pull/6552)
* Update JSON Schema documentation for V2 by @tpdorsey in [#6492](https://github.com/pydantic/pydantic/pull/6492)
* Add documentation of cyclic reference handling by @dmontagu in [#6493](https://github.com/pydantic/pydantic/pull/6493)
* Remove the need for change files by @samuelcolvin in [#6556](https://github.com/pydantic/pydantic/pull/6556)
* add "north star" benchmark by @davidhewitt in [#6547](https://github.com/pydantic/pydantic/pull/6547)
* Update Dataclasses docs by @tpdorsey in [#6470](https://github.com/pydantic/pydantic/pull/6470)
* ♻️ Use different error message on v1 redirects by @Kludex in [#6595](https://github.com/pydantic/pydantic/pull/6595)
* ⬆ Upgrade `pydantic-core` to v2.2.0 by @lig in [#6589](https://github.com/pydantic/pydantic/pull/6589)
* Fix serialization for IPvAny by @dmontagu in [#6572](https://github.com/pydantic/pydantic/pull/6572)
* Improve CI by using PDM instead of pip to install typing-extensions by @adriangb in [#6602](https://github.com/pydantic/pydantic/pull/6602)
* Add `enum` error type docs  by @lig in [#6603](https://github.com/pydantic/pydantic/pull/6603)
* 🐛 Fix `max_length` for unicode strings by @lig in [#6559](https://github.com/pydantic/pydantic/pull/6559)
* Add documentation for accessing features via `pydantic.v1` by @tpdorsey in [#6604](https://github.com/pydantic/pydantic/pull/6604)
* Include extra when iterating over a model by @adriangb in [#6562](https://github.com/pydantic/pydantic/pull/6562)
* Fix typing of model_validator by @adriangb in [#6514](https://github.com/pydantic/pydantic/pull/6514)
* Touch up Decimal validator by @adriangb in [#6327](https://github.com/pydantic/pydantic/pull/6327)
* Fix various docstrings using fixed pytest-examples by @dmontagu in [#6607](https://github.com/pydantic/pydantic/pull/6607)
* Handle function validators in a discriminated union by @dmontagu in [#6570](https://github.com/pydantic/pydantic/pull/6570)
* Review json_schema.md by @tpdorsey in [#6608](https://github.com/pydantic/pydantic/pull/6608)
* Make validate_call work on basemodel methods by @dmontagu in [#6569](https://github.com/pydantic/pydantic/pull/6569)
* add test for big int json serde by @davidhewitt in [#6614](https://github.com/pydantic/pydantic/pull/6614)
* Fix pydantic dataclass problem with dataclasses.field default_factory by @hramezani in [#6616](https://github.com/pydantic/pydantic/pull/6616)
* Fixed mypy type inference for TypeAdapter by @zakstucke in [#6617](https://github.com/pydantic/pydantic/pull/6617)
* Make it work to use None as a generic parameter by @dmontagu in [#6609](https://github.com/pydantic/pydantic/pull/6609)
* Make it work to use `$ref` as an alias by @dmontagu in [#6568](https://github.com/pydantic/pydantic/pull/6568)
* add note to migration guide about changes to `AnyUrl` etc by @davidhewitt in [#6618](https://github.com/pydantic/pydantic/pull/6618)
* 🐛 Support defining `json_schema_extra` on `RootModel` using `Field` by @lig in [#6622](https://github.com/pydantic/pydantic/pull/6622)
* Update pre-commit to prevent commits to main branch on accident by @dmontagu in [#6636](https://github.com/pydantic/pydantic/pull/6636)
* Fix PDM CI for python 3.7 on MacOS/windows by @dmontagu in [#6627](https://github.com/pydantic/pydantic/pull/6627)
* Produce more accurate signatures for pydantic dataclasses by @dmontagu in [#6633](https://github.com/pydantic/pydantic/pull/6633)
* Updates to Url types for Pydantic V2 by @tpdorsey in [#6638](https://github.com/pydantic/pydantic/pull/6638)
* Fix list markdown in `transform` docstring by @StefanBRas in [#6649](https://github.com/pydantic/pydantic/pull/6649)
* simplify slots_dataclass construction to appease mypy by @davidhewitt in [#6639](https://github.com/pydantic/pydantic/pull/6639)
* Update TypedDict schema generation docstring by @adriangb in [#6651](https://github.com/pydantic/pydantic/pull/6651)
* Detect and lint-error for prints by @dmontagu in [#6655](https://github.com/pydantic/pydantic/pull/6655)
* Add xfailing test for pydantic-core PR 766 by @dmontagu in [#6641](https://github.com/pydantic/pydantic/pull/6641)
* Ignore unrecognized fields from dataclasses metadata by @dmontagu in [#6634](https://github.com/pydantic/pydantic/pull/6634)
* Make non-existent class getattr a mypy error by @dmontagu in [#6658](https://github.com/pydantic/pydantic/pull/6658)
* Update pydantic-core to 2.3.0 by @hramezani in [#6648](https://github.com/pydantic/pydantic/pull/6648)
* Use OrderedDict from typing_extensions by @dmontagu in [#6664](https://github.com/pydantic/pydantic/pull/6664)
* Fix typehint for JSON schema extra callable by @dmontagu in [#6659](https://github.com/pydantic/pydantic/pull/6659)

## v2.0.2 (2023-07-05)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.0.2)

* Fix bug where round-trip pickling/unpickling a `RootModel` would change the value of `__dict__`, [#6457](https://github.com/pydantic/pydantic/pull/6457) by @dmontagu
* Allow single-item discriminated unions, [#6405](https://github.com/pydantic/pydantic/pull/6405) by @dmontagu
* Fix issue with union parsing of enums, [#6440](https://github.com/pydantic/pydantic/pull/6440) by @dmontagu
* Docs: Fixed `constr` documentation, renamed old `regex` to new `pattern`, [#6452](https://github.com/pydantic/pydantic/pull/6452) by @miili
* Change `GenerateJsonSchema.generate_definitions` signature, [#6436](https://github.com/pydantic/pydantic/pull/6436) by @dmontagu

See the full changelog [here](https://github.com/pydantic/pydantic/releases/tag/v2.0.2)

## v2.0.1 (2023-07-04)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.0.1)

First patch release of Pydantic V2

* Extra fields added via `setattr` (i.e. `m.some_extra_field = 'extra_value'`)
  are added to `.model_extra` if `model_config` `extra='allowed'`. Fixed [#6333](https://github.com/pydantic/pydantic/pull/6333), [#6365](https://github.com/pydantic/pydantic/pull/6365) by @aaraney
* Automatically unpack JSON schema '$ref' for custom types, [#6343](https://github.com/pydantic/pydantic/pull/6343) by @adriangb
* Fix tagged unions multiple processing in submodels, [#6340](https://github.com/pydantic/pydantic/pull/6340) by @suharnikov

See the full changelog [here](https://github.com/pydantic/pydantic/releases/tag/v2.0.1)

## v2.0 (2023-06-30)

[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v2.0)

Pydantic V2 is here! :tada:

See [this post](https://docs.pydantic.dev/2.0/blog/pydantic-v2-final/) for more details.

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

<!-- package description limit -->

## v1.10.13 (2023-09-27)

* Fix: Add max length check to `pydantic.validate_email`, #7673 by @hramezani
* Docs: Fix pip commands to install v1, #6930 by @chbndrhnns

## v1.10.12 (2023-07-24)

* Fixes the `maxlen` property being dropped on `deque` validation. Happened only if the deque item has been typed. Changes the `_validate_sequence_like` func, [#6581](https://github.com/pydantic/pydantic/pull/6581) by @maciekglowka

## v1.10.11 (2023-07-04)

* Importing create_model in tools.py through relative path instead of absolute path - so that it doesn't import V2 code when copied over to V2 branch, [#6361](https://github.com/pydantic/pydantic/pull/6361) by @SharathHuddar

## v1.10.10 (2023-06-30)

* Add Pydantic `Json` field support to settings management, [#6250](https://github.com/pydantic/pydantic/pull/6250) by @hramezani
* Fixed literal validator errors for unhashable values, [#6188](https://github.com/pydantic/pydantic/pull/6188) by @markus1978
* Fixed bug with generics receiving forward refs, [#6130](https://github.com/pydantic/pydantic/pull/6130) by @mark-todd
* Update install method of FastAPI for internal tests in CI, [#6117](https://github.com/pydantic/pydantic/pull/6117) by @Kludex

## v1.10.9 (2023-06-07)

* Fix trailing zeros not ignored in Decimal validation, [#5968](https://github.com/pydantic/pydantic/pull/5968) by @hramezani
* Fix mypy plugin for v1.4.0, [#5928](https://github.com/pydantic/pydantic/pull/5928) by @cdce8p
* Add future and past date hypothesis strategies, [#5850](https://github.com/pydantic/pydantic/pull/5850) by @bschoenmaeckers
* Discourage usage of Cython 3 with Pydantic 1.x, [#5845](https://github.com/pydantic/pydantic/pull/5845) by @lig

## v1.10.8 (2023-05-23)

* Fix a bug in `Literal` usage with `typing-extension==4.6.0`, [#5826](https://github.com/pydantic/pydantic/pull/5826) by @hramezani
* This solves the (closed) issue [#3849](https://github.com/pydantic/pydantic/pull/3849) where aliased fields that use discriminated union fail to validate when the data contains the non-aliased field name, [#5736](https://github.com/pydantic/pydantic/pull/5736) by @benwah
* Update email-validator dependency to >=2.0.0post2, [#5627](https://github.com/pydantic/pydantic/pull/5627) by @adriangb
* update `AnyClassMethod` for changes in [python/typeshed#9771](https://github.com/python/typeshed/issues/9771), [#5505](https://github.com/pydantic/pydantic/pull/5505) by @ITProKyle

## v1.10.7 (2023-03-22)

* Fix creating schema from model using `ConstrainedStr` with `regex` as dict key, [#5223](https://github.com/pydantic/pydantic/pull/5223) by @matejetz
* Address bug in mypy plugin caused by explicit_package_bases=True, [#5191](https://github.com/pydantic/pydantic/pull/5191) by @dmontagu
* Add implicit defaults in the mypy plugin for Field with no default argument, [#5190](https://github.com/pydantic/pydantic/pull/5190) by @dmontagu
* Fix schema generated for Enum values used as Literals in discriminated unions, [#5188](https://github.com/pydantic/pydantic/pull/5188) by @javibookline
* Fix mypy failures caused by the pydantic mypy plugin when users define `from_orm` in their own classes, [#5187](https://github.com/pydantic/pydantic/pull/5187) by @dmontagu
* Fix `InitVar` usage with pydantic dataclasses, mypy version `1.1.1` and the custom mypy plugin, [#5162](https://github.com/pydantic/pydantic/pull/5162) by @cdce8p

## v1.10.6 (2023-03-08)

* Implement logic to support creating validators from non standard callables by using defaults to identify them and unwrapping `functools.partial` and `functools.partialmethod` when checking the signature, [#5126](https://github.com/pydantic/pydantic/pull/5126) by @JensHeinrich
* Fix mypy plugin for v1.1.1, and fix `dataclass_transform` decorator for pydantic dataclasses, [#5111](https://github.com/pydantic/pydantic/pull/5111) by @cdce8p
* Raise `ValidationError`, not `ConfigError`, when a discriminator value is unhashable, [#4773](https://github.com/pydantic/pydantic/pull/4773) by @kurtmckee

## v1.10.5 (2023-02-15)

* Fix broken parametrized bases handling with `GenericModel`s with complex sets of models, [#5052](https://github.com/pydantic/pydantic/pull/5052) by @MarkusSintonen
* Invalidate mypy cache if plugin config changes, [#5007](https://github.com/pydantic/pydantic/pull/5007) by @cdce8p
* Fix `RecursionError` when deep-copying dataclass types wrapped by pydantic, [#4949](https://github.com/pydantic/pydantic/pull/4949) by @mbillingr
* Fix `X | Y` union syntax breaking `GenericModel`, [#4146](https://github.com/pydantic/pydantic/pull/4146) by @thenx
* Switch coverage badge to show coverage for this branch/release, [#5060](https://github.com/pydantic/pydantic/pull/5060) by @samuelcolvin

## v1.10.4 (2022-12-30)

* Change dependency to `typing-extensions>=4.2.0`, [#4885](https://github.com/pydantic/pydantic/pull/4885) by @samuelcolvin

## v1.10.3 (2022-12-29)

**NOTE: v1.10.3 was ["yanked"](https://pypi.org/help/#yanked) from PyPI due to [#4885](https://github.com/pydantic/pydantic/pull/4885) which is fixed in v1.10.4**

* fix parsing of custom root models, [#4883](https://github.com/pydantic/pydantic/pull/4883) by @gou177
* fix: use dataclass proxy for frozen or empty dataclasses, [#4878](https://github.com/pydantic/pydantic/pull/4878) by @PrettyWood
* Fix `schema` and `schema_json` on models where a model instance is a one of default values, [#4781](https://github.com/pydantic/pydantic/pull/4781) by @Bobronium
* Add Jina AI to sponsors on docs index page, [#4767](https://github.com/pydantic/pydantic/pull/4767) by @samuelcolvin
* fix: support assignment on `DataclassProxy`, [#4695](https://github.com/pydantic/pydantic/pull/4695) by @PrettyWood
* Add `postgresql+psycopg` as allowed scheme for `PostgreDsn` to make it usable with SQLAlchemy 2, [#4689](https://github.com/pydantic/pydantic/pull/4689) by @morian
* Allow dict schemas to have both `patternProperties` and `additionalProperties`, [#4641](https://github.com/pydantic/pydantic/pull/4641) by @jparise
* Fixes error passing None for optional lists with `unique_items`, [#4568](https://github.com/pydantic/pydantic/pull/4568) by @mfulgo
* Fix `GenericModel` with `Callable` param raising a `TypeError`, [#4551](https://github.com/pydantic/pydantic/pull/4551) by @mfulgo
* Fix field regex with `StrictStr` type annotation, [#4538](https://github.com/pydantic/pydantic/pull/4538) by @sisp
* Correct `dataclass_transform` keyword argument name from `field_descriptors` to `field_specifiers`, [#4500](https://github.com/pydantic/pydantic/pull/4500) by @samuelcolvin
* fix: avoid multiple calls of `__post_init__` when dataclasses are inherited, [#4487](https://github.com/pydantic/pydantic/pull/4487) by @PrettyWood
* Reduce the size of binary wheels, [#2276](https://github.com/pydantic/pydantic/pull/2276) by @samuelcolvin

## v1.10.2 (2022-09-05)

* **Revert Change:** Revert percent encoding of URL parts which was originally added in [#4224](https://github.com/pydantic/pydantic/pull/4224), [#4470](https://github.com/pydantic/pydantic/pull/4470) by @samuelcolvin
* Prevent long (length > `4_300`) strings/bytes as input to int fields, see
  [python/cpython#95778](https://github.com/python/cpython/issues/95778) and
  [CVE-2020-10735](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-10735), [#1477](https://github.com/pydantic/pydantic/pull/1477) by @samuelcolvin
* fix: dataclass wrapper was not always called, [#4477](https://github.com/pydantic/pydantic/pull/4477) by @PrettyWood
* Use `tomllib` on Python 3.11 when parsing `mypy` configuration, [#4476](https://github.com/pydantic/pydantic/pull/4476) by @hauntsaninja
* Basic fix of `GenericModel` cache to detect order of arguments in `Union` models, [#4474](https://github.com/pydantic/pydantic/pull/4474) by @sveinugu
* Fix mypy plugin when using bare types like `list` and `dict` as `default_factory`, [#4457](https://github.com/pydantic/pydantic/pull/4457) by @samuelcolvin

## v1.10.1 (2022-08-31)

* Add `__hash__` method to `pydancic.color.Color` class, [#4454](https://github.com/pydantic/pydantic/pull/4454) by @czaki

## v1.10.0 (2022-08-30)

* Refactor the whole _pydantic_ `dataclass` decorator to really act like its standard lib equivalent.
  It hence keeps `__eq__`, `__hash__`, ... and makes comparison with its non-validated version possible.
  It also fixes usage of `frozen` dataclasses in fields and usage of `default_factory` in nested dataclasses.
  The support of `Config.extra` has been added.
  Finally, config customization directly via a `dict` is now possible, [#2557](https://github.com/pydantic/pydantic/pull/2557) by @PrettyWood
  <br/><br/>
  **BREAKING CHANGES:**
  - The `compiled` boolean (whether _pydantic_ is compiled with cython) has been moved from `main.py` to `version.py`
  - Now that `Config.extra` is supported, `dataclass` ignores by default extra arguments (like `BaseModel`)
* Fix PEP487 `__set_name__` protocol in `BaseModel` for PrivateAttrs, [#4407](https://github.com/pydantic/pydantic/pull/4407) by @tlambert03
* Allow for custom parsing of environment variables via `parse_env_var` in `Config`, [#4406](https://github.com/pydantic/pydantic/pull/4406) by @acmiyaguchi
* Rename `master` to `main`, [#4405](https://github.com/pydantic/pydantic/pull/4405) by @hramezani
* Fix `StrictStr` does not raise `ValidationError` when `max_length` is present in `Field`, [#4388](https://github.com/pydantic/pydantic/pull/4388) by @hramezani
* Make `SecretStr` and `SecretBytes` hashable, [#4387](https://github.com/pydantic/pydantic/pull/4387) by @chbndrhnns
* Fix `StrictBytes` does not raise `ValidationError` when `max_length` is present in `Field`, [#4380](https://github.com/pydantic/pydantic/pull/4380) by @JeanArhancet
* Add support for bare `type`, [#4375](https://github.com/pydantic/pydantic/pull/4375) by @hramezani
* Support Python 3.11, including binaries for 3.11 in PyPI, [#4374](https://github.com/pydantic/pydantic/pull/4374) by @samuelcolvin
* Add support for `re.Pattern`, [#4366](https://github.com/pydantic/pydantic/pull/4366) by @hramezani
* Fix `__post_init_post_parse__` is incorrectly passed keyword arguments when no `__post_init__` is defined, [#4361](https://github.com/pydantic/pydantic/pull/4361) by @hramezani
* Fix implicitly importing `ForwardRef` and `Callable` from `pydantic.typing` instead of `typing` and also expose `MappingIntStrAny`, [#4358](https://github.com/pydantic/pydantic/pull/4358) by @aminalaee
* remove `Any` types from the `dataclass` decorator so it can be used with the `disallow_any_expr` mypy option, [#4356](https://github.com/pydantic/pydantic/pull/4356) by @DetachHead
* moved repo to `pydantic/pydantic`, [#4348](https://github.com/pydantic/pydantic/pull/4348) by @yezz123
* fix "extra fields not permitted" error when dataclass with `Extra.forbid` is validated multiple times, [#4343](https://github.com/pydantic/pydantic/pull/4343) by @detachhead
* Add Python 3.9 and 3.10 examples to docs, [#4339](https://github.com/pydantic/pydantic/pull/4339) by @Bobronium
* Discriminated union models now use `oneOf` instead of `anyOf` when generating OpenAPI schema definitions, [#4335](https://github.com/pydantic/pydantic/pull/4335) by @MaxwellPayne
* Allow type checkers to infer inner type of `Json` type. `Json[list[str]]` will be now inferred as `list[str]`,
  `Json[Any]` should be used instead of plain `Json`.
  Runtime behaviour is not changed, [#4332](https://github.com/pydantic/pydantic/pull/4332) by @Bobronium
* Allow empty string aliases by using a `alias is not None` check, rather than `bool(alias)`, [#4253](https://github.com/pydantic/pydantic/pull/4253) by @sergeytsaplin
* Update `ForwardRef`s in `Field.outer_type_`, [#4249](https://github.com/pydantic/pydantic/pull/4249) by @JacobHayes
* The use of `__dataclass_transform__` has been replaced by `typing_extensions.dataclass_transform`, which is the preferred way to mark pydantic models as a dataclass under [PEP 681](https://peps.python.org/pep-0681/), [#4241](https://github.com/pydantic/pydantic/pull/4241) by @multimeric
* Use parent model's `Config` when validating nested `NamedTuple` fields, [#4219](https://github.com/pydantic/pydantic/pull/4219) by @synek
* Update `BaseModel.construct` to work with aliased Fields, [#4192](https://github.com/pydantic/pydantic/pull/4192) by @kylebamos
* Catch certain raised errors in `smart_deepcopy` and revert to `deepcopy` if so, [#4184](https://github.com/pydantic/pydantic/pull/4184) by @coneybeare
* Add `Config.anystr_upper` and `to_upper` kwarg to constr and conbytes, [#4165](https://github.com/pydantic/pydantic/pull/4165) by @satheler
* Fix JSON schema for `set` and `frozenset` when they include default values, [#4155](https://github.com/pydantic/pydantic/pull/4155) by @aminalaee
* Teach the mypy plugin that methods decorated by `@validator` are classmethods, [#4102](https://github.com/pydantic/pydantic/pull/4102) by @DMRobertson
* Improve mypy plugin's ability to detect required fields, [#4086](https://github.com/pydantic/pydantic/pull/4086) by @richardxia
* Support fields of type `Type[]` in schema, [#4051](https://github.com/pydantic/pydantic/pull/4051) by @aminalaee
* Add `default` value in JSON Schema when `const=True`, [#4031](https://github.com/pydantic/pydantic/pull/4031) by @aminalaee
* Adds reserved word check to signature generation logic, [#4011](https://github.com/pydantic/pydantic/pull/4011) by @strue36
* Fix Json strategy failure for the complex nested field, [#4005](https://github.com/pydantic/pydantic/pull/4005) by @sergiosim
* Add JSON-compatible float constraint `allow_inf_nan`, [#3994](https://github.com/pydantic/pydantic/pull/3994) by @tiangolo
* Remove undefined behaviour when `env_prefix` had characters in common with `env_nested_delimiter`, [#3975](https://github.com/pydantic/pydantic/pull/3975) by @arsenron
* Support generics model with `create_model`, [#3945](https://github.com/pydantic/pydantic/pull/3945) by @hot123s
* allow submodels to overwrite extra field info, [#3934](https://github.com/pydantic/pydantic/pull/3934) by @PrettyWood
* Document and test structural pattern matching ([PEP 636](https://peps.python.org/pep-0636/)) on `BaseModel`, [#3920](https://github.com/pydantic/pydantic/pull/3920) by @irgolic
* Fix incorrect deserialization of python timedelta object to ISO 8601 for negative time deltas.
  Minus was serialized in incorrect place ("P-1DT23H59M59.888735S" instead of correct "-P1DT23H59M59.888735S"), [#3899](https://github.com/pydantic/pydantic/pull/3899) by @07pepa
* Fix validation of discriminated union fields with an alias when passing a model instance, [#3846](https://github.com/pydantic/pydantic/pull/3846) by @chornsby
* Add a CockroachDsn type to validate CockroachDB connection strings. The type
  supports the following schemes: `cockroachdb`, `cockroachdb+psycopg2` and `cockroachdb+asyncpg`, [#3839](https://github.com/pydantic/pydantic/pull/3839) by @blubber
* Fix MyPy plugin to not override pre-existing `__init__` method in models, [#3824](https://github.com/pydantic/pydantic/pull/3824) by @patrick91
* Fix mypy version checking, [#3783](https://github.com/pydantic/pydantic/pull/3783) by @KotlinIsland
* support overwriting dunder attributes of `BaseModel` instances, [#3777](https://github.com/pydantic/pydantic/pull/3777) by @PrettyWood
* Added `ConstrainedDate` and `condate`, [#3740](https://github.com/pydantic/pydantic/pull/3740) by @hottwaj
* Support `kw_only` in dataclasses, [#3670](https://github.com/pydantic/pydantic/pull/3670) by @detachhead
* Add comparison method for `Color` class, [#3646](https://github.com/pydantic/pydantic/pull/3646) by @aminalaee
* Drop support for python3.6, associated cleanup, [#3605](https://github.com/pydantic/pydantic/pull/3605) by @samuelcolvin
* created new function `to_lower_camel()` for "non pascal case" camel case, [#3463](https://github.com/pydantic/pydantic/pull/3463) by @schlerp
* Add checks to `default` and `default_factory` arguments in Mypy plugin, [#3430](https://github.com/pydantic/pydantic/pull/3430) by @klaa97
* fix mangling of `inspect.signature` for `BaseModel`, [#3413](https://github.com/pydantic/pydantic/pull/3413) by @fix-inspect-signature
* Adds the `SecretField` abstract class so that all the current and future secret fields like `SecretStr` and `SecretBytes` will derive from it, [#3409](https://github.com/pydantic/pydantic/pull/3409) by @expobrain
* Support multi hosts validation in `PostgresDsn`, [#3337](https://github.com/pydantic/pydantic/pull/3337) by @rglsk
* Fix parsing of very small numeric timedelta values, [#3315](https://github.com/pydantic/pydantic/pull/3315) by @samuelcolvin
* Update `SecretsSettingsSource` to respect `config.case_sensitive`, [#3273](https://github.com/pydantic/pydantic/pull/3273) by @JeanArhancet
* Add MongoDB network data source name (DSN) schema, [#3229](https://github.com/pydantic/pydantic/pull/3229) by @snosratiershad
* Add support for multiple dotenv files, [#3222](https://github.com/pydantic/pydantic/pull/3222) by @rekyungmin
* Raise an explicit `ConfigError` when multiple fields are incorrectly set for a single validator, [#3215](https://github.com/pydantic/pydantic/pull/3215) by @SunsetOrange
* Allow ellipsis on `Field`s inside `Annotated` for `TypedDicts` required, [#3133](https://github.com/pydantic/pydantic/pull/3133) by @ezegomez
* Catch overflow errors in `int_validator`, [#3112](https://github.com/pydantic/pydantic/pull/3112) by @ojii
* Adds a `__rich_repr__` method to `Representation` class which enables pretty printing with [Rich](https://github.com/willmcgugan/rich), [#3099](https://github.com/pydantic/pydantic/pull/3099) by @willmcgugan
* Add percent encoding in `AnyUrl` and descendent types, [#3061](https://github.com/pydantic/pydantic/pull/3061) by @FaresAhmedb
* `validate_arguments` decorator now supports `alias`, [#3019](https://github.com/pydantic/pydantic/pull/3019) by @MAD-py
* Avoid `__dict__` and `__weakref__` attributes in `AnyUrl` and IP address fields, [#2890](https://github.com/pydantic/pydantic/pull/2890) by @nuno-andre
* Add ability to use `Final` in a field type annotation, [#2766](https://github.com/pydantic/pydantic/pull/2766) by @uriyyo
* Update requirement to `typing_extensions>=4.1.0` to guarantee `dataclass_transform` is available, [#4424](https://github.com/pydantic/pydantic/pull/4424) by @commonism
* Add Explosion and AWS to main sponsors, [#4413](https://github.com/pydantic/pydantic/pull/4413) by @samuelcolvin
* Update documentation for `copy_on_model_validation` to reflect recent changes, [#4369](https://github.com/pydantic/pydantic/pull/4369) by @samuelcolvin
* Runtime warning if `__slots__` is passed to `create_model`, `__slots__` is then ignored, [#4432](https://github.com/pydantic/pydantic/pull/4432) by @samuelcolvin
* Add type hints to `BaseSettings.Config` to avoid mypy errors, also correct mypy version compatibility notice in docs, [#4450](https://github.com/pydantic/pydantic/pull/4450) by @samuelcolvin

## v1.10.0b1 (2022-08-24)

Pre-release, see [the GitHub release](https://github.com/pydantic/pydantic/releases/tag/v1.10.0b1) for details.

## v1.10.0a2 (2022-08-24)

Pre-release, see [the GitHub release](https://github.com/pydantic/pydantic/releases/tag/v1.10.0a2) for details.

## v1.10.0a1 (2022-08-22)

Pre-release, see [the GitHub release](https://github.com/pydantic/pydantic/releases/tag/v1.10.0a1) for details.

## v1.9.2 (2022-08-11)

**Revert Breaking Change**: _v1.9.1_ introduced a breaking change where model fields were
deep copied by default, this release reverts the default behaviour to match _v1.9.0_ and before,
while also allow deep-copy behaviour via `copy_on_model_validation = 'deep'`. See [#4092](https://github.com/pydantic/pydantic/pull/4092) for more information.

* Allow for shallow copies of model fields, `Config.copy_on_model_validation` is now a str which must be
  `'none'`, `'deep'`, or `'shallow'` corresponding to not copying, deep copy & shallow copy; default `'shallow'`,
  [#4093](https://github.com/pydantic/pydantic/pull/4093) by @timkpaine

## v1.9.1 (2022-05-19)

Thank you to pydantic's sponsors:
@tiangolo, @stellargraph, @JonasKs, @grillazz, @Mazyod, @kevinalh, @chdsbd, @povilasb, @povilasb, @jina-ai,
@mainframeindustries, @robusta-dev, @SendCloud, @rszamszur, @jodal, @hardbyte, @corleyma, @daddycocoaman,
@Rehket, @jokull, @reillysiemens, @westonsteimel, @primer-io, @koxudaxi, @browniebroke, @stradivari96,
@adriangb, @kamalgill, @jqueguiner, @dev-zero, @datarootsio, @RedCarpetUp
for their kind support.

* Limit the size of `generics._generic_types_cache` and `generics._assigned_parameters`
  to avoid unlimited increase in memory usage, [#4083](https://github.com/pydantic/pydantic/pull/4083) by @samuelcolvin
* Add Jupyverse and FPS as Jupyter projects using pydantic, [#4082](https://github.com/pydantic/pydantic/pull/4082) by @davidbrochart
* Speedup `__isinstancecheck__` on pydantic models when the type is not a model, may also avoid memory "leaks", [#4081](https://github.com/pydantic/pydantic/pull/4081) by @samuelcolvin
* Fix in-place modification of `FieldInfo` that caused problems with PEP 593 type aliases, [#4067](https://github.com/pydantic/pydantic/pull/4067) by @adriangb
* Add support for autocomplete in VS Code via `__dataclass_transform__` when using `pydantic.dataclasses.dataclass`, [#4006](https://github.com/pydantic/pydantic/pull/4006) by @giuliano-oliveira
* Remove benchmarks from codebase and docs, [#3973](https://github.com/pydantic/pydantic/pull/3973) by @samuelcolvin
* Typing checking with pyright in CI, improve docs on vscode/pylance/pyright, [#3972](https://github.com/pydantic/pydantic/pull/3972) by @samuelcolvin
* Fix nested Python dataclass schema regression, [#3819](https://github.com/pydantic/pydantic/pull/3819) by @himbeles
* Update documentation about lazy evaluation of sources for Settings, [#3806](https://github.com/pydantic/pydantic/pull/3806) by @garyd203
* Prevent subclasses of bytes being converted to bytes, [#3706](https://github.com/pydantic/pydantic/pull/3706) by @samuelcolvin
* Fixed "error checking inheritance of" when using PEP585 and PEP604 type hints, [#3681](https://github.com/pydantic/pydantic/pull/3681) by @aleksul
* Allow self referencing `ClassVar`s in models, [#3679](https://github.com/pydantic/pydantic/pull/3679) by @samuelcolvin
* **Breaking Change, see [#4106](https://github.com/pydantic/pydantic/pull/4106)**: Fix issue with self-referencing dataclass, [#3675](https://github.com/pydantic/pydantic/pull/3675) by @uriyyo
* Include non-standard port numbers in rendered URLs, [#3652](https://github.com/pydantic/pydantic/pull/3652) by @dolfinus
* `Config.copy_on_model_validation` does a deep copy and not a shallow one, [#3641](https://github.com/pydantic/pydantic/pull/3641) by @PrettyWood
* fix: clarify that discriminated unions do not support singletons, [#3636](https://github.com/pydantic/pydantic/pull/3636) by @tommilligan
* Add `read_text(encoding='utf-8')` for `setup.py`, [#3625](https://github.com/pydantic/pydantic/pull/3625) by @hswong3i
* Fix JSON Schema generation for Discriminated Unions within lists, [#3608](https://github.com/pydantic/pydantic/pull/3608) by @samuelcolvin

## v1.9.0 (2021-12-31)

Thank you to pydantic's sponsors:
@sthagen, @timdrijvers, @toinbis, @koxudaxi, @ginomempin, @primer-io, @and-semakin, @westonsteimel, @reillysiemens,
@es3n1n, @jokull, @JonasKs, @Rehket, @corleyma, @daddycocoaman, @hardbyte, @datarootsio, @jodal, @aminalaee, @rafsaf,
@jqueguiner, @chdsbd, @kevinalh, @Mazyod, @grillazz, @JonasKs, @simw, @leynier, @xfenix
for their kind support.

### Highlights

* add Python 3.10 support, [#2885](https://github.com/pydantic/pydantic/pull/2885) by @PrettyWood
* [Discriminated unions](https://docs.pydantic.dev/usage/types/#discriminated-unions-aka-tagged-unions), [#619](https://github.com/pydantic/pydantic/pull/619) by @PrettyWood
* [`Config.smart_union` for better union logic](https://docs.pydantic.dev/usage/model_config/#smart-union), [#2092](https://github.com/pydantic/pydantic/pull/2092) by @PrettyWood
* Binaries for Macos M1 CPUs, [#3498](https://github.com/pydantic/pydantic/pull/3498) by @samuelcolvin
* Complex types can be set via [nested environment variables](https://docs.pydantic.dev/usage/settings/#parsing-environment-variable-values), e.g. `foo___bar`, [#3159](https://github.com/pydantic/pydantic/pull/3159) by @Air-Mark
* add a dark mode to _pydantic_ documentation, [#2913](https://github.com/pydantic/pydantic/pull/2913) by @gbdlin
* Add support for autocomplete in VS Code via `__dataclass_transform__`, [#2721](https://github.com/pydantic/pydantic/pull/2721) by @tiangolo
* Add "exclude" as a field parameter so that it can be configured using model config, [#660](https://github.com/pydantic/pydantic/pull/660) by @daviskirk

### v1.9.0 (2021-12-31) Changes

* Apply `update_forward_refs` to `Config.json_encodes` prevent name clashes in types defined via strings, [#3583](https://github.com/pydantic/pydantic/pull/3583) by @samuelcolvin
* Extend pydantic's mypy plugin to support mypy versions `0.910`, `0.920`, `0.921` & `0.930`, [#3573](https://github.com/pydantic/pydantic/pull/3573) & [#3594](https://github.com/pydantic/pydantic/pull/3594) by @PrettyWood, @christianbundy, @samuelcolvin

### v1.9.0a2 (2021-12-24) Changes

* support generic models with discriminated union, [#3551](https://github.com/pydantic/pydantic/pull/3551) by @PrettyWood
* keep old behaviour of `json()` by default, [#3542](https://github.com/pydantic/pydantic/pull/3542) by @PrettyWood
* Removed typing-only `__root__` attribute from `BaseModel`, [#3540](https://github.com/pydantic/pydantic/pull/3540) by @layday
* Build Python 3.10 wheels, [#3539](https://github.com/pydantic/pydantic/pull/3539) by @mbachry
* Fix display of `extra` fields with model `__repr__`, [#3234](https://github.com/pydantic/pydantic/pull/3234) by @cocolman
* models copied via `Config.copy_on_model_validation` always have all fields, [#3201](https://github.com/pydantic/pydantic/pull/3201) by @PrettyWood
* nested ORM from nested dictionaries, [#3182](https://github.com/pydantic/pydantic/pull/3182) by @PrettyWood
* fix link to discriminated union section by @PrettyWood

### v1.9.0a1 (2021-12-18) Changes

* Add support for `Decimal`-specific validation configurations in `Field()`, additionally to using `condecimal()`,
  to allow better support from editors and tooling, [#3507](https://github.com/pydantic/pydantic/pull/3507) by @tiangolo
* Add `arm64` binaries suitable for MacOS with an M1 CPU to PyPI, [#3498](https://github.com/pydantic/pydantic/pull/3498) by @samuelcolvin
* Fix issue where `None` was considered invalid when using a `Union` type containing `Any` or `object`, [#3444](https://github.com/pydantic/pydantic/pull/3444) by @tharradine
* When generating field schema, pass optional `field` argument (of type
  `pydantic.fields.ModelField`) to `__modify_schema__()` if present, [#3434](https://github.com/pydantic/pydantic/pull/3434) by @jasujm
* Fix issue when pydantic fail to parse `typing.ClassVar` string type annotation, [#3401](https://github.com/pydantic/pydantic/pull/3401) by @uriyyo
* Mention Python >= 3.9.2 as an alternative to `typing_extensions.TypedDict`, [#3374](https://github.com/pydantic/pydantic/pull/3374) by @BvB93
* Changed the validator method name in the [Custom Errors example](https://docs.pydantic.dev/usage/models/#custom-errors)
  to more accurately describe what the validator is doing; changed from `name_must_contain_space` to ` value_must_equal_bar`, [#3327](https://github.com/pydantic/pydantic/pull/3327) by @michaelrios28
* Add `AmqpDsn` class, [#3254](https://github.com/pydantic/pydantic/pull/3254) by @kludex
* Always use `Enum` value as default in generated JSON schema, [#3190](https://github.com/pydantic/pydantic/pull/3190) by @joaommartins
* Add support for Mypy 0.920, [#3175](https://github.com/pydantic/pydantic/pull/3175) by @christianbundy
* `validate_arguments` now supports `extra` customization (used to always be `Extra.forbid`), [#3161](https://github.com/pydantic/pydantic/pull/3161) by @PrettyWood
* Complex types can be set by nested environment variables, [#3159](https://github.com/pydantic/pydantic/pull/3159) by @Air-Mark
* Fix mypy plugin to collect fields based on `pydantic.utils.is_valid_field` so that it ignores untyped private variables, [#3146](https://github.com/pydantic/pydantic/pull/3146) by @hi-ogawa
* fix `validate_arguments` issue with `Config.validate_all`, [#3135](https://github.com/pydantic/pydantic/pull/3135) by @PrettyWood
* avoid dict coercion when using dict subclasses as field type, [#3122](https://github.com/pydantic/pydantic/pull/3122) by @PrettyWood
* add support for `object` type, [#3062](https://github.com/pydantic/pydantic/pull/3062) by @PrettyWood
* Updates pydantic dataclasses to keep `_special` properties on parent classes, [#3043](https://github.com/pydantic/pydantic/pull/3043) by @zulrang
* Add a `TypedDict` class for error objects, [#3038](https://github.com/pydantic/pydantic/pull/3038) by @matthewhughes934
* Fix support for using a subclass of an annotation as a default, [#3018](https://github.com/pydantic/pydantic/pull/3018) by @JacobHayes
* make `create_model_from_typeddict` mypy compliant, [#3008](https://github.com/pydantic/pydantic/pull/3008) by @PrettyWood
* Make multiple inheritance work when using `PrivateAttr`, [#2989](https://github.com/pydantic/pydantic/pull/2989) by @hmvp
* Parse environment variables as JSON, if they have a `Union` type with a complex subfield, [#2936](https://github.com/pydantic/pydantic/pull/2936) by @cbartz
* Prevent `StrictStr` permitting `Enum` values where the enum inherits from `str`, [#2929](https://github.com/pydantic/pydantic/pull/2929) by @samuelcolvin
* Make `SecretsSettingsSource` parse values being assigned to fields of complex types when sourced from a secrets file,
  just as when sourced from environment variables, [#2917](https://github.com/pydantic/pydantic/pull/2917) by @davidmreed
* add a dark mode to _pydantic_ documentation, [#2913](https://github.com/pydantic/pydantic/pull/2913) by @gbdlin
* Make `pydantic-mypy` plugin compatible with `pyproject.toml` configuration, consistent with `mypy` changes.
  See the [doc](https://docs.pydantic.dev/mypy_plugin/#configuring-the-plugin) for more information, [#2908](https://github.com/pydantic/pydantic/pull/2908) by @jrwalk
* add Python 3.10 support, [#2885](https://github.com/pydantic/pydantic/pull/2885) by @PrettyWood
* Correctly parse generic models with `Json[T]`, [#2860](https://github.com/pydantic/pydantic/pull/2860) by @geekingfrog
* Update contrib docs re: Python version to use for building docs, [#2856](https://github.com/pydantic/pydantic/pull/2856) by @paxcodes
* Clarify documentation about _pydantic_'s support for custom validation and strict type checking,
  despite _pydantic_ being primarily a parsing library, [#2855](https://github.com/pydantic/pydantic/pull/2855) by @paxcodes
* Fix schema generation for `Deque` fields, [#2810](https://github.com/pydantic/pydantic/pull/2810) by @sergejkozin
* fix an edge case when mixing constraints and `Literal`, [#2794](https://github.com/pydantic/pydantic/pull/2794) by @PrettyWood
* Fix postponed annotation resolution for `NamedTuple` and `TypedDict` when they're used directly as the type of fields
  within Pydantic models, [#2760](https://github.com/pydantic/pydantic/pull/2760) by @jameysharp
* Fix bug when `mypy` plugin fails on `construct` method call for `BaseSettings` derived classes, [#2753](https://github.com/pydantic/pydantic/pull/2753) by @uriyyo
* Add function overloading for a `pydantic.create_model` function, [#2748](https://github.com/pydantic/pydantic/pull/2748) by @uriyyo
* Fix mypy plugin issue with self field declaration, [#2743](https://github.com/pydantic/pydantic/pull/2743) by @uriyyo
* The colon at the end of the line "The fields which were supplied when user was initialised:" suggests that the code following it is related.
  Changed it to a period, [#2733](https://github.com/pydantic/pydantic/pull/2733) by @krisaoe
* Renamed variable `schema` to `schema_` to avoid shadowing of global variable name, [#2724](https://github.com/pydantic/pydantic/pull/2724) by @shahriyarr
* Add support for autocomplete in VS Code via `__dataclass_transform__`, [#2721](https://github.com/pydantic/pydantic/pull/2721) by @tiangolo
* add missing type annotations in `BaseConfig` and handle `max_length = 0`, [#2719](https://github.com/pydantic/pydantic/pull/2719) by @PrettyWood
* Change `orm_mode` checking to allow recursive ORM mode parsing with dicts, [#2718](https://github.com/pydantic/pydantic/pull/2718) by @nuno-andre
* Add episode 313 of the *Talk Python To Me* podcast, where Michael Kennedy and Samuel Colvin discuss Pydantic, to the docs, [#2712](https://github.com/pydantic/pydantic/pull/2712) by @RatulMaharaj
* fix JSON schema generation when a field is of type `NamedTuple` and has a default value, [#2707](https://github.com/pydantic/pydantic/pull/2707) by @PrettyWood
* `Enum` fields now properly support extra kwargs in schema generation, [#2697](https://github.com/pydantic/pydantic/pull/2697) by @sammchardy
* **Breaking Change, see [#3780](https://github.com/pydantic/pydantic/pull/3780)**: Make serialization of referenced pydantic models possible, [#2650](https://github.com/pydantic/pydantic/pull/2650) by @PrettyWood
* Add `uniqueItems` option to `ConstrainedList`, [#2618](https://github.com/pydantic/pydantic/pull/2618) by @nuno-andre
* Try to evaluate forward refs automatically at model creation, [#2588](https://github.com/pydantic/pydantic/pull/2588) by @uriyyo
* Switch docs preview and coverage display to use [smokeshow](https://smokeshow.helpmanual.io/), [#2580](https://github.com/pydantic/pydantic/pull/2580) by @samuelcolvin
* Add `__version__` attribute to pydantic module, [#2572](https://github.com/pydantic/pydantic/pull/2572) by @paxcodes
* Add `postgresql+asyncpg`, `postgresql+pg8000`, `postgresql+psycopg2`, `postgresql+psycopg2cffi`, `postgresql+py-postgresql`
  and `postgresql+pygresql` schemes for `PostgresDsn`, [#2567](https://github.com/pydantic/pydantic/pull/2567) by @postgres-asyncpg
* Enable the Hypothesis plugin to generate a constrained decimal when the `decimal_places` argument is specified, [#2524](https://github.com/pydantic/pydantic/pull/2524) by @cwe5590
* Allow `collections.abc.Callable` to be used as type in Python 3.9, [#2519](https://github.com/pydantic/pydantic/pull/2519) by @daviskirk
* Documentation update how to custom compile pydantic when using pip install, small change in `setup.py`
  to allow for custom CFLAGS when compiling, [#2517](https://github.com/pydantic/pydantic/pull/2517) by @peterroelants
* remove side effect of `default_factory` to run it only once even if `Config.validate_all` is set, [#2515](https://github.com/pydantic/pydantic/pull/2515) by @PrettyWood
* Add lookahead to ip regexes for `AnyUrl` hosts. This allows urls with DNS labels
  looking like IPs to validate as they are perfectly valid host names, [#2512](https://github.com/pydantic/pydantic/pull/2512) by @sbv-csis
* Set `minItems` and `maxItems` in generated JSON schema for fixed-length tuples, [#2497](https://github.com/pydantic/pydantic/pull/2497) by @PrettyWood
* Add `strict` argument to `conbytes`, [#2489](https://github.com/pydantic/pydantic/pull/2489) by @koxudaxi
* Support user defined generic field types in generic models, [#2465](https://github.com/pydantic/pydantic/pull/2465) by @daviskirk
* Add an example and a short explanation of subclassing `GetterDict` to docs, [#2463](https://github.com/pydantic/pydantic/pull/2463) by @nuno-andre
* add `KafkaDsn` type, `HttpUrl` now has default port 80 for http and 443 for https, [#2447](https://github.com/pydantic/pydantic/pull/2447) by @MihanixA
* Add `PastDate` and `FutureDate` types, [#2425](https://github.com/pydantic/pydantic/pull/2425) by @Kludex
* Support generating schema for `Generic` fields with subtypes, [#2375](https://github.com/pydantic/pydantic/pull/2375) by @maximberg
* fix(encoder): serialize `NameEmail` to str, [#2341](https://github.com/pydantic/pydantic/pull/2341) by @alecgerona
* add `Config.smart_union` to prevent coercion in `Union` if possible, see
 [the doc](https://docs.pydantic.dev/usage/model_config/#smart-union) for more information, [#2092](https://github.com/pydantic/pydantic/pull/2092) by @PrettyWood
* Add ability to use `typing.Counter` as a model field type, [#2060](https://github.com/pydantic/pydantic/pull/2060) by @uriyyo
* Add parameterised subclasses to `__bases__` when constructing new parameterised classes, so that `A <: B => A[int] <: B[int]`, [#2007](https://github.com/pydantic/pydantic/pull/2007) by @diabolo-dan
* Create `FileUrl` type that allows URLs that conform to [RFC 8089](https://tools.ietf.org/html/rfc8089#section-2).
  Add `host_required` parameter, which is `True` by default (`AnyUrl` and subclasses), `False` in `RedisDsn`, `FileUrl`, [#1983](https://github.com/pydantic/pydantic/pull/1983) by @vgerak
* add `confrozenset()`, analogous to `conset()` and `conlist()`, [#1897](https://github.com/pydantic/pydantic/pull/1897) by @PrettyWood
* stop calling parent class `root_validator` if overridden, [#1895](https://github.com/pydantic/pydantic/pull/1895) by @PrettyWood
* Add `repr` (defaults to `True`) parameter to `Field`, to hide it from the default representation of the `BaseModel`, [#1831](https://github.com/pydantic/pydantic/pull/1831) by @fnep
* Accept empty query/fragment URL parts, [#1807](https://github.com/pydantic/pydantic/pull/1807) by @xavier

## v1.8.2 (2021-05-11)

!!! warning
    A security vulnerability, level "moderate" is fixed in v1.8.2. Please upgrade **ASAP**.
    See security advisory [CVE-2021-29510](https://github.com/pydantic/pydantic/security/advisories/GHSA-5jqp-qgf6-3pvh)

* **Security fix:** Fix `date` and `datetime` parsing so passing either `'infinity'` or `float('inf')`
  (or their negative values) does not cause an infinite loop,
  see security advisory [CVE-2021-29510](https://github.com/pydantic/pydantic/security/advisories/GHSA-5jqp-qgf6-3pvh)
* fix schema generation with Enum by generating a valid name, [#2575](https://github.com/pydantic/pydantic/pull/2575) by @PrettyWood
* fix JSON schema generation with a `Literal` of an enum member, [#2536](https://github.com/pydantic/pydantic/pull/2536) by @PrettyWood
* Fix bug with configurations declarations that are passed as
  keyword arguments during class creation, [#2532](https://github.com/pydantic/pydantic/pull/2532) by @uriyyo
* Allow passing `json_encoders` in class kwargs, [#2521](https://github.com/pydantic/pydantic/pull/2521) by @layday
* support arbitrary types with custom `__eq__`, [#2483](https://github.com/pydantic/pydantic/pull/2483) by @PrettyWood
* support `Annotated` in `validate_arguments` and in generic models with Python 3.9, [#2483](https://github.com/pydantic/pydantic/pull/2483) by @PrettyWood

## v1.8.1 (2021-03-03)

Bug fixes for regressions and new features from `v1.8`

* allow elements of `Config.field` to update elements of a `Field`, [#2461](https://github.com/pydantic/pydantic/pull/2461) by @samuelcolvin
* fix validation with a `BaseModel` field and a custom root type, [#2449](https://github.com/pydantic/pydantic/pull/2449) by @PrettyWood
* expose `Pattern` encoder to `fastapi`, [#2444](https://github.com/pydantic/pydantic/pull/2444) by @PrettyWood
* enable the Hypothesis plugin to generate a constrained float when the `multiple_of` argument is specified, [#2442](https://github.com/pydantic/pydantic/pull/2442) by @tobi-lipede-oodle
* Avoid `RecursionError` when using some types like `Enum` or `Literal` with generic models, [#2436](https://github.com/pydantic/pydantic/pull/2436) by @PrettyWood
* do not overwrite declared `__hash__` in subclasses of a model, [#2422](https://github.com/pydantic/pydantic/pull/2422) by @PrettyWood
* fix `mypy` complaints on `Path` and `UUID` related custom types, [#2418](https://github.com/pydantic/pydantic/pull/2418) by @PrettyWood
* Support properly variable length tuples of compound types, [#2416](https://github.com/pydantic/pydantic/pull/2416) by @PrettyWood

## v1.8 (2021-02-26)

Thank you to pydantic's sponsors:
@jorgecarleitao, @BCarley, @chdsbd, @tiangolo, @matin, @linusg, @kevinalh, @koxudaxi, @timdrijvers, @mkeen, @meadsteve,
@ginomempin, @primer-io, @and-semakin, @tomthorogood, @AjitZK, @westonsteimel, @Mazyod, @christippett, @CarlosDomingues,
@Kludex, @r-m-n
for their kind support.

### Highlights

* [Hypothesis plugin](https://docs.pydantic.dev/hypothesis_plugin/) for testing, [#2097](https://github.com/pydantic/pydantic/pull/2097) by @Zac-HD
* support for [`NamedTuple` and `TypedDict`](https://docs.pydantic.dev/usage/types/#annotated-types), [#2216](https://github.com/pydantic/pydantic/pull/2216) by @PrettyWood
* Support [`Annotated` hints on model fields](https://docs.pydantic.dev/usage/schema/#typingannotated-fields), [#2147](https://github.com/pydantic/pydantic/pull/2147) by @JacobHayes
* [`frozen` parameter on `Config`](https://docs.pydantic.dev/usage/model_config/) to allow models to be hashed, [#1880](https://github.com/pydantic/pydantic/pull/1880) by @rhuille

### Changes

* **Breaking Change**, remove old deprecation aliases from v1, [#2415](https://github.com/pydantic/pydantic/pull/2415) by @samuelcolvin:
  * remove notes on migrating to v1 in docs
  * remove `Schema` which was replaced by `Field`
  * remove `Config.case_insensitive` which was replaced by `Config.case_sensitive` (default `False`)
  * remove `Config.allow_population_by_alias` which was replaced by `Config.allow_population_by_field_name`
  * remove `model.fields` which was replaced by `model.__fields__`
  * remove `model.to_string()` which was replaced by `str(model)`
  * remove `model.__values__` which was replaced by `model.__dict__`
* **Breaking Change:** always validate only first sublevel items with `each_item`.
  There were indeed some edge cases with some compound types where the validated items were the last sublevel ones, [#1933](https://github.com/pydantic/pydantic/pull/1933) by @PrettyWood
* Update docs extensions to fix local syntax highlighting, [#2400](https://github.com/pydantic/pydantic/pull/2400) by @daviskirk
* fix: allow `utils.lenient_issubclass` to handle `typing.GenericAlias` objects like `list[str]` in Python >= 3.9, [#2399](https://github.com/pydantic/pydantic/pull/2399) by @daviskirk
* Improve field declaration for _pydantic_ `dataclass` by allowing the usage of _pydantic_ `Field` or `'metadata'` kwarg of `dataclasses.field`, [#2384](https://github.com/pydantic/pydantic/pull/2384) by @PrettyWood
* Making `typing-extensions` a required dependency, [#2368](https://github.com/pydantic/pydantic/pull/2368) by @samuelcolvin
* Make `resolve_annotations` more lenient, allowing for missing modules, [#2363](https://github.com/pydantic/pydantic/pull/2363) by @samuelcolvin
* Allow configuring models through class kwargs, [#2356](https://github.com/pydantic/pydantic/pull/2356) by @Bobronium
* Prevent `Mapping` subclasses from always being coerced to `dict`, [#2325](https://github.com/pydantic/pydantic/pull/2325) by @ofek
* fix: allow `None` for type `Optional[conset / conlist]`, [#2320](https://github.com/pydantic/pydantic/pull/2320) by @PrettyWood
* Support empty tuple type, [#2318](https://github.com/pydantic/pydantic/pull/2318) by @PrettyWood
* fix: `python_requires` metadata to require >=3.6.1, [#2306](https://github.com/pydantic/pydantic/pull/2306) by @hukkinj1
* Properly encode `Decimal` with, or without any decimal places, [#2293](https://github.com/pydantic/pydantic/pull/2293) by @hultner
* fix: update `__fields_set__` in `BaseModel.copy(update=…)`, [#2290](https://github.com/pydantic/pydantic/pull/2290) by @PrettyWood
* fix: keep order of fields with `BaseModel.construct()`, [#2281](https://github.com/pydantic/pydantic/pull/2281) by @PrettyWood
* Support generating schema for Generic fields, [#2262](https://github.com/pydantic/pydantic/pull/2262) by @maximberg
* Fix `validate_decorator` so `**kwargs` doesn't exclude values when the keyword
  has the same name as the `*args` or `**kwargs` names, [#2251](https://github.com/pydantic/pydantic/pull/2251) by @cybojenix
* Prevent overriding positional arguments with keyword arguments in
  `validate_arguments`, as per behaviour with native functions, [#2249](https://github.com/pydantic/pydantic/pull/2249) by @cybojenix
* add documentation for `con*` type functions, [#2242](https://github.com/pydantic/pydantic/pull/2242) by @tayoogunbiyi
* Support custom root type (aka `__root__`) when using `parse_obj()` with nested models, [#2238](https://github.com/pydantic/pydantic/pull/2238) by @PrettyWood
* Support custom root type (aka `__root__`) with `from_orm()`, [#2237](https://github.com/pydantic/pydantic/pull/2237) by @PrettyWood
* ensure cythonized functions are left untouched when creating models, based on [#1944](https://github.com/pydantic/pydantic/pull/1944) by @kollmats, [#2228](https://github.com/pydantic/pydantic/pull/2228) by @samuelcolvin
* Resolve forward refs for stdlib dataclasses converted into _pydantic_ ones, [#2220](https://github.com/pydantic/pydantic/pull/2220) by @PrettyWood
* Add support for `NamedTuple` and `TypedDict` types.
  Those two types are now handled and validated when used inside `BaseModel` or _pydantic_ `dataclass`.
  Two utils are also added `create_model_from_namedtuple` and `create_model_from_typeddict`, [#2216](https://github.com/pydantic/pydantic/pull/2216) by @PrettyWood
* Do not ignore annotated fields when type is `Union[Type[...], ...]`, [#2213](https://github.com/pydantic/pydantic/pull/2213) by @PrettyWood
* Raise a user-friendly `TypeError` when a `root_validator` does not return a `dict` (e.g. `None`), [#2209](https://github.com/pydantic/pydantic/pull/2209) by @masalim2
* Add a `FrozenSet[str]` type annotation to the `allowed_schemes` argument on the `strict_url` field type, [#2198](https://github.com/pydantic/pydantic/pull/2198) by @Midnighter
* add `allow_mutation` constraint to `Field`, [#2195](https://github.com/pydantic/pydantic/pull/2195) by @sblack-usu
* Allow `Field` with a `default_factory` to be used as an argument to a function
  decorated with `validate_arguments`, [#2176](https://github.com/pydantic/pydantic/pull/2176) by @thomascobb
* Allow non-existent secrets directory by only issuing a warning, [#2175](https://github.com/pydantic/pydantic/pull/2175) by @davidolrik
* fix URL regex to parse fragment without query string, [#2168](https://github.com/pydantic/pydantic/pull/2168) by @andrewmwhite
* fix: ensure to always return one of the values in `Literal` field type, [#2166](https://github.com/pydantic/pydantic/pull/2166) by @PrettyWood
* Support `typing.Annotated` hints on model fields. A `Field` may now be set in the type hint with `Annotated[..., Field(...)`; all other annotations are ignored but still visible with `get_type_hints(..., include_extras=True)`, [#2147](https://github.com/pydantic/pydantic/pull/2147) by @JacobHayes
* Added `StrictBytes` type as well as `strict=False` option to `ConstrainedBytes`, [#2136](https://github.com/pydantic/pydantic/pull/2136) by @rlizzo
* added `Config.anystr_lower` and `to_lower` kwarg to `constr` and `conbytes`, [#2134](https://github.com/pydantic/pydantic/pull/2134) by @tayoogunbiyi
* Support plain `typing.Tuple` type, [#2132](https://github.com/pydantic/pydantic/pull/2132) by @PrettyWood
* Add a bound method `validate` to functions decorated with `validate_arguments`
  to validate parameters without actually calling the function, [#2127](https://github.com/pydantic/pydantic/pull/2127) by @PrettyWood
* Add the ability to customize settings sources (add / disable / change priority order), [#2107](https://github.com/pydantic/pydantic/pull/2107) by @kozlek
* Fix mypy complaints about most custom _pydantic_ types, [#2098](https://github.com/pydantic/pydantic/pull/2098) by @PrettyWood
* Add a [Hypothesis](https://hypothesis.readthedocs.io/) plugin for easier [property-based testing](https://increment.com/testing/in-praise-of-property-based-testing/) with Pydantic's custom types - [usage details here](https://docs.pydantic.dev/hypothesis_plugin/), [#2097](https://github.com/pydantic/pydantic/pull/2097) by @Zac-HD
* add validator for `None`, `NoneType` or `Literal[None]`, [#2095](https://github.com/pydantic/pydantic/pull/2095) by @PrettyWood
* Handle properly fields of type `Callable` with a default value, [#2094](https://github.com/pydantic/pydantic/pull/2094) by @PrettyWood
* Updated `create_model` return type annotation to return type which inherits from `__base__` argument, [#2071](https://github.com/pydantic/pydantic/pull/2071) by @uriyyo
* Add merged `json_encoders` inheritance, [#2064](https://github.com/pydantic/pydantic/pull/2064) by @art049
* allow overwriting `ClassVar`s in sub-models without having to re-annotate them, [#2061](https://github.com/pydantic/pydantic/pull/2061) by @layday
* add default encoder for `Pattern` type, [#2045](https://github.com/pydantic/pydantic/pull/2045) by @PrettyWood
* Add `NonNegativeInt`, `NonPositiveInt`, `NonNegativeFloat`, `NonPositiveFloat`, [#1975](https://github.com/pydantic/pydantic/pull/1975) by @mdavis-xyz
* Use % for percentage in string format of colors, [#1960](https://github.com/pydantic/pydantic/pull/1960) by @EdwardBetts
* Fixed issue causing `KeyError` to be raised when building schema from multiple `BaseModel` with the same names declared in separate classes, [#1912](https://github.com/pydantic/pydantic/pull/1912) by @JSextonn
* Add `rediss` (Redis over SSL) protocol to `RedisDsn`
  Allow URLs without `user` part (e.g., `rediss://:pass@localhost`), [#1911](https://github.com/pydantic/pydantic/pull/1911) by @TrDex
* Add a new `frozen` boolean parameter to `Config` (default: `False`).
  Setting `frozen=True` does everything that `allow_mutation=False` does, and also generates a `__hash__()` method for the model. This makes instances of the model potentially hashable if all the attributes are hashable, [#1880](https://github.com/pydantic/pydantic/pull/1880) by @rhuille
* fix schema generation with multiple Enums having the same name, [#1857](https://github.com/pydantic/pydantic/pull/1857) by @PrettyWood
* Added support for 13/19 digits VISA credit cards in `PaymentCardNumber` type, [#1416](https://github.com/pydantic/pydantic/pull/1416) by @AlexanderSov
* fix: prevent `RecursionError` while using recursive `GenericModel`s, [#1370](https://github.com/pydantic/pydantic/pull/1370) by @xppt
* use `enum` for `typing.Literal` in JSON schema, [#1350](https://github.com/pydantic/pydantic/pull/1350) by @PrettyWood
* Fix: some recursive models did not require `update_forward_refs` and silently behaved incorrectly, [#1201](https://github.com/pydantic/pydantic/pull/1201) by @PrettyWood
* Fix bug where generic models with fields where the typevar is nested in another type `a: List[T]` are considered to be concrete. This allows these models to be subclassed and composed as expected, [#947](https://github.com/pydantic/pydantic/pull/947) by @daviskirk
* Add `Config.copy_on_model_validation` flag. When set to `False`, _pydantic_ will keep models used as fields
  untouched on validation instead of reconstructing (copying) them, [#265](https://github.com/pydantic/pydantic/pull/265) by @PrettyWood

## v1.7.4 (2021-05-11)

* **Security fix:** Fix `date` and `datetime` parsing so passing either `'infinity'` or `float('inf')`
  (or their negative values) does not cause an infinite loop,
  See security advisory [CVE-2021-29510](https://github.com/pydantic/pydantic/security/advisories/GHSA-5jqp-qgf6-3pvh)

## v1.7.3 (2020-11-30)

Thank you to pydantic's sponsors:
@timdrijvers, @BCarley, @chdsbd, @tiangolo, @matin, @linusg, @kevinalh, @jorgecarleitao, @koxudaxi, @primer-api,
@mkeen, @meadsteve for their kind support.

* fix: set right default value for required (optional) fields, [#2142](https://github.com/pydantic/pydantic/pull/2142) by @PrettyWood
* fix: support `underscore_attrs_are_private` with generic models, [#2138](https://github.com/pydantic/pydantic/pull/2138) by @PrettyWood
* fix: update all modified field values in `root_validator` when `validate_assignment` is on, [#2116](https://github.com/pydantic/pydantic/pull/2116) by @PrettyWood
* Allow pickling of `pydantic.dataclasses.dataclass` dynamically created from a built-in `dataclasses.dataclass`, [#2111](https://github.com/pydantic/pydantic/pull/2111) by @aimestereo
* Fix a regression where Enum fields would not propagate keyword arguments to the schema, [#2109](https://github.com/pydantic/pydantic/pull/2109) by @bm424
* Ignore `__doc__` as private attribute when `Config.underscore_attrs_are_private` is set, [#2090](https://github.com/pydantic/pydantic/pull/2090) by @PrettyWood

## v1.7.2 (2020-11-01)

* fix slow `GenericModel` concrete model creation, allow `GenericModel` concrete name reusing in module, [#2078](https://github.com/pydantic/pydantic/pull/2078) by @Bobronium
* keep the order of the fields when `validate_assignment` is set, [#2073](https://github.com/pydantic/pydantic/pull/2073) by @PrettyWood
* forward all the params of the stdlib `dataclass` when converted into _pydantic_ `dataclass`, [#2065](https://github.com/pydantic/pydantic/pull/2065) by @PrettyWood

## v1.7.1 (2020-10-28)

Thank you to pydantic's sponsors:
@timdrijvers, @BCarley, @chdsbd, @tiangolo, @matin, @linusg, @kevinalh, @jorgecarleitao, @koxudaxi, @primer-api, @mkeen
for their kind support.

* fix annotation of `validate_arguments` when passing configuration as argument, [#2055](https://github.com/pydantic/pydantic/pull/2055) by @layday
* Fix mypy assignment error when using `PrivateAttr`, [#2048](https://github.com/pydantic/pydantic/pull/2048) by @aphedges
* fix `underscore_attrs_are_private` causing `TypeError` when overriding `__init__`, [#2047](https://github.com/pydantic/pydantic/pull/2047) by @samuelcolvin
* Fixed regression introduced in v1.7 involving exception handling in field validators when `validate_assignment=True`, [#2044](https://github.com/pydantic/pydantic/pull/2044) by @johnsabath
* fix: _pydantic_ `dataclass` can inherit from stdlib `dataclass`
  and `Config.arbitrary_types_allowed` is supported, [#2042](https://github.com/pydantic/pydantic/pull/2042) by @PrettyWood

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
  Use `.get_default()` method on fields in `__fields__` attribute instead, [#1732](https://github.com/pydantic/pydantic/pull/1732) by @PrettyWood
* Rearrange CI to run linting as a separate job, split install recipes for different tasks, [#2020](https://github.com/pydantic/pydantic/pull/2020) by @samuelcolvin
* Allows subclasses of generic models to make some, or all, of the superclass's type parameters concrete, while
  also defining new type parameters in the subclass, [#2005](https://github.com/pydantic/pydantic/pull/2005) by @choogeboom
* Call validator with the correct `values` parameter type in `BaseModel.__setattr__`,
  when `validate_assignment = True` in model config, [#1999](https://github.com/pydantic/pydantic/pull/1999) by @me-ransh
* Force `fields.Undefined` to be a singleton object, fixing inherited generic model schemas, [#1981](https://github.com/pydantic/pydantic/pull/1981) by @daviskirk
* Include tests in source distributions, [#1976](https://github.com/pydantic/pydantic/pull/1976) by @sbraz
* Add ability to use `min_length/max_length` constraints with secret types, [#1974](https://github.com/pydantic/pydantic/pull/1974) by @uriyyo
* Also check `root_validators` when `validate_assignment` is on, [#1971](https://github.com/pydantic/pydantic/pull/1971) by @PrettyWood
* Fix const validators not running when custom validators are present, [#1957](https://github.com/pydantic/pydantic/pull/1957) by @hmvp
* add `deque` to field types, [#1935](https://github.com/pydantic/pydantic/pull/1935) by @wozniakty
* add basic support for Python 3.9, [#1832](https://github.com/pydantic/pydantic/pull/1832) by @PrettyWood
* Fix typo in the anchor of exporting_models.md#modelcopy and incorrect description, [#1821](https://github.com/pydantic/pydantic/pull/1821) by @KimMachineGun
* Added ability for `BaseSettings` to read "secret files", [#1820](https://github.com/pydantic/pydantic/pull/1820) by @mdgilene
* add `parse_raw_as` utility function, [#1812](https://github.com/pydantic/pydantic/pull/1812) by @PrettyWood
* Support home directory relative paths for `dotenv` files (e.g. `~/.env`), [#1803](https://github.com/pydantic/pydantic/pull/1803) by @PrettyWood
* Clarify documentation for `parse_file` to show that the argument
  should be a file *path* not a file-like object, [#1794](https://github.com/pydantic/pydantic/pull/1794) by @mdavis-xyz
* Fix false positive from mypy plugin when a class nested within a `BaseModel` is named `Model`, [#1770](https://github.com/pydantic/pydantic/pull/1770) by @selimb
* add basic support of Pattern type in schema generation, [#1767](https://github.com/pydantic/pydantic/pull/1767) by @PrettyWood
* Support custom title, description and default in schema of enums, [#1748](https://github.com/pydantic/pydantic/pull/1748) by @PrettyWood
* Properly represent `Literal` Enums when `use_enum_values` is True, [#1747](https://github.com/pydantic/pydantic/pull/1747) by @noelevans
* Allows timezone information to be added to strings to be formatted as time objects. Permitted formats are `Z` for UTC
  or an offset for absolute positive or negative time shifts. Or the timezone data can be omitted, [#1744](https://github.com/pydantic/pydantic/pull/1744) by @noelevans
* Add stub `__init__` with Python 3.6 signature for `ForwardRef`, [#1738](https://github.com/pydantic/pydantic/pull/1738) by @sirtelemak
* Fix behaviour with forward refs and optional fields in nested models, [#1736](https://github.com/pydantic/pydantic/pull/1736) by @PrettyWood
* add `Enum` and `IntEnum` as valid types for fields, [#1735](https://github.com/pydantic/pydantic/pull/1735) by @PrettyWood
* Change default value of `__module__` argument of `create_model` from `None` to `'pydantic.main'`.
  Set reference of created concrete model to it's module to allow pickling (not applied to models created in
  functions), [#1686](https://github.com/pydantic/pydantic/pull/1686) by @Bobronium
* Add private attributes support, [#1679](https://github.com/pydantic/pydantic/pull/1679) by @Bobronium
* add `config` to `@validate_arguments`, [#1663](https://github.com/pydantic/pydantic/pull/1663) by @samuelcolvin
* Allow descendant Settings models to override env variable names for the fields defined in parent Settings models with
  `env` in their `Config`. Previously only `env_prefix` configuration option was applicable, [#1561](https://github.com/pydantic/pydantic/pull/1561) by @ojomio
* Support `ref_template` when creating schema `$ref`s, [#1479](https://github.com/pydantic/pydantic/pull/1479) by @kilo59
* Add a `__call__` stub to `PyObject` so that mypy will know that it is callable, [#1352](https://github.com/pydantic/pydantic/pull/1352) by @brianmaissy
* `pydantic.dataclasses.dataclass` decorator now supports built-in `dataclasses.dataclass`.
  It is hence possible to convert an existing `dataclass` easily to add Pydantic validation.
  Moreover nested dataclasses are also supported, [#744](https://github.com/pydantic/pydantic/pull/744) by @PrettyWood

## v1.6.2 (2021-05-11)

* **Security fix:** Fix `date` and `datetime` parsing so passing either `'infinity'` or `float('inf')`
  (or their negative values) does not cause an infinite loop,
  See security advisory [CVE-2021-29510](https://github.com/pydantic/pydantic/security/advisories/GHSA-5jqp-qgf6-3pvh)

## v1.6.1 (2020-07-15)

* fix validation and parsing of nested models with `default_factory`, [#1710](https://github.com/pydantic/pydantic/pull/1710) by @PrettyWood

## v1.6 (2020-07-11)

Thank you to pydantic's sponsors: @matin, @tiangolo, @chdsbd, @jorgecarleitao, and 1 anonymous sponsor for their kind support.

* Modify validators for `conlist` and `conset` to not have `always=True`, [#1682](https://github.com/pydantic/pydantic/pull/1682) by @samuelcolvin
* add port check to `AnyUrl` (can't exceed 65536) ports are 16 insigned bits: `0 <= port <= 2**16-1` src: [rfc793 header format](https://tools.ietf.org/html/rfc793#section-3.1), [#1654](https://github.com/pydantic/pydantic/pull/1654) by @flapili
* Document default `regex` anchoring semantics, [#1648](https://github.com/pydantic/pydantic/pull/1648) by @yurikhan
* Use `chain.from_iterable` in class_validators.py. This is a faster and more idiomatic way of using `itertools.chain`.
  Instead of computing all the items in the iterable and storing them in memory, they are computed one-by-one and never
  stored as a huge list. This can save on both runtime and memory space, [#1642](https://github.com/pydantic/pydantic/pull/1642) by @cool-RR
* Add `conset()`, analogous to `conlist()`, [#1623](https://github.com/pydantic/pydantic/pull/1623) by @patrickkwang
* make Pydantic errors (un)pickable, [#1616](https://github.com/pydantic/pydantic/pull/1616) by @PrettyWood
* Allow custom encoding for `dotenv` files, [#1615](https://github.com/pydantic/pydantic/pull/1615) by @PrettyWood
* Ensure `SchemaExtraCallable` is always defined to get type hints on BaseConfig, [#1614](https://github.com/pydantic/pydantic/pull/1614) by @PrettyWood
* Update datetime parser to support negative timestamps, [#1600](https://github.com/pydantic/pydantic/pull/1600) by @mlbiche
* Update mypy, remove `AnyType` alias for `Type[Any]`, [#1598](https://github.com/pydantic/pydantic/pull/1598) by @samuelcolvin
* Adjust handling of root validators so that errors are aggregated from _all_ failing root validators, instead of reporting on only the first root validator to fail, [#1586](https://github.com/pydantic/pydantic/pull/1586) by @beezee
* Make `__modify_schema__` on Enums apply to the enum schema rather than fields that use the enum, [#1581](https://github.com/pydantic/pydantic/pull/1581) by @therefromhere
* Fix behavior of `__all__` key when used in conjunction with index keys in advanced include/exclude of fields that are sequences, [#1579](https://github.com/pydantic/pydantic/pull/1579) by @xspirus
* Subclass validators do not run when referencing a `List` field defined in a parent class when `each_item=True`. Added an example to the docs illustrating this, [#1566](https://github.com/pydantic/pydantic/pull/1566) by @samueldeklund
* change `schema.field_class_to_schema` to support `frozenset` in schema, [#1557](https://github.com/pydantic/pydantic/pull/1557) by @wangpeibao
* Call `__modify_schema__` only for the field schema, [#1552](https://github.com/pydantic/pydantic/pull/1552) by @PrettyWood
* Move the assignment of `field.validate_always` in `fields.py` so the `always` parameter of validators work on inheritance, [#1545](https://github.com/pydantic/pydantic/pull/1545) by @dcHHH
* Added support for UUID instantiation through 16 byte strings such as `b'\x12\x34\x56\x78' * 4`. This was done to support `BINARY(16)` columns in sqlalchemy, [#1541](https://github.com/pydantic/pydantic/pull/1541) by @shawnwall
* Add a test assertion that `default_factory` can return a singleton, [#1523](https://github.com/pydantic/pydantic/pull/1523) by @therefromhere
* Add `NameEmail.__eq__` so duplicate `NameEmail` instances are evaluated as equal, [#1514](https://github.com/pydantic/pydantic/pull/1514) by @stephen-bunn
* Add datamodel-code-generator link in pydantic document site, [#1500](https://github.com/pydantic/pydantic/pull/1500) by @koxudaxi
* Added a "Discussion of Pydantic" section to the documentation, with a link to "Pydantic Introduction" video by Alexander Hultnér, [#1499](https://github.com/pydantic/pydantic/pull/1499) by @hultner
* Avoid some side effects of `default_factory` by calling it only once
  if possible and by not setting a default value in the schema, [#1491](https://github.com/pydantic/pydantic/pull/1491) by @PrettyWood
* Added docs about dumping dataclasses to JSON, [#1487](https://github.com/pydantic/pydantic/pull/1487) by @mikegrima
* Make `BaseModel.__signature__` class-only, so getting `__signature__` from model instance will raise `AttributeError`, [#1466](https://github.com/pydantic/pydantic/pull/1466) by @Bobronium
* include `'format': 'password'` in the schema for secret types, [#1424](https://github.com/pydantic/pydantic/pull/1424) by @atheuz
* Modify schema constraints on `ConstrainedFloat` so that `exclusiveMinimum` and
  minimum are not included in the schema if they are equal to `-math.inf` and
  `exclusiveMaximum` and `maximum` are not included if they are equal to `math.inf`, [#1417](https://github.com/pydantic/pydantic/pull/1417) by @vdwees
* Squash internal `__root__` dicts in `.dict()` (and, by extension, in `.json()`), [#1414](https://github.com/pydantic/pydantic/pull/1414) by @patrickkwang
* Move `const` validator to post-validators so it validates the parsed value, [#1410](https://github.com/pydantic/pydantic/pull/1410) by @selimb
* Fix model validation to handle nested literals, e.g. `Literal['foo', Literal['bar']]`, [#1364](https://github.com/pydantic/pydantic/pull/1364) by @DBCerigo
* Remove `user_required = True` from `RedisDsn`, neither user nor password are required, [#1275](https://github.com/pydantic/pydantic/pull/1275) by @samuelcolvin
* Remove extra `allOf` from schema for fields with `Union` and custom `Field`, [#1209](https://github.com/pydantic/pydantic/pull/1209) by @mostaphaRoudsari
* Updates OpenAPI schema generation to output all enums as separate models.
  Instead of inlining the enum values in the model schema, models now use a `$ref`
  property to point to the enum definition, [#1173](https://github.com/pydantic/pydantic/pull/1173) by @calvinwyoung

## v1.5.1 (2020-04-23)

* Signature generation with `extra: allow` never uses a field name, [#1418](https://github.com/pydantic/pydantic/pull/1418) by @prettywood
* Avoid mutating `Field` default value, [#1412](https://github.com/pydantic/pydantic/pull/1412) by @prettywood

## v1.5 (2020-04-18)

* Make includes/excludes arguments for `.dict()`, `._iter()`, ..., immutable, [#1404](https://github.com/pydantic/pydantic/pull/1404) by @AlexECX
* Always use a field's real name with includes/excludes in `model._iter()`, regardless of `by_alias`, [#1397](https://github.com/pydantic/pydantic/pull/1397) by @AlexECX
* Update constr regex example to include start and end lines, [#1396](https://github.com/pydantic/pydantic/pull/1396) by @lmcnearney
* Confirm that shallow `model.copy()` does make a shallow copy of attributes, [#1383](https://github.com/pydantic/pydantic/pull/1383) by @samuelcolvin
* Renaming `model_name` argument of `main.create_model()` to `__model_name` to allow using `model_name` as a field name, [#1367](https://github.com/pydantic/pydantic/pull/1367) by @kittipatv
* Replace raising of exception to silent passing  for non-Var attributes in mypy plugin, [#1345](https://github.com/pydantic/pydantic/pull/1345) by @b0g3r
* Remove `typing_extensions` dependency for Python 3.8, [#1342](https://github.com/pydantic/pydantic/pull/1342) by @prettywood
* Make `SecretStr` and `SecretBytes` initialization idempotent, [#1330](https://github.com/pydantic/pydantic/pull/1330) by @atheuz
* document making secret types dumpable using the json method, [#1328](https://github.com/pydantic/pydantic/pull/1328) by @atheuz
* Move all testing and build to github actions, add windows and macos binaries,
  thank you @StephenBrown2 for much help, [#1326](https://github.com/pydantic/pydantic/pull/1326) by @samuelcolvin
* fix card number length check in `PaymentCardNumber`, `PaymentCardBrand` now inherits from `str`, [#1317](https://github.com/pydantic/pydantic/pull/1317) by @samuelcolvin
* Have `BaseModel` inherit from `Representation` to make mypy happy when overriding `__str__`, [#1310](https://github.com/pydantic/pydantic/pull/1310) by @FuegoFro
* Allow `None` as input to all optional list fields, [#1307](https://github.com/pydantic/pydantic/pull/1307) by @prettywood
* Add `datetime` field to `default_factory` example, [#1301](https://github.com/pydantic/pydantic/pull/1301) by @StephenBrown2
* Allow subclasses of known types to be encoded with superclass encoder, [#1291](https://github.com/pydantic/pydantic/pull/1291) by @StephenBrown2
* Exclude exported fields from all elements of a list/tuple of submodels/dicts with `'__all__'`, [#1286](https://github.com/pydantic/pydantic/pull/1286) by @masalim2
* Add pydantic.color.Color objects as available input for Color fields, [#1258](https://github.com/pydantic/pydantic/pull/1258) by @leosussan
* In examples, type nullable fields as `Optional`, so that these are valid mypy annotations, [#1248](https://github.com/pydantic/pydantic/pull/1248) by @kokes
* Make `pattern_validator()` accept pre-compiled `Pattern` objects. Fix `str_validator()` return type to `str`, [#1237](https://github.com/pydantic/pydantic/pull/1237) by @adamgreg
* Document how to manage Generics and inheritance, [#1229](https://github.com/pydantic/pydantic/pull/1229) by @esadruhn
* `update_forward_refs()` method of BaseModel now copies `__dict__` of class module instead of modyfying it, [#1228](https://github.com/pydantic/pydantic/pull/1228) by @paul-ilyin
* Support instance methods and class methods with `@validate_arguments`, [#1222](https://github.com/pydantic/pydantic/pull/1222) by @samuelcolvin
* Add `default_factory` argument to `Field` to create a dynamic default value by passing a zero-argument callable, [#1210](https://github.com/pydantic/pydantic/pull/1210) by @prettywood
* add support for `NewType` of `List`, `Optional`, etc, [#1207](https://github.com/pydantic/pydantic/pull/1207) by @Kazy
* fix mypy signature for `root_validator`, [#1192](https://github.com/pydantic/pydantic/pull/1192) by @samuelcolvin
* Fixed parsing of nested 'custom root type' models, [#1190](https://github.com/pydantic/pydantic/pull/1190) by @Shados
* Add `validate_arguments` function decorator which checks the arguments to a function matches type annotations, [#1179](https://github.com/pydantic/pydantic/pull/1179) by @samuelcolvin
* Add `__signature__` to models, [#1034](https://github.com/pydantic/pydantic/pull/1034) by @Bobronium
* Refactor `._iter()` method, 10x speed boost for `dict(model)`, [#1017](https://github.com/pydantic/pydantic/pull/1017) by @Bobronium

## v1.4 (2020-01-24)

* **Breaking Change:** alias precedence logic changed so aliases on a field always take priority over
  an alias from `alias_generator` to avoid buggy/unexpected behaviour,
  see [here](https://docs.pydantic.dev/usage/model_config/#alias-precedence) for details, [#1178](https://github.com/pydantic/pydantic/pull/1178) by @samuelcolvin
* Add support for unicode and punycode in TLDs, [#1182](https://github.com/pydantic/pydantic/pull/1182) by @jamescurtin
* Fix `cls` argument in validators during assignment, [#1172](https://github.com/pydantic/pydantic/pull/1172) by @samuelcolvin
* completing Luhn algorithm for `PaymentCardNumber`, [#1166](https://github.com/pydantic/pydantic/pull/1166) by @cuencandres
* add support for generics that implement `__get_validators__` like a custom data type, [#1159](https://github.com/pydantic/pydantic/pull/1159) by @tiangolo
* add support for infinite generators with `Iterable`, [#1152](https://github.com/pydantic/pydantic/pull/1152) by @tiangolo
* fix `url_regex` to accept schemas with `+`, `-` and `.` after the first character, [#1142](https://github.com/pydantic/pydantic/pull/1142) by @samuelcolvin
* move `version_info()` to `version.py`, suggest its use in issues, [#1138](https://github.com/pydantic/pydantic/pull/1138) by @samuelcolvin
* Improve pydantic import time by roughly 50% by deferring some module loading and regex compilation, [#1127](https://github.com/pydantic/pydantic/pull/1127) by @samuelcolvin
* Fix `EmailStr` and `NameEmail` to accept instances of themselves in cython, [#1126](https://github.com/pydantic/pydantic/pull/1126) by @koxudaxi
* Pass model class to the `Config.schema_extra` callable, [#1125](https://github.com/pydantic/pydantic/pull/1125) by @therefromhere
* Fix regex for username and password in URLs, [#1115](https://github.com/pydantic/pydantic/pull/1115) by @samuelcolvin
* Add support for nested generic models, [#1104](https://github.com/pydantic/pydantic/pull/1104) by @dmontagu
* add `__all__` to `__init__.py` to prevent "implicit reexport" errors from mypy, [#1072](https://github.com/pydantic/pydantic/pull/1072) by @samuelcolvin
* Add support for using "dotenv" files with `BaseSettings`, [#1011](https://github.com/pydantic/pydantic/pull/1011) by @acnebs

## v1.3 (2019-12-21)

* Change `schema` and `schema_model` to handle dataclasses by using their `__pydantic_model__` feature, [#792](https://github.com/pydantic/pydantic/pull/792) by @aviramha
* Added option for `root_validator` to be skipped if values validation fails using keyword `skip_on_failure=True`, [#1049](https://github.com/pydantic/pydantic/pull/1049) by @aviramha
* Allow `Config.schema_extra` to be a callable so that the generated schema can be post-processed, [#1054](https://github.com/pydantic/pydantic/pull/1054) by @selimb
* Update mypy to version 0.750, [#1057](https://github.com/pydantic/pydantic/pull/1057) by @dmontagu
* Trick Cython into allowing str subclassing, [#1061](https://github.com/pydantic/pydantic/pull/1061) by @skewty
* Prevent type attributes being added to schema unless the attribute `__schema_attributes__` is `True`, [#1064](https://github.com/pydantic/pydantic/pull/1064) by @samuelcolvin
* Change `BaseModel.parse_file` to use `Config.json_loads`, [#1067](https://github.com/pydantic/pydantic/pull/1067) by @kierandarcy
* Fix for optional `Json` fields, [#1073](https://github.com/pydantic/pydantic/pull/1073) by @volker48
* Change the default number of threads used when compiling with cython to one,
  allow override via the `CYTHON_NTHREADS` environment variable, [#1074](https://github.com/pydantic/pydantic/pull/1074) by @samuelcolvin
* Run FastAPI tests during Pydantic's CI tests, [#1075](https://github.com/pydantic/pydantic/pull/1075) by @tiangolo
* My mypy strictness constraints, and associated tweaks to type annotations, [#1077](https://github.com/pydantic/pydantic/pull/1077) by @samuelcolvin
* Add `__eq__` to SecretStr and SecretBytes to allow "value equals", [#1079](https://github.com/pydantic/pydantic/pull/1079) by @sbv-trueenergy
* Fix schema generation for nested None case, [#1088](https://github.com/pydantic/pydantic/pull/1088) by @lutostag
* Consistent checks for sequence like objects, [#1090](https://github.com/pydantic/pydantic/pull/1090) by @samuelcolvin
* Fix `Config` inheritance on `BaseSettings` when used with `env_prefix`, [#1091](https://github.com/pydantic/pydantic/pull/1091) by @samuelcolvin
* Fix for `__modify_schema__` when it conflicted with `field_class_to_schema*`, [#1102](https://github.com/pydantic/pydantic/pull/1102) by @samuelcolvin
* docs: Fix explanation of case sensitive environment variable names when populating `BaseSettings` subclass attributes, [#1105](https://github.com/pydantic/pydantic/pull/1105) by @tribals
* Rename django-rest-framework benchmark in documentation, [#1119](https://github.com/pydantic/pydantic/pull/1119) by @frankie567

## v1.2 (2019-11-28)

* **Possible Breaking Change:** Add support for required `Optional` with `name: Optional[AnyType] = Field(...)`
  and refactor `ModelField` creation to preserve `required` parameter value, [#1031](https://github.com/pydantic/pydantic/pull/1031) by @tiangolo;
  see [here](https://docs.pydantic.dev/usage/models/#required-optional-fields) for details
* Add benchmarks for `cattrs`, [#513](https://github.com/pydantic/pydantic/pull/513) by @sebastianmika
* Add `exclude_none` option to `dict()` and friends, [#587](https://github.com/pydantic/pydantic/pull/587) by @niknetniko
* Add benchmarks for `valideer`, [#670](https://github.com/pydantic/pydantic/pull/670) by @gsakkis
* Add `parse_obj_as` and `parse_file_as` functions for ad-hoc parsing of data into arbitrary pydantic-compatible types, [#934](https://github.com/pydantic/pydantic/pull/934) by @dmontagu
* Add `allow_reuse` argument to validators, thus allowing validator reuse, [#940](https://github.com/pydantic/pydantic/pull/940) by @dmontagu
* Add support for mapping types for custom root models, [#958](https://github.com/pydantic/pydantic/pull/958) by @dmontagu
* Mypy plugin support for dataclasses, [#966](https://github.com/pydantic/pydantic/pull/966) by @koxudaxi
* Add support for dataclasses default factory, [#968](https://github.com/pydantic/pydantic/pull/968) by @ahirner
* Add a `ByteSize` type for converting byte string (`1GB`) to plain bytes, [#977](https://github.com/pydantic/pydantic/pull/977) by @dgasmith
* Fix mypy complaint about `@root_validator(pre=True)`, [#984](https://github.com/pydantic/pydantic/pull/984) by @samuelcolvin
* Add manylinux binaries for Python 3.8 to pypi, also support manylinux2010, [#994](https://github.com/pydantic/pydantic/pull/994) by @samuelcolvin
* Adds ByteSize conversion to another unit, [#995](https://github.com/pydantic/pydantic/pull/995) by @dgasmith
* Fix `__str__` and `__repr__` inheritance for models, [#1022](https://github.com/pydantic/pydantic/pull/1022) by @samuelcolvin
* add testimonials section to docs, [#1025](https://github.com/pydantic/pydantic/pull/1025) by @sullivancolin
* Add support for `typing.Literal` for Python 3.8, [#1026](https://github.com/pydantic/pydantic/pull/1026) by @dmontagu

## v1.1.1 (2019-11-20)

* Fix bug where use of complex fields on sub-models could cause fields to be incorrectly configured, [#1015](https://github.com/pydantic/pydantic/pull/1015) by @samuelcolvin

## v1.1 (2019-11-07)

* Add a mypy plugin for type checking `BaseModel.__init__` and more, [#722](https://github.com/pydantic/pydantic/pull/722) by @dmontagu
* Change return type typehint for `GenericModel.__class_getitem__` to prevent PyCharm warnings, [#936](https://github.com/pydantic/pydantic/pull/936) by @dmontagu
* Fix usage of `Any` to allow `None`, also support `TypeVar` thus allowing use of un-parameterised collection types
  e.g. `Dict` and `List`, [#962](https://github.com/pydantic/pydantic/pull/962) by @samuelcolvin
* Set `FieldInfo` on subfields to fix schema generation for complex nested types, [#965](https://github.com/pydantic/pydantic/pull/965) by @samuelcolvin

## v1.0 (2019-10-23)

* **Breaking Change:** deprecate the `Model.fields` property, use `Model.__fields__` instead, [#883](https://github.com/pydantic/pydantic/pull/883) by @samuelcolvin
* **Breaking Change:** Change the precedence of aliases so child model aliases override parent aliases,
  including using `alias_generator`, [#904](https://github.com/pydantic/pydantic/pull/904) by @samuelcolvin
* **Breaking change:** Rename `skip_defaults` to `exclude_unset`, and add ability to exclude actual defaults, [#915](https://github.com/pydantic/pydantic/pull/915) by @dmontagu
* Add `**kwargs` to `pydantic.main.ModelMetaclass.__new__` so `__init_subclass__` can take custom parameters on extended
  `BaseModel` classes, [#867](https://github.com/pydantic/pydantic/pull/867) by @retnikt
* Fix field of a type that has a default value, [#880](https://github.com/pydantic/pydantic/pull/880) by @koxudaxi
* Use `FutureWarning` instead of `DeprecationWarning` when `alias` instead of `env` is used for settings models, [#881](https://github.com/pydantic/pydantic/pull/881) by @samuelcolvin
* Fix issue with `BaseSettings` inheritance and `alias` getting set to `None`, [#882](https://github.com/pydantic/pydantic/pull/882) by @samuelcolvin
* Modify `__repr__` and `__str__` methods to be consistent across all public classes, add `__pretty__` to support
  python-devtools, [#884](https://github.com/pydantic/pydantic/pull/884) by @samuelcolvin
* deprecation warning for `case_insensitive` on `BaseSettings` config, [#885](https://github.com/pydantic/pydantic/pull/885) by @samuelcolvin
* For `BaseSettings` merge environment variables and in-code values recursively, as long as they create a valid object
  when merged together, to allow splitting init arguments, [#888](https://github.com/pydantic/pydantic/pull/888) by @idmitrievsky
* change secret types example, [#890](https://github.com/pydantic/pydantic/pull/890) by @ashears
* Change the signature of `Model.construct()` to be more user-friendly, document `construct()` usage, [#898](https://github.com/pydantic/pydantic/pull/898) by @samuelcolvin
* Add example for the `construct()` method, [#907](https://github.com/pydantic/pydantic/pull/907) by @ashears
* Improve use of `Field` constraints on complex types, raise an error if constraints are not enforceable,
  also support tuples with an ellipsis `Tuple[X, ...]`, `Sequence` and `FrozenSet` in schema, [#909](https://github.com/pydantic/pydantic/pull/909) by @samuelcolvin
* update docs for bool missing valid value, [#911](https://github.com/pydantic/pydantic/pull/911) by @trim21
* Better `str`/`repr` logic for `ModelField`, [#912](https://github.com/pydantic/pydantic/pull/912) by @samuelcolvin
* Fix `ConstrainedList`, update schema generation to reflect `min_items` and `max_items` `Field()` arguments, [#917](https://github.com/pydantic/pydantic/pull/917) by @samuelcolvin
* Allow abstracts sets (eg. dict keys) in the `include` and `exclude` arguments of `dict()`, [#921](https://github.com/pydantic/pydantic/pull/921) by @samuelcolvin
* Fix JSON serialization errors on `ValidationError.json()` by using `pydantic_encoder`, [#922](https://github.com/pydantic/pydantic/pull/922) by @samuelcolvin
* Clarify usage of `remove_untouched`, improve error message for types with no validators, [#926](https://github.com/pydantic/pydantic/pull/926) by @retnikt

## v1.0b2 (2019-10-07)

* Mark `StrictBool` typecheck as `bool` to allow for default values without mypy errors, [#690](https://github.com/pydantic/pydantic/pull/690) by @dmontagu
* Transfer the documentation build from sphinx to mkdocs, re-write much of the documentation, [#856](https://github.com/pydantic/pydantic/pull/856) by @samuelcolvin
* Add support for custom naming schemes for `GenericModel` subclasses, [#859](https://github.com/pydantic/pydantic/pull/859) by @dmontagu
* Add `if TYPE_CHECKING:` to the excluded lines for test coverage, [#874](https://github.com/pydantic/pydantic/pull/874) by @dmontagu
* Rename `allow_population_by_alias` to `allow_population_by_field_name`, remove unnecessary warning about it, [#875](https://github.com/pydantic/pydantic/pull/875) by @samuelcolvin

## v1.0b1 (2019-10-01)

* **Breaking Change:** rename `Schema` to `Field`, make it a function to placate mypy, [#577](https://github.com/pydantic/pydantic/pull/577) by @samuelcolvin
* **Breaking Change:** modify parsing behavior for `bool`, [#617](https://github.com/pydantic/pydantic/pull/617) by @dmontagu
* **Breaking Change:** `get_validators` is no longer recognised, use `__get_validators__`.
  `Config.ignore_extra` and `Config.allow_extra` are no longer recognised, use `Config.extra`, [#720](https://github.com/pydantic/pydantic/pull/720) by @samuelcolvin
* **Breaking Change:** modify default config settings for `BaseSettings`; `case_insensitive` renamed to `case_sensitive`,
  default changed to `case_sensitive = False`, `env_prefix` default changed to `''` - e.g. no prefix, [#721](https://github.com/pydantic/pydantic/pull/721) by @dmontagu
* **Breaking change:** Implement `root_validator` and rename root errors from `__obj__` to `__root__`, [#729](https://github.com/pydantic/pydantic/pull/729) by @samuelcolvin
* **Breaking Change:** alter the behaviour of `dict(model)` so that sub-models are nolonger
  converted to dictionaries, [#733](https://github.com/pydantic/pydantic/pull/733) by @samuelcolvin
* **Breaking change:** Added `initvars` support to `post_init_post_parse`, [#748](https://github.com/pydantic/pydantic/pull/748) by @Raphael-C-Almeida
* **Breaking Change:** Make `BaseModel.json()` only serialize the `__root__` key for models with custom root, [#752](https://github.com/pydantic/pydantic/pull/752) by @dmontagu
* **Breaking Change:** complete rewrite of `URL` parsing logic, [#755](https://github.com/pydantic/pydantic/pull/755) by @samuelcolvin
* **Breaking Change:** preserve superclass annotations for field-determination when not provided in subclass, [#757](https://github.com/pydantic/pydantic/pull/757) by @dmontagu
* **Breaking Change:** `BaseSettings` now uses the special `env` settings to define which environment variables to
  read, not aliases, [#847](https://github.com/pydantic/pydantic/pull/847) by @samuelcolvin
* add support for `assert` statements inside validators, [#653](https://github.com/pydantic/pydantic/pull/653) by @abdusco
* Update documentation to specify the use of `pydantic.dataclasses.dataclass` and subclassing `pydantic.BaseModel`, [#710](https://github.com/pydantic/pydantic/pull/710) by @maddosaurus
* Allow custom JSON decoding and encoding via `json_loads` and `json_dumps` `Config` properties, [#714](https://github.com/pydantic/pydantic/pull/714) by @samuelcolvin
* make all annotated fields occur in the order declared, [#715](https://github.com/pydantic/pydantic/pull/715) by @dmontagu
* use pytest to test `mypy` integration, [#735](https://github.com/pydantic/pydantic/pull/735) by @dmontagu
* add `__repr__` method to `ErrorWrapper`, [#738](https://github.com/pydantic/pydantic/pull/738) by @samuelcolvin
* Added support for `FrozenSet` members in dataclasses, and a better error when attempting to use types from the `typing` module that are not supported by Pydantic, [#745](https://github.com/pydantic/pydantic/pull/745) by @djpetti
* add documentation for Pycharm Plugin, [#750](https://github.com/pydantic/pydantic/pull/750) by @koxudaxi
* fix broken examples in the docs, [#753](https://github.com/pydantic/pydantic/pull/753) by @dmontagu
* moving typing related objects into `pydantic.typing`, [#761](https://github.com/pydantic/pydantic/pull/761) by @samuelcolvin
* Minor performance improvements to `ErrorWrapper`, `ValidationError` and datetime parsing, [#763](https://github.com/pydantic/pydantic/pull/763) by @samuelcolvin
* Improvements to `datetime`/`date`/`time`/`timedelta` types: more descriptive errors,
  change errors to `value_error` not `type_error`, support bytes, [#766](https://github.com/pydantic/pydantic/pull/766) by @samuelcolvin
* fix error messages for `Literal` types with multiple allowed values, [#770](https://github.com/pydantic/pydantic/pull/770) by @dmontagu
* Improved auto-generated `title` field in JSON schema by converting underscore to space, [#772](https://github.com/pydantic/pydantic/pull/772) by @skewty
* support `mypy --no-implicit-reexport` for dataclasses, also respect `--no-implicit-reexport` in pydantic itself, [#783](https://github.com/pydantic/pydantic/pull/783) by @samuelcolvin
* add the `PaymentCardNumber` type, [#790](https://github.com/pydantic/pydantic/pull/790) by @matin
* Fix const validations for lists, [#794](https://github.com/pydantic/pydantic/pull/794) by @hmvp
* Set `additionalProperties` to false in schema for models with extra fields disallowed, [#796](https://github.com/pydantic/pydantic/pull/796) by @Code0x58
* `EmailStr` validation method now returns local part case-sensitive per RFC 5321, [#798](https://github.com/pydantic/pydantic/pull/798) by @henriklindgren
* Added ability to validate strictness to `ConstrainedFloat`, `ConstrainedInt` and `ConstrainedStr` and added
  `StrictFloat` and `StrictInt` classes, [#799](https://github.com/pydantic/pydantic/pull/799) by @DerRidda
* Improve handling of `None` and `Optional`, replace `whole` with `each_item` (inverse meaning, default `False`)
  on validators, [#803](https://github.com/pydantic/pydantic/pull/803) by @samuelcolvin
* add support for `Type[T]` type hints, [#807](https://github.com/pydantic/pydantic/pull/807) by @timonbimon
* Performance improvements from removing `change_exceptions`, change how pydantic error are constructed, [#819](https://github.com/pydantic/pydantic/pull/819) by @samuelcolvin
* Fix the error message arising when a `BaseModel`-type model field causes a `ValidationError` during parsing, [#820](https://github.com/pydantic/pydantic/pull/820) by @dmontagu
* allow `getter_dict` on `Config`, modify `GetterDict` to be more like a `Mapping` object and thus easier to work with, [#821](https://github.com/pydantic/pydantic/pull/821) by @samuelcolvin
* Only check `TypeVar` param on base `GenericModel` class, [#842](https://github.com/pydantic/pydantic/pull/842) by @zpencerq
* rename `Model._schema_cache` -> `Model.__schema_cache__`, `Model._json_encoder` -> `Model.__json_encoder__`,
  `Model._custom_root_type` -> `Model.__custom_root_type__`, [#851](https://github.com/pydantic/pydantic/pull/851) by @samuelcolvin

## v0.32.2 (2019-08-17)

(Docs are available [here](https://5d584fcca7c9b70007d1c997--pydantic-docs.netlify.com))

* fix `__post_init__` usage with dataclass inheritance, fix [#739](https://github.com/pydantic/pydantic/pull/739) by @samuelcolvin
* fix required fields validation on GenericModels classes, [#742](https://github.com/pydantic/pydantic/pull/742) by @amitbl
* fix defining custom `Schema` on `GenericModel` fields, [#754](https://github.com/pydantic/pydantic/pull/754) by @amitbl

## v0.32.1 (2019-08-08)

* do not validate extra fields when `validate_assignment` is on, [#724](https://github.com/pydantic/pydantic/pull/724) by @YaraslauZhylko

## v0.32 (2019-08-06)

* add model name to `ValidationError` error message, [#676](https://github.com/pydantic/pydantic/pull/676) by @dmontagu
* **breaking change**: remove `__getattr__` and rename `__values__` to `__dict__` on `BaseModel`,
  deprecation warning on use `__values__` attr, attributes access speed increased up to 14 times, [#712](https://github.com/pydantic/pydantic/pull/712) by @Bobronium
* support `ForwardRef` (without self-referencing annotations) in Python 3.6, [#706](https://github.com/pydantic/pydantic/pull/706) by @koxudaxi
* implement `schema_extra` in `Config` sub-class, [#663](https://github.com/pydantic/pydantic/pull/663) by @tiangolo

## v0.31.1 (2019-07-31)

* fix json generation for `EnumError`, [#697](https://github.com/pydantic/pydantic/pull/697) by @dmontagu
* update numerous dependencies

## v0.31 (2019-07-24)

* better support for floating point `multiple_of` values, [#652](https://github.com/pydantic/pydantic/pull/652) by @justindujardin
* fix schema generation for `NewType` and `Literal`, [#649](https://github.com/pydantic/pydantic/pull/649) by @dmontagu
* fix `alias_generator` and field config conflict, [#645](https://github.com/pydantic/pydantic/pull/645) by @gmetzker and [#658](https://github.com/pydantic/pydantic/pull/658) by @Bobronium
* more detailed message for `EnumError`, [#673](https://github.com/pydantic/pydantic/pull/673) by @dmontagu
* add advanced exclude support for `dict`, `json` and `copy`, [#648](https://github.com/pydantic/pydantic/pull/648) by @Bobronium
* fix bug in `GenericModel` for models with concrete parameterized fields, [#672](https://github.com/pydantic/pydantic/pull/672) by @dmontagu
* add documentation for `Literal` type, [#651](https://github.com/pydantic/pydantic/pull/651) by @dmontagu
* add `Config.keep_untouched` for custom descriptors support, [#679](https://github.com/pydantic/pydantic/pull/679) by @Bobronium
* use `inspect.cleandoc` internally to get model description, [#657](https://github.com/pydantic/pydantic/pull/657) by @tiangolo
* add `Color` to schema generation, by @euri10
* add documentation for Literal type, [#651](https://github.com/pydantic/pydantic/pull/651) by @dmontagu

## v0.30.1 (2019-07-15)

* fix so nested classes which inherit and change `__init__` are correctly processed while still allowing `self` as a
  parameter, [#644](https://github.com/pydantic/pydantic/pull/644) by @lnaden and @dgasmith

## v0.30 (2019-07-07)

* enforce single quotes in code, [#612](https://github.com/pydantic/pydantic/pull/612) by @samuelcolvin
* fix infinite recursion with dataclass inheritance and `__post_init__`, [#606](https://github.com/pydantic/pydantic/pull/606) by @Hanaasagi
* fix default values for `GenericModel`, [#610](https://github.com/pydantic/pydantic/pull/610) by @dmontagu
* clarify that self-referencing models require Python 3.7+, [#616](https://github.com/pydantic/pydantic/pull/616) by @vlcinsky
* fix truncate for types, [#611](https://github.com/pydantic/pydantic/pull/611) by @dmontagu
* add `alias_generator` support, [#622](https://github.com/pydantic/pydantic/pull/622) by @Bobronium
* fix unparameterized generic type schema generation, [#625](https://github.com/pydantic/pydantic/pull/625) by @dmontagu
* fix schema generation with multiple/circular references to the same model, [#621](https://github.com/pydantic/pydantic/pull/621) by @tiangolo and @wongpat
* support custom root types, [#628](https://github.com/pydantic/pydantic/pull/628) by @koxudaxi
* support `self` as a field name in `parse_obj`, [#632](https://github.com/pydantic/pydantic/pull/632) by @samuelcolvin

## v0.29 (2019-06-19)

* support dataclasses.InitVar, [#592](https://github.com/pydantic/pydantic/pull/592) by @pfrederiks
* Updated documentation to elucidate the usage of `Union` when defining multiple types under an attribute's
  annotation and showcase how the type-order can affect marshalling of provided values, [#594](https://github.com/pydantic/pydantic/pull/594) by @somada141
* add `conlist` type, [#583](https://github.com/pydantic/pydantic/pull/583) by @hmvp
* add support for generics, [#595](https://github.com/pydantic/pydantic/pull/595) by @dmontagu

## v0.28 (2019-06-06)

* fix support for JSON Schema generation when using models with circular references in Python 3.7, [#572](https://github.com/pydantic/pydantic/pull/572) by @tiangolo
* support `__post_init_post_parse__` on dataclasses, [#567](https://github.com/pydantic/pydantic/pull/567) by @sevaho
* allow dumping dataclasses to JSON, [#575](https://github.com/pydantic/pydantic/pull/575) by @samuelcolvin and @DanielOberg
* ORM mode, [#562](https://github.com/pydantic/pydantic/pull/562) by @samuelcolvin
* fix `pydantic.compiled` on ipython, [#573](https://github.com/pydantic/pydantic/pull/573) by @dmontagu and @samuelcolvin
* add `StrictBool` type, [#579](https://github.com/pydantic/pydantic/pull/579) by @cazgp

## v0.27 (2019-05-30)

* **breaking change**  `_pydantic_post_init` to execute dataclass' original `__post_init__` before
  validation, [#560](https://github.com/pydantic/pydantic/pull/560) by @HeavenVolkoff
* fix handling of generic types without specified parameters, [#550](https://github.com/pydantic/pydantic/pull/550) by @dmontagu
* **breaking change** (maybe): this is the first release compiled with **cython**, see the docs and please
  submit an issue if you run into problems

## v0.27.0a1 (2019-05-26)

* fix JSON Schema for `list`, `tuple`, and `set`, [#540](https://github.com/pydantic/pydantic/pull/540) by @tiangolo
* compiling with cython, `manylinux` binaries, some other performance improvements, [#548](https://github.com/pydantic/pydantic/pull/548) by @samuelcolvin

## v0.26 (2019-05-22)

* fix to schema generation for `IPvAnyAddress`, `IPvAnyInterface`, `IPvAnyNetwork` [#498](https://github.com/pydantic/pydantic/pull/498) by @pilosus
* fix variable length tuples support, [#495](https://github.com/pydantic/pydantic/pull/495) by @pilosus
* fix return type hint for `create_model`, [#526](https://github.com/pydantic/pydantic/pull/526) by @dmontagu
* **Breaking Change:** fix `.dict(skip_keys=True)` skipping values set via alias (this involves changing
  `validate_model()` to always returns `Tuple[Dict[str, Any], Set[str], Optional[ValidationError]]`), [#517](https://github.com/pydantic/pydantic/pull/517) by @sommd
* fix to schema generation for `IPv4Address`, `IPv6Address`, `IPv4Interface`,
  `IPv6Interface`, `IPv4Network`, `IPv6Network` [#532](https://github.com/pydantic/pydantic/pull/532) by @euri10
* add `Color` type, [#504](https://github.com/pydantic/pydantic/pull/504) by @pilosus and @samuelcolvin

## v0.25 (2019-05-05)

* Improve documentation on self-referencing models and annotations, [#487](https://github.com/pydantic/pydantic/pull/487) by @theenglishway
* fix `.dict()` with extra keys, [#490](https://github.com/pydantic/pydantic/pull/490) by @JaewonKim
* support `const` keyword in `Schema`, [#434](https://github.com/pydantic/pydantic/pull/434) by @Sean1708

## v0.24 (2019-04-23)

* fix handling `ForwardRef` in sub-types, like `Union`, [#464](https://github.com/pydantic/pydantic/pull/464) by @tiangolo
* fix secret serialization, [#465](https://github.com/pydantic/pydantic/pull/465) by @atheuz
* Support custom validators for dataclasses, [#454](https://github.com/pydantic/pydantic/pull/454) by @primal100
* fix `parse_obj` to cope with dict-like objects, [#472](https://github.com/pydantic/pydantic/pull/472) by @samuelcolvin
* fix to schema generation in nested dataclass-based models, [#474](https://github.com/pydantic/pydantic/pull/474) by @NoAnyLove
* fix `json` for `Path`, `FilePath`, and `DirectoryPath` objects, [#473](https://github.com/pydantic/pydantic/pull/473) by @mikegoodspeed

## v0.23 (2019-04-04)

* improve documentation for contributing section, [#441](https://github.com/pydantic/pydantic/pull/441) by @pilosus
* improve README.rst to include essential information about the package, [#446](https://github.com/pydantic/pydantic/pull/446) by @pilosus
* `IntEnum` support, [#444](https://github.com/pydantic/pydantic/pull/444) by @potykion
* fix PyObject callable value, [#409](https://github.com/pydantic/pydantic/pull/409) by @pilosus
* fix `black` deprecation warnings after update, [#451](https://github.com/pydantic/pydantic/pull/451) by @pilosus
* fix `ForwardRef` collection bug, [#450](https://github.com/pydantic/pydantic/pull/450) by @tigerwings
* Support specialized `ClassVars`, [#455](https://github.com/pydantic/pydantic/pull/455) by @tyrylu
* fix JSON serialization for `ipaddress` types, [#333](https://github.com/pydantic/pydantic/pull/333) by @pilosus
* add `SecretStr` and `SecretBytes` types, [#452](https://github.com/pydantic/pydantic/pull/452) by @atheuz

## v0.22 (2019-03-29)

* add `IPv{4,6,Any}Network` and `IPv{4,6,Any}Interface` types from `ipaddress` stdlib, [#333](https://github.com/pydantic/pydantic/pull/333) by @pilosus
* add docs for `datetime` types, [#386](https://github.com/pydantic/pydantic/pull/386) by @pilosus
* fix to schema generation in dataclass-based models, [#408](https://github.com/pydantic/pydantic/pull/408) by @pilosus
* fix path in nested models, [#437](https://github.com/pydantic/pydantic/pull/437) by @kataev
* add `Sequence` support, [#304](https://github.com/pydantic/pydantic/pull/304) by @pilosus

## v0.21.0 (2019-03-15)

* fix typo in `NoneIsNotAllowedError` message, [#414](https://github.com/pydantic/pydantic/pull/414) by @YaraslauZhylko
* add `IPvAnyAddress`, `IPv4Address` and `IPv6Address` types, [#333](https://github.com/pydantic/pydantic/pull/333) by @pilosus

## v0.20.1 (2019-02-26)

* fix type hints of `parse_obj` and similar methods, [#405](https://github.com/pydantic/pydantic/pull/405) by @erosennin
* fix submodel validation, [#403](https://github.com/pydantic/pydantic/pull/403) by @samuelcolvin
* correct type hints for `ValidationError.json`, [#406](https://github.com/pydantic/pydantic/pull/406) by @layday

## v0.20.0 (2019-02-18)

* fix tests for Python 3.8, [#396](https://github.com/pydantic/pydantic/pull/396) by @samuelcolvin
* Adds fields to the `dir` method for autocompletion in interactive sessions, [#398](https://github.com/pydantic/pydantic/pull/398) by @dgasmith
* support `ForwardRef` (and therefore `from __future__ import annotations`) with dataclasses, [#397](https://github.com/pydantic/pydantic/pull/397) by @samuelcolvin

## v0.20.0a1 (2019-02-13)

* **breaking change** (maybe): more sophisticated argument parsing for validators, any subset of
  `values`, `config` and `field` is now permitted, eg. `(cls, value, field)`,
  however the variadic key word argument ("`**kwargs`") **must** be called `kwargs`, [#388](https://github.com/pydantic/pydantic/pull/388) by @samuelcolvin
* **breaking change**: Adds `skip_defaults` argument to `BaseModel.dict()` to allow skipping of fields that
  were not explicitly set, signature of `Model.construct()` changed, [#389](https://github.com/pydantic/pydantic/pull/389) by @dgasmith
* add `py.typed` marker file for PEP-561 support, [#391](https://github.com/pydantic/pydantic/pull/391) by @je-l
* Fix `extra` behaviour for multiple inheritance/mix-ins, [#394](https://github.com/pydantic/pydantic/pull/394) by @YaraslauZhylko

## v0.19.0 (2019-02-04)

* Support `Callable` type hint, fix [#279](https://github.com/pydantic/pydantic/pull/279) by @proofit404
* Fix schema for fields with `validator` decorator, fix [#375](https://github.com/pydantic/pydantic/pull/375) by @tiangolo
* Add `multiple_of` constraint to `ConstrainedDecimal`, `ConstrainedFloat`, `ConstrainedInt`
  and their related types `condecimal`, `confloat`, and `conint` [#371](https://github.com/pydantic/pydantic/pull/371), thanks @StephenBrown2
* Deprecated `ignore_extra` and `allow_extra` Config fields in favor of `extra`, [#352](https://github.com/pydantic/pydantic/pull/352) by @liiight
* Add type annotations to all functions, test fully with mypy, [#373](https://github.com/pydantic/pydantic/pull/373) by @samuelcolvin
* fix for 'missing' error with `validate_all` or `validate_always`, [#381](https://github.com/pydantic/pydantic/pull/381) by @samuelcolvin
* Change the second/millisecond watershed for date/datetime parsing to `2e10`, [#385](https://github.com/pydantic/pydantic/pull/385) by @samuelcolvin

## v0.18.2 (2019-01-22)

* Fix to schema generation with `Optional` fields, fix [#361](https://github.com/pydantic/pydantic/pull/361) by @samuelcolvin

## v0.18.1 (2019-01-17)

* add `ConstrainedBytes` and `conbytes` types, [#315](https://github.com/pydantic/pydantic/pull/315) @Gr1N
* adding `MANIFEST.in` to include license in package `.tar.gz`, [#358](https://github.com/pydantic/pydantic/pull/358) by @samuelcolvin

## v0.18.0 (2019-01-13)

* **breaking change**: don't call validators on keys of dictionaries, [#254](https://github.com/pydantic/pydantic/pull/254) by @samuelcolvin
* Fix validators with `always=True` when the default is `None` or the type is optional, also prevent
  `whole` validators being called for sub-fields, fix [#132](https://github.com/pydantic/pydantic/pull/132) by @samuelcolvin
* improve documentation for settings priority and allow it to be easily changed, [#343](https://github.com/pydantic/pydantic/pull/343) by @samuelcolvin
* fix `ignore_extra=False` and `allow_population_by_alias=True`, fix [#257](https://github.com/pydantic/pydantic/pull/257) by @samuelcolvin
* **breaking change**: Set `BaseConfig` attributes `min_anystr_length` and `max_anystr_length` to
  `None` by default, fix [#349](https://github.com/pydantic/pydantic/pull/349) in [#350](https://github.com/pydantic/pydantic/pull/350) by @tiangolo
* add support for postponed annotations, [#348](https://github.com/pydantic/pydantic/pull/348) by @samuelcolvin

## v0.17.0 (2018-12-27)

* fix schema for `timedelta` as number, [#325](https://github.com/pydantic/pydantic/pull/325) by @tiangolo
* prevent validators being called repeatedly after inheritance, [#327](https://github.com/pydantic/pydantic/pull/327) by @samuelcolvin
* prevent duplicate validator check in ipython, fix [#312](https://github.com/pydantic/pydantic/pull/312) by @samuelcolvin
* add "Using Pydantic" section to docs, [#323](https://github.com/pydantic/pydantic/pull/323) by @tiangolo & [#326](https://github.com/pydantic/pydantic/pull/326) by @samuelcolvin
* fix schema generation for fields annotated as `: dict`, `: list`,
  `: tuple` and `: set`, [#330](https://github.com/pydantic/pydantic/pull/330) & [#335](https://github.com/pydantic/pydantic/pull/335) by @nkonin
* add support for constrained strings as dict keys in schema, [#332](https://github.com/pydantic/pydantic/pull/332) by @tiangolo
* support for passing Config class in dataclasses decorator, [#276](https://github.com/pydantic/pydantic/pull/276) by @jarekkar
  (**breaking change**: this supersedes the `validate_assignment` argument with `config`)
* support for nested dataclasses, [#334](https://github.com/pydantic/pydantic/pull/334) by @samuelcolvin
* better errors when getting an `ImportError` with `PyObject`, [#309](https://github.com/pydantic/pydantic/pull/309) by @samuelcolvin
* rename `get_validators` to `__get_validators__`, deprecation warning on use of old name, [#338](https://github.com/pydantic/pydantic/pull/338) by @samuelcolvin
* support `ClassVar` by excluding such attributes from fields, [#184](https://github.com/pydantic/pydantic/pull/184) by @samuelcolvin

## v0.16.1 (2018-12-10)

* fix `create_model` to correctly use the passed `__config__`, [#320](https://github.com/pydantic/pydantic/pull/320) by @hugoduncan

## v0.16.0 (2018-12-03)

* **breaking change**: refactor schema generation to be compatible with JSON Schema and OpenAPI specs, [#308](https://github.com/pydantic/pydantic/pull/308) by @tiangolo
* add `schema` to `schema` module to generate top-level schemas from base models, [#308](https://github.com/pydantic/pydantic/pull/308) by @tiangolo
* add additional fields to `Schema` class to declare validation for `str` and numeric values, [#311](https://github.com/pydantic/pydantic/pull/311) by @tiangolo
* rename `_schema` to `schema` on fields, [#318](https://github.com/pydantic/pydantic/pull/318) by @samuelcolvin
* add `case_insensitive` option to `BaseSettings` `Config`, [#277](https://github.com/pydantic/pydantic/pull/277) by @jasonkuhrt

## v0.15.0 (2018-11-18)

* move codebase to use black, [#287](https://github.com/pydantic/pydantic/pull/287) by @samuelcolvin
* fix alias use in settings, [#286](https://github.com/pydantic/pydantic/pull/286) by @jasonkuhrt and @samuelcolvin
* fix datetime parsing in `parse_date`, [#298](https://github.com/pydantic/pydantic/pull/298) by @samuelcolvin
* allow dataclass inheritance, fix [#293](https://github.com/pydantic/pydantic/pull/293) by @samuelcolvin
* fix `PyObject = None`, fix [#305](https://github.com/pydantic/pydantic/pull/305) by @samuelcolvin
* allow `Pattern` type, fix [#303](https://github.com/pydantic/pydantic/pull/303) by @samuelcolvin

## v0.14.0 (2018-10-02)

* dataclasses decorator, [#269](https://github.com/pydantic/pydantic/pull/269) by @Gaunt and @samuelcolvin

## v0.13.1 (2018-09-21)

* fix issue where int_validator doesn't cast a `bool` to an `int` [#264](https://github.com/pydantic/pydantic/pull/264) by @nphyatt
* add deep copy support for `BaseModel.copy()` [#249](https://github.com/pydantic/pydantic/pull/249), @gangefors

## v0.13.0 (2018-08-25)

* raise an exception if a field's name shadows an existing `BaseModel` attribute [#242](https://github.com/pydantic/pydantic/pull/242)
* add `UrlStr` and `urlstr` types [#236](https://github.com/pydantic/pydantic/pull/236)
* timedelta json encoding ISO8601 and total seconds, custom json encoders [#247](https://github.com/pydantic/pydantic/pull/247), by @cfkanesan and @samuelcolvin
* allow `timedelta` objects as values for properties of type `timedelta` (matches `datetime` etc. behavior) [#247](https://github.com/pydantic/pydantic/pull/247)

## v0.12.1 (2018-07-31)

* fix schema generation for fields defined using `typing.Any` [#237](https://github.com/pydantic/pydantic/pull/237)

## v0.12.0 (2018-07-31)

* add `by_alias` argument in `.dict()` and `.json()` model methods [#205](https://github.com/pydantic/pydantic/pull/205)
* add Json type support [#214](https://github.com/pydantic/pydantic/pull/214)
* support tuples [#227](https://github.com/pydantic/pydantic/pull/227)
* major improvements and changes to schema [#213](https://github.com/pydantic/pydantic/pull/213)

## v0.11.2 (2018-07-05)

* add `NewType` support [#115](https://github.com/pydantic/pydantic/pull/115)
* fix `list`, `set` & `tuple` validation [#225](https://github.com/pydantic/pydantic/pull/225)
* separate out `validate_model` method, allow errors to be returned along with valid values [#221](https://github.com/pydantic/pydantic/pull/221)

## v0.11.1 (2018-07-02)

* support Python 3.7 [#216](https://github.com/pydantic/pydantic/pull/216), thanks @layday
* Allow arbitrary types in model [#209](https://github.com/pydantic/pydantic/pull/209), thanks @oldPadavan

## v0.11.0 (2018-06-28)

* make `list`, `tuple` and `set` types stricter [#86](https://github.com/pydantic/pydantic/pull/86)
* **breaking change**: remove msgpack parsing [#201](https://github.com/pydantic/pydantic/pull/201)
* add `FilePath` and `DirectoryPath` types [#10](https://github.com/pydantic/pydantic/pull/10)
* model schema generation [#190](https://github.com/pydantic/pydantic/pull/190)
* JSON serialization of models and schemas [#133](https://github.com/pydantic/pydantic/pull/133)

## v0.10.0 (2018-06-11)

* add `Config.allow_population_by_alias` [#160](https://github.com/pydantic/pydantic/pull/160), thanks @bendemaree
* **breaking change**: new errors format [#179](https://github.com/pydantic/pydantic/pull/179), thanks @Gr1N
* **breaking change**: removed `Config.min_number_size` and `Config.max_number_size` [#183](https://github.com/pydantic/pydantic/pull/183), thanks @Gr1N
* **breaking change**: correct behaviour of `lt` and `gt` arguments to `conint` etc. [#188](https://github.com/pydantic/pydantic/pull/188)
  for the old behaviour use `le` and `ge` [#194](https://github.com/pydantic/pydantic/pull/194), thanks @jaheba
* added error context and ability to redefine error message templates using `Config.error_msg_templates` [#183](https://github.com/pydantic/pydantic/pull/183),
  thanks @Gr1N
* fix typo in validator exception [#150](https://github.com/pydantic/pydantic/pull/150)
* copy defaults to model values, so different models don't share objects [#154](https://github.com/pydantic/pydantic/pull/154)

## v0.9.1 (2018-05-10)

* allow custom `get_field_config` on config classes [#159](https://github.com/pydantic/pydantic/pull/159)
* add `UUID1`, `UUID3`, `UUID4` and `UUID5` types [#167](https://github.com/pydantic/pydantic/pull/167), thanks @Gr1N
* modify some inconsistent docstrings and annotations [#173](https://github.com/pydantic/pydantic/pull/173), thanks @YannLuo
* fix type annotations for exotic types [#171](https://github.com/pydantic/pydantic/pull/171), thanks @Gr1N
* re-use type validators in exotic types [#171](https://github.com/pydantic/pydantic/pull/171)
* scheduled monthly requirements updates [#168](https://github.com/pydantic/pydantic/pull/168)
* add `Decimal`, `ConstrainedDecimal` and `condecimal` types [#170](https://github.com/pydantic/pydantic/pull/170), thanks @Gr1N

## v0.9.0 (2018-04-28)

* tweak email-validator import error message [#145](https://github.com/pydantic/pydantic/pull/145)
* fix parse error of `parse_date()` and `parse_datetime()` when input is 0 [#144](https://github.com/pydantic/pydantic/pull/144), thanks @YannLuo
* add `Config.anystr_strip_whitespace` and `strip_whitespace` kwarg to `constr`,
  by default values is `False` [#163](https://github.com/pydantic/pydantic/pull/163), thanks @Gr1N
* add `ConstrainedFloat`, `confloat`, `PositiveFloat` and `NegativeFloat` types [#166](https://github.com/pydantic/pydantic/pull/166), thanks @Gr1N

## v0.8.0 (2018-03-25)

* fix type annotation for `inherit_config` [#139](https://github.com/pydantic/pydantic/pull/139)
* **breaking change**: check for invalid field names in validators [#140](https://github.com/pydantic/pydantic/pull/140)
* validate attributes of parent models [#141](https://github.com/pydantic/pydantic/pull/141)
* **breaking change**: email validation now uses
  [email-validator](https://github.com/JoshData/python-email-validator) [#142](https://github.com/pydantic/pydantic/pull/142)

## v0.7.1 (2018-02-07)

* fix bug with `create_model` modifying the base class

## v0.7.0 (2018-02-06)

* added compatibility with abstract base classes (ABCs) [#123](https://github.com/pydantic/pydantic/pull/123)
* add `create_model` method [#113](https://github.com/pydantic/pydantic/pull/113) [#125](https://github.com/pydantic/pydantic/pull/125)
* **breaking change**: rename `.config` to `.__config__` on a model
* **breaking change**: remove deprecated `.values()` on a model, use `.dict()` instead
* remove use of `OrderedDict` and use simple dict [#126](https://github.com/pydantic/pydantic/pull/126)
* add `Config.use_enum_values` [#127](https://github.com/pydantic/pydantic/pull/127)
* add wildcard validators of the form `@validate('*')` [#128](https://github.com/pydantic/pydantic/pull/128)

## v0.6.4 (2018-02-01)

* allow Python date and times objects [#122](https://github.com/pydantic/pydantic/pull/122)

## v0.6.3 (2017-11-26)

* fix direct install without `README.rst` present

## v0.6.2 (2017-11-13)

* errors for invalid validator use
* safer check for complex models in `Settings`

## v0.6.1 (2017-11-08)

* prevent duplicate validators, [#101](https://github.com/pydantic/pydantic/pull/101)
* add `always` kwarg to validators, [#102](https://github.com/pydantic/pydantic/pull/102)

## v0.6.0 (2017-11-07)

* assignment validation [#94](https://github.com/pydantic/pydantic/pull/94), thanks petroswork!
* JSON in environment variables for complex types, [#96](https://github.com/pydantic/pydantic/pull/96)
* add `validator` decorators for complex validation, [#97](https://github.com/pydantic/pydantic/pull/97)
* depreciate `values(...)` and replace with `.dict(...)`, [#99](https://github.com/pydantic/pydantic/pull/99)

## v0.5.0 (2017-10-23)

* add `UUID` validation [#89](https://github.com/pydantic/pydantic/pull/89)
* remove `index` and `track` from error object (json) if they're null [#90](https://github.com/pydantic/pydantic/pull/90)
* improve the error text when a list is provided rather than a dict [#90](https://github.com/pydantic/pydantic/pull/90)
* add benchmarks table to docs [#91](https://github.com/pydantic/pydantic/pull/91)

## v0.4.0 (2017-07-08)

* show length in string validation error
* fix aliases in config during inheritance [#55](https://github.com/pydantic/pydantic/pull/55)
* simplify error display
* use unicode ellipsis in `truncate`
* add `parse_obj`, `parse_raw` and `parse_file` helper functions [#58](https://github.com/pydantic/pydantic/pull/58)
* switch annotation only fields to come first in fields list not last

## v0.3.0 (2017-06-21)

* immutable models via `config.allow_mutation = False`, associated cleanup and performance improvement [#44](https://github.com/pydantic/pydantic/pull/44)
* immutable helper methods `construct()` and `copy()` [#53](https://github.com/pydantic/pydantic/pull/53)
* allow pickling of models [#53](https://github.com/pydantic/pydantic/pull/53)
* `setattr` is removed as `__setattr__` is now intelligent [#44](https://github.com/pydantic/pydantic/pull/44)
* `raise_exception` removed, Models now always raise exceptions [#44](https://github.com/pydantic/pydantic/pull/44)
* instance method validators removed
* django-restful-framework benchmarks added [#47](https://github.com/pydantic/pydantic/pull/47)
* fix inheritance bug [#49](https://github.com/pydantic/pydantic/pull/49)
* make str type stricter so list, dict etc are not coerced to strings. [#52](https://github.com/pydantic/pydantic/pull/52)
* add `StrictStr` which only always strings as input [#52](https://github.com/pydantic/pydantic/pull/52)

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
