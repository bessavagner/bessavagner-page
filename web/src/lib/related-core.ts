// web/src/lib/related-core.ts
// Pure, framework-free tag-overlap relatedness. No `astro:content` / `import.meta`
// here, so it runs under `node --test`. Used for BOTH blog posts and buildlog
// updates — both carry { id, data: { tags, pubDate } }.

/** Minimal shape needed to rank relatedness. */
export interface RelatableLike {
  id: string;
  data: { tags: string[]; pubDate: Date };
}

/** Number of tags shared between two tag lists. */
function sharedTagCount(a: string[], b: string[]): number {
  const set = new Set(a);
  let n = 0;
  for (const t of b) if (set.has(t)) n += 1;
  return n;
}

/** The best `n` items related to `target`, self-excluded. Ranked by shared-tag
 *  count (desc), then `pubDate` (desc). When overlap is empty (untagged target
 *  or no shared tags) the date tiebreak degrades it to a recent-in-collection
 *  fallback, so every post still gets `n` onward links. */
export function relatedPosts<T extends RelatableLike>(target: T, all: T[], n: number): T[] {
  if (n <= 0) return [];
  return all
    .filter((p) => p.id !== target.id)
    .map((p) => ({ p, score: sharedTagCount(target.data.tags, p.data.tags) }))
    .sort((a, b) => b.score - a.score || b.p.data.pubDate.getTime() - a.p.data.pubDate.getTime())
    .slice(0, n)
    .map((x) => x.p);
}
