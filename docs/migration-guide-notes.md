# Note: This file's contents should be merged into migration.md, and this file should be deleted before this PR is done.

Migration guide
---------------

* Validation behavior changes (Maybe a separate top-level section)
	* [idea: this contains the part of the coercion table that has changed from v1 to v2]
	* Some examples:
		* int, float, decimal no longer coerced to string
		* iterable of pairs no longer coerced to a dict

* Types
	* JSON schema
		* no longer preserves namedtuples


* Catch-all for moved/deprecated/removed methods, functions, and config keys
	* [not sure if goes here:] pydantic.tools functions (e.g. parse_obj_as) replaced by TypeAdapter

	* Moved v1 functionality
		* ... [list things in `MOVED_IN_V2`]
		* ... [list config keys in `V2_RENAMED_KEYS`]
		* PyObject -> ImportString

	* Deprecated v1 functionality
		* `parse_file` and `parse_raw` are gone; `model_validate_json` is like `parse_raw` for json; otherwise, load data and use `model_validate`
		* ... [list BaseModel methods that have been deprecated]
		* ... [list things from `DEPRECATED_MOVED_IN_V2`]
        * `GetterDict` has been removed, as it was just an implementation detail for `orm_mode`, which has been removed.

	* Removed v1 functionality
		* Config.fields
		* stricturl
		* __post_init_post_parse__
		* ... [list things in `REMOVED_IN_V2`]
		* ... [list config keys in `V2_REMOVED_KEYS`]

* Various deprecated things are available in `pydantic.v1`
