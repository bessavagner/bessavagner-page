# Notes for update 03: the E8 validation run

> Raw material, not a draft. This is a `.md`, so the buildlog collection
> (`**/*.mdx`) ignores it and the build never sees it, the same trick
> `writing-style.md` uses on itself.
>
> Every number below was verified by running the command, not read off an
> agent's summary. Where something is unverified it says so. Nothing here is
> reconstructed from memory.

Recorded 2026-07-22.

## The one-line version

supskill drove a real sprint on a brand new project all the way from an empty
repo to a closed Gate 3, which is the thing the blinkebot run never managed. It
found real defects in the code it was building, and the run found seven defects
in supskill itself.

## What the run was

A new project, `playset`: a local, single-user web app that turns a link to a
video or a playlist into MP3 files. Localhost only, no auth, fixed MP3 output,
no database because the output directory is the state. Built as the E8
validation target, so the point was never the app.

The backlog was written by hand before the conductor touched anything, because
supskill cannot produce the backlog it requires. That gap is parked in
supskill's own backlog as SK-090.

Sprint s1 committed epic E1: the tool seam and the output store. Three stories,
13 points at commit time.

## Verified numbers

Cost per stage, from `.supskill/runs/s1/costs.jsonl`:

| Stage | Tokens |
|---|---:|
| SCOPE | 49,973 |
| REFINE | 82,818 |
| PLAN | 164,426 |
| EXECUTE | 1,469,251 |
| REVIEW | 202,669 |
| **Total** | **1,969,137** |

EXECUTE is 75% of the run. Worth stating plainly, because the instinct before
seeing this was that planning was the expensive part.

Other verified figures:

- Scope grew 13 to 21 points at REFINE.
- 14 commits on branch `s1`, off `4e8255e`.
- 165 tests passing (132 at the EXECUTE halt, plus 33 from the two blocker
  fixes), `ruff` clean, `mypy` clean on 5 source files. Suite runs in 0.13s.
- 14 PAR findings: 1 Critical/high, 3 Important/high, 1 Important/actionable,
  5 Minor/high, 4 Minor/actionable. Nine matched across both reviewers.
- Gate 3 writeback: 27 insertions, 0 removals, new epic E1b, 5 rows, 10 points.

The three gate decisions, verbatim from `.supskill/gates.jsonl`:

- G1 `approved`: "Approved if you set output folder to ./output not ./download"
- G2 `approved`: "Approve"
- G3 `replan`: "Replan — generative writeback"

The G1 one is a nice detail. That amendment travelled all the way into a test
called `test_constants_match_the_gate_1_amendment`. An operator's offhand
sentence at a gate became a named assertion in the suite.

## Angle 1, probably the strongest: the plan that laundered a false proof

The PLAN stage produced 1,867 lines. Before saving, the planning agent
assembled every source and test block into a scratch project outside the repo
and ran it: 127 passed, `ruff` clean, `mypy` clean. It caught three real
defects in its own text that way, including seven `E402` violations from
appended import blocks.

Its self-review section then mapped acceptance criteria to test names,
including this pairing: PLS-002 acceptance 11, "two distinct items never
collide", to `test_distinct_items_never_collide`.

The shipped `derive_path` was not injective. Two confirmed collisions:

```
id='a/b'  and id='a\b'  with one title -> Same Title.a_b.mp3
title='a.b',id='c'  and  title='a',id='b.c' -> a.b.c.mp3
```

Both reproduced against the built package, not inferred.

So a green scratch run became a claim of proof for a property it never
actually checked. The scratch suite tested the hostile cases someone thought
of; it never searched for collisions. That is the finding: not that
pre-execution wastes tokens, but that it converts an assumption into the word
"verified", and every downstream stage reads that word as evidence.

The cost objection turned out to be small. PLAN was 164k of 1.97M, about 8%.
The correctness objection is the real one.

And EXECUTE caught it. That matters for honesty: the worry that a plan
containing working code turns EXECUTE into transcription did not happen.
EXECUTE spent 9x what PLAN did and found two blockers the plan's green run
missed.

## Angle 2: the refinement thesis, tested on an empty repo

Every prior data point for "refinement against live source grows scope" came
from a codebase that already existed. This was the first run against a repo
containing three files: a `.gitignore` and two docs.

Scope still grew, 13 to 21. But the *shape* of the finding inverted. Normally
REFINE catches a document that drifted from code that moved underneath it.
Here it caught the opposite: there is no code at all, and the sprint document
had assumed a project existed to add three modules to.

It also derived the whole toolchain from the only on-disk evidence available,
which was my `.gitignore`: pytest from `.pytest_cache/`, ruff from
`.ruff_cache/`, a local venv from `.venv/`, and the default output root from
`downloads/`.

That last one is the uncomfortable part and belongs in the post. I typed
`downloads/` into a `.gitignore` as boilerplate. The refinement pass correctly
treated the only on-disk evidence as authoritative and turned it into a
specification. My scaffolding became the spec by accident. The Gate 1
amendment above exists because of exactly this.

## Angle 3: what you install is not what you validated

This bit us twice, which is what makes it worth writing.

The blinkebot run had already reported that the marketplace plugin was behind
the dev repo and had to run the development binary instead. So before starting
playset, I bumped to 0.2.0, pushed, tagged, and confirmed CI green on the exact
SHA.

Then I told the operator the reload had picked up 0.2.0. It had not. I had
tested `./scripts/supskill-state` from inside the supskill checkout, which is
the dev copy, and inferred wrongly. The installed copies were both stale:

- `~/.claude/plugins/cache/supskill/supskill/0.1.0/`
- `~/.claude/plugins/marketplaces/supskill/` sitting at a July 14 commit

Both exposed only 10 subcommands. The four that 0.2.0 added, `config`,
`review`, `replan-guard`, `worktree`, were missing.

The mechanics worth documenting, because they are not obvious:

- `/reload-plugins` reloads what is on disk. It does not re-fetch from the
  remote.
- `claude plugin marketplace update supskill` updates the marketplace clone.
- `claude plugin update supskill` fails with `Plugin "supskill" not found`.
  The qualified name is required: `claude plugin update supskill@supskill`.

There is a good general point here: an installed-version check is a different
question from a source-version check, and being the author of the thing makes
you worse at telling them apart, not better.

## Angle 4: two of supskill's own invariants in conflict

Gate 3's generative writeback is append-only. Verified: 27 insertions, 0
removals. Prior rows and point totals untouched, which is the safety property
the shape exists to guarantee.

The result is a document that no longer agrees with itself:

| | |
|---|---|
| Story rows in the body | 22 rows, 73 pts |
| Summary table | 5 epics, 63 pts, no E1b |
| Stated total | still "Total: 63 pts" |

This is not cosmetic. `scope-prompt.md:41` tells the SCOPE agent its scope is
"the first epic in the backlog's recommended build order whose stories are
still unchecked", and the recommended build order *is* that summary table. E1b
is not in it. Meanwhile E1's rows still read unchecked on `main` because the
work is on an unmerged branch. So the next SCOPE would pick E1, which is
already built, and never see E1b.

The structural bit: correcting "Total: 63 pts" to 73 requires deleting a line,
which append-only forbids. The safety rule and document consistency cannot both
hold, and nothing in the shape resolves it. That is a better finding than a
simple bug because it is a genuine design tension, not an oversight.

## The seven supskill findings, for the record

1. Prompt templates hardcode `SK-0xx` (`scope-prompt.md:41`,
   `plan-prompt.md:46`, `replan-shapes.md:23`) while the parsers honor the
   configured prefix (`plan_coverage.py:31,78`). Only the REFINE agent noticing
   and overriding it kept the run alive. Judgment saved it, not mechanism.
2. `writing-plans` emits pre-executed implementations, and its self-review
   presents a green scratch run as proof. See angle 1.
3. No runtime preflight that the four dispatched skills resolve. If a
   dependency is missing the stage improvises, which is the exact failure the
   project exists to prevent. The irony is sharp: playset's own PLS-040 story
   is "refuse to start when a required external tool is missing".
4. An SDD fix subagent ran `git add -A` and swept `.omc/` harness state into a
   commit. The controller caught it and reset to the three intended files.
5. Task 9's plan instruction was unconditionally wrong, telling the agent to
   tick all three backlog stories when two were blocked. The controller
   overrode it correctly.
6. There is no inverse of `block`. After both blockers were resolved,
   `show --json` still reported "open blockers: 2", and Gate 3 presented two
   settled decisions as live ones.
7. Append-only writeback versus document consistency. See angle 4.

Findings 1, 3 and 6 are the ones a new user would hit. 2 and 7 are the
interesting ones.

## The defects in playset itself

Worth a short section because they are good examples of what adversarial review
actually buys.

The Critical, found independently by both reviewers and confirmed by me:
`derive_path` spends all 255 bytes of the filename budget on the final name,
then `temp_path_for` adds 6 more for a leading dot and a `.part` suffix. Any
title long enough to be truncated therefore produces a final path that writes
and a temp path that does not.

```
title len 230 -> final 246B, temp 252B -> writes OK
title len 300 -> final 255B, temp 261B -> OSError: File name too long
title len 500 -> final 255B, temp 261B -> OSError: File name too long
```

`"x"*500` is in the project's own hostile-input table. It passes
`test_hostile_input_fits_the_byte_budget` and can never be fetched. The reason
165 green tests said nothing about it is the sharpest line available: the
hostile-input tests exercise `derive_path` alone, every `atomic_fetch` test
uses a short title, and the two halves are never composed.

Also confirmed by direct test: the seam guard's denylist misses the entire `os`
spawn family. `posix_spawn`, `fork`, `spawnv`, `pty`, `multiprocessing`, all
planted, all returned NOT CAUGHT. This matters because `os` cannot be
import-banned, since `os.replace` is what makes the atomic write atomic, so the
call denylist is the only barrier there is.

## The disclosure that has to be in the post

I fixed the injectivity blocker with an `encode_id` that percent-encodes every
byte outside `[A-Za-z0-9_-]`. It is the right fix and both collisions died.

It also tripled the byte cost of non-ASCII ids. The overflow threshold moved
from about 124 characters to 43:

```
 40 non-ASCII chars -> old  80B | encode_id 240B
 43 non-ASCII chars -> old  86B | encode_id 258B
124 non-ASCII chars -> old 248B | encode_id 744B
```

I noticed the expansion while writing it, decided it fell inside an
already-deferred gap, and did not mention it. PAR found it instead. The post
should say that in the first person and without softening it, because the whole
project is an argument about not letting an agent quietly decide something on
your behalf, and I did exactly that to my own operator.

## Recurring harness quirk, third sighting

Dispatched subagents returned degenerate final messages again, placeholders
instead of their actual report, while having genuinely done the work. Both PAR
reviewers hit it and the conductor recovered their findings from the
transcripts.

This is the third run where it has appeared. It was in the SK-070 fixture
report and the SK-071 blinkebot report too. Three independent sightings is
enough to state it as a property of the environment rather than an anecdote.
The workaround both earlier reports landed on, write the deliverable to a file
and confirm it with a read before replying, still looks correct.

## Things I must not claim in the post

- Do not say E8 is closed. The reports are not written and the backlog rows for
  SK-070 and SK-071 are still unchecked as of this note.
- Do not say playset works. Nothing has been fetched. E1 is pure Python, there
  was no operator run, and no MP3 has ever been produced.
- Do not treat 165 green tests as evidence the store is correct. The Critical
  is the counterexample.
- Do not repeat update 2's unverified claim about cross-marketplace dependency
  fetching from a bare profile. Still unverified, and update 2 already flagged
  it honestly.
- `[TODO: whether branch s1 was merged, and how the backlog.md conflict between
  main and s1 was resolved. PLS-008 owns it. Unresolved when this note was
  written.]`
- `[TODO: the E8 report verdicts once written, and whether SK-071's caveat is
  considered answered by this run.]`

## Addendum, 2026-07-22: the sprint after this one inverted a prediction

Added after the note above was written. Full running record lives in
`supskill/validation/reports/playset-s2-2026-07-22.md`; only the angle is here.

playset s2 ran the remediation epic that s1's Gate 3 wrote back. Before it
started I predicted refinement would look weakest on the empty repo, since its
whole thesis is reading live source and there had been no source to read.

Backwards:

| | committed | after REFINE | growth |
|---|---:|---:|---:|
| s1, empty repo, rows I wrote by hand | 13 | 21 | +62% |
| s2, real codebase, rows from PAR findings | 9 | 10 | +11% |

The largest growth on record came from the repo with three files in it. The
smallest came from the mature codebase.

The explanation is probably not maturity but provenance. E1b's rows were
written back from defects two independent reviewers confirmed and I reproduced
by hand, so they arrived already carrying file, symptom, reproduction, and in
one case a measured byte count. Refinement had almost nothing left to find.
E1's rows came out of a brainstorming conversation about work nobody had looked
at yet, so refinement had to find everything.

If that holds up, the DoR growth number is a proxy for how well-sourced the
input was, not a constant tax on every sprint. It also makes an argument for the
generative writeback shape that I did not anticipate: a row written by a review
is cheaper to refine than a row written by a human imagining the work. One pair
of runs is not a trend, and the note should say so.

A caveat worth keeping in the post: three things differ between s1 and s2 at
once, not one. Codebase maturity, input provenance, and a conductor fix all
changed. The provenance explanation is the most plausible, not the proven one.

## Loose thread worth its own note

The brainstorm-to-backlog step is not a skill yet. I hand-wrote playset's
backlog in conversation before the conductor could start. supskill parks this
as SK-090, "a separate product, revisit after v1". It is a real gap at the
front of the chain and it is where I would look next.
