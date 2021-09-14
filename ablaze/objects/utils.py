from typing import Callable, Optional, TypeVar, Union

from ablaze.internal.utils import _UNSET
from ablaze.objects.abc import Snowflake

_T = TypeVar("_T")
_R = TypeVar("_R")


def nullmap(optional: Optional[_T], fn: Callable[[_T], _R]) -> Optional[_R]:
    if optional is None:
        return None
    return fn(optional)


def unsetmap(optional: Union[_T, _UNSET], fn: Callable[[_T], _R]) -> Union[_R, _UNSET]:
    if isinstance(optional, _UNSET):
        return optional
    return fn(optional)


def extract_int(obj: Union[Snowflake, int]) -> int:
    if isinstance(obj, int):
        return obj
    return obj.id
