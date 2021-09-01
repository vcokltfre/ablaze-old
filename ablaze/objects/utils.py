from ablaze.objects.abc import Snowflake
from typing import Optional, TypeVar, Callable, Union


_T = TypeVar("_T")
_R = TypeVar("_R")


def nullmap(optional: Optional[_T], fn: Callable[[_T], _R]) -> Optional[_R]:
    if optional is None:
        return None
    return fn(optional)


def extract_int(obj: Union[Snowflake, int]) -> int:
    if isinstance(obj, int):
        return obj
    return obj.id