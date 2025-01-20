import logging
from aiohttp import web
from app.routes import setup
from app.settings import PORT, DEBUG


logger = logging.getLogger("main")


def create_app():
    app = web.Application()
    setup(app)
    return app

def start_server():
    app = create_app()
    web.run_app(app, port=PORT)


if __name__ == "__main__":
    logger.debug("Starting server...")
    if not DEBUG:
        start_server()
        logger.debug("Server started")
    else:
        try:
            from watchfiles import run_process
            logger.debug("Debug mode is on. Live reloading enabled.")
            run_process("./", target=start_server, debounce=500)
        except ImportError as err:
            logger.warning(
                "%s: Install 'watchfiles' to use live reloading", err
            )
            logger.debug("Debug mode is on.")
            start_server()
