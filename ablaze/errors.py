"""
MIT License

Copyright (c) 2021 vcokltfre

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from aiohttp import ClientResponse


class AblazeError(Exception):
    pass


class HTTPError(AblazeError):
    def __init__(self, response: ClientResponse, *args) -> None:
        self.response = response

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
