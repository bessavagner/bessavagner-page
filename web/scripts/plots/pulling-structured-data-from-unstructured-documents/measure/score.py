"""Per-field precision / recall / F1. Pure, and the only part of this benchmark
with a green/red signal.

Two rules, and both of them are a bug that has already happened in this repo:

NOTHING MEASURED IS NOT ZERO. A field with no gold labels and no predictions has
no F1. Not 0.0 — None. A 0.0 plotted on a chart is a measurement the reader will
believe, and it would be one nobody made. (Sprint 09 shipped this bug three
times in the analytics lane: sum([]) is 0, len([]) is 0, and every one of them
was a fabrication waiting for something to divide into it.)

A DROPPED DOCUMENT IS A MISS, NOT AN ABSENCE. If a technique crashes on a
document and we skip it, we have rewarded it for crashing. Its gold labels stay
in the denominator as false negatives.
"""
from __future__ import annotations


def _norm(v: str) -> str:
    """Compare extracted values the way a human would: trimmed, case-folded."""
    return " ".join(v.split()).casefold()


def score_field(predicted: list[str], gold: list[str]) -> dict:
    """Set-based P/R/F1 for one field on one document (or aggregated counts).

    Set-based, not list-based: finding the same email twice is finding one fact,
    not two, and must not double-count.
    """
    p, g = {_norm(v) for v in predicted if v}, {_norm(v) for v in gold if v}

    if not p and not g:
        # Nothing was claimed and nothing was expected. There is no score here.
        return {"tp": 0, "fp": 0, "fn": 0, "precision": None, "recall": None, "f1": None}

    tp = len(p & g)
    fp = len(p - g)
    fn = len(g - p)
    return {"tp": tp, "fp": fp, "fn": fn, **_prf(tp, fp, fn)}


def _prf(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def score_corpus(
    predictions: dict[str, dict[str, list[str]]],
    gold: dict[str, dict[str, list[str]]],
    fields: list[str],
) -> dict[str, dict]:
    """Aggregate per-field counts across every GOLD document, then compute P/R/F1.

    Iterates `gold`, never `predictions` — a document the pipeline dropped keeps
    its gold labels in the denominator, so a crash costs recall instead of
    quietly improving the score.
    """
    out: dict[str, dict] = {}
    for field in fields:
        tp = fp = fn = 0
        measured = False
        for doc_id, gold_fields in gold.items():
            g = gold_fields.get(field, [])
            p = predictions.get(doc_id, {}).get(field, [])
            if g or p:
                measured = True
            counts = score_field(p, g)
            tp += counts["tp"]
            fp += counts["fp"]
            fn += counts["fn"]
        if not measured:
            out[field] = {
                "tp": 0, "fp": 0, "fn": 0,
                "precision": None, "recall": None, "f1": None,
            }
            continue
        out[field] = {"tp": tp, "fp": fp, "fn": fn, **_prf(tp, fp, fn)}
    return out
