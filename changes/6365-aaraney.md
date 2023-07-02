Extra fields added via `setattr` (i.e. `m.some_extra_field = 'extra_value'`)
are added to `.model_extra` if `model_config` `extra='allowed'`. Fixed #6333.
