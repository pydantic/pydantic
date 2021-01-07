"""This module defines a fragment model for pydantic.

To do:
    - schema generation currently only works when done directly
      on a concrete instance of the model.
    - calling schema() on a model containing a Fragment will
      currently fail
    - is it possible to make Fragment(FullModel, a=1, b=2)
      equivalent to Fragment[FullModel](a=1, b=2)?
"""

from __future__ import annotations

from typing import Any, Dict, Generic, Optional, Set, Type, TypeVar

from pydantic import BaseModel, ValidationError
from pydantic.error_wrappers import ErrorWrapper
from pydantic.generics import GenericModel

DictStrAny = Dict[str, Any]

T = TypeVar('T', bound=BaseModel)

_missing = object()


class Fragment(GenericModel, Generic[T]):
    """Fragment of a pydantic model.


    A fragment of a model is a subset of that model, requiring that
    set attributes are individually valid but not requiring any
    attributes to be set.
    """

    model_: Type[T]

    class Config:
        extra = 'allow'  # essentially everything is extra.
        allow_mutation = False

    def __init__(__pydantic_self__, __model__: Optional[Type[T]] = None, **data: Any):
        """Initialises the Fragment by validating against __model__'s fields.
        Args:
            __model__: The model this is a fragment of - positional only.
            **data: The fields expected by the __model__.
        """

        model = __model__  # __model__ is underscored in the method arguments to prevent a name clash.

        if model is None and __pydantic_self__.__concrete__:
            expected_model_type = __pydantic_self__.__fields__['model_'].type_.__args__[0]
            model = expected_model_type

        elif model and not __pydantic_self__.__concrete__:
            # Still generic
            expected_model_type = model

        elif model is None and not __pydantic_self__.__concrete__:
            raise TypeError('Fragments must be of another model.')

        else:
            if model != expected_model_type:
                raise TypeError(f'Expected a fragment of {expected_model_type}.')

        values: Dict[str, Any] = {}
        errors = []
        fields_set: Set[str] = set()
        for name, field in model.__fields__.items():
            value = data.pop(field.alias, _missing)
            # using_name = False
            if value is _missing and model.__config__.allow_population_by_field_name and field.alt_alias:
                value = data.get(field.name, _missing)
                # using_name = True
            if value is not _missing:
                # add to field_set?
                # check_extra?
                v_, errors_ = field.validate(value, values, loc=field.alias, cls=model)
                if isinstance(errors_, ErrorWrapper):
                    errors.append(errors_)
                elif isinstance(errors_, list):
                    errors.extend(errors_)
                else:
                    values[name] = v_
        if errors:
            raise (ValidationError(errors, model))
        else:
            if model.__config__.extra == 'allow':
                values.update(data)
            values['model_'] = model
            object.__setattr__(__pydantic_self__, '__dict__', values)
            object.__setattr__(__pydantic_self__, '__fields_set__', fields_set)
            __pydantic_self__._init_private_attributes()

    @classmethod
    def schema(cls, *args: Any, **kwargs: Any) -> DictStrAny:
        """Overrides the standard BaseModel schema.

        The standard basemodel schema is generated, but all fields
        are removed from 'required'. 'Fragment' is appended to the title of the schema.

        The model_ field is excluded from the schema as it represents a type.
        """
        if cls.__concrete__:
            model = cls.__fields__['model_'].type_.__args__[0]
            model_schema = model.schema(*args, **kwargs)
            title = model_schema['title'] + 'Fragment'
            return {**model_schema, **{'required': [], 'title': title}}
        else:
            # todo: no idea what to return of not concrete,
            #       and because classmethod can't use __pydantic_self__.model_
            return {}

    def dict(__pydantic_self__, *args: Any, **kwargs: Any) -> DictStrAny:
        """Overrides the standard BaseModel dict to exclude 'model_'."""
        exclude = {
            'model_',
        }
        user_exclude = kwargs.pop('exclude', None)
        if user_exclude:
            exclude = exclude.union(user_exclude)
        return super().dict(*args, exclude=exclude, **kwargs)
