import re
import logging

import aiohttp_jinja2
from aiohttp import web

from app.utils import send_email, send_confirmation_email
from app.content import load_content
from app.settings import EMAIL_USERNAME


logger = logging.getLogger("views")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MAX_MESSAGE_LEN = 5000
_MAX_NAME_LEN = 200


class HomeView(web.View):
    @aiohttp_jinja2.template("home.html")
    async def get(self):
        """Serve the home.html file."""
        return {"title": "Vagner Bessa", **load_content()}

    @aiohttp_jinja2.template("home.html")
    async def post(self):
        """Handle contact-form submission."""
        context = {"title": "Vagner Bessa", **load_content()}
        try:
            data = await self.request.post()

            # Honeypot: bots fill hidden fields; humans never see them.
            if (data.get("company") or "").strip():
                logger.info("Honeypot triggered; dropping submission silently.")
                context["success_message"] = (
                    "Thank you for your message! I'll get back to you soon."
                )
                return context

            name = (data.get("name") or "").strip()
            email = (data.get("email") or "").strip()
            message = (data.get("message") or "").strip()

            if not all([name, email, message]):
                context["error_message"] = "All fields are required."
                return context
            if not _EMAIL_RE.match(email):
                context["error_message"] = "Please enter a valid email address."
                return context
            if len(name) > _MAX_NAME_LEN or len(message) > _MAX_MESSAGE_LEN:
                context["error_message"] = "Your message is too long."
                return context

            logger.info("Contact form submitted by %s <%s>", name, email)

            subject = f"New Message from {name}"
            body = f"Name: {name}\nEmail: {email}\nMessage:\n{message}"

            try:
                await send_email(subject, [EMAIL_USERNAME], body)
                await send_confirmation_email(name, email, message)
                context["success_message"] = (
                    "Thank you for your message! I'll get back to you soon."
                )
            except Exception:
                # Do not leak internal/SMTP details to the visitor.
                logger.exception("Failed to send contact email")
                context["error_message"] = (
                    "Sorry, we couldn't send your message right now. "
                    "Please try again later or email me directly."
                )
        except Exception:
            logger.exception("Error handling form submission")
            context["error_message"] = (
                "An error occurred while submitting your message. Please try again."
            )
        return context


class ColorsView(web.View):
    @aiohttp_jinja2.template("colors.html")
    async def get(self):
        """Serve the colors.html file."""
        return {"title": "Vagner Bessa"}
