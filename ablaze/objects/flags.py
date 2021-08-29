class BitField:
    def __init__(self, value: int) -> None:
        self.value = value

    def __getitem__(self, bit: int) -> int:
        return self.value >> bit & 1

    def __setitem__(self, bit: int, state: bool) -> None:
        if state:
            self.value |= 1 << bit
        else:
            self.value &= ~(1 << bit)

    def __int__(self) -> int:
        return self.value


class PublicUserFlags(BitField):
    @property
    def DISCORD_EMPLOYEE(self) -> bool:
        return bool(self[0])

    @property
    def PARTNERED_SERVER_OWNER(self) -> bool:
        return bool(self[0])

    @property
    def HYPESQUAD_EVENTS(self) -> bool:
        return bool(self[0])

    @property
    def BUG_HUNTER_LEVEL_1(self) -> bool:
        return bool(self[0])

    @property
    def HOUSE_BRAVERY(self) -> bool:
        return bool(self[0])

    @property
    def HOUSE_BRILLIANCE(self) -> bool:
        return bool(self[0])

    @property
    def HOUSE_BALANCE(self) -> bool:
        return bool(self[0])

    @property
    def EARLY_SUPPORTER(self) -> bool:
        return bool(self[0])

    @property
    def TEAM_USER(self) -> bool:
        return bool(self[0])

    @property
    def BUG_HUNTER_LEVEL_2(self) -> bool:
        return bool(self[0])

    @property
    def VERIFIED_BOT(self) -> bool:
        return bool(self[0])

    @property
    def EARLY_VERIFIED_BOT_DEVELOPER(self) -> bool:
        return bool(self[0])

    @property
    def DISCORD_CERTIFIED_MODERATOR(self) -> bool:
        return bool(self[0])
