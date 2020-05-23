Updates OpenAPI schema generation to output all enums as separate models.
Instead of inlining the enum values in the model schema, models now use a `$ref`
property to point to the enum definition.