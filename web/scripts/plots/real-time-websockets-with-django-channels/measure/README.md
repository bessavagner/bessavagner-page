# Push vs. poll: measured delivery latency

Measured, not illustrative. `latencies.csv` is a real capture used by
`../latency.py` to draw the post's figure.

## Methodology

- Single machine, loopback (`127.0.0.1`): client and server share one host
  clock, so a one-way latency is `t_receive - t_emit` with no clock skew.
  The network hop is loopback-cheap; on a real network both transports pay
  the same extra WAN hop on top.
- `server.py`: a single-file Django Channels app served by daphne, using
  the post's consumer pattern (`group_add` on connect, `group_send`
  fan-out) with the in-memory channel layer. Every event is stamped once
  on the server and exposed to both transports: pushed to the WebSocket
  group and appended to the store behind the HTTP `/poll/` endpoint.
- `client.py`: an emitter sends 300 events at uniform-random gaps
  (mean 0.2 s). An observer WebSocket connection records push latency per
  event; an HTTP client polling every 3 s records poll latency per event.
- Snapshot: 2026-07-13, Python 3.12.3, Django 6.0.7, Channels 4.3.2,
  daphne 4.2.2, Linux. One environment on one day; the *shape* is the
  point, not the absolute numbers.

## Reproduce

```bash
python3 -m venv .venv
.venv/bin/pip install django channels daphne websockets aiohttp

# terminal 1
.venv/bin/daphne -b 127.0.0.1 -p 8765 server:application

# terminal 2 (about 70 s)
.venv/bin/python client.py
```

Then regenerate the figure with the plots venv:

```bash
cd .. && ../.venv/bin/python latency.py
```
