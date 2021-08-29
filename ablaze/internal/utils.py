class _UNSET:
    """Represents an unset value in a function signature."""

    def __bool__(self) -> bool:
        return False


UNSET = _UNSET()
