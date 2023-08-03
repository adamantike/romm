import uvicorn
import alembic.config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from config import DEV_PORT, DEV_HOST
from handler.socket_manager import SocketManager
from endpoints import scan, search, platform, rom

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(search.router)
app.include_router(platform.router)
app.include_router(rom.router)

add_pagination(app)

sm = SocketManager()
sm.mount_to("/ws", app)


async def scan_handler(*args):
    try:
        await scan.scan(sm, *args)
    except Exception as err:
        await sm.emit("scan:done_ko", str(err))
        raise (err)


sm.on("scan", handler=scan_handler)


@app.on_event("startup")
def startup() -> None:
    """Startup application."""
    pass


if __name__ == "__main__":
    # Run migrations
    alembic.config.main(argv=["upgrade", "head"])

    # Run application
    uvicorn.run("main:app", host=DEV_HOST, port=DEV_PORT, reload=True)
