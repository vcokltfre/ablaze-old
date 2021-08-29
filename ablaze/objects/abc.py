from datetime import datetime


class Snowflake:
    def __init__(self, id: int) -> None:
        self.id = id

    @property
    def created_at(self) -> datetime:
        return datetime.fromtimestamp(((self.id >> 22) + 1420070400000) / 1000)
