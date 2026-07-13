"""Single-file Django Channels app for the push-vs-poll measurement.

The consumer is the post's pattern reduced to its skeleton: group_add on
connect, group_send fan-out on receive, group_discard on disconnect. Every
event is stamped exactly once on the server (t_emit) and exposed over both
transports: pushed to the WebSocket group and appended to the store the
HTTP /poll/ endpoint reads.

Run from this directory (see README.md):

    .venv/bin/daphne -b 127.0.0.1 -p 8765 server:application
"""

import json
import time

import django
from django.conf import settings

settings.configure(
    DEBUG=False,
    SECRET_KEY="measure-only",
    ALLOWED_HOSTS=["*"],
    INSTALLED_APPS=["channels"],
    ROOT_URLCONF=__name__,
    CHANNEL_LAYERS={
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    },
)
django.setup()

from channels.generic.websocket import AsyncWebsocketConsumer  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from django.core.asgi import get_asgi_application  # noqa: E402
from django.http import JsonResponse  # noqa: E402
from django.urls import path, re_path  # noqa: E402

EVENTS = []  # {"id": int, "t_emit": float}, in emit order


def poll(request):
    cursor = int(request.GET.get("cursor", 0))
    fresh = EVENTS[cursor:]
    return JsonResponse({"cursor": cursor + len(fresh), "events": fresh})


urlpatterns = [path("poll/", poll)]


class EventConsumer(AsyncWebsocketConsumer):

    group_name = "events"

    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(self.group_name, self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name, self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        stamped = {"id": data["id"], "t_emit": time.time()}
        EVENTS.append(stamped)
        await self.channel_layer.group_send(
            self.group_name, {"type": "notify.client", "data": stamped}
        )

    async def notify_client(self, event):
        await self.send(json.dumps(event["data"]))


application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": URLRouter(
            [re_path(r"^ws/events/$", EventConsumer.as_asgi())]
        ),
    }
)
