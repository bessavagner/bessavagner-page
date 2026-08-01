"""Does the `keywords` parameter actually fix proper-noun errors?

Takes the utterances where gpt-transcribe misheard a name in the n=40 run and
re-runs them three ways: bare, with keywords, and with keywords + prompt.
"""

import json
import os
import sys

import jiwer
from openai import OpenAI

LS = "LibriSpeech/test-clean"
NORM = jiwer.Compose([
    jiwer.ToLowerCase(), jiwer.RemovePunctuation(),
    jiwer.RemoveMultipleSpaces(), jiwer.Strip(),
    jiwer.ReduceToListOfListOfWords(),
])

# Utterances whose only errors were proper nouns, with the names the API missed.
CASES = [
    {
        "id": "8555-284449-0004",
        "keywords": ["Ghip Ghisizzle", "Boolooroo"],
        "prompt": "An excerpt from a whimsical children's fantasy novel set in the Land of Oz.",
    },
    {
        "id": "5639-40744-0007",
        "keywords": ["Rodolfo", "Leocadia"],
        "prompt": "A Spanish novella read aloud; characters have Spanish names.",
    },
    {
        "id": "5639-40744-0039",
        "keywords": ["Rodolfo", "Leocadia", "senora"],
        "prompt": "A Spanish novella read aloud; characters have Spanish names.",
    },
]

MODEL = sys.argv[1] if len(sys.argv) > 1 else "gpt-transcribe"


def flac_for(uid):
    spk, chap, _ = uid.split("-")
    return f"{LS}/{spk}/{chap}/{uid}.flac"


def ref_for(uid):
    spk, chap, _ = uid.split("-")
    for line in open(f"{LS}/{spk}/{chap}/{spk}-{chap}.trans.txt"):
        k, _, text = line.strip().partition(" ")
        if k == uid:
            return text
    raise KeyError(uid)


def wer(ref, hyp):
    return jiwer.process_words([ref], [hyp], reference_transform=NORM,
                               hypothesis_transform=NORM).wer


def main():
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    rows = []
    for case in CASES:
        uid = case["id"]
        ref = ref_for(uid)
        variants = {
            "bare": {},
            "keywords": {"keywords": case["keywords"]},
            "keywords+prompt": {"keywords": case["keywords"], "prompt": case["prompt"]},
        }
        row = {"id": uid, "ref": ref, "keywords": case["keywords"]}
        for label, extra in variants.items():
            try:
                with open(flac_for(uid), "rb") as fh:
                    r = client.audio.transcriptions.create(model=MODEL, file=fh, **extra)
                row[label] = {"text": r.text.strip(), "wer": wer(ref, r.text)}
            except Exception as e:
                row[label] = {"error": f"{type(e).__name__}: {str(e)[:300]}"}
        rows.append(row)
        print(f"\n=== {uid}\nREF  {ref}")
        for label in variants:
            v = row[label]
            if "error" in v:
                print(f"{label:16} ERROR {v['error']}")
            else:
                print(f"{label:16} WER {v['wer']*100:5.1f}%  {v['text']}")

    json.dump(rows, open(f"out/keywords-{MODEL}.json", "w"), indent=2)


if __name__ == "__main__":
    main()
