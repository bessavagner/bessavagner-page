import logging
import aiohttp_jinja2
from aiohttp import web


logger = logging.getLogger("views")


class HomeView(web.View):
    @aiohttp_jinja2.template("home.html")
    async def get(self):
        """Serve the home.html file."""
        logger.debug(dir(self.request))
        context = {
            "title": "Vagner Bessa",
        }
        return context

class ColorsView(web.View):
    @aiohttp_jinja2.template("colors.html")
    async def get(self):
        """Serve the colors.html file."""
        logger.debug(dir(self.request))
        context = {
            "title": "Vagner Bessa",
        }
        return context
