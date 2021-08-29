from asyncio import AbstractEventLoop, Event, Lock


class BucketLock:
    def __init__(self, loop: AbstractEventLoop, lock: Lock) -> None:
        """A per-bucket lock class to lock routes from being requested.

        :param loop: The event loop to run on.
        :type loop: AbstractEventLoop
        :param lock: The lock to manage.
        :type lock: Lock
        """

        self._loop = loop
        self._lock = lock
        self._deferring = False

    async def __aenter__(self):
        await self._lock.acquire()

    async def __aexit__(self, exec_type, exc, tb):
        if not self._deferring:
            self._lock.release()

    def defer(self, time: float) -> None:
        """Defer the release time when ratelimited.

        :param time: After how many seconds to release.
        :type time: float
        """

        self._deferring = True
        self._loop.call_later(time, self._release)

    def _release(self) -> None:
        self._lock.release()
        self._deferring = False


class RateLimitManager:
    def __init__(self, loop: AbstractEventLoop) -> None:
        """A ratelimit bucket lock manager.

        :param loop: The event loop to run on.
        :type loop: AbstractEventLoop
        """

        self._loop = loop
        self._global = Event(loop=loop)
        self._global.set()

        self._buckets = {}

    async def get_lock(self, bucket: str) -> BucketLock:
        """Get a lock for a specific bucket.

        :param bucket: The bucket to fetch the lock for.
        :type bucket: str
        :return: The lock for the bucket.
        :rtype: BucketLock
        """
        await self._global.wait()

        if lock := self._buckets.get(bucket):
            return lock

        self._buckets[bucket] = BucketLock(self._loop, Lock(loop=self._loop))
        return self._buckets[bucket]

    def clear_global(self, wait: float) -> None:
        """Lock all requests for the global ratelimit.

        :param wait: How long to lock requests for.
        :type wait: float
        """

        self._global.clear()
        self._loop.call_later(wait, self._global.set)
