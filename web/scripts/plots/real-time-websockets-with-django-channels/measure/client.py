"""Measure delivery latency over both transports against the live server.

One emitter WebSocket client sends N_EVENTS events at uniform-random gaps.
The server stamps each event once (t_emit). An observer WebSocket client
records push latency as it receives each broadcast; an HTTP client polling
every POLL_INTERVAL seconds records poll latency for the events each poll
carries back. Client and server share the same host, so one clock times
both sides and the network hop is loopback.

Writes latencies.csv (id, push_ms, poll_ms) next to this file.

    .venv/bin/python client.py   # with server.py already running
"""

import asyncio
import csv
import json
import pathlib
import random
import statistics
import time

import aiohttp
import websockets

HOST = "127.0.0.1:8765"
N_EVENTS = 300
MEAN_GAP = 0.2  # s between events -> roughly a 60 s run
POLL_INTERVAL = 3.0  # s, the interval the post discusses

push_lat = {}
poll_lat = {}


async def observer(done):
    async with websockets.connect(f"ws://{HOST}/ws/events/") as ws:
        while len(push_lat) < N_EVENTS:
            msg = json.loads(await ws.recv())
            push_lat[msg["id"]] = (time.time() - msg["t_emit"]) * 1000
    done.set()


async def poller():
    cursor = 0
    async with aiohttp.ClientSession() as sess:
        while len(poll_lat) < N_EVENTS:
            await asyncio.sleep(POLL_INTERVAL)
            async with sess.get(
                f"http://{HOST}/poll/", params={"cursor": cursor}
            ) as resp:
                body = await resp.json()
            t_recv = time.time()
            cursor = body["cursor"]
            for ev in body["events"]:
                poll_lat[ev["id"]] = (t_recv - ev["t_emit"]) * 1000


async def drain(ws):
    # The emitter sits in the broadcast group too, so it receives every
    # echo. Without draining them, the client library's receive queue
    # fills, frame reading (keepalive pongs included) stops, and the
    # connection dies of a ping timeout -- the no-backpressure failure
    # mode the post describes, observed live on the first attempt.
    try:
        async for _ in ws:
            pass
    except websockets.ConnectionClosed:
        pass


async def emitter():
    async with websockets.connect(f"ws://{HOST}/ws/events/") as ws:
        drainer = asyncio.create_task(drain(ws))
        for i in range(N_EVENTS):
            await asyncio.sleep(random.uniform(0, 2 * MEAN_GAP))
            await ws.send(json.dumps({"id": i}))
        # keep the socket open until the last poll drains the tail
        await asyncio.sleep(POLL_INTERVAL * 2)
        drainer.cancel()


async def main():
    done = asyncio.Event()
    obs = asyncio.create_task(observer(done))
    pol = asyncio.create_task(poller())
    await emitter()
    await asyncio.wait_for(done.wait(), timeout=30)
    while len(poll_lat) < N_EVENTS:
        await asyncio.sleep(1)
    obs.cancel()
    pol.cancel()

    out = pathlib.Path(__file__).with_name("latencies.csv")
    with out.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "push_ms", "poll_ms"])
        for i in range(N_EVENTS):
            writer.writerow(
                [i, f"{push_lat[i]:.3f}", f"{poll_lat[i]:.3f}"]
            )
    print(f"wrote {out}")

    for name, d in (("push", push_lat), ("poll", poll_lat)):
        vals = sorted(d.values())
        print(
            f"{name}: n={len(vals)} median={statistics.median(vals):.2f}ms "
            f"mean={statistics.mean(vals):.2f}ms max={vals[-1]:.2f}ms"
        )


asyncio.run(main())
