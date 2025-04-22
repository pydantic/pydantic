from typing import TypedDict

from typing_extensions import TypeAlias
from pydantic._internal._decorators import inspect_validator, inspect_annotated_serializer
from pydantic_core import CoreSchema, core_schema


ValidatorFunction: TypeAlias = core_schema.NoInfoValidatorFunction | core_schema.WithInfoValidatorFunction


class ValidationSpec(TypedDict):
    python: ValidatorFunction
    json: ValidatorFunction


class SerializationSpec(TypedDict, total=False):
    python: core_schema.SerializerFunction
    json: core_schema.SerializerFunction


def _val_schema(validator: ValidatorFunction) -> core_schema.PlainValidatorFunctionSchema:
    if inspect_validator(validator, mode='plain'):
        return core_schema.with_info_plain_validator_function(validator)
    else:
        return core_schema.no_info_plain_validator_function(validator)


def _ser_schema(
    serializer: core_schema.SerializerFunction, when_used: core_schema.WhenUsed = 'always'
) -> core_schema.PlainSerializerFunctionSerSchema:
    return core_schema.plain_serializer_function_ser_schema(
        function=serializer,
        info_arg=inspect_annotated_serializer(serializer, mode='plain'),
        when_used=when_used,
    )


def custom_type_schema(
    validator: ValidatorFunction | ValidationSpec,
    # TODO core_schema.SerializerFunction is too broad
    serializer: core_schema.SerializerFunction | SerializationSpec | None = None,
) -> CoreSchema:
    if callable(validator):
        val_schema = _val_schema(validator)

        if callable(serializer):
            val_schema['serialization'] = _ser_schema(serializer)
            schema = val_schema
        elif serializer is not None:
            json_serializer = serializer.get('json')
            python_serializer = serializer.get('python')
            if json_serializer is not None and python_serializer is None:
                val_schema['serialization'] = _ser_schema(json_serializer, when_used='json')
                schema = val_schema
            else:
                schema = core_schema.json_or_python_schema(
                    json_schema=val_schema,
                    python_schema=val_schema.copy(),
                )
                if python_serializer is not None:
                    schema['python_schema']['serialization'] = _ser_schema(python_serializer)
                if json_serializer is not None:
                    schema['json_schema']['serialization'] = _ser_schema(json_serializer)
        else:
            schema = val_schema
    else:
        json_validator = validator['json']
        python_validator = validator['python']

        json_schema = _val_schema(json_validator)
        python_schema = _val_schema(python_validator)
        schema = core_schema.json_or_python_schema(
            json_schema=json_schema,
            python_schema=python_schema,
        )
        if callable(serializer):
            schema['serialization'] = _ser_schema(serializer)
        elif serializer is not None:
            json_serializer = serializer.get('json')
            python_serializer = serializer.get('python')
            if json_serializer is not None:
                schema['json_schema']['serialization'] = _ser_schema(json_serializer)
                if python_serializer is None:
                    # If no Python serializer is set, we can also set the JSON serialization
                    # schema on the python_schema (with when_used='json'). This will be used
                    # when doing `model_dump(mode='json')`. Else, there's no way to support it.
                    schema['python_schema']['serialization'] = _ser_schema(json_serializer, when_used='json')
            if python_serializer is not None:
                schema['python_schema']['serialization'] = _ser_schema(python_serializer)

    return schema
