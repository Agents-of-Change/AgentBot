from aiohttp import web
from pathlib import Path
from config import HOST, PORT

app = web.Application()
routes = web.RouteTableDef()
static_dir = Path(__file__).parent / "static"


@routes.get("/")
async def hello(req):
    return web.FileResponse(static_dir / "index.html")


async def start_app():
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()
    print(f"Listening on http://{HOST}:{PORT}")
