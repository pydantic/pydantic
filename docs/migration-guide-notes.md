# Note: This file's contents should be merged into migration.md, and this file should be deleted before this PR is done.

Migration guide
---------------

* Validation behavior changes (Maybe a separate top-level section)
	* [idea: this contains the part of the coercion table that has changed from v1 to v2]
	* Some examples:
		* int, float, decimal no longer coerced to string
		* iterable of pairs no longer coerced to a dict

* Types
	* Standard types
        * Change to validation of unions where _instances_ are accepted before being validated
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

* Various deprecated things are available in `pydantic.v1`
