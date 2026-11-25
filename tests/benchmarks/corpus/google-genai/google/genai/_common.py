# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Frozen model corpus; modified from google-genai 2.34.0; see README.md and LICENSE.
import base64
import collections.abc
import datetime
import enum
import functools
import logging
import re
import sys
import typing
from typing import Any, Callable, FrozenSet, Optional, Union, get_args, get_origin
import uuid
import warnings
import pydantic
from pydantic import alias_generators
from typing_extensions import TypeAlias
logger = logging.getLogger('google_genai._common')
StringDict: TypeAlias = dict[str, Any]

def loaded_requests() -> Optional[Any]:
    return sys.modules.get('requests')

class ExperimentalWarning(Warning):
    """Warning for experimental features."""

def set_value_by_path(data: Optional[dict[Any, Any]], keys: list[str], value: Any) -> None:
    if value is None:
        return
    for i, key in enumerate(keys[:-1]):
        if key.endswith('[]'):
            key_name = key[:-2]
            if data is not None and key_name not in data:
                if isinstance(value, list):
                    data[key_name] = [{} for _ in range(len(value))]
                else:
                    raise ValueError(f'value {value} must be a list given an array path {key}')
            if isinstance(value, list) and data is not None:
                for j, d in enumerate(data[key_name]):
                    set_value_by_path(d, keys[i + 1:], value[j])
            elif data is not None:
                for d in data[key_name]:
                    set_value_by_path(d, keys[i + 1:], value)
            return
        elif key.endswith('[0]'):
            key_name = key[:-3]
            if data is not None and key_name not in data:
                data[key_name] = [{}]
            if data is not None:
                set_value_by_path(data[key_name][0], keys[i + 1:], value)
            return
        if data is not None:
            data = data.setdefault(key, {})
    if data is not None:
        existing_data = data.get(keys[-1])
        if existing_data is not None:
            if not value:
                pass
            elif value == existing_data:
                pass
            elif isinstance(existing_data, dict) and isinstance(value, dict):
                existing_data.update(value)
            else:
                raise ValueError(f'Cannot set value for an existing key. Key: {keys[-1]}; Existing value: {existing_data}; New value: {value}.')
        elif keys[-1] == '_self' and isinstance(data, dict) and isinstance(value, dict):
            data.update(value)
        else:
            data[keys[-1]] = value

def get_value_by_path(data: Any, keys: list[str], *, default_value: Any=None) -> Any:
    if keys == ['_self']:
        return data
    for i, key in enumerate(keys):
        if not data:
            return default_value
        if key.endswith('[]'):
            key_name = key[:-2]
            if key_name in data:
                return [get_value_by_path(d, keys[i + 1:], default_value=default_value) for d in data[key_name]]
            else:
                return default_value
        elif key.endswith('[0]'):
            key_name = key[:-3]
            if key_name in data and data[key_name]:
                return get_value_by_path(data[key_name][0], keys[i + 1:], default_value=default_value)
            else:
                return default_value
        elif key in data:
            data = data[key]
        elif isinstance(data, BaseModel) and hasattr(data, key):
            data = getattr(data, key)
        else:
            return default_value
    return data

def move_value_by_path(data: Any, paths: dict[str, str]) -> None:
    for source_path, dest_path in paths.items():
        source_keys = source_path.split('.')
        dest_keys = dest_path.split('.')
        exclude_keys = set()
        wildcard_idx = -1
        for i, key in enumerate(source_keys):
            if key == '*':
                wildcard_idx = i
                break
        if wildcard_idx != -1 and len(dest_keys) > wildcard_idx:
            for i in range(wildcard_idx, len(dest_keys)):
                key = dest_keys[i]
                if key != '*' and (not key.endswith('[]')) and (not key.endswith('[0]')):
                    exclude_keys.add(key)
        _move_value_recursive(data, source_keys, dest_keys, 0, exclude_keys)

def _move_value_recursive(data: Any, source_keys: list[str], dest_keys: list[str], key_idx: int, exclude_keys: set[str]) -> None:
    if key_idx >= len(source_keys):
        return
    key = source_keys[key_idx]
    if key.endswith('[]'):
        key_name = key[:-2]
        if key_name in data and isinstance(data[key_name], list):
            for item in data[key_name]:
                _move_value_recursive(item, source_keys, dest_keys, key_idx + 1, exclude_keys)
    elif key == '*':
        if isinstance(data, dict):
            keys_to_move = [k for k in list(data.keys()) if not k.startswith('_') and k not in exclude_keys]
            values_to_move = {k: data[k] for k in keys_to_move}
            for k, v in values_to_move.items():
                new_dest_keys = []
                for dk in dest_keys[key_idx:]:
                    if dk == '*':
                        new_dest_keys.append(k)
                    else:
                        new_dest_keys.append(dk)
                set_value_by_path(data, new_dest_keys, v)
            for k in keys_to_move:
                del data[k]
    elif key in data:
        _move_value_recursive(data[key], source_keys, dest_keys, key_idx + 1, exclude_keys)

def maybe_snake_to_camel(snake_str: str, convert: bool=True) -> str:
    if not convert:
        return snake_str
    return re.sub('_([a-zA-Z])', lambda match: match.group(1).upper(), snake_str)

def convert_to_dict(obj: object, convert_keys: bool=False) -> Any:
    if isinstance(obj, pydantic.BaseModel):
        return convert_to_dict(obj.model_dump(exclude_none=True), convert_keys)
    elif isinstance(obj, dict):
        return {maybe_snake_to_camel(key, convert_keys): convert_to_dict(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_dict(item, convert_keys) for item in obj]
    else:
        return obj

def _is_struct_type(annotation: type) -> bool:
    outer_origin = get_origin(annotation)
    outer_args = get_args(annotation)
    if outer_origin is not list:
        return False
    if not outer_args or len(outer_args) != 1:
        return False
    inner_annotation = outer_args[0]
    inner_origin = get_origin(inner_annotation)
    inner_args = get_args(inner_annotation)
    if inner_origin is not dict:
        return False
    if not inner_args or len(inner_args) != 2:
        return False
    key_type, value_type = inner_args
    return key_type is str and value_type is typing.Any

def _as_base_model_type(annotation: Any) -> Optional[typing.Type[pydantic.BaseModel]]:
    while typing.get_origin(annotation) is typing.Annotated:
        annotation = typing.get_args(annotation)[0]
    if isinstance(annotation, type) and issubclass(annotation, pydantic.BaseModel):
        return annotation
    return None

def _remove_extra_fields(model: Any, response: dict[str, object]) -> None:
    if isinstance(model, type) and issubclass(model, pydantic.BaseModel):
        model.model_rebuild(raise_errors=False)
    key_values = list(response.items())
    for key, value in key_values:
        alias_map = {field_info.alias: key for key, field_info in model.model_fields.items()}
        if key not in model.model_fields and key not in alias_map:
            response.pop(key)
            continue
        key = alias_map.get(key, key)
        annotation = model.model_fields[key].annotation
        if typing.get_origin(annotation) is Union:
            annotation = typing.get_args(annotation)[0]
        model_type = _as_base_model_type(annotation)
        if isinstance(value, dict) and model_type is not None:
            _remove_extra_fields(model_type, value)
        elif isinstance(value, list):
            if _is_struct_type(annotation):
                continue
            item_type_args = typing.get_args(annotation)
            item_type = _as_base_model_type(item_type_args[0] if item_type_args else None)
            if item_type is None:
                continue
            for item in value:
                if isinstance(item, dict):
                    _remove_extra_fields(item_type, item)
T = typing.TypeVar('T', bound='BaseModel')

def _pretty_repr(obj: Any, *, indent_level: int=0, indent_delta: int=2, max_len: int=100, max_items: int=5, depth: int=6, visited: Optional[FrozenSet[int]]=None) -> str:
    if visited is None:
        visited = frozenset()
    obj_id = id(obj)
    if obj_id in visited:
        return '<... Circular reference ...>'
    if depth < 0:
        return '<... Max depth ...>'
    visited = frozenset(list(visited) + [obj_id])
    indent = ' ' * indent_level
    next_indent_str = ' ' * (indent_level + indent_delta)
    if isinstance(obj, pydantic.BaseModel):
        cls_name = obj.__class__.__name__
        items = []
        fields = sorted(type(obj).model_fields)
        for field_name in fields:
            field_info = type(obj).model_fields[field_name]
            if not field_info.repr:
                continue
            try:
                value = getattr(obj, field_name)
            except AttributeError:
                continue
            if value is None:
                continue
            value_repr = _pretty_repr(value, indent_level=indent_level + indent_delta, indent_delta=indent_delta, max_len=max_len, max_items=max_items, depth=depth - 1, visited=visited)
            items.append(f'{next_indent_str}{field_name}={value_repr}')
        if not items:
            return f'{cls_name}()'
        return f'{cls_name}(\n' + ',\n'.join(items) + f'\n{indent})'
    elif isinstance(obj, str):
        if '\n' in obj:
            escaped = obj.replace('"""', '\\"\\"\\"')
            return f'"""{escaped}"""'
        return repr(obj)
    elif isinstance(obj, bytes):
        if len(obj) > max_len:
            return f"{repr(obj[:max_len - 3])[:-1]}...'"
        return repr(obj)
    elif isinstance(obj, collections.abc.Mapping):
        if not obj:
            return '{}'
        if depth <= 0:
            item_count_str = f"{len(obj)} item{('s' if len(obj) != 1 else '')}"
            return f'{{<... {item_count_str} at Max depth ...>}}'
        if len(obj) > max_items:
            return f'<dict len={len(obj)}>'
        items = []
        try:
            sorted_keys = sorted(obj.keys(), key=str)
        except TypeError:
            sorted_keys = list(obj.keys())
        for k in sorted_keys:
            v = obj[k]
            k_repr = _pretty_repr(k, indent_level=indent_level + indent_delta, indent_delta=indent_delta, max_len=max_len, max_items=max_items, depth=depth - 1, visited=visited)
            v_repr = _pretty_repr(v, indent_level=indent_level + indent_delta, indent_delta=indent_delta, max_len=max_len, max_items=max_items, depth=depth - 1, visited=visited)
            items.append(f'{next_indent_str}{k_repr}: {v_repr}')
        return f'{{\n' + ',\n'.join(items) + f'\n{indent}}}'
    elif isinstance(obj, (list, tuple, set)):
        return _format_collection(obj, indent_level=indent_level, indent_delta=indent_delta, max_len=max_len, max_items=max_items, depth=depth, visited=visited)
    else:
        raw_repr = repr(obj)
        return raw_repr.replace('\n', f'\n{next_indent_str}')

def _format_collection(obj: Any, *, indent_level: int, indent_delta: int, max_len: int, max_items: int, depth: int, visited: FrozenSet[int]) -> str:
    if isinstance(obj, list):
        brackets = ('[', ']')
        internal_obj = obj
    elif isinstance(obj, tuple):
        brackets = ('(', ')')
        internal_obj = list(obj)
    elif isinstance(obj, set):
        internal_obj = list(obj)
        if obj:
            brackets = ('{', '}')
        else:
            brackets = ('set(', ')')
    else:
        raise ValueError(f'Unsupported collection type: {type(obj)}')
    if not internal_obj:
        return brackets[0] + brackets[1]
    if depth <= 0:
        item_count_str = f"{len(internal_obj)} item{'s' * (len(internal_obj) != 1)}"
        return f'{brackets[0]}<... {item_count_str} at Max depth ...>{brackets[1]}'
    indent = ' ' * indent_level
    next_indent_str = ' ' * (indent_level + indent_delta)
    elements = []
    num_to_show = min(len(internal_obj), max_items)
    for i in range(num_to_show):
        elem = internal_obj[i]
        elements.append(next_indent_str + _pretty_repr(elem, indent_level=indent_level + indent_delta, indent_delta=indent_delta, max_len=max_len, max_items=max_items, depth=depth - 1, visited=visited))
    if len(internal_obj) > max_items:
        elements.append(f'{next_indent_str}<... {len(internal_obj) - max_items} more items ...>')
    return f'{brackets[0]}\n' + ',\n'.join(elements) + f',\n{indent}{brackets[1]}'

class BaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(alias_generator=alias_generators.to_camel, populate_by_name=True, from_attributes=True, protected_namespaces=(), extra='forbid', arbitrary_types_allowed=True, ser_json_bytes='base64', val_json_bytes='base64', ignored_types=(typing.TypeVar,), defer_build=False)

    @pydantic.model_validator(mode='before')
    @classmethod
    def _check_field_type_mismatches(cls, data: Any) -> Any:
        if not isinstance(data, (dict, pydantic.BaseModel)):
            return data
        for field_name, field_info in cls.model_fields.items():
            if isinstance(data, dict):
                value = data.get(field_name)
            else:
                value = getattr(data, field_name, None)
            if value is None:
                continue
            expected_type = field_info.annotation
            origin = get_origin(expected_type)
            if origin is Union:
                args = get_args(expected_type)
                non_none_types = [arg for arg in args if arg is not type(None)]
                if len(non_none_types) == 1:
                    expected_type = non_none_types[0]
            if isinstance(expected_type, type) and get_origin(expected_type) is None and issubclass(expected_type, pydantic.BaseModel) and isinstance(value, pydantic.BaseModel) and (not isinstance(value, expected_type)):
                logger.warning(f'Type mismatch in {cls.__name__}.{field_name}: expected {expected_type.__name__}, got {type(value).__name__}')
        return data

class CaseInSensitiveEnum(str, enum.Enum):
    """Case insensitive enum."""

    @classmethod
    def _missing_(cls, value: Any) -> Any:
        try:
            return cls[value.upper()]
        except KeyError:
            try:
                return cls[value.lower()]
            except KeyError:
                warnings.warn(f'{value} is not a valid {cls.__name__}')
                try:
                    unknown_enum_val = super().__new__(cls, value)
                    unknown_enum_val._name_ = str(value)
                    unknown_enum_val._value_ = value
                    return unknown_enum_val
                except:
                    return None

def timestamped_unique_name() -> str:
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    unique_id = uuid.uuid4().hex[0:5]
    return f'{timestamp}_{unique_id}'

def encode_unserializable_types(data: dict[str, object]) -> dict[str, object]:
    processed_data: dict[str, object] = {}
    if not isinstance(data, dict):
        return data
    for key, value in data.items():
        if isinstance(value, bytes):
            processed_data[key] = base64.urlsafe_b64encode(value).decode('ascii')
        elif isinstance(value, datetime.datetime):
            processed_data[key] = value.isoformat()
        elif isinstance(value, dict):
            processed_data[key] = encode_unserializable_types(value)
        elif isinstance(value, list):
            if all((isinstance(v, bytes) for v in value)):
                processed_data[key] = [base64.urlsafe_b64encode(v).decode('ascii') for v in value]
            if all((isinstance(v, datetime.datetime) for v in value)):
                processed_data[key] = [v.isoformat() for v in value]
            else:
                processed_data[key] = [encode_unserializable_types(v) for v in value]
        else:
            processed_data[key] = value
    return processed_data

def experimental_warning(message: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        warning_done = False

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal warning_done
            if not warning_done:
                warning_done = True
                warnings.warn(message=message, category=ExperimentalWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def _normalize_key_for_matching(key_str: str) -> str:
    return key_str.replace('_', '').lower()

def align_key_case(target_dict: StringDict, update_dict: StringDict) -> StringDict:
    aligned_update_dict: StringDict = {}
    target_keys_map = {_normalize_key_for_matching(key): key for key in target_dict.keys()}
    for key, value in update_dict.items():
        normalized_update_key = _normalize_key_for_matching(key)
        if normalized_update_key in target_keys_map:
            aligned_key = target_keys_map[normalized_update_key]
        else:
            aligned_key = key
        if isinstance(value, dict) and isinstance(target_dict.get(aligned_key), dict):
            aligned_update_dict[aligned_key] = align_key_case(target_dict[aligned_key], value)
        elif isinstance(value, list) and isinstance(target_dict.get(aligned_key), list):
            aligned_update_dict[aligned_key] = value
        else:
            aligned_update_dict[aligned_key] = value
    return aligned_update_dict

def recursive_dict_update(target_dict: StringDict, update_dict: StringDict) -> None:
    aligned_update_dict = align_key_case(target_dict, update_dict)
    for key, value in aligned_update_dict.items():
        if key in target_dict and isinstance(target_dict[key], dict) and isinstance(value, dict):
            recursive_dict_update(target_dict[key], value)
        elif key in target_dict and (not isinstance(target_dict[key], type(value))):
            logger.warning(f"Type mismatch for key '{key}'. Existing type: {type(target_dict[key])}, new type: {type(value)}. Overwriting.")
            target_dict[key] = value
        else:
            target_dict[key] = value

def is_duck_type_of(obj: Any, cls: type[pydantic.BaseModel]) -> bool:
    if isinstance(obj, dict) or not hasattr(cls, 'model_fields'):
        return False
    all_matched = all((hasattr(obj, field) for field in cls.model_fields))
    if not all_matched and isinstance(obj, pydantic.BaseModel):
        try:
            obj_private = cls()
            all_matched = all((hasattr(obj_private, f) for f in type(obj).model_fields))
        except ValueError:
            return False
    return all_matched
