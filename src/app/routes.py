import datetime

import aiohttp_jinja2
from aiohttp import web
from jinja2 import FileSystemLoader

from app.views import HomeView, ColorsView
from app.middlewares import security_headers_middleware, rate_limit_middleware
from app.settings import STATIC_DIR, TEMPLATES_DIR, SITE_URL


def static_path(path):
    return f"/static/{path}"


async def robots_txt(request: web.Request) -> web.Response:
    body = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"
    return web.Response(text=body, content_type="text/plain")


async def sitemap_xml(request: web.Request) -> web.Response:
    today = datetime.date.today().isoformat()
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod>"
        "<changefreq>monthly</changefreq><priority>1.0</priority></url>\n"
        "</urlset>\n"
    )
    return web.Response(text=body, content_type="application/xml")


def setup(app: web.Application):
    """Define and add routes and middlewares to the application."""

    app.middlewares.append(security_headers_middleware)
    app.middlewares.append(rate_limit_middleware(max_requests=5, window_seconds=600))

    aiohttp_jinja2.setup(app, loader=FileSystemLoader(TEMPLATES_DIR))

    app["static_url"] = "/static/"
    env = aiohttp_jinja2.get_env(app)
    env.globals["static"] = static_path
    env.globals["site_url"] = SITE_URL
    env.globals["current_year"] = datetime.date.today().year

    app.router.add_view("/", HomeView)
    app.router.add_view("/colors", ColorsView)
    app.router.add_get("/robots.txt", robots_txt)
    app.router.add_get("/sitemap.xml", sitemap_xml)
    app.router.add_static("/static", path=STATIC_DIR, name="static")
