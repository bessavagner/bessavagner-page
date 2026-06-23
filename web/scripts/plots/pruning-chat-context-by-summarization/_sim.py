"""Synthetic multi-turn conversation reductions under a fixed token window.

We model a chat that keeps growing: every turn adds a user message and an
assistant reply, each a few hundred tokens. A fixed context window forces a
reduction strategy once the running total would overflow. We compare three:

* **FIFO truncation** — drop whole oldest turns until it fits. Cheap, but the
  earliest context is gone for good.
* **Per-message pruning** — drop the single oldest *message* at a time (finer
  grained than whole turns), still pure deletion.
* **Summarization-pruning** — condense the middle of the conversation into one
  compact summary message, keeping the system prompt and the latest turn. This
  is what aigents does, falling back to deletion only when it can't help.

"Effective turns retained" counts how many of the original turns still have
their meaning represented in the window — a dropped turn counts 0, a turn
folded into the summary counts as a fraction (the summary is lossy), and a
verbatim turn counts 1. Numbers are illustrative, not measured from a model.
"""

from __future__ import annotations

import numpy as np

WINDOW = 8000          # context window, tokens
USER_TOKENS = 180      # avg tokens in a user message
ASSISTANT_TOKENS = 420  # avg tokens in an assistant reply
TURN_TOKENS = USER_TOKENS + ASSISTANT_TOKENS

# A summary keeps a fraction of the meaning of what it replaces, at a fraction
# of the tokens. These mirror the aigents knobs: the summarizer is capped at
# max_tokens // 4, so a summary can never be larger than a quarter of the
# window, and it preserves most but not all of the condensed meaning.
SUMMARY_MEANING_RETENTION = 0.7   # lossy: 70% of folded turns' meaning survives
SUMMARY_COMPRESSION = 0.18        # summary tokens as a fraction of input tokens
SUMMARY_CAP = WINDOW // 4         # hard ceiling, like max_tokens // 4


def simulate(n_turns: int = 60):
    """Return per-turn effective-turns-retained for the three strategies,
    plus the cumulative count of extra summarizer calls."""
    turns = np.arange(1, n_turns + 1)

    fifo = np.empty(n_turns)
    per_message = np.empty(n_turns)
    summarize = np.empty(n_turns)
    summarizer_calls = np.empty(n_turns)

    calls = 0
    for k, t in enumerate(turns):
        raw_tokens = t * TURN_TOKENS

        # FIFO: keep as many of the most recent whole turns as fit.
        kept_turns = min(t, WINDOW // TURN_TOKENS)
        fifo[k] = kept_turns

        # Per-message pruning: messages are smaller than turns, so the window
        # holds a few more messages' worth of meaning, but it is still pure
        # deletion of the oldest content.
        kept_messages = min(2 * t, WINDOW // ((USER_TOKENS + ASSISTANT_TOKENS) // 2))
        per_message[k] = kept_messages / 2.0

        # Summarization-pruning: keep the latest turn verbatim, fold the rest
        # into one summary that fits under the cap.
        if raw_tokens <= WINDOW:
            summarize[k] = t  # everything still fits verbatim
        else:
            folded = t - 1  # all but the most recent turn get summarized
            summary_tokens = min(folded * TURN_TOKENS * SUMMARY_COMPRESSION, SUMMARY_CAP)
            if summary_tokens + TURN_TOKENS <= WINDOW:
                summarize[k] = 1 + folded * SUMMARY_MEANING_RETENTION
                calls += 1
            else:
                # Summary itself too big: fall back to FIFO for this turn.
                summarize[k] = kept_turns
        summarizer_calls[k] = calls

    return {
        "turns": turns,
        "raw_tokens": turns * TURN_TOKENS,
        "fifo": fifo,
        "per_message": per_message,
        "summarize": summarize,
        "summarizer_calls": summarizer_calls,
        "window": WINDOW,
    }
