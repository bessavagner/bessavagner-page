import aiohttp_jinja2
from aiohttp import web
from jinja2 import FileSystemLoader
from app.views import HomeView, ColorsView
from app.settings import STATIC_DIR, TEMPLATES_DIR

def static_path(path):
    return f"/static/{path}"

def setup(app: web.Application):
    """Define and add routes to the application."""
    
    aiohttp_jinja2.setup(app, loader=FileSystemLoader(TEMPLATES_DIR))
    
    app["static_url"] = "/static/"
    aiohttp_jinja2.get_env(app).globals["static"] = static_path
    
    app.router.add_view("/", HomeView)
    app.router.add_view("/colors", ColorsView)
    app.router.add_static("/static", path=STATIC_DIR, name="static")
