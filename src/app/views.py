import logging
import aiohttp_jinja2
from aiohttp import web


logger = logging.getLogger("views")


class HomeView(web.View):
    @aiohttp_jinja2.template("home.html")
    async def get(self):
        """Serve the home.html file."""
        # logger.debug(dir(self.request))
        context = {
            "title": "Vagner Bessa",
        }
        return context

    @aiohttp_jinja2.template("home.html")
    async def post(self):
        """Handle form submission."""
        try:
            # Retrieve form data
            data = await self.request.post()
            name = data.get("name")
            email = data.get("email")
            message = data.get("message")

            # Log the form data (for debugging or further processing)
            logger.info(f"Form submitted: Name={name}, Email={email}, Message={message}")

            # Example: Store data or send an email (logic depends on your app's purpose)

            # Add a success message to the context
            context = {
                "title": "Vagner Bessa",
                "success_message": "Thank you for your message! I'll get back to you soon.",
            }
            return context
        except Exception as e:
            logger.error(f"Error handling form submission: {e}")
            # Add an error message to the context
            context = {
                "title": "Vagner Bessa",
                "error_message": "An error occurred while submitting your message. Please try again.",
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
