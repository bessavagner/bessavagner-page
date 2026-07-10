// web/src/lib/clock.ts
// One instant per build. Visibility is a pure function of (commit, PUBLISH_AT).
//
// This is not cosmetic: Dockerfile runs `pnpm build`, and the deploy workflow's
// check job runs `pnpm build` too. Two builds, two wall clocks. Pinning the
// instant is what makes them agree.
export function resolvePublishAt(env: { PUBLISH_AT?: string }, fallback: number): number {
  const raw = env.PUBLISH_AT?.trim();
  if (!raw) return fallback;
  const parsed = Date.parse(raw);
  if (Number.isNaN(parsed)) {
    throw new Error(`PUBLISH_AT is set but unparsable: ${JSON.stringify(raw)}`);
  }
  return parsed;
}
