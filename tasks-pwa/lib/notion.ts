import { Client, isFullPage } from "@notionhq/client";
import type { PageObjectResponse } from "@notionhq/client";
import { israelToday } from "./dates";
import { DONE, STATUSES, type Course, type Status, type Task, type TaskFile, type TasksPayload } from "./types";

// Exact property names in the Notion tasks database
const P = {
  title: "שם המשימה",
  type: "סוג",
  status: "סטטוס",
  priority: "עדיפות",
  due: "תאריך יעד",
  course: "קורס",
  files: "קבצים ומדיה",
} as const;

const TASKS_TTL_MS = 30_000;
const COURSES_TTL_MS = 10 * 60_000;
const MIN_FORCED_REFRESH_MS = 5_000;

// Module-level state survives between requests on a warm serverless instance (best-effort cache).
const g = globalThis as unknown as {
  __notion?: Client;
  __tasksDsId?: string;
  __coursesDsId?: string | null;
  __courses?: { at: number; list: Course[] };
  __courseNames?: Map<string, string>;
  __tasksCache?: { key: string; at: number; data: TasksPayload };
  __tasksInflight?: Promise<TasksPayload>;
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

const courseNameMap = () => (g.__courseNames ??= new Map());

async function tasksDataSourceId(): Promise<string> {
  if (g.__tasksDsId) return g.__tasksDsId;
  const dbId = process.env.NOTION_TASKS_DB_ID || "acdf3733-b809-4725-9b02-9166af369c09";
  const db = await notion().databases.retrieve({ database_id: dbId });
  const ds = "data_sources" in db ? db.data_sources?.[0] : undefined;
  if (!ds) throw new Error("No data source found for tasks database");
  g.__tasksDsId = ds.id;
  return ds.id;
}

async function coursesDataSourceId(): Promise<string | null> {
  if (g.__coursesDsId !== undefined) return g.__coursesDsId;
  const ds = await notion().dataSources.retrieve({ data_source_id: await tasksDataSourceId() });
  const prop = "properties" in ds ? ds.properties[P.course] : undefined;
  g.__coursesDsId = prop?.type === "relation" ? prop.relation.data_source_id : null;
  return g.__coursesDsId;
}

function pageTitle(page: PageObjectResponse): string {
  const t = Object.values(page.properties).find((p) => p.type === "title");
  return t?.type === "title" ? t.title.map((x) => x.plain_text).join("") : "";
}

/** All courses (one paginated query, cached 10 min). Also feeds the id→name map. */
export async function getCourses(): Promise<Course[]> {
  if (g.__courses && Date.now() - g.__courses.at < COURSES_TTL_MS) return g.__courses.list;
  const dsId = await coursesDataSourceId();
  const list: Course[] = [];
  if (dsId) {
    let cursor: string | undefined;
    do {
      const res = await notion().dataSources.query({ data_source_id: dsId, start_cursor: cursor, page_size: 100 });
      for (const r of res.results) {
        if (r.object === "page" && isFullPage(r)) list.push({ id: r.id, name: pageTitle(r) || "ללא שם" });
      }
      cursor = res.has_more ? (res.next_cursor ?? undefined) : undefined;
    } while (cursor);
  }
  list.sort((a, b) => a.name.localeCompare(b.name, "he"));
  const names = courseNameMap();
  for (const c of list) names.set(c.id, c.name);
  g.__courses = { at: Date.now(), list };
  return list;
}

/** Resolve course names; falls back to single page lookups for ids missing from the list. */
async function resolveCourseNames(ids: string[]): Promise<void> {
  const names = courseNameMap();
  if ([...new Set(ids)].some((id) => !names.has(id))) {
    await getCourses().catch(() => undefined);
  }
  const missing = [...new Set(ids)].filter((id) => !names.has(id)).slice(0, 10);
  for (const id of missing) {
    try {
      const page = await notion().pages.retrieve({ page_id: id });
      names.set(id, isFullPage(page) ? pageTitle(page) || "ללא שם" : "");
    } catch {
      names.set(id, ""); // not shared with integration / deleted
    }
  }
}

const IMG_RE = /\.(png|jpe?g|gif|webp|heic|heif|avif|bmp|svg)$/i;

function toTask(page: PageObjectResponse): Task {
  const props = page.properties;
  const title = props[P.title];
  const type = props[P.type];
  const status = props[P.status];
  const priority = props[P.priority];
  const due = props[P.due];
  const course = props[P.course];
  const files = props[P.files];
  const statusName = status?.type === "status" ? status.status?.name : undefined;
  const courseIds = course?.type === "relation" ? course.relation.map((r) => r.id) : [];
  const names = courseNameMap();
  return {
    id: page.id,
    title: title?.type === "title" ? title.title.map((t) => t.plain_text).join("") || "ללא שם" : "ללא שם",
    status: (STATUSES as readonly string[]).includes(statusName ?? "") ? (statusName as Status) : "לא התחלתי",
    type: type?.type === "select" ? (type.select?.name ?? null) : null,
    priority: priority?.type === "select" ? (priority.select?.name ?? null) : null,
    due: due?.type === "date" && due.date?.start ? due.date.start.slice(0, 10) : null,
    courseIds,
    courses: courseIds.map((id) => names.get(id) ?? "").filter(Boolean),
    files:
      files?.type === "files"
        ? files.files.map((f): TaskFile => {
            const url = f.type === "file" ? f.file.url : f.external.url;
            const path = (() => {
              try {
                return new URL(url).pathname;
              } catch {
                return "";
              }
            })();
            return { name: f.name, url, image: IMG_RE.test(f.name) || IMG_RE.test(path) };
          })
        : [],
    url: page.url,
  };
}

/**
 * One query serves every screen: all open tasks + everything dated today or later.
 * (Today = overdue/today/tomorrow, Week = next 7 days, Courses = open tasks.)
 */
async function fetchTasks(today: string): Promise<TasksPayload> {
  const dsId = await tasksDataSourceId();
  const pages: PageObjectResponse[] = [];
  let cursor: string | undefined;
  do {
    const res = await notion().dataSources.query({
      data_source_id: dsId,
      start_cursor: cursor,
      page_size: 100,
      filter: {
        or: [
          { property: P.status, status: { does_not_equal: DONE } },
          { property: P.due, date: { on_or_after: today } },
        ],
      },
      sorts: [{ property: P.due, direction: "ascending" }],
    });
    for (const r of res.results) if (r.object === "page" && isFullPage(r)) pages.push(r);
    cursor = res.has_more ? (res.next_cursor ?? undefined) : undefined;
  } while (cursor);

  await resolveCourseNames(
    pages.flatMap((p) => {
      const c = p.properties[P.course];
      return c?.type === "relation" ? c.relation.map((r) => r.id) : [];
    }),
  );
  return { today, tasks: pages.map(toTask), fetchedAt: Date.now() };
}

export async function getTasks(force = false): Promise<TasksPayload> {
  const today = israelToday();
  const c = g.__tasksCache;
  const age = c && c.key === today ? Date.now() - c.at : Infinity;
  // Forced refresh (pull-to-refresh) still respects a 5s floor to protect the rate limit.
  if (age < (force ? MIN_FORCED_REFRESH_MS : TASKS_TTL_MS)) return c!.data;
  if (g.__tasksInflight) return g.__tasksInflight;
  g.__tasksInflight = fetchTasks(today)
    .then((data) => {
      g.__tasksCache = { key: today, at: Date.now(), data };
      return data;
    })
    .finally(() => {
      g.__tasksInflight = undefined;
    });
  return g.__tasksInflight;
}

/** Replace a task in the server cache so the next read reflects a write without another query. */
function putInCache(task: Task) {
  const c = g.__tasksCache;
  if (!c) return;
  const i = c.data.tasks.findIndex((t) => t.id === task.id);
  if (i >= 0) c.data.tasks[i] = task;
  else c.data.tasks.push(task);
}

export async function updateTask(pageId: string, patch: { status?: Status; due?: string | null }): Promise<Task> {
  const properties: Parameters<Client["pages"]["update"]>[0]["properties"] = {};
  if (patch.status) properties[P.status] = { status: { name: patch.status } };
  if (patch.due !== undefined) properties[P.due] = { date: patch.due ? { start: patch.due } : null };
  const page = await notion().pages.update({ page_id: pageId, properties });
  if (!isFullPage(page)) throw new Error("partial page");
  const task = toTask(page);
  putInCache(task);
  return task;
}

export async function createTask(input: {
  title: string;
  courseId: string | null;
  type: string | null;
  due: string | null;
  priority: string | null;
}): Promise<Task> {
  const properties: Parameters<Client["pages"]["create"]>[0]["properties"] = {
    [P.title]: { title: [{ text: { content: input.title } }] },
    [P.status]: { status: { name: "לא התחלתי" } },
  };
  if (input.type) properties[P.type] = { select: { name: input.type } };
  if (input.priority) properties[P.priority] = { select: { name: input.priority } };
  if (input.due) properties[P.due] = { date: { start: input.due } };
  if (input.courseId) properties[P.course] = { relation: [{ id: input.courseId }] };
  const page = await notion().pages.create({
    parent: { type: "data_source_id", data_source_id: await tasksDataSourceId() },
    properties,
  });
  if (!isFullPage(page)) throw new Error("partial page");
  await resolveCourseNames(input.courseId ? [input.courseId] : []);
  const task = toTask(page);
  putInCache(task);
  return task;
}

/** Upload a file to Notion and append it to the task's "קבצים ומדיה" property. */
export async function addFile(pageId: string, file: File): Promise<Task> {
  const client = notion();
  const upload = await client.fileUploads.create({
    mode: "single_part",
    filename: file.name,
    content_type: file.type || undefined,
  });
  await client.fileUploads.send({ file_upload_id: upload.id, file: { filename: file.name, data: file } });

  // The files property is replaced on update, so re-send the existing files (fresh URLs from a fresh read).
  const page = await client.pages.retrieve({ page_id: pageId });
  if (!isFullPage(page)) throw new Error("partial page");
  const prop = page.properties[P.files];
  const existing =
    prop?.type === "files"
      ? prop.files.map((f) =>
          f.type === "file"
            ? { type: "file" as const, name: f.name, file: { url: f.file.url } }
            : { type: "external" as const, name: f.name, external: { url: f.external.url } },
        )
      : [];
  const updated = await client.pages.update({
    page_id: pageId,
    properties: {
      [P.files]: {
        files: [...existing, { type: "file_upload", file_upload: { id: upload.id }, name: file.name }],
      },
    },
  });
  if (!isFullPage(updated)) throw new Error("partial page");
  const task = toTask(updated);
  putInCache(task);
  return task;
}
