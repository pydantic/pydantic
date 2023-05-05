Below are details on common errors developers can see when working with pydantic, together
with some suggestions on how to fix them.

{% raw %}
## Decorator on missing field {#decorator-missing-field}

TODO

## Dataclass not fully defined {#dataclass-not-fully-defined}

TODO

## Discriminator no field {#discriminator-no-field}

TODO

## Discriminator alias type {#discriminator-alias-type}

TODO

## Discriminator needs literal {#discriminator-needs-literal}

TODO

## Discriminator alias {#discriminator-alias}

TODO

## TypedDict version {#typed-dict-version}

TODO

## Model parent field overridden {#model-field-overridden}

TODO

## Model field missing annotation {#model-field-missing-annotation}

TODO

## Model not fully defined {#model-not-fully-defined}

TODO

## Config and model_config both defined {#config-both}

TODO

## Keyword arguments deprecated {#deprecated_kwargs}

The keyword arguments are not available in Pydantic V2.

## JSON Schema invalid type {#invalid-for-json-schema}

TODO

## JSON Schema already used {#json-schema-already-used}

TODO

## BaseModel instantiated {#base-model-instantiated}

TODO

## Undefined annotation {#undefined-annotation}

TODO

## Schema for unknown type {#schema-for-unknown-type}

TODO

## Import error {#import-error}

This error is raised when you try to import an object that was available in V1 but has been removed in V2.

## create_model field definitions {#create-model-field-definitions}

TODO

## create_model config base {#create-model-config-base}

TODO

## Validator with no fields {#validator-no-fields}

validator should be used with fields and keyword arguments, not bare.

E.g. usage should be `@validator('<field_name>', ...)`

## Invalid validator fields {#validator-invalid-fields}

validator fields should be passed as separate string args.

E.g. usage should be `@validator('<field_name_1>', '<field_name_2>', ...)`

## Validator on instance method {#validator-instance-method}

`@validator` cannot be applied to instance methods

## Root Validator, pre, skip_on_failure {#root-validator-pre-skip}

If you use `@root_validator` with pre=False (the default) you MUST specify `skip_on_failure=True`.
The `skip_on_failure=False` option is no longer available.
If you were not trying to set `skip_on_failure=False` you can safely set `skip_on_failure=True`.
If you do, this root validator will no longer be called if validation fails for any of the fields.

Please see the migration guide for more details. TODO link

## model_validator instance methods {#model-serializer-instance-method}

`@model_serializer` must be applied to instance methods

## validator, field, config and info {#validator-field-config-info}

The `field` and `config` parameters are not available in Pydantic V2.
Please use the `info` parameter instead. You can access the configuration via `info.config`
but it is a dictionary instead of an object like it was in Pydantic V1.
The `field` argument is no longer available.

## V1 validator signature {#validator-v1-signature}

TODO

## Unrecognized field_validator signature {#field-validator-signature}

TODO

## Unrecognized field_serializer signature {#field-serializer-signature}

Valid serializer signatures are:

```py test="skip" lint="skip" upgrade="skip"
from pydantic import model_serializer

# an instance method with the default mode or `mode='plain'`
@model_serializer('x')  # or @serialize('x', mode='plain')
def ser_x(self, value: Any, info: pydantic.FieldSerializationInfo): ...

# a static method or free-standing function with the default mode or `mode='plain'`
@model_serializer('x')  # or @serialize('x', mode='plain')
@staticmethod
def ser_x(value: Any, info: pydantic.FieldSerializationInfo): ...
# equivalent to
def ser_x(value: Any, info: pydantic.FieldSerializationInfo): ...
serializer('x')(ser_x)

# an instance method with `mode='wrap'`
@model_serializer('x', mode='wrap')
def ser_x(self, value: Any, nxt: pydantic.SerializerFunctionWrapHandler, info: pydantic.FieldSerializationInfo): ...

# a static method or free-standing function with `mode='wrap'`
@model_serializer('x', mode='wrap')
@staticmethod
def ser_x(value: Any, nxt: pydantic.SerializerFunctionWrapHandler, info: pydantic.FieldSerializationInfo): ...
# equivalent to
def ser_x(value: Any, nxt: pydantic.SerializerFunctionWrapHandler, info: pydantic.FieldSerializationInfo): ...
serializer('x')(ser_x)

For all of these, you can also choose to omit the `info` argument, for example:

@model_serializer('x')
def ser_x(self, value: Any): ...

@model_serializer('x', mode='wrap')
def ser_x(self, value: Any, handler: pydantic.SerializerFunctionWrapHandler): ...
```

## Unrecognized model_serializer signature {#model-serializer-signature}

TODO

## Multiple field serializers {#multiple-field-serializers}

TODO
{% endraw %}
