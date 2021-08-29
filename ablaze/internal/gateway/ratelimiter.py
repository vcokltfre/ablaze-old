from asyncio import AbstractEventLoop, Semaphore


class Ratelimiter:
    def __init__(self, rate: int, per: int, loop: AbstractEventLoop) -> None:
        """A gateway send ratelimiter.

        :param rate: The rate at which requests can be made.
        :type rate: int
        :param per: How often the bucket is refilled.
        :type per: int
        :param loop: The even loop to run on.
        :type loop: AbstractEventLoop
        """

        self.per = per
        self.loop = loop

        self.lock = Semaphore(rate)

    async def wait(self) -> None:
        await self.lock.acquire()

        self.loop.call_later(self.per, self.lock.release)
