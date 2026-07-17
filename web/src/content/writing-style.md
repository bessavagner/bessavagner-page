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
**1,500–2,500 words for a standard post.** (Measured 2026-07-14: the 17
published posts run 1,545 to 2,850, median 1,900. The old ~600–1,200 range was
aspirational and every post broke it, so it was not governing anything.) A
**pillar** — a page that a cluster of spokes hangs off, and that has to answer
the whole intent rather than one slice of it — runs longer, and that is expected;
it earns the length by covering the cluster, not by padding. Below ~1,200 words,
ask whether it is a post at all or a section of an existing one (see *What earns
a new post* above).

Scannable: short paragraphs, descriptive subheads, real code blocks where they
earn their place. One clear idea per post. Lead with substance.

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
- **Cut a trailing "X, not Y" clause once the positive statement already lands.**
  A recurring habit: state a claim, then append a contrastive clause spelling out
  the negative case the claim already implies, `cost is visible per tenant, not
  just as one aggregate bill at the end of the month`; `gets onto a laptop, not a
  copy-paste from a teammate`; `gets rotated the moment there's any doubt it
  stayed contained, not just when a scanner flags it`. The positive half almost
  always carries the point on its own; the "not Y" half restates it rather than
  adding anything. Cut it before it ships. (Observed across four separate answers
  in one editing pass, 2026-07-16; distinct from "don't announce honesty" above,
  this is redundant negation, not self-conscious framing.) The same instinct
  applies front-loaded: `isn't A, it's B` or `doesn't do X, it does Y` gets cut
  to just `B` / `Y` once the positive statement can carry the sentence alone,
  e.g. `The dangerous gap isn't the one on a list with an owner and a deadline.
  It's the one nobody thought to check` became `The dangerous gap is the one
  nobody thought to check`; `The matcher code doesn't check first and insert
  second, it calls a single get-or-create operation` became `The matcher calls
  a single get-or-create operation`. Negation-first framing reads as
  throat-clearing the same way a trailing "not Y" does, whichever end of the
  sentence it sits on. (Three separate instances, 2026-07-16.)
- **Cut the closing "here's the takeaway" recap once parallel examples already show it.** When an answer builds two or more structurally parallel examples on purpose (a uniqueness constraint here, a `sent`-flag check there), a final paragraph spelling out the shared logic afterward restates rather than adds: `That contrast is the actual lesson: a unique constraint or an idempotent upsert make a duplicate structurally impossible, while a check-then-write pattern only makes it unlikely` got cut entirely once the two examples above it already made the point. Same family as "show, don't announce," at the paragraph/structural level instead of the sentence level. Watch for this whenever a draft ends with an explicit "the pattern here is..." / "what ties these together is..." line after 2+ parallel illustrations, and cut it before it ships. (Observed across two separate answers in a questionnaire pass, 2026-07-16.)
- **Don't narrate the Q&A format itself, answer as if there is no format.** Cut
  any line that comments on the question being asked or the document's own
  structure instead of just answering it: `so I'll walk through both` (announcing
  the answer's own organization), `that's exactly the gap the next question is
  about` (referencing a different question), `so I'd say that plainly in an
  interview` (narrating the act of answering), `the core problem with that
  question is baked into its own premise` (commentary about the question rather
  than the answer). Skip straight to the content the meta-line was about to
  introduce. (Observed across three separate answers in a questionnaire pass,
  2026-07-16; a corollary of "don't announce what you're about to do," extended
  from whole-document framing to individual Q&A pairs.)
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
- **Don't pre-empt confusion the reader doesn't have.** A term can be technically
  overloaded (e.g. "framework" meaning something different at build time than at
  runtime) without needing a defensive clarification. The reader is the fellow
  developer defined above; explaining a distinction they already know reads as
  talking down. Add a clarifying beat only when there's a real, specific signal of
  confusion in the material itself, not just because a term is overloaded in
  general. (Observed on a questionnaire draft: an "Astro isn't a JS framework"
  aside got written to head off a contradiction I imagined, then cut once it was
  clear the actual reader wouldn't have raised it.)
- **Titles: wordplay plus famous keywords, still specific.** A little play in the
  title is welcome (e.g. #3's "From mocking to knocking" rhyme, where "mocking" is
  also the literal testing term for the fakes being replaced), but pair it with
  recognizable, searchable terms (AI, LLM, Django, production, the pattern name) and
  let the colon-subtitle carry the concrete specifics. The play is the hook; the
  subtitle is the substance. Titles don't drive the URL (the slug comes from the
  `NN-slug` filename), so retitling a draft is free.
- **Write as the builder, not a columnist narrating to a stranger.** The failure
  mode isn't formality, it's *distance*: prose that reads like an outside observer
  explaining my codebase back to me, rather than me at the terminal having just run
  the thing. Stay in first-person *doing* ("I bumped the trials to ten and drew the
  spread"), not first-person *narrating* ("A new pure history layer walks every
  committed snapshot"). Report what I looked at, what surprised me, what I chose and
  the tradeoff. The reader is a stranger to the project (so still define terms), but
  the *voice* is the person who did the work, not a documentarian of it.
- **Don't mythologize the work with mic-drop aphorisms.** The two-part contrast
  landing (above) is a real tool, but it turns into a tell the moment *every* section
  ends on a quotable image. Lines like "a confidence interval you haven't earned is a
  smoke detector you painted onto the ceiling" read as generated blog polish, not as
  me talking. Use at most one such landing in a post, prefer the plain sentence, and
  never let the flourish stand in for the concrete point it's decorating. Same family
  as "show, don't announce": a tidy aphorism is often announcing insight instead of
  showing the work that earned it.
- **Show the plot.** A build-log update about a metric, a chart, or any visual output
  needs the actual figure embedded, not just a table describing it. Import it with
  Astro's `<Image>` (see `blog/beating-browser-fingerprinting.mdx`; assets live under
  `src/assets/<collection>/<slug>/`), and make the figure earn its place: it should
  *show* the post's thesis, not merely decorate it. A post arguing "the spread
  matters" whose only picture has no error bars is hollow, so fix the picture.
- **Cut trivial code dumps.** A three-line helper that a sentence can describe
  ("min/max/mean and population stdev") does not earn a fenced code block. Reserve
  snippets for genuinely load-bearing code (a non-obvious mechanism, an interface, the
  one line that carries the decision) and describe the rest in prose. Pasting simple
  functions is filler that makes a post read as padded.
- **Lead with the finding, not the plumbing.** Open on the interesting thing (what the
  data said, the surprise, the decision), and demote the supporting machinery (schema
  versioning, formatting helpers, config wiring) to a compressed section later or a
  single sentence. If the genuinely interesting content is buried under setup, the post
  reads as a chore log instead of a discovery.
- **Audit each update against the last for repeated shape.** Reinforces "vary the
  shape" above, but specifically across *consecutive* updates: before publishing, check
  the new post isn't the same arc as the previous one. Two updates in a row that both
  land on "my design/discipline held up" makes the series feel formulaic even when each
  is individually fine. Rotate the frame (discovery, decision, honest grind,
  struggle→breakthrough) deliberately.

## What earns a new post, and what deepens an existing one

A query with real, measured demand and a distinct intent earns its own post. A
query with a handful of impressions is noise, and writing a post for it splits
the authority of a page that is already ranking. The test, in order:

1. **Is there measured demand?** Look it up in Search Console (the pinned-page
   and top-query tables in the monthly report, `docs/.ai/reports/analytics/`).
   Fewer than ~5 impressions in a month is noise at this site's volume: it does
   not earn anything, and it does not deserve a section either.
2. **Is the intent distinct from an existing page's?** If a reader searching it
   would be satisfied by a section inside an existing post, it is a **section**.
   If they would bounce off that post because it answers a different question,
   it is a **spoke**.
3. **Is there a hub for it to hang off?** A spoke that links to no pillar, and
   that no pillar links back to, is an orphan. Write the pillar first.

Worked examples, from a Search Console pull over 2026-06-22 → 2026-07-12 (21
days, the window GSC had processed at the time — a live pull, not the monthly
report, which covers a different, shorter window):

- **`unstructured document parsing`** — 4 impressions, average position 30.5,
  inside the 151-impression demand around
  [pulling structured data out of unstructured documents](/blog/pulling-structured-data-from-unstructured-documents/).
  Low volume, but the intent is genuinely distinct: parsing the *document*
  (layout, geometry, tables) is a different question from extracting the
  *fields*, and it already ranks better than the pillar's own average. **It
  earns a spoke**, hung off the pillar.
- **`fingerprint browser selenium`** — position 17.2 against
  [beating browser fingerprinting](/blog/beating-browser-fingerprinting/)'s own
  average of 18.0. The page is already the right answer and is already closer on
  this query than on its average. **It earns a section, not a post.** Writing a
  second page here would compete with the first.
- **A 2-impression one-off** earns nothing. Not a post, not a section, not a
  line. It is below the noise floor of a site with this much traffic, and
  treating it as a signal is how a content plan becomes busywork.

A pillar is deepened, never split. If a question belongs inside the pillar's
argument, it goes in the pillar.

## Internal linking (every post earns its place in the web)
Before publishing any post, run this checklist so the post is stitched into the
site, not a dead-end:
- **3–8 descriptive contextual in-body links per post.** Link where the sentence
  already refers to another thing I wrote or built, not as a footer dump. The
  related-posts module and series nav are separate; these are *in-prose* links.
- **Descriptive, varied anchor text.** The anchor names the destination
  ("how I gave the agent memory", "the RegWatch deploy"), never "click here",
  "this post", or a bare URL. Vary the wording across links.
- **Link real, existing URLs only** — `/blog/<slug>/` for posts,
  `/building/<project>/<slug>/` for updates. No links to unwritten posts.
- **Link the project or CV where it's natural** — when a post grew out of a build,
  point to the build hub; when it demonstrates the kind of work I do, the CV/contact.
- **Don't over-link.** One link per idea; the same destination once. If a
  paragraph has three links it probably has none worth keeping.

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
