// web/src/lib/search-core.ts
// Framework-free helpers for the search UI. No DOM, no Pagefind import here —
// this is the pure, node:test-covered core (mirrors the *-core.ts convention).

export type PagefindResultData = {
  url: string;
  meta: Record<string, string | undefined>;
  excerpt: string;
};

export type SearchRowType = 'blog' | 'buildlog' | 'other';

export type SearchRow = {
  url: string;
  title: string;
  type: SearchRowType;
  typeLabel: string;
  date: string;
  dateLabel: string;
  excerptHtml: string;
};

const TYPE_LABEL: Record<SearchRowType, string> = {
  blog: 'Blog',
  buildlog: 'Build log',
  other: 'Page',
};

function normalizeType(raw: string | undefined): SearchRowType {
  return raw === 'blog' || raw === 'buildlog' ? raw : 'other';
}

/** ISO date string → "Jan 2, 2026". Empty/invalid input → "". Formats in UTC
 *  so the label matches the frontmatter date regardless of the viewer's zone. */
export function formatDate(iso: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  });
}

/** Map a Pagefind result-data object to a view-model row. */
export function toRow(data: PagefindResultData): SearchRow {
  const type = normalizeType(data.meta.type);
  const date = data.meta.date ?? '';
  return {
    url: data.url,
    title: data.meta.title ?? 'Untitled',
    type,
    typeLabel: TYPE_LABEL[type],
    date,
    dateLabel: formatDate(date),
    excerptHtml: data.excerpt ?? '',
  };
}

/** Trailing debounce: fire once, `ms` after the last call, with the last args. */
export function debounce<T extends (...args: any[]) => void>(
  fn: T,
  ms: number,
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout> | undefined;
  return (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}
