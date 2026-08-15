"""!!! abstract "Usage Documentation"
    [JSON Schema](../concepts/json_schema.md)

The `json_schema` module contains classes and functions to allow the way [JSON Schema](https://json-schema.org/)
is generated to be customized.

In general you shouldn't need to use this module directly; instead, you can use
[`BaseModel.model_json_schema`][pydantic.BaseModel.model_json_schema] and
[`TypeAdapter.json_schema`][pydantic.TypeAdapter.json_schema].
"""

from __future__ import annotations as _annotations

import collections.abc
import dataclasses
import inspect
import math
import os
import re
import warnings
from collections import Counter, defaultdict
from collections.abc import Callable, Hashable, Iterable, Sequence
from copy import deepcopy
from enum import Enum
from re import Pattern
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
)

# Decimal JSON schema pattern formatted without look-around assertions for cross-engine compatibility (#13630)
DECIMAL_REGEX_PATTERN = r'^-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)$'
