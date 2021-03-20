from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional, Pattern, Tuple, TypeVar, Union

from typing_extensions import Annotated

from pydantic.types import StrictBool, conbytes, condecimal, confloat, conint, conlist, conset, constr
from pydantic.typing import get_args, get_origin
from pydantic.utils import Representation

__all__ = 'Constraints', 'Strict', 'convert_type_to_constrained_if_needed'


def conbool(*, strict: bool = False) -> type:
    return StrictBool if strict else bool


CONSTRAINED_TYPES_MAPPING: Dict[type, Any] = {
    bool: conbool,
    int: conint,
    float: confloat,
    Decimal: condecimal,
    bytes: conbytes,
    str: constr,
    list: conlist,
    set: conset,
}


@dataclass(repr=False)
class Constraints(Representation):
    strict: Optional[bool] = None

    # int, float, decimal
    gt: Union[int, float, Decimal, None] = None
    ge: Union[int, float, Decimal, None] = None
    lt: Union[int, float, Decimal, None] = None
    le: Union[int, float, Decimal, None] = None
    multiple_of: Union[int, float, Decimal, None] = None

    # extra for decimal
    max_digits: Optional[int] = None
    decimal_places: Optional[int] = None

    # str, bytes
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    regex: Optional[Pattern[str]] = None
    curtail_length: Optional[int] = None
    strip_whitespace: Optional[bool] = None
    to_lower: Optional[bool] = None

    # other collections (list, tuple, set, ...)
    min_items: Optional[int] = None
    max_items: Optional[int] = None

    def todict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    def __repr_args__(self) -> List[Tuple[str, Any]]:
        return list(self.todict().items())


T = TypeVar('T')
Strict = Annotated[T, Constraints(strict=True)]


def convert_type_to_constrained_if_needed(tp: Any) -> Any:
    """
    From a type like `Strict[Annotated[int, Constraints(ge=2)]]`,
    return `conint(strict=True, ge=2)`
    """
    if get_origin(tp) is not Annotated:
        return tp

    type_, *metadata = get_args(tp)

    constraints_kwargs: Dict[str, Any] = {}
    type_origin = get_origin(type_)
    if type_origin in {list, set}:
        # type_ can be `list[int]` for example
        item_type = get_args(type_)[0]
        # item_type can itself have constraints
        constraints_kwargs['item_type'] = convert_type_to_constrained_if_needed(item_type)
        type_ = type_origin

    all_constraints = [x for x in metadata if isinstance(x, Constraints)]
    if type_ in CONSTRAINED_TYPES_MAPPING:
        for constraint in all_constraints:
            constraints_kwargs.update(constraint.todict())
        return CONSTRAINED_TYPES_MAPPING[type_](**constraints_kwargs)
    else:
        return type_
