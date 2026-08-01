"""Head-to-head: local faster-whisper tiers vs OpenAI gpt-transcribe.

Same utterances, same normalization, same machine, so the comparison inside this
run is apples-to-apples. Numbers are NOT comparable to any vendor benchmark that
uses a different dataset.

Usage:
    .venv/bin/python bench.py --n 40
"""

import argparse
import json
import os
import pathlib
import random
import time

import jiwer
import soundfile as sf

ROOT = pathlib.Path(__file__).resolve().parent
LS = ROOT / "LibriSpeech" / "test-clean"
OUT = ROOT / "out"

# Case- and punctuation-insensitive, matching the first post's methodology.
NORM = jiwer.Compose(
    [
        jiwer.ToLowerCase(),
        jiwer.RemovePunctuation(),
        jiwer.RemoveMultipleSpaces(),
        jiwer.Strip(),
        jiwer.ReduceToListOfListOfWords(),
    ]
)


def load_utterances(n, seed=1337):
    """Deterministic sample of (flac_path, reference_text) from test-clean."""
    pairs = []
    for trans in sorted(LS.rglob("*.trans.txt")):
        for line in trans.read_text().splitlines():
            uid, _, text = line.partition(" ")
            flac = trans.parent / f"{uid}.flac"
            if flac.exists():
                pairs.append((flac, text))
    pairs.sort(key=lambda p: p[0].name)
    rng = random.Random(seed)
    return rng.sample(pairs, n)


def corpus_wer(refs, hyps):
    """Aggregate WER: total edits / total reference words."""
    m = jiwer.process_words(refs, hyps, reference_transform=NORM, hypothesis_transform=NORM)
    return m.wer, m


def run_local(size, utts):
    from faster_whisper import WhisperModel

    model = WhisperModel(size, device="cpu", compute_type="int8")
    hyps, elapsed = [], 0.0
    for i, (flac, _) in enumerate(utts, 1):
        t0 = time.perf_counter()
        segments, _info = model.transcribe(str(flac), beam_size=1)
        text = " ".join(s.text for s in segments).strip()
        elapsed += time.perf_counter() - t0
        hyps.append(text)
        print(f"  [{size}] {i}/{len(utts)}", end="\r", flush=True)
    print()
    return hyps, elapsed


def run_api(model_name, utts, **ctx):
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    hyps, elapsed = [], 0.0
    for i, (flac, _) in enumerate(utts, 1):
        t0 = time.perf_counter()
        with open(flac, "rb") as fh:
            resp = client.audio.transcriptions.create(model=model_name, file=fh, **ctx)
        elapsed += time.perf_counter() - t0
        hyps.append(resp.text.strip())
        print(f"  [{model_name}] {i}/{len(utts)}", end="\r", flush=True)
    print()
    return hyps, elapsed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--local", nargs="*", default=["base", "small", "medium"])
    ap.add_argument("--api", nargs="*", default=["gpt-transcribe"])
    args = ap.parse_args()

    utts = load_utterances(args.n)
    refs = [text for _, text in utts]
    audio_sec = sum(sf.info(str(f)).duration for f, _ in utts)
    print(f"{len(utts)} utterances, {audio_sec:.1f}s of audio\n")

    OUT.mkdir(exist_ok=True)
    results = {}

    for size in args.local:
        hyps, sec = run_local(size, utts)
        wer, m = corpus_wer(refs, hyps)
        results[size] = dict(
            kind="local", wer=wer, seconds=sec,
            sub=m.substitutions, dele=m.deletions, ins=m.insertions, hits=m.hits,
            hyps=hyps,
        )
        print(f"  -> WER {wer*100:.2f}%  {sec:.1f}s\n")

    for name in args.api:
        hyps, sec = run_api(name, utts)
        wer, m = corpus_wer(refs, hyps)
        results[name] = dict(
            kind="api", wer=wer, seconds=sec,
            sub=m.substitutions, dele=m.deletions, ins=m.insertions, hits=m.hits,
            hyps=hyps,
        )
        print(f"  -> WER {wer*100:.2f}%  {sec:.1f}s\n")

    payload = dict(
        n=len(utts), audio_seconds=audio_sec,
        utterances=[dict(id=f.stem, ref=t) for f, t in utts],
        results=results,
    )
    (OUT / "bench.json").write_text(json.dumps(payload, indent=2))

    print(f"{'model':18} {'WER%':>7} {'sec':>8} {'xRT':>7}")
    for k, v in results.items():
        print(f"{k:18} {v['wer']*100:7.2f} {v['seconds']:8.1f} {audio_sec/v['seconds']:7.1f}")


if __name__ == "__main__":
    main()
