#!/usr/bin/env python3

import asyncio

from aiohttp import web
from random import randint


class Feeder(object):
    counter = 0

    def __init__(self):
        app = web.Application()
        app.router.add_routes(
            [
                web.get('/clientId', self.handle_client_id),
                web.get('/clientId/reset', self.reset_client_id),
                web.get('/wait/{ms}', self.wait),
                web.get('/wait/{min_ms}/{max_ms}', self.wait_between),
                web.get('/status/{code}', self.status_code),
                web.get('/{name}', self.handle)
            ]
        )
        web.run_app(app, port=3456)

    async def reset_client_id(self, request):
        Feeder.counter = 0
        return web.Response(text=str(Feeder.counter))

    async def handle_client_id(self, request):
        Feeder.counter += 1
        return web.Response(text=str(Feeder.counter))

    async def wait(self, request):
        seconds = int(request.match_info.get('ms', 100)) / 1000.0
        await asyncio.sleep(seconds)
        return web.Response(text='You have waited for {} seconds.'.format(seconds))

    async def wait_between(self, request):
        min_ms = int(request.match_info.get('min_ms', 100))
        max_ms = int(request.match_info.get('max_ms', 100))
        seconds = randint(min_ms, max_ms) / 1000.0
        await asyncio.sleep(seconds)
        return web.Response(text='You have waited for {} seconds.'.format(seconds))

    async def status_code(self, request):
        code = int(request.match_info.get('code', 200))
        return web.Response(status=code, text='Http Status Code {}'.format(code))

    async def handle(self, request):
        name = request.match_info.get('name', "Anonymous")
        text = "Hello, " + name
        return web.Response(text=text)


if __name__ == '__main__':
    Feeder()
