# Blog Batch #2 — Fifteen Posts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce 15 publishable blog posts (`web/src/content/blog/<slug>.mdx`, `status: draft`), each grounded in a real artifact from Vagner's repos and, where honest, pegged to a July 2026 trend, all compliant with `web/src/content/writing-style.md`.

**Architecture:** Each post is one task. A task is not just prose: it runs the full production pipeline for that post — gather source truth from the real repo (via codegraph), targeted web research for trend claims, run the real code in a sandbox to capture true output/numbers, generate a figure that shows the thesis, draft to the style guide, lint, and commit as a draft. **Authoring and approval are separate passes:** a task ends at `status: draft`; `pnpm post:approve` happens later in a distinct review pass (never self-approved in the authoring context).

**Tech Stack:** Astro content collections (MDX), `astro:assets` `<Image>`, `bessaviz` (TikZ/LuaLaTeX → SVG/PNG) for figures, `pnpm post:*` tooling, `codegraph` MCP for reading source repos, WebSearch for trend sourcing.

---

## Global Constraints

Every task's requirements implicitly include this section. Values are copied verbatim from `web/src/content/writing-style.md` and `web/src/content.config.ts`.

- **Never fabricate.** Every number, quote, error, screenshot, and code snippet must trace to a real artifact gathered in the task. If a fact is unavailable, insert an explicit `[TODO: …]` placeholder for Vagner — never guess. "Genuinely smooth" beats a manufactured crisis.
- **Voice:** first-person singular, the builder at the terminal (not a columnist narrating the codebase). English, for a peer/recruiter international audience. Gloss Brazil-specific terms in one line.
- **Length:** 1,500–2,500 words for a standard post. Below ~1,200 words, ask whether it is a section of an existing post instead.
- **No em-dash.** Replace with a colon (introduces), comma/parentheses (aside), or a full stop (new sentence).
- **No AI-slop vocab:** no "in today's world", "dive in", "unlock", "leverage", "game-changer", "delve". Cut hype adjectives. Show, don't announce.
- **Be precise with AI vocabulary:** an LLM call is not an "agent"; a fixed pipeline is not "autonomous".
- **Name the pattern:** Ports & Adapters, Dependency Inversion, idempotency, N+1, EDD, etc. — say the recognized term and gloss it in the same breath.
- **Internal linking:** 3–8 descriptive, varied-anchor, in-body links to real existing URLs only (`/blog/<slug>/` for posts, `/building/<project>/<slug>/` for updates). No links to unwritten posts. One link per idea; a destination once.
- **Figures must show the thesis** (`web/src/content/writing-style.md` "Show the plot"), imported via `<Image>` from `web/src/assets/blog/<slug>/`. No decorative figures. Cut trivial code dumps (a 3-line helper is a sentence, not a fenced block).
- **Frontmatter schema** (`content.config.ts`): required `title`, `description`, `pubDate` (full ISO `-03:00`), `tags` (array); `status: draft` for all posts in this batch; optional `cta` ∈ {`lets-talk`,`cv`,`follow-build`,`subscribe`}, `heroImage`. **Never hand-edit `reviewedAt` / `reviewHash`** (set only by `pnpm post:approve`).
- **Tooling:** this repo uses **pnpm**, run from `web/`. `npm install` fails; `pnpm` run-scripts only.
- **Commits:** repo convention `content(blog): <verb> <slug>`. For this batch use `content(blog): draft <slug>`. **NO AI attribution** — no `Co-Authored-By`, no "Generated with", no Claude/Anthropic mention (Vagner's standing rule).
- **Clean-room framing:** reference prior/confidential techniques as references only; never imply reuse of NDA or proprietary code. `blinkebot` is off-limits as a subject.
- **Audit each post against the previously drafted one for repeated arc** (struggle→breakthrough / discovery / decision / honest grind) — rotate the shape deliberately.

## Suggested publish schedule (adjustable; `pubDate` only gates go-live, drafts are safe to merge early)

The current batch publishes through `2026-07-25`. Schedule batch #2 after that, news-pegged (⏱) posts first because they decay. All at `05:00:00-03:00`.

| # | Slug | pubDate | Flag |
|---|------|---------|------|
| 1 | `when-a-model-broke-containment` | 2026-07-27 | ⏱ |
| 11 | `model-churn-is-a-maintenance-tax` | 2026-08-04 | ⏱ |
| 14 | `a-code-knowledge-graph-in-my-editor` | 2026-08-05 | ⏱ |
| 4 | `dont-let-the-llm-do-the-math` | 2026-08-07 | |
| 6 | `htmx-crud-react-islands-dashboard` | 2026-08-09 | |
| 8 | `typed-domain-exceptions-stable-error-codes` | 2026-08-11 | |
| 9 | `finding-the-n-plus-one-before-prod` | 2026-08-13 | |
| 2 | `evaluation-driven-development-for-agents` | 2026-08-15 | |
| 10 | `an-api-first-vault-my-agents-can-call` | 2026-08-18 | |
| 5 | `pgvector-agent-long-term-memory` | 2026-08-20 | |
| 12 | `rendering-my-blog-diagrams-as-code` | 2026-08-22 | |
| 3 | `the-boring-controls-that-stop-an-agent` | 2026-08-25 | |
| 13 | `retiring-a-python-app-for-static-astro` | 2026-08-27 | |
| 7 | `voice-note-to-ledger-entry` | 2026-08-29 | spoke-risk |
| 15 | `context-engineering-a-fleet-of-subagents` | 2026-09-01 | |

---

## Standard Post Production Workflow

Each task below instantiates this ordered workflow with its own concrete inputs. A task lists which optional steps (⌕ research, ▶ sandbox/data, ▣ figure) apply. **Do not skip step 1 or step 7.**

- **S1 · Gather source truth.** Read the cited repo artifacts with `codegraph_explore` (pass the exact symbol/file names the task lists). If that repo has **no `.codegraph/`**, index it first (run codegraph indexing + start the daemon for that workspace), then explore. Collect the real code, commit SHAs, and file paths. Nothing enters the post that was not read here.
- **S2 · ⌕ Research.** Run the exact WebSearch queries the task lists. Record the source URLs; every trend claim in the post links a real source.
- **S3 · ▶ Sandbox / data.** Run the exact commands the task lists against a real fixture in the source repo. Capture the **real** terminal output / numbers to embed. Non-reproducible number → `[TODO]`, never invented.
- **S4 · ▣ Figure.** Produce the figure per the task's spec into `web/src/assets/blog/<slug>/`. It must show the thesis. If the task says "prose only", skip.
- **S5 · Draft** `web/src/content/blog/<slug>.mdx`, building ONLY from S1–S4. Follow the arc; name the pattern; add exactly the internal links the task lists; obey never-fabricate + `[TODO]`.
- **S6 · Frontmatter** — paste the task's block verbatim (`status: draft`).
- **S7 · Self-review vs `writing-style.md`** — run the checklist below; fix in place.
- **S8 · Verify:** `cd web && pnpm post:lint` (frontmatter + links) and `pnpm post:status` (shows the post as draft). Confirm word count 1,500–2,500 and that every internal link resolves to an existing route. Preview with `astro dev --background` if a figure/layout needs eyes.
- **S9 · Commit:** `git add web/src/content/blog/<slug>.mdx web/src/assets/blog/<slug>/ && git commit -m "content(blog): draft <slug>"` (no AI attribution).

**S7 self-review checklist (every post):**
- [ ] Every fact traces to an S1–S3 artifact; open questions are `[TODO]`, not guesses.
- [ ] No em-dash; no AI-slop vocab; AI terms used precisely.
- [ ] 1,500–2,500 words; one clear idea; leads with the finding, not the plumbing.
- [ ] The named pattern is stated and glossed.
- [ ] 3–8 in-body links, varied anchor text, all to existing routes.
- [ ] Any figure shows the thesis (not decoration); trivial code dumps cut.
- [ ] Arc differs from the previously drafted post (rotate the shape).
- [ ] `status: draft`; `reviewedAt`/`reviewHash` absent.

**Approval is out of scope for these tasks.** After a separate review pass (human or `oh-my-claudecode:code-reviewer`/`verifier`) signs off, run `cd web && pnpm post:approve web/src/content/blog/<slug>.mdx` in that pass.

---

## Task 1: ⏱ "When a model broke containment: what my LLM sandbox actually stops"

**Files:**
- Create: `web/src/content/blog/when-a-model-broke-containment.mdx`
- Assets: `web/src/assets/blog/when-a-model-broke-containment/`
- Source repo: `~/Documents/projetos/friday` (the `blog-rewrite-sandboxing` merge, 2026-06-23) + existing pillar `web/src/content/blog/running-llm-generated-code-safely.mdx`

**Applies:** S1, ⌕S2, ▶S3, ▣S4, S5–S9.

- [ ] **S1** — `codegraph_explore` on `friday` for the sandbox execution path (query: `sandbox run subprocess isolation exec llm code`). `friday` has **no `.codegraph/`** → index it first. Also re-read the existing pillar `running-llm-generated-code-safely.mdx` in full to avoid restating it.
- [ ] **⌕S2** — WebSearch exactly: `OpenAI Hugging Face model containment breach ExploitGym July 2026`; `Cloud Security Alliance research note OpenAI sandbox escape Hugging Face`. Cite: TechCrunch (2026-07-21), the CSA research note, and OpenAI's own incident post. One-line gloss of what ExploitGym was.
- [ ] **▶S3** — In `friday`'s sandbox, run one snippet that attempts network egress and one that attempts a filesystem escape; capture the real "blocked" output to embed as the concrete proof the sandbox holds. If the sandbox is CLI-invokable, record the exact command + output; else `[TODO: capture blocked-egress output]`.
- [ ] **▣S4** — Figure: a threat-model diagram (bessaviz `two_lane_flow` or ports-adapters composer) showing "untrusted LLM code → sandbox boundary → {denied: egress, fs, creds} / {allowed: cpu, tmp}". Export SVG to the assets dir. Must map to the real controls found in S1.
- [ ] **S5** — Arc = **discovery/decision** (read a real containment failure against my own threat model). Open by grounding the reader: what "breaking containment" means, one sentence on the HF incident, then pivot to my sandbox's assumptions: what it stops, what it deliberately doesn't, and why that's a defensible line. Name the pattern: **capability confinement / least privilege**. In-body links (choose 3–5): `/blog/running-llm-generated-code-safely/` (the pillar), `/building/replaygate/05-the-llm-judge-that-cant-fail-your-build/`, `/blog/spec-driven-scaffolding/` (determinism-where-you-can). End on an honest question about where readers draw their own containment line.
- [ ] **S6** — Frontmatter:
```yaml
---
title: "When a model broke containment: what my LLM sandbox actually stops"
description: "OpenAI says its models escaped a sandbox and attacked Hugging Face to cheat an eval. I read that failure against my own LLM code sandbox: what it confines, what it deliberately doesn't, and why least privilege is the only line that holds."
pubDate: 2026-07-27T05:00:00-03:00
tags: ["security", "llm", "sandboxing", "ai-safety", "python"]
status: draft
cta: follow-build
---
```
- [ ] **S7 / S8 / S9** — checklist; `pnpm post:lint`; commit `content(blog): draft when-a-model-broke-containment`.

---

## Task 2: "Evaluation-driven development for agents: a regress-gate that can't fail your build"

**Files:**
- Create: `web/src/content/blog/evaluation-driven-development-for-agents.mdx`
- Assets: `web/src/assets/blog/evaluation-driven-development-for-agents/`
- Source repo: `~/Documents/projetos/replaygate` + its buildlog series (`web/src/content/buildlog/replaygate/01…05`)

**Applies:** S1, ⌕S2, ▶S3, ▣S4, S5–S9.

- [ ] **S1** — Read all five `replaygate` buildlog entries + `codegraph_explore` on `replaygate` (query: `record replay regress gate llm judge cross version`). Extract the real methodology (record → offline replay → regress-gate → cross-version diverged → advisory LLM judge). This blog post is the **pillar** those spokes hang off; it must generalize, not restate any single update.
- [ ] **⌕S2** — WebSearch: `evaluation-driven development AI agents 2026 Promptfoo Galileo`; confirm the OpenAI/Promptfoo acquisition (Mar 2026) and the "82% prompt engineering insufficient" survey stat. Link both.
- [ ] **▶S3** — Run the `replaygate` regress-gate against a recorded fixture and capture the real pass/diverged output to show the gate in action. `[TODO]` any figure the run can't produce.
- [ ] **▣S4** — Figure: the EDD loop (bessaviz pipeline composer): record → replay → regress-gate → judge (advisory). Show why the LLM judge is advisory (can't fail the build). SVG to assets dir.
- [ ] **S5** — Arc = **the honest grind → method**. Thesis: agents need EDD the way code needs tests, but the "assert" is fuzzy, so the judge advises and the deterministic replay gates. Name the patterns: **evaluation-driven development**, **golden/replay testing**, **advisory oracle**. Links (3–6): the five buildlog updates (link the series hub `/building/replaygate/` once + at most two specific updates), `/blog/spec-driven-scaffolding/` (determinism-where-you-can), `/blog/running-llm-generated-code-safely/`.
- [ ] **S6** — Frontmatter:
```yaml
---
title: "Evaluation-driven development for agents: a regress-gate that can't fail your build"
description: "Agents need tests the way code does, but the assertion is fuzzy. Here's the EDD loop I built into ReplayGate: deterministic offline replay that gates the build, and an LLM judge that only ever advises."
pubDate: 2026-08-15T05:00:00-03:00
tags: ["ai-agents", "testing", "evaluation", "llm", "ci"]
status: draft
cta: follow-build
---
```
- [ ] **S7 / S8 / S9** — commit `content(blog): draft evaluation-driven-development-for-agents`.

---

## Task 3: "The boring controls that stop an agent: non-root, egress filtering, read-only mounts, timeouts"

**Files:**
- Create: `web/src/content/blog/the-boring-controls-that-stop-an-agent.mdx`
- Assets: `web/src/assets/blog/the-boring-controls-that-stop-an-agent/`
- Source repo: `~/Documents/projetos/friday` sandbox config (same path as Task 1's S1)

**Applies:** S1, ⌕S2, ▶S3, prose-only (no figure unless a controls table earns an image), S5–S9.
**Merge-guard:** if while drafting this reads as one argument with Task 1, fold this checklist into Task 1 and drop this task (promote an alternate). Spoke, not a split: link both ways.

- [ ] **S1** — From `friday`'s sandbox, enumerate the real runtime controls actually in place (user/uid, network policy, mount flags, timeout). Only write controls that exist; a control I don't implement is named as a deliberate gap, not claimed.
- [ ] **⌕S2** — WebSearch: `sandbox AI agents 2026 microVM gVisor Kata egress filtering non-root Northflank Modal`. Cite the 2026 stack and the "~90% fewer incidents" figure as external context, then contrast with my simpler-but-real controls.
- [ ] **▶S3** — Demonstrate one control catching something: run a snippet that exceeds the timeout, and one that tries to write a read-only mount; capture the real failures.
- [ ] **S5** — Arc = **honest grind**. Lead with the finding (the unglamorous controls do most of the work); demote theory. Name the pattern: **defense in depth / least privilege**. Be candid about what I deferred (e.g. microVM isolation) and why it's safe for my threat model. Links (3–4): `/blog/when-a-model-broke-containment/` (Task 1), `/blog/running-llm-generated-code-safely/`, `/blog/spec-driven-scaffolding/`.
- [ ] **S6** — Frontmatter:
```yaml
---
title: "The boring controls that stop an agent"
description: "MicroVMs and gVisor get the headlines. The controls that actually stopped things in my LLM sandbox were duller: a non-root user, egress filtering, read-only mounts, and a hard timeout. Here's each one and what it caught."
pubDate: 2026-08-25T05:00:00-03:00
tags: ["security", "sandboxing", "devops", "llm", "linux"]
status: draft
cta: follow-build
---
```
- [ ] **S7 / S8 / S9** — commit `content(blog): draft the-boring-controls-that-stop-an-agent`.

---

## Task 4: "Don't let the LLM do the math: deterministic discount proration for receipt OCR"

**Files:**
- Create: `web/src/content/blog/dont-let-the-llm-do-the-math.mdx`
- Assets: `web/src/assets/blog/dont-let-the-llm-do-the-math/`
- Source repo: `~/Documents/projetos/expense_tracker_v2` (has `.codegraph/`)

**Applies:** S1, ▶S3, ▣S4, S5–S9. (No web research required; evergreen craft.)

- [ ] **S1** — `codegraph_explore` on `expense_tracker_v2` (query: `receipt discount prorate line items sum amount paid`). Find the real proration function (the one that splits a discount across line items so the sum equals the amount paid). Record its exact location and logic. Confirm it is distinct from `credit-card-billing-cycles.mdx` (which month) and `pulling-structured-data-from-unstructured-documents.mdx` (field extraction).
- [ ] **▶S3** — Run the proration function against a real (or fixture) receipt with a whole-order discount; capture output showing line-item shares summing exactly to the paid total (including the rounding-remainder handling). This IS the post's proof. If there is a unit test, run it and quote the assertion; if not, note that as a candidate test to add.
- [ ] **▣S4** — Figure: a small "vision model extracts → Python prorates → sums to total" flow (bessaviz `two_lane_flow`, "LLM" lane vs "deterministic" lane), or a numeric table image showing the split summing to the paid amount. Must show the thesis (the split reconciles).
- [ ] **S5** — Arc = **discovery** (the LLM's arithmetic drifts by cents; move the math to Python). Open with the concrete "a receipt is line items plus one order-level discount" framing. Name the pattern: **deterministic core, probabilistic edge** (LLM only where ambiguity lives). Include the one load-bearing snippet (the proration + remainder distribution); cut trivial helpers. Links (3–5): `/blog/pulling-structured-data-from-unstructured-documents/` (pillar), `/blog/credit-card-billing-cycles/`, `/blog/spec-driven-scaffolding/`.
- [ ] **S6** — Frontmatter:
```yaml
---
title: "Don't let the LLM do the math: deterministic discount proration for receipt OCR"
description: "A vision model reads the receipt fine, then quietly loses a cent splitting the discount. Here's why I moved the arithmetic out of the model into a small Python function whose shares always sum to the amount paid."
pubDate: 2026-08-07T05:00:00-03:00
tags: ["python", "llm", "ocr", "fintech", "domain-driven-design"]
status: draft
cta: lets-talk
---
```
- [ ] **S7 / S8 / S9** — commit `content(blog): draft dont-let-the-llm-do-the-math`.

---

## Task 5: "pgvector as an agent's long-term memory: user rules that survive the session"

**Files:**
- Create: `web/src/content/blog/pgvector-agent-long-term-memory.mdx`
- Assets: `web/src/assets/blog/pgvector-agent-long-term-memory/`
- Source repo: `~/Documents/projetos/expense_tracker_v2` (has `.codegraph/`)

**Applies:** S1, ⌕S2, ▶S3, ▣S4, S5–S9. **Spoke-guard:** must not restate `giving-an-llm-agent-memory.mdx`; if it can't clear that pillar's authority, convert to a section there instead (alternate A/B fills the slot).

- [ ] **S1** — `codegraph_explore` on `expense_tracker_v2` (query: `pgvector embedding user rule semantic memory retrieve category`). Find how user rules ("cigarettes → Álcool") are embedded, stored, and retrieved at registration time. Read `giving-an-llm-agent-memory.mdx` to draw a clean boundary (summarization memory vs embedding retrieval).
- [ ] **⌕S2** — WebSearch: `context engineering persistent memory pgvector agents 2026`; cite one 2026 context-engineering source for the "memory outside the window" framing.
- [ ] **▶S3** — Run a real query: given a note, show the retrieved rule and the resulting category decision; capture the actual embedding-match output (distance/score + chosen rule). `[TODO]` if not reproducible offline.
- [ ] **▣S4** — Figure: retrieval flow (note → embed → nearest user-rule → applied category), bessaviz pipeline. Show the thesis (the rule persists across sessions).
- [ ] **S5** — Arc = **decision** (why embeddings, not a rules table or a bigger prompt). Name the patterns: **retrieval-augmented memory**, **vector similarity**. Links (3–5): `/blog/giving-an-llm-agent-memory/` (pillar), `/blog/pruning-chat-context-by-summarization/`, `/blog/dont-let-the-llm-do-the-math/` (Task 4, same app).
- [ ] **S6** — Frontmatter:
```yaml
---
title: "pgvector as an agent's long-term memory: user rules that survive the session"
description: "My bookkeeping assistant kept re-learning that I file cigarettes under Álcool. The fix wasn't a bigger prompt: it was storing each learned rule as a pgvector embedding and retrieving it by similarity at registration time."
pubDate: 2026-08-20T05:00:00-03:00
tags: ["llm", "pgvector", "postgres", "ai-agents", "django"]
status: draft
cta: lets-talk
---
```
- [ ] **S7 / S8 / S9** — commit `content(blog): draft pgvector-agent-long-term-memory`.

---

## Task 6: "HTMX for the CRUD, React islands for the dashboard: one Django app, two rendering strategies"

**Files:**
- Create: `web/src/content/blog/htmx-crud-react-islands-dashboard.mdx`
- Assets: `web/src/assets/blog/htmx-crud-react-islands-dashboard/`
- Source repo: `~/Documents/projetos/expense_tracker_v2` (has `.codegraph/`)

**Applies:** S1, ⌕S2, ▣S4, S5–S9. (No sandbox run required; architecture-decision post. Optional ▶S3 to show a real HTMX vs island response.)

- [ ] **S1** — `codegraph_explore` on `expense_tracker_v2` (query: `htmx partial template react island dashboard mount DRF api`). Identify concretely which pages are HTMX-driven and which are React+Recharts islands over the DRF API, and where the seam is.
- [ ] **⌕S2** — WebSearch: `2026 Django AI stack HTMX React islands async ORM`; cite one trend piece to place the pattern, then ground it in my real seam.
- [ ] **▣S4** — Figure: architecture diagram (bessaviz ports-adapters or two-lane) — "server-rendered HTMX CRUD | JSON DRF API | React island dashboard". Show the decision rule (interactivity gradient).
- [ ] **S5** — Arc = **decision** (the fork: when a page earns a client island vs when HTMX is enough). Lead with the rule I settled on, then the two real examples. Name the pattern: **islands architecture / progressive enhancement**. Be honest about the cost (two mental models, two build paths). Links (3–5): `/blog/dont-let-the-llm-do-the-math/`, `/blog/pgvector-agent-long-term-memory/`, `/blog/real-time-websockets-with-django-channels/` (adjacent Django interactivity).
- [ ] **S6** — Frontmatter:
```yaml
---
title: "HTMX for the CRUD, React islands for the dashboard: one Django app, two rendering strategies"
description: "Not every page earns a client-side framework. In my expense tracker, HTMX drives the CRUD-heavy pages and React islands power only the analytics dashboard and chat widget. Here's the rule I use to decide which gets which."
pubDate: 2026-08-09T05:00:00-03:00
tags: ["django", "htmx", "react", "frontend-architecture", "full-stack"]
status: draft
cta: cv
---
```
- [ ] **S7 / S8 / S9** — commit `content(blog): draft htmx-crud-react-islands-dashboard`.

---

## Task 7: "Voice note to ledger entry: a media pipeline that persists nothing"

**Files:**
- Create: `web/src/content/blog/voice-note-to-ledger-entry.mdx`
- Assets: `web/src/assets/blog/voice-note-to-ledger-entry/`
- Source repo: `~/Documents/projetos/expense_tracker_v2` (has `.codegraph/`)

**Applies:** S1, ▣S4, S5–S9. **Spoke-guard (high):** must not restate `local-whisper-transcription-pipeline.mdx`; the distinct angle is the **privacy-first discard design + routing into a structured registration flow**. If it can't clear that, drop for alternate A (CSV importer) or B (PWA→TWA).

- [ ] **S1** — `codegraph_explore` on `expense_tracker_v2` (query: `voice note transcribe media temp delete discard registration flow`). Confirm the real "processed and discarded, never persisted" handling and the routing into the same entry-registration path as text.
- [ ] **▣S4** — Figure: media lifecycle (record → transcribe → route → **discard**), bessaviz pipeline, with the discard step emphasized. Show the thesis (nothing is retained).
- [ ] **S5** — Arc = **decision** (a privacy default: process in memory, keep the structured entry, drop the audio). Name the pattern: **data minimization**. Explicitly link and defer transcription mechanics to the existing post rather than repeat them. Links (3–5): `/blog/local-whisper-transcription-pipeline/` (pillar for the transcription), `/blog/dont-let-the-llm-do-the-math/`, `/blog/pulling-structured-data-from-unstructured-documents/`.
- [ ] **S6** — Frontmatter:
```yaml
---
title: "Voice note to ledger entry: a media pipeline that persists nothing"
description: "You record 'gastei 45 no mercado', and a structured expense appears. The audio never touches disk. Here's the deliberately forgetful media pipeline behind it, and why data minimization was the default I wanted."
pubDate: 2026-08-29T05:00:00-03:00
tags: ["python", "privacy", "audio", "django", "llm"]
status: draft
cta: lets-talk
---
```
- [ ] **S7 / S8 / S9** — commit `content(blog): draft voice-note-to-ledger-entry`.

---

## Task 8: "Typed domain exceptions with stable error codes: errors your frontend can branch on"

**Files:**
- Create: `web/src/content/blog/typed-domain-exceptions-stable-error-codes.mdx`
- Assets: `web/src/assets/blog/typed-domain-exceptions-stable-error-codes/`
- Source repo: `~/Documents/projetos/ledgerus` (has `.codegraph/`; the "typed domain exceptions with stable error codes" commit, 2026-07-23)

**Applies:** S1, ⌕S2 (light demand check only), ▶S3, S5–S9. (Prose + one snippet; figure optional.)

- [ ] **S1** — `codegraph_explore` on `ledgerus` (query: `domain exception error code typed hierarchy serializer response`). Read the real exception hierarchy, the stable error-code registry, and how it maps to an API error body. Read the ADRs if they justify it.
- [ ] **⌕S2** — Optional GSC/demand sanity: WebSearch `django domain exceptions stable error codes API` to confirm the phrasing readers use; align title/tags.
- [ ] **▶S3** — Trigger one domain error through the API and capture the real JSON error body (code + message + shape). Show a client branching on the stable code. `[TODO]` if the endpoint isn't runnable offline.
- [ ] **S5** — Arc = **honest grind → payoff** (untyped 400s vs a code the frontend can switch on). Name the patterns: **domain exceptions**, **error taxonomy**, **anti-corruption at the boundary**. One load-bearing snippet: the base exception + code enum + the serializer hook. Links (3–5): `/blog/polymorphic-vaults-in-drf/`, `/blog/real-time-websockets-with-django-channels/`, `/building/regwatch/08-one-stack-trace-two-root-causes/` (error-handling adjacency).
- [ ] **S6** — Frontmatter:
```yaml
---
title: "Typed domain exceptions with stable error codes: errors your frontend can branch on"
description: "A bare HTTP 400 tells the frontend nothing. In Ledgerus I gave every domain failure a typed exception and a stable error code, so the client can branch on the code instead of string-matching a message that changes."
pubDate: 2026-08-11T05:00:00-03:00
tags: ["python", "django", "drf", "domain-driven-design", "api-design"]
status: draft
cta: cv
---
```
- [ ] **S7 / S8 / S9** — commit `content(blog): draft typed-domain-exceptions-stable-error-codes`.

---

## Task 9: "Finding the N+1 before it finds prod: testing query counts, naive vs eager"

**Files:**
- Create: `web/src/content/blog/finding-the-n-plus-one-before-prod.mdx`
- Assets: `web/src/assets/blog/finding-the-n-plus-one-before-prod/`
- Source repo: `~/Documents/projetos/personal-registry` (**no `.codegraph/`** — index first; the "measure Item list query counts (naive vs eager)" commit, 2026-07-09)

**Applies:** S1, ▶S3, ▣S4, S5–S9.

- [ ] **S1** — Index `personal-registry` with codegraph, then `codegraph_explore` (query: `assertNumQueries item list select_related prefetch_related vault endpoint`). Find the real query-count test and the naive vs eager fetch on the vault `Item` list.
- [ ] **▶S3** — Run the query-count test both ways; capture the **real** numbers (e.g. naive N+1 count vs eager count) from `assertNumQueries` / Django Debug Toolbar. These two numbers are the post's spine.
- [ ] **▣S4** — Figure: a bar chart (bessaviz raster or hand-authored SVG) of queries-per-request, naive vs eager, at a couple of list sizes — showing the naive line growing with N and the eager staying flat. Must show the thesis (N+1 scales, eager doesn't).
- [ ] **S5** — Arc = **discovery** (the list endpoint looked fine until the fixture grew). Name the pattern: **N+1 query problem**, `select_related`/`prefetch_related`, **query-count regression test**. Include the `assertNumQueries` snippet (load-bearing). Links (3–5): `/blog/polymorphic-vaults-in-drf/` (same vault), `/blog/idempotent-scheduled-jobs-with-celery-beat/`, `/building/regwatch/03-the-daily-run-made-real/`.
- [ ] **S6** — Frontmatter:
```yaml
---
title: "Finding the N+1 before it finds prod: testing query counts, naive vs eager"
description: "The vault list endpoint was fine with ten items and quietly quadratic with a thousand. Here's the N+1 query bug, the one-line eager-loading fix, and the assertNumQueries test that keeps it from coming back."
pubDate: 2026-08-13T05:00:00-03:00
tags: ["django", "orm", "performance", "testing", "drf"]
status: draft
cta: cv
---
```
- [ ] **S7 / S8 / S9** — commit `content(blog): draft finding-the-n-plus-one-before-prod`.

---

## Task 10: "An API-first vault my agents can call: designing a DRF backend for MCP-style consumers"

**Files:**
- Create: `web/src/content/blog/an-api-first-vault-my-agents-can-call.mdx`
- Assets: `web/src/assets/blog/an-api-first-vault-my-agents-can-call/`
- Source repo: `~/Documents/projetos/personal-registry` (index if not already from Task 9)

**Applies:** S1, ⌕S2, ▣S4, S5–S9. **Spoke-guard:** distinct from `polymorphic-vaults-in-drf.mdx` (that's the polymorphism; this is the agent-consumer API design).

- [ ] **S1** — `codegraph_explore` on `personal-registry` (query: `DRF viewset serializer stable UUID idempotent create OpenAPI spectacular vault API`). Extract the real API-design choices that make it agent-consumable: UUID IDs, metadata JSON, idempotent create, drf-spectacular schema.
- [ ] **⌕S2** — WebSearch: `MCP 2026-07-28 specification agents as API clients tools`; cite the MCP spec release and one "agents-as-clients" framing. Position the vault as the kind of stable backend an MCP tool wraps.
- [ ] **▣S4** — Figure: consumer diagram (bessaviz) — "OpenClaw skill / MCP tool → DRF vault API → structured items". Show the thesis (the same API serves a human UI and an agent).
- [ ] **S5** — Arc = **decision** (design the API for a non-human caller: stable IDs, idempotency, discoverable schema). Name the patterns: **API-first**, **idempotency keys**, **machine-discoverable schema (OpenAPI)**. Links (3–5): `/blog/polymorphic-vaults-in-drf/` (pillar), `/blog/giving-an-llm-agent-memory/`, `/blog/spec-driven-scaffolding/`.
- [ ] **S6** — Frontmatter:
```yaml
---
title: "An API-first vault my agents can call: designing a DRF backend for MCP-style consumers"
description: "I built the vault so a skill or an agent could store and fetch structured items without me rewriting the domain each time. That meant designing the DRF API for a non-human caller: stable UUIDs, idempotent writes, and a discoverable OpenAPI schema."
pubDate: 2026-08-18T05:00:00-03:00
tags: ["drf", "api-design", "mcp", "ai-agents", "django"]
status: draft
cta: follow-build
---
```
- [ ] **S7 / S8 / S9** — commit `content(blog): draft an-api-first-vault-my-agents-can-call`.

---

## Task 11: ⏱ "Model churn is a maintenance tax: what broke when GPT-5.6 and Gemini renamed everything"

**Files:**
- Create: `web/src/content/blog/model-churn-is-a-maintenance-tax.mdx`
- Assets: `web/src/assets/blog/model-churn-is-a-maintenance-tax/`
- Source repo: `~/Documents/projetos/aigents` (**no `.codegraph/`** — index first; the "refresh provider models to current IDs (gpt-5.6, gemini…)" commit, 2026-07-20)

**Applies:** S1, ⌕S2, ▶S3, S5–S9. **Spoke-guard:** distinct from `provider-agnostic-llm-abstraction.mdx` (the 30× hot-path pillar) — this is the ongoing maintenance cost behind that abstraction, not the abstraction itself.

- [ ] **S1** — Index `aigents`, then `codegraph_explore` (query: `provider model id registry chatter openai google gemini default model map`). Read the real model-ID map and what the "refresh to current IDs" commit actually changed (diff the commit).
- [ ] **⌕S2** — WebSearch: `LLM model releases July 2026 GPT-5.6 Sol Gemini GLM 5.2`; cite the model-wave sources. Ground the churn in dated real releases.
- [ ] **▶S3** — Show the real diff of the ID refresh (`git -C ~/Documents/projetos/aigents show <sha> -- <model map file>`); capture the before/after IDs as the concrete artifact.
- [ ] **S5** — Arc = **honest grind** (the abstraction was the easy part; keeping it current is the recurring tax). Name the pattern: **anti-corruption layer / adapter** absorbing provider churn. Lead with the finding (what actually broke: renamed IDs, changed defaults, capability drift). Links (3–5): `/blog/provider-agnostic-llm-abstraction/` (pillar), `/blog/sub-second-llm-triage/`, `/blog/running-llm-generated-code-safely/`.
- [ ] **S6** — Frontmatter:
```yaml
---
title: "Model churn is a maintenance tax: what broke when GPT-5.6 and Gemini renamed everything"
description: "A provider-agnostic layer is the easy part. The recurring cost is keeping the model IDs and capabilities current as GPT-5.6 and Gemini reshuffle underneath you. Here's the churn my adapter absorbed this month, and the diff that fixed it."
pubDate: 2026-08-04T05:00:00-03:00
tags: ["llm", "python", "api", "maintenance", "ai-engineering"]
status: draft
cta: lets-talk
---
```
- [ ] **S7 / S8 / S9** — commit `content(blog): draft model-churn-is-a-maintenance-tax`.

---

## Task 12: "Rendering my own blog diagrams as code: brand-themed TikZ with LuaLaTeX"

**Files:**
- Create: `web/src/content/blog/rendering-my-blog-diagrams-as-code.mdx`
- Assets: `web/src/assets/blog/rendering-my-blog-diagrams-as-code/`
- Source repo: `~/Documents/projetos/bessaviz` (**no `.codegraph/`** — index first)

**Applies:** S1, ▶S3, ▣S4 (the figure IS the demo), S5–S9.

- [ ] **S1** — Index `bessaviz`, then `codegraph_explore` (query: `two_lane_flow ports adapters PngExporter theme raster brand palette composer`). Read the real DDD structure (domain/application/adapters) and the `two_lane_flow` composer + `PngExporter`.
- [ ] **▶S3 / ▣S4** — Actually render a diagram with `bessaviz` (light + dark) and use that exact output as a figure in the post — the post demonstrates the tool by being illustrated with it. Capture the Python snippet that produced it. Export SVG/PNG to the assets dir.
- [ ] **S5** — Arc = **decision** (why generate figures as code: version-controlled, on-brand, regenerable, dark-mode for free). Name the pattern: **diagrams-as-code**, **Domain-Driven Design layering**. Connect to the site's own "show the plot" practice. Links (3–5): `/blog/branded-social-preview-images-at-build-time/` (pillar, build-time image gen), `/blog/beating-browser-fingerprinting/` (a post whose SVG figure this could render), CV/portfolio.
- [ ] **S6** — Frontmatter:
```yaml
---
title: "Rendering my own blog diagrams as code: brand-themed TikZ with LuaLaTeX"
description: "The figures in these posts aren't drawn by hand. They're generated by bessaviz, a small TikZ/LuaLaTeX library with my brand palette baked in: version-controlled, regenerable, and dark-mode for free. This post is illustrated with it."
pubDate: 2026-08-22T05:00:00-03:00
tags: ["latex", "tikz", "python", "dataviz", "tooling"]
status: draft
cta: follow-build
---
```
- [ ] **S7 / S8 / S9** — commit `content(blog): draft rendering-my-blog-diagrams-as-code`.

---

## Task 13: "Retiring a Python web app for a static Astro site: the cutover and what I gave up"

**Files:**
- Create: `web/src/content/blog/retiring-a-python-app-for-static-astro.mdx`
- Assets: `web/src/assets/blog/retiring-a-python-app-for-static-astro/`
- Source repo: `~/Documents/projetos/friday` (**no `.codegraph/`** — index if needed; this very site's repo)

**Applies:** S1, ▶S3, ▣S4 (optional), S5–S9.

- [ ] **S1** — In `friday`, read the git history around the aiohttp→Astro cutover (the README notes "the previous aiohttp/Python app was retired"). Find the real commit(s) removing the Python app, and the `projects.json` (schema-validated source of truth) → `portfolio.json` (build working copy) sync. Use `git log`/`git show` for the actual cutover.
- [ ] **▶S3** — Capture one real artifact of the win: e.g. the deploy config diff (aiohttp container vs nginx-static image on Cloud Run) or a build-output/size comparison if reproducible. `[TODO]` any metric not measurable now.
- [ ] **▣S4** — Optional figure: before/after architecture (dynamic Python server → static build + CDN/nginx on Cloud Run). Only if it shows the thesis; else prose.
- [ ] **S5** — Arc = **decision** (why static won here, and the honest list of what I gave up: no server-side dynamic bits, form handling moved, etc.). Name the pattern: **static-site generation / content as data (single source of truth)**. Links (3–5): `/blog/branded-social-preview-images-at-build-time/` (build-time generation on this site), `/blog/machine-readable-plan-format/` (schema-validated data adjacency), CV.
- [ ] **S6** — Frontmatter:
```yaml
---
title: "Retiring a Python web app for a static Astro site: the cutover and what I gave up"
description: "My portfolio used to be an aiohttp app. I replaced it with a static Astro site built into an nginx image on Cloud Run, driven by one schema-validated JSON source. Here's the cutover, and the honest list of what going static cost me."
pubDate: 2026-08-27T05:00:00-03:00
tags: ["astro", "static-site", "python", "cloud-run", "architecture"]
status: draft
cta: cv
---
```
- [ ] **S7 / S8 / S9** — commit `content(blog): draft retiring-a-python-app-for-static-astro`.

---

## Task 14: ⏱ "A code knowledge graph in my editor: how I actually use codegraph (MCP) to explore code"

**Files:**
- Create: `web/src/content/blog/a-code-knowledge-graph-in-my-editor.mdx`
- Assets: `web/src/assets/blog/a-code-knowledge-graph-in-my-editor/`
- Source: my real daily workflow with the `codegraph` MCP server across these repos (this repo's `CLAUDE.md` documents it).

**Applies:** S1, ⌕S2, ▶S3, ▣S4 (optional), S5–S9. **Framing-guard:** write as a *user* of codegraph (an MCP server I run), not its author, unless authorship is verified. No overclaiming.

- [ ] **S1** — Read this repo's `CLAUDE.md` "Code intelligence (codegraph)" section for the exact tool surface (`codegraph_explore`, `codegraph_callers`, etc.) and how I use it (read-before-edit, ~1s watcher lag, gitignored `.codegraph/`).
- [ ] **⌕S2** — WebSearch: `Model Context Protocol 2026-07-28 spec 10000 servers MCP Apps Linux Foundation`; cite the spec release and the adoption numbers to place codegraph in the MCP moment.
- [ ] **▶S3** — Capture a real before/after: one concrete question ("how does X work") answered by a single `codegraph_explore` call vs the grep+read loop it replaces. Use an actual query/result from one of these repos (redact nothing sensitive; pick a public-safe repo like `personal-registry`).
- [ ] **▣S4** — Optional figure: "question → codegraph index → verbatim source grouped by file" vs "question → grep → read → read → …". Show the collapse of many calls to one.
- [ ] **S5** — Arc = **discovery** (a pre-built index changed how I explore, not just how fast). Name the pattern: **code knowledge graph**, **Model Context Protocol (MCP)**, tool-augmented retrieval. Be precise: it's a search index I query, not magic. Links (3–5): `/blog/spec-driven-scaffolding/`, `/blog/giving-an-llm-agent-memory/`, `/blog/provider-agnostic-llm-abstraction/`.
- [ ] **S6** — Frontmatter:
```yaml
---
title: "A code knowledge graph in my editor: how I actually use codegraph over MCP"
description: "Before I edit a repo I don't grep it, I ask it. codegraph keeps a live SQLite graph of every symbol and edge, served over MCP, and one query returns the verbatim source a dozen greps would have chased. Here's how it changed the way I explore code."
pubDate: 2026-08-05T05:00:00-03:00
tags: ["mcp", "developer-tools", "code-intelligence", "ai-engineering", "workflow"]
status: draft
cta: follow-build
---
```
- [ ] **S7 / S8 / S9** — commit `content(blog): draft a-code-knowledge-graph-in-my-editor`.

---

## Task 15: "Context engineering over prompt engineering: running a fleet of subagents to plan this blog"

**Files:**
- Create: `web/src/content/blog/context-engineering-a-fleet-of-subagents.mdx`
- Assets: `web/src/assets/blog/context-engineering-a-fleet-of-subagents/`
- Source: this very planning session (parallel repo-scan subagents, isolated context windows, condensed summaries, this plan document).

**Applies:** S1, ⌕S2, ▣S4, S5–S9. **Meta-guard:** must show real decisions/transcript excerpts, not theory, or cut for the alternate. Never inflate "orchestration" into "autonomy".

- [ ] **S1** — Use this plan and the session's real structure as source: two parallel `Explore` subagents scanning `projetos/`/`trabalhos/` with isolated context, the trend WebSearches, the synthesis into 15 grounded tasks. Reference the real tools (Agent, subagent isolation, condensed summaries).
- [ ] **⌕S2** — WebSearch: `context engineering vs prompt engineering 2026 subagents isolated context`; cite the "82%" survey stat and Anthropic's subagent pattern (isolated windows, 1–2k-token summaries).
- [ ] **▣S4** — Figure: orchestrator → N isolated subagents → condensed summaries → synthesis (bessaviz). Show the thesis (isolation + summarization beats one giant context).
- [ ] **S5** — Arc = **decision / honest grind** (why I fanned out isolated subagents instead of one long context to plan this batch, and where it actually helped vs added overhead). Name the pattern: **context engineering**, **subagent isolation**, **map-reduce over context**. Be honest that a subagent returned only a summary and I gathered some data directly, faster. Links (3–5): `/blog/pruning-chat-context-by-summarization/` (pillar), `/blog/giving-an-llm-agent-memory/`, `/blog/spec-driven-scaffolding/`.
- [ ] **S6** — Frontmatter:
```yaml
---
title: "Context engineering over prompt engineering: running a fleet of subagents to plan this blog"
description: "To plan this fifteen-post batch I didn't write one giant prompt. I fanned out isolated subagents to scan my repos, kept only their condensed summaries, and synthesized. Here's what context engineering bought me, and where it just added overhead."
pubDate: 2026-09-01T05:00:00-03:00
tags: ["ai-agents", "context-engineering", "llm", "workflow", "meta"]
status: draft
cta: subscribe
---
```
- [ ] **S7 / S8 / S9** — commit `content(blog): draft context-engineering-a-fleet-of-subagents`.

---

## Task 16 (wrap): Batch cross-audit + internal-link graph

**Files:** all 15 `.mdx` from Tasks 1–15.

- [ ] **Step 1** — Read the 15 drafts in intended-publish order (schedule table). For each consecutive pair, verify the narrative arc differs (rotate: discovery / decision / honest grind / struggle→breakthrough). Fix any two-in-a-row same-shape.
- [ ] **Step 2** — Verify the internal-link graph: every in-body link points to an existing route (published post or `/building/<project>/<slug>/`); no post links to an unwritten sibling in this batch unless that sibling is already drafted; anchors are varied. Run `cd web && pnpm post:lint` across the batch.
- [ ] **Step 3** — Confirm spoke/pillar discipline: Tasks 3, 5, 7, 10, 11 read as spokes that add distinct intent, not authority-splitters against their pillars (Tasks 1, `giving-an-llm-agent-memory`, `local-whisper-transcription-pipeline`, `polymorphic-vaults-in-drf`, `provider-agnostic-llm-abstraction`). Collapse any that fail into a section of the pillar and promote an alternate (A: receipt CSV importer; B: PWA→TWA; C: cash-flow domain kernel).
- [ ] **Step 4** — `cd web && pnpm post:status` — confirm all 15 are `status: draft` with no stray `reviewedAt`/`reviewHash`. Approval is a separate pass.
- [ ] **Step 5** — Commit any audit fixes: `content(blog): batch-2 cross-audit fixes`.

---

## Alternates / bench (swap in per Task 16 Step 3)

- **A.** `web/src/content/blog/the-receipt-csv-importer.mdx` — `expense_tracker_v2`'s 4-step import wizard (upload → column-map → preview/conflict-resolve → bulk). Evergreen data-migration craft.
- **B.** `web/src/content/blog/pwa-to-android-twa.mdx` — `expense_tracker_v2` shipped as a PWA wrapped in a Trusted Web Activity; service worker, generated icons, native-feel install.
- **C.** `web/src/content/blog/cash-flow-as-a-domain-kernel.mdx` — `ledgerus`'s ADR-first cash-flow kernel: modeling money before building the app.

## Self-review (spec coverage / placeholders / consistency)

- **Coverage:** all 15 posts from the approved batch map to Tasks 1–15; the three deferred repos (blinkebot, ai-job-search, playset) and their reasons are recorded in the batch plan and excluded deliberately.
- **Placeholders:** no "TBD/implement later". Where post *content* can't be pre-written without fabricating, the task gives a concrete instruction to gather the real artifact (exact codegraph query, exact WebSearch, exact command) and to insert `[TODO]` only for genuinely missing facts — which is the never-fabricate rule, not a plan placeholder.
- **Consistency:** slugs, asset paths, frontmatter keys (`status: draft`, `cta` enum values), and the `content(blog): draft <slug>` commit form are identical across tasks and match `content.config.ts` and the shipped posts inspected (`spec-driven-scaffolding`, `credit-card-billing-cycles`).
