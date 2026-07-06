# Writing style guide: blog posts and build-log updates

> Lives in `web/src/content/` (next to the `blog/` and `buildlog/` collections) so
> it's easy to find when writing a post. It is **not** a content entry itself: the
> collections only load `**/*.mdx` under `blog/` and `buildlog/`, so this `.md` at
> the content root is ignored by the build.

**Scope.** These rules cover everything I publish here: standalone **blog posts**
(`blog/`) and **build-log updates** (`buildlog/`). They're the same voice, so most
notes apply to both. Where one is specific to build-log updates (threading to the
next update, the running-series recap), it says so; treat those as optional for a
one-off blog post.

## Related guides
Cover letters and job proposals have their own directive at
`docs/job_applications/cover-letter-style.md`. This guide is the source of the
rules that travel across everything I write — never fabricate, avoid the em-dash,
show-don't-announce, name the pattern, be precise with AI vocabulary — and the
cover-letter guide inherits them and layers on the proposal-specific parts (lead
with the single strongest real proof, keep the body plain-text for the Upwork
box, de-risk the close with a small sample before the full commit). Keep the
shared rules defined here; when one changes, it changes for both.

## Who's writing, for whom
- Voice: me, Vagner — a full-stack/AI engineer building in public. First person
  singular ("I") by default; use "we" only when a real collaborator was involved.
- Reader: a fellow developer — peers and technically-literate recruiters, an
  international audience. Gloss Brazil-specific context (e.g. what the Diário
  Oficial is) in a line, without condescending.
- Language: English. Conversational and concrete — like explaining my code to a
  sharp friend who doesn't know this domain.

## The rule that overrides everything: never fabricate
Every detail must be true and traceable to a real artifact — a real commit, a
real test count, an error that actually happened, a real screenshot.
- Do NOT invent struggles, bugs, metrics, timelines, or error messages to
  improve the story.
- If a fact (a number, a screenshot) isn't available, insert an explicit
  `[TODO: …]` placeholder for me to fill — never guess.
- "This part was genuinely smooth" beats a manufactured crisis.
- Never expose secrets, credentials, `.env` values, or NDA-covered material.
  Refer to prior confidential work only in general terms.
- No AI-slop: avoid "in today's world," "let's dive in," "unlock," "leverage,"
  "game-changer," "delve." Cut hype adjectives. Concrete > abstract. Vary
  sentence length. Show, don't announce.

## Tone
- Personal, direct, human — not a press release.
- Confident but honest: I know my craft and I'm open about the messy parts.
  Humility = showing the real process (the forum dead-ends, the prompt tweaks),
  not self-deprecation. Avoid both arrogance and false modesty.
- Technical yet instructive: use standard terms (refactor, deploy, stack, MVP,
  TDD, idempotency) naturally; gloss the non-obvious ones in a few words.

## Narrative — tell a story, but don't force one shape
Frame the work as a journey when it's true: what I set out to do → what actually
happened (incl. the friction) → the turn → where it landed. Vary the shape so the
series doesn't feel formulaic:
- struggle → breakthrough (a real roadblock)
- discovery (something the docs got wrong; a surprising finding)
- decision (a fork in the road and why I chose)
- the honest grind (unglamorous but necessary work)
The roadblocks and what they taught are the heart — but only the real ones.

## Structure (flexible default, not a cage)
1. Title — concrete and specific; a struggle or real goal. Specificity is the
   hook; no clickbait or manufactured drama.
2. Hook — 2–4 honest sentences: the goal + a true teaser of how it went.
3. The story — grounded in real artifacts: link the commit, show a small real
   code snippet or real terminal output, name the actual tools.
4. What I learned — a takeaway the reader can use.
5. What's next (build-log updates) — one line threading to the next update, so the
   series reads as a *log*. Optional for a standalone blog post.
6. CTA — a genuine one: a real question I want input on, or "follow the repo /
   the series." Vary it; never bolt on a generic "what do you think?".

## Length & format
~600–1,200 words. Scannable: short paragraphs, descriptive subheads, real code
blocks where they earn their place. One clear idea per post. Lead with substance.

## Voice notes — observed from the published posts
These are habits the early posts already show; lean into them, don't sand them off.
- **Subheads can have personality.** The body stays concrete and technical, but a
  subhead is allowed to be playful — e.g. update #2 runs a light Lord of the Rings
  motif ("One function to rule them all", "Testing became legend, legend became
  design"). The head entertains; the paragraph under it does the real work. Use a
  running motif at most once per post, and never let the joke obscure the point.
- **Cross-link my own writing generously.** Thread the series together: link back
  to the previous build-log update, and link out to a relevant blog deep-dive when
  one exists (e.g. #2 points to *Scraping a fragile legacy site* when it raises
  scraper resilience). Use real, existing URLs only — `/building/<project>/<slug>/`
  for updates, `/blog/<slug>/` for posts.
- **The honesty beat is a feature.** When I deferred something on purpose
  (resilience, a hardening pass), name it plainly and say why I judged it safe to
  defer. That candor is what makes the log credible — don't bury it.
- **Clean-room framing when it applies.** Reference techniques/tools as references
  only; never imply reuse of confidential or prior proprietary code.
- **Avoid the em-dash.** An editing pass on the fingerprinting post stripped nearly
  every `—`. Replace it with the punctuation that *names* the relationship: a colon
  when it introduces (`patch the executable: find the byte sequences`), a comma or
  paired commas for an aside (`and, crucially, cookies`), parentheses for a true
  aside, or a full stop that starts a new sentence (`…the remote driver doesn't. So
  if you run a grid…`). Em-dash pile-ups read as generated prose; splitting the
  sentence usually reads better than spanning it with dashes.
- **Don't announce honesty — show it.** The same pass cut self-conscious
  throat-clearing: `Honest answer: …` became the claim itself, `One honest caveat
  about dates:` became `A caveat:`, and `measured it instead of hand-waving` became
  `measured it`. The candor belongs in the facts, not in adverbs about them. (A
  corollary of "Show, don't announce" above.)
- **Ground a cold reader before the recap.** Open by defining the domain and the
  product in their own short, standalone sentences (what the *Diário Oficial* is,
  what RegWatch does) *before* any "in #2 I…". A recap that buries the definition
  inside a subordinate clause loses everyone who arrives cold, exactly the peers
  and recruiters the log is for. Definitions first, then the story. (Observed: an
  edit pass on #3 split the flowing hook into atomic "X is Y" sentences and led
  with them.)
- **A direct question can open a post.** Aiming an honest question straight at the
  reader ("Are you one of those who sends every document to an AI?") or dropping a
  quick "right?" into a setup ("Not practical at all, right?") pulls a peer in
  faster than a flat declarative lede, and it suits the "explaining to a sharp
  friend" voice. Keep it a real question they might actually answer, not
  manufactured engagement bait, and keep it tight: don't pad it with throat-clearing
  ("I think you'd agree that…"), which is the same self-conscious hedge the "show,
  don't announce" note warns against. One or two per post at most; the paragraphs
  under it still carry the substance. (Observed: an edit pass on the
  document-extraction post opened with the reader, then landed the concrete "a
  résumé is a database row wearing a costume.")
- **Name the principle plainly, then cash it out. Don't mythologize the process.**
  An early draft of update #3 opened a section with "I write these features from a
  machine-readable plan, test-first, one task at a time." It named no recognized
  principle and paid nothing off: an oblique, almost mystical line dropped into the
  middle of the post, a riddle with no reason to be there. The fix names the actual
  principle in plain words (test-driven development, the thing I build everything
  on) and immediately shows what it bought *this time*: a routing bug that left no
  mark on the page but went red the instant a test hit it. If you invoke how you
  work, say the recognized name for it and tie it straight to the concrete thing it
  did in this update, or cut the sentence. Process description that pays off nothing
  reads as filler. (Corollary of "Name the pattern" and "Show, don't announce.")
- **Land the takeaway as a two-part contrast.** The lines that stick in update #1 are
  antitheses: a claim and its turn set side by side, so the point arrives in two beats
  the reader can hold. `A [TODO] in the code is a smell. A tracked gate with a reason
  is a decision.` `Fail-closed everywhere is a slogan; the login path is where it meets
  reality.` `A green isolation test under a superuser proves nothing. It's a smoke
  detector wired to a light switch.` The shape is: the thing that looks fine, then the
  thing that makes it not fine (or the reverse). Where you can, make the second half a
  concrete image (the smoke detector, the light switch) rather than another abstraction,
  which is "show, don't announce" doing the landing. Use it to close a section or a
  lesson, not every paragraph, or the rhythm becomes a tic.
- **Name the pattern.** When an established pattern or principle is carrying the
  work, name it: Ports and Adapters / Hexagonal Architecture, Dependency Inversion,
  idempotency, test doubles. The recognized term is a keyword that signals
  competence and lets a reader map the idea onto something they already know. Gloss
  it in the same breath, but say the name.
- **Lists for sequences, prose for arguments.** A pipeline or any ordered process
  reads better as a numbered list than as a comma-spliced sentence. Reserve flowing
  prose for the reasoning; break the steps out.
- **Anchor with a plain analogy before the code.** "Think of it as an AI summarizer
  that emails you" lands before any snippet does. Lead with the everyday framing,
  then earn it with the technical detail underneath.
- **Be precise with AI vocabulary.** Don't inflate a single model call into an
  "agent" or call a fixed pipeline "autonomous." Use the honest word (an LLM call, a
  model, "AI" as the umbrella term). Overclaiming reads as hype to the exact
  technical readers you most want to convince, and it collides with the
  never-fabricate rule.
- **Titles: wordplay plus famous keywords, still specific.** A little play in the
  title is welcome (e.g. #3's "From mocking to knocking" rhyme, where "mocking" is
  also the literal testing term for the fakes being replaced), but pair it with
  recognizable, searchable terms (AI, LLM, Django, production, the pattern name) and
  let the colon-subtitle carry the concrete specifics. The play is the hook; the
  subtitle is the substance. Titles don't drive the URL (the slug comes from the
  `NN-slug` filename), so retitling a draft is free.

## Publishing mechanics (so a post doesn't go live early)
`pubDate` is enforced in production: a post whose `pubDate` is in the future is
filtered out of the prod build until that moment arrives (see `isUpdateVisible` /
`isVisible`). So it's safe to merge and push a finished post ahead of time — set
`pubDate` to the intended go-live (a full ISO timestamp like
`2026-06-28T08:00:00-03:00` pins the hour in BRT; a bare date coerces to UTC
midnight). `draft: true` hides it unconditionally. In `astro dev` everything is
visible regardless, for previewing.

## Inputs for each post
The real source material: commits/diffs, the spec/plan/findings docs, my rough
notes, the session transcript. Build the post from those. When unsure of a fact,
ask or leave a `[TODO]` — don't fill the gap with invention.
