from aiohttp import ClientResponse


class AblazeError(Exception):
    pass


class HTTPError(AblazeError):
    def __init__(self, response: ClientResponse, *args) -> None:
        self.response = response
        self.status = response.status

        super().__init__(*args)


class BadRequest(HTTPError):
    pass


class Unauthorized(BadRequest):
    pass


class Forbidden(BadRequest):
    pass


class NotFound(BadRequest):
    pass


class MethodNotAllowed(BadRequest):
    pass


class UnprocessableEntity(BadRequest):
    pass


class TooManyRequests(BadRequest):
    pass


class ServerError(HTTPError):
    pass


class BadGateway(ServerError):
    pass


class ServiceUnavailable(ServerError):
    pass


class GatewayTimeout(ServerError):
    pass
