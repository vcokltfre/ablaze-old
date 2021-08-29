from asyncio import Semaphore, get_running_loop


class Ratelimiter:
    def __init__(self, rate: int, per: int) -> None:
        """A gateway send ratelimiter.

        :param rate: The rate at which requests can be made.
        :type rate: int
        :param per: How often the bucket is refilled.
        :type per: int
        """

        self.per = per
        self.loop = get_running_loop()

        self.lock = Semaphore(rate)

    async def wait(self) -> None:
        await self.lock.acquire()

        self.loop.call_later(self.per, self.lock.release)
