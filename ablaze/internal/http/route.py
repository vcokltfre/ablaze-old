_API_URL = "https://discord.com/api/v9"


class Route:
    def __init__(self, path: str, *, api_url: str = None, **kwargs) -> None:
        """An HTTP route for ratelimiting.

        :param path: The unformatted route path.
        :type path: str
        :param api_url: The Discord API URL to use.
        :type api_url: str
        """

        _api_url = api_url or _API_URL
        self.url = _api_url + path.format(**kwargs)

        channel_id = kwargs.pop("channel_id", None)
        guild_id = kwargs.pop("guild_id", None)
        self.webhook_id = kwargs.pop("webhook_id", None)

        self.bucket = f"{path}:{channel_id}/{guild_id}/{self.webhook_id}"
