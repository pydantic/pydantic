Add `Config.copy_on_model_validation` flag. When set to `False`, _pydantic_ will keep models used as fields
untouched on validation instead of reconstructing (copying) them