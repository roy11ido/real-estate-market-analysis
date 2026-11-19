import { Client, isFullPage } from "@notionhq/client";
import type { PageObjectResponse } from "@notionhq/client";
import { addDays, israelToday } from "./dates";
import { DONE, STATUSES, type Status, type Task, type TodayPayload } from "./types";

// Exact property names in the Notion tasks database
const P = {
  title: "שם המשימה",
  type: "סוג",
  status: "סטטוס",
  priority: "עדיפות",
  due: "תאריך יעד",
  course: "קורס",
} as const;

const TASKS_TTL_MS = 30_000;
const COURSE_TTL_MS = 60 * 60_000;
const MIN_FORCED_REFRESH_MS = 5_000;

// Module-level state survives between requests on a warm serverless instance (best-effort cache).
const g = globalThis as unknown as {
  __notion?: Client;
  __dataSourceId?: string;
  __courseCache?: Map<string, { name: string; at: number }>;
  __todayCache?: { key: string; at: number; data: TodayPayload };
  __todayInflight?: Promise<TodayPayload>;
};

function notion(): Client {
  if (!g.__notion) {
    const auth = process.env.NOTION_TOKEN;
    if (!auth) throw new Error("NOTION_TOKEN missing");
    // Client retries 429/529 automatically, honoring Retry-After.
    g.__notion = new Client({ auth, retry: { maxRetries: 3 } });
  }
  return g.__notion;
}

async function dataSourceId(): Promise<string> {
  if (g.__dataSourceId) return g.__dataSourceId;
  const dbId = process.env.NOTION_TASKS_DB_ID || "acdf3733-b809-4725-9b02-9166af369c09";
  const db = await notion().databases.retrieve({ database_id: dbId });
  const ds = "data_sources" in db ? db.data_sources?.[0] : undefined;
  if (!ds) throw new Error("No data source found for tasks database");
  g.__dataSourceId = ds.id;
  return ds.id;
}

/** Run async jobs with limited concurrency (Notion allows ~3 req/s). */
async function mapLimit<T, R>(items: T[], limit: number, fn: (t: T) => Promise<R>): Promise<R[]> {
  const out: R[] = new Array(items.length);
  let i = 0;
  const workers = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (i < items.length) {
      const idx = i++;
      out[idx] = await fn(items[idx]);
    }
  });
  await Promise.all(workers);
  return out;
}

async function courseNames(ids: string[]): Promise<Map<string, string>> {
  const cache = (g.__courseCache ??= new Map());
  const now = Date.now();
  const missing = [...new Set(ids)].filter((id) => {
    const c = cache.get(id);
    return !c || now - c.at > COURSE_TTL_MS;
  });
  await mapLimit(missing, 3, async (id) => {
    try {
      const page = await notion().pages.retrieve({ page_id: id });
      let name = "";
      if (isFullPage(page)) {
        const titleProp = Object.values(page.properties).find((p) => p.type === "title");
        if (titleProp?.type === "title") name = titleProp.title.map((t) => t.plain_text).join("");
      }
      cache.set(id, { name: name || "ללא שם", at: now });
    } catch {
      // Course DB not shared with the integration, or page deleted. Keep stale value if we have one.
      if (!cache.has(id)) cache.set(id, { name: "", at: now });
    }
  });
  const result = new Map<string, string>();
  for (const id of ids) result.set(id, cache.get(id)?.name ?? "");
  return result;
}

function toTask(page: PageObjectResponse, courses: Map<string, string>): Task {
  const props = page.properties;
  const title = props[P.title];
  const type = props[P.type];
  const status = props[P.status];
  const priority = props[P.priority];
  const due = props[P.due];
  const course = props[P.course];
  const statusName = status?.type === "status" ? status.status?.name : undefined;
  return {
    id: page.id,
    title: title?.type === "title" ? title.title.map((t) => t.plain_text).join("") || "ללא שם" : "ללא שם",
    status: (STATUSES as readonly string[]).includes(statusName ?? "") ? (statusName as Status) : "לא התחלתי",
    type: type?.type === "select" ? (type.select?.name ?? null) : null,
    priority: priority?.type === "select" ? (priority.select?.name ?? null) : null,
    due: due?.type === "date" && due.date?.start ? due.date.start.slice(0, 10) : null,
    courses:
      course?.type === "relation"
        ? course.relation.map((r) => courses.get(r.id) ?? "").filter(Boolean)
        : [],
    url: page.url,
  };
}

function sortTasks(a: Task, b: Task): number {
  const doneA = a.status === DONE ? 1 : 0;
  const doneB = b.status === DONE ? 1 : 0;
  if (doneA !== doneB) return doneA - doneB;
  const hiA = a.priority === "גבוהה" ? 0 : 1;
  const hiB = b.priority === "גבוהה" ? 0 : 1;
  if (hiA !== hiB) return hiA - hiB;
  return (a.due ?? "").localeCompare(b.due ?? "");
}

async function fetchToday(today: string): Promise<TodayPayload> {
  const tomorrow = addDays(today, 1);
  const dsId = await dataSourceId();
  const pages: PageObjectResponse[] = [];
  let cursor: string | undefined;
  do {
    const res = await notion().dataSources.query({
      data_source_id: dsId,
      start_cursor: cursor,
      page_size: 100,
      filter: {
        and: [
          // +2 days buffer so date-times late tomorrow are never cut by timezone handling; trimmed below.
          { property: P.due, date: { on_or_before: addDays(today, 2) } },
          {
            or: [
              { property: P.status, status: { does_not_equal: DONE } },
              { property: P.due, date: { on_or_after: today } },
            ],
          },
        ],
      },
      sorts: [{ property: P.due, direction: "ascending" }],
    });
    for (const r of res.results) if (r.object === "page" && isFullPage(r)) pages.push(r);
    cursor = res.has_more ? (res.next_cursor ?? undefined) : undefined;
  } while (cursor);

  const relIds = pages.flatMap((p) => {
    const c = p.properties[P.course];
    return c?.type === "relation" ? c.relation.map((r) => r.id) : [];
  });
  const courses = await courseNames(relIds);
  const tasks = pages.map((p) => toTask(p, courses));

  return {
    today,
    tomorrow,
    overdue: tasks.filter((t) => t.due! < today && t.status !== DONE).sort(sortTasks),
    todayTasks: tasks.filter((t) => t.due === today).sort(sortTasks),
    tomorrowTasks: tasks.filter((t) => t.due === tomorrow).sort(sortTasks),
    fetchedAt: Date.now(),
  };
}

export async function getToday(force = false): Promise<TodayPayload> {
  const today = israelToday();
  const c = g.__todayCache;
  const age = c && c.key === today ? Date.now() - c.at : Infinity;
  // Forced refresh (pull-to-refresh) still respects a 5s floor to protect the rate limit.
  if (age < (force ? MIN_FORCED_REFRESH_MS : TASKS_TTL_MS)) return c!.data;
  if (g.__todayInflight) return g.__todayInflight;
  g.__todayInflight = fetchToday(today)
    .then((data) => {
      g.__todayCache = { key: today, at: Date.now(), data };
      return data;
    })
    .finally(() => {
      g.__todayInflight = undefined;
    });
  return g.__todayInflight;
}

export async function setStatus(pageId: string, status: Status): Promise<void> {
  await notion().pages.update({
    page_id: pageId,
    properties: { [P.status]: { status: { name: status } } },
  });
  // Patch the cached copy so the next read reflects the change without another Notion query.
  const c = g.__todayCache;
  if (c) {
    for (const list of [c.data.overdue, c.data.todayTasks, c.data.tomorrowTasks]) {
      const t = list.find((x) => x.id === pageId);
      if (t) t.status = status;
    }
  }
}
