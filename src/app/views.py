import logging
import aiohttp_jinja2
from aiohttp import web

from app.utils import send_email, send_confirmation_email
from app.settings import EMAIL_USERNAME


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
        context = {
            "title": "Vagner Bessa",
        }
        try:
            # Retrieve form data
            data = await self.request.post()
            name = data.get("name")
            email = data.get("email")
            message = data.get("message")

            if not all([name, email, message]):
                context["error_message"] = "All fields are required."
                return context
            logger.info(
                "Form submitted: Name=%s, Email=%s, Message=%s",
                name, email, message
            )

            subject = f"New Message from {name}"
            recipients = [EMAIL_USERNAME]
            body = f"Name: {name}\nEmail: {email}\nMessage:\n{message}"

            try:
                await send_email(subject, recipients, body)
                await send_confirmation_email(name, email, message)
                context["success_message"] = (
                    "Thank you for your message! I'll get back to you soon."
                )
            except Exception as err:
                context["error_message"] = f"Failed to send email: {str(err)}"
        except Exception as err:
            logger.error("Error handling form submission: %s", str(err))
            context["error_message"] = (
                "An error occurred while submitting your message. "
                "Please try again."
            )
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
