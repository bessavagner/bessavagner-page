"""Stream real audio to gpt-live-transcribe over the Realtime WebSocket.

Paces audio at wall-clock speed so the measured latency means something: how
long after the words are spoken does the text arrive.

Usage:
    .venv/bin/python live.py <file.flac> [--keywords A B C] [--prompt "..."]
"""

import argparse
import asyncio
import base64
import json
import os
import pathlib
import subprocess
import time

import websockets

RATE = 24000
CHUNK_MS = 100
CHUNK_BYTES = RATE * 2 * CHUNK_MS // 1000  # pcm16 mono

URL = "wss://api.openai.com/v1/realtime?intent=transcription"


def to_pcm(path):
    """Decode any input to raw mono pcm16 @ 24 kHz."""
    out = subprocess.run(
        ["ffmpeg", "-v", "quiet", "-i", str(path), "-f", "s16le",
         "-acodec", "pcm_s16le", "-ac", "1", "-ar", str(RATE), "-"],
        capture_output=True, check=True,
    )
    return out.stdout


async def run(path, keywords, prompt, model="gpt-live-transcribe"):
    pcm = to_pcm(path)
    audio_sec = len(pcm) / (RATE * 2)

    transcription = {"model": model}
    if prompt:
        transcription["prompt"] = prompt
    if keywords:
        transcription["keywords"] = list(keywords)

    session = {
        "type": "session.update",
        "session": {
            "type": "transcription",
            "audio": {
                "input": {
                    "format": {"type": "audio/pcm", "rate": RATE},
                    "transcription": transcription,
                    # gpt-live-transcribe segments internally and rejects this
                    # being set at all: "Turn detection is not supported for
                    # this transcription model."
                    "turn_detection": None,
                }
            },
        },
    }

    headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}
    deltas, finals, events = [], [], []
    t_start = None

    async with websockets.connect(URL, additional_headers=headers, max_size=None) as ws:
        await ws.send(json.dumps(session))

        async def receive():
            async for raw in ws:
                ev = json.loads(raw)
                et = ev.get("type", "")
                events.append(et)
                if et.endswith("transcription.delta"):
                    deltas.append((time.perf_counter() - t_start, ev.get("delta", "")))
                elif et.endswith("transcription.completed"):
                    finals.append((time.perf_counter() - t_start, ev.get("transcript", "")))
                elif et == "error":
                    print("ERROR EVENT:", json.dumps(ev)[:500])

        recv_task = asyncio.create_task(receive())
        t_start = time.perf_counter()

        # Pace the audio at real time, as a live microphone would.
        for i in range(0, len(pcm), CHUNK_BYTES):
            chunk = pcm[i:i + CHUNK_BYTES]
            await ws.send(json.dumps({
                "type": "input_audio_buffer.append",
                "audio": base64.b64encode(chunk).decode(),
            }))
            await asyncio.sleep(CHUNK_MS / 1000)

        # Let the tail drain.
        try:
            await asyncio.wait_for(recv_task, timeout=15)
        except asyncio.TimeoutError:
            recv_task.cancel()

    return {
        "audio_seconds": audio_sec,
        "first_delta_s": deltas[0][0] if deltas else None,
        "last_delta_s": deltas[-1][0] if deltas else None,
        "final_s": finals[-1][0] if finals else None,
        "n_deltas": len(deltas),
        "transcript": (finals[-1][1] if finals else "".join(d for _, d in deltas)).strip(),
        "event_types": sorted(set(events)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--keywords", nargs="*", default=[])
    ap.add_argument("--prompt", default="")
    ap.add_argument("--model", default="gpt-live-transcribe")
    args = ap.parse_args()

    r = asyncio.run(run(pathlib.Path(args.audio), args.keywords, args.prompt, args.model))
    print(json.dumps(r, indent=2))


if __name__ == "__main__":
    main()
