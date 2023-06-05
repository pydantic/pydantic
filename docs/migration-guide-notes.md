# Note: This file's contents should be merged into migration.md, and this file should be deleted before this PR is done.

Migration guide
---------------

* Dataclasses
	* Cannot parse tuples/lists into dataclasses used as fields, only dicts
	* Config is not "pushed down" for vanilla dataclases
	* __pydantic_model__ on pydantic dataclasses (use TypeAdapter; may not need to use a pydantic dataclass)


* Validation
	* @root_validator is deprecated (and may have had changes to what it should return..?)
		* Can't run with `skip_on_failure=False`
		* must not be bare [we should at least error..]
		* should be replaced by @model_validator; note under some circumstances `@model_validator` may receive an instance, not a dict
	* @validator is deprecated
		* should be replaced by @field_validator
		* @field_validator does not support each_item; use annotations on the generic parameters
			* Explain that List[int] = Field(..., ge=0) -> List[Annotated[int, Field(ge=0)]]
		* changes to signature of functions (no longer provide field or config -- use info)
	* Raising a TypeError inside a validator no longer produces a ValidationError
	* `validate_arguments` raises TypeError if you call the function with an invalid signature
	* always=True / validate_default will apply "standard" field validators, not just custom
		* [what does always=True mean in this case?]
	* Changes in validator overriding behavior, and removal of `allow_reuse`
	* Change to validation of unions where _instances_ are accepted before being validated


* Validation behavior changes (Maybe a separate top-level section)
	* [idea: this contains the part of the coercion table that has changed from v1 to v2]
	* Some examples:
		* int, float, decimal no longer coerced to string
		* iterable of pairs no longer coerced to a dict


* Types
	* Standard types
		* Issue with validating "large" ints (need to re-confirm, but I think it's an issue for JSON still; #5151)
		* Annotations of subclasses of builtins will be validated into the builtin (re-confirm; #5151)
		* No longer accept a plain dict or mapping as input to a list/set/frozenset field

	* Custom types
		* Replace __get_validators__ with __get_pydantic_core_schema__
		* Replace __modify_schema__ with __get_pydantic_json_schema__
		* Note: there is now more advanced functionality for using annotations to control the generation of the core/json schemas; more documentation to follow

	* JSON schema
		* no longer preserves namedtuples
		* Note: there is now more advanced functionality for overriding the generation of JSON schema; more documentation to follow


* Catch-all for moved/deprecated/removed methods, functions, and config keys
	* [not sure if goes here:] pydantic.tools functions (e.g. parse_obj_as) replaced by TypeAdapter

	* Moved v1 functionality
		* ... [list things in `MOVED_IN_V2`]
		* ... [list config keys in `V2_RENAMED_KEYS`]
		* PyObject -> ImporString

	* Deprecated v1 functionality
		* `parse_file` and `parse_raw` are gone; `model_validate_json` is like `parse_raw` for json; otherwise, load data and use `model_validate`
		* ... [list BaseModel methods that have been deprecated]
		* ... [list things from `DEPRECATED_MOVED_IN_V2`]

	* Removed v1 functionality
		* Config.fields
		* stricturl
		* __post_init_post_parse__
		* ... [list things in `REMOVED_IN_V2`]
		* ... [list config keys in `V2_REMOVED_KEYS`]
