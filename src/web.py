from aiohttp import web

from aiohttp import web
from config import HOST, PORT

app = web.Application()
routes = web.RouteTableDef()


@routes.get("/")
async def hello(req):
    return web.Response(text="Hello, world!")


async def start_app():
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()
    print(f"Listening on http://{HOST}:{PORT}")
