"""Token cost of one plan written as prose vs as machine-readable structure.

Honest, reproducible measurement. We write the SAME small plan twice:

* ``PROSE`` — how a human would naturally describe a two-step change, repeating
  the same edit shape in words both times.
* ``STRUCTURED`` — the same plan as XML-tagged tasks with the repeated edit
  shape lifted into a single referenced pattern.

Both versions instruct an agent to do the identical work. We count tokens with
tiktoken's ``cl100k_base`` encoding (the encoding used by GPT-4-class models and
a reasonable, public stand-in for "how many tokens does this context cost").
The numbers printed by this script are the numbers in the chart; nothing is
hand-tuned to make a point.
"""

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import tiktoken  # noqa: E402

# A human-style memo describing a two-step change. It explains the same
# "find this block, replace it with that block, then verify" shape twice.
PROSE = """\
We need to make the order service idempotent so that retried requests do not
create duplicate orders. There are two places to change.

First, in the order creation handler, find the part where we currently insert a
new order directly into the database without checking whether one already
exists for this request. You should replace that logic so that before inserting
we look up any existing order that has the same idempotency key, and if one is
found we return it instead of creating a second one. After you have made this
change, please run the order service test suite and confirm that all of the
tests pass, and that the new idempotency test in particular is green. Then make
a commit describing what you changed and why it was necessary.

Second, in the payment handler, find the part where we currently charge the
customer directly without checking whether we have already charged them for
this request. You should replace that logic so that before charging we look up
any existing charge that has the same idempotency key, and if one is found we
return it instead of charging a second time. After you have made this change,
please run the payment service test suite and confirm that all of the tests
pass, and that the new idempotency test in particular is green. Then make a
commit describing what you changed and why it was necessary.
"""

# The same plan, structured. The repeated "look up by key, else act" shape is
# defined once as a pattern and referenced; each task is an atomic edit with an
# explicit verification checklist.
STRUCTURED = """\
<goal>Make order + payment idempotent on retried requests.</goal>

<pattern name="dedupe_by_key">
existing = store.find_by_idempotency_key(key)
if existing:
    return existing
return store.create(...)
</pattern>

<task id="1" file="orders/handler.py">
<edit>apply @dedupe_by_key to the create-order path</edit>
<verify>
- [ ] run: test orders
- [ ] idempotency test passes
- [ ] commit: fix(orders): dedupe by idempotency key
</verify>
</task>

<task id="2" file="payments/handler.py">
<edit>apply @dedupe_by_key to the charge path</edit>
<verify>
- [ ] run: test payments
- [ ] idempotency test passes
- [ ] commit: fix(payments): dedupe by idempotency key
</verify>
</task>
"""

enc = tiktoken.get_encoding("cl100k_base")
prose_tokens = len(enc.encode(PROSE))
structured_tokens = len(enc.encode(STRUCTURED))
print(f"prose:      {prose_tokens} tokens")
print(f"structured: {structured_tokens} tokens")
print(f"reduction:  {100 * (1 - structured_tokens / prose_tokens):.0f}%")

apply()
fig, ax = plt.subplots(figsize=(6.0, 3.4))
labels = ["Prose memo", "Structured plan"]
values = [prose_tokens, structured_tokens]
bars = ax.bar(labels, values, color=[PALETTE[1], PALETTE[0]], width=0.55)
ax.bar_label(bars, padding=3, fmt="%d tokens")
ax.set_ylabel("Tokens (cl100k_base)")
ax.set_title("Same two-step plan, two ways of writing it")
ax.set_ylim(0, max(values) * 1.18)

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/machine-readable-plan-format/tokens.svg",
)
print(f"wrote {out}")
