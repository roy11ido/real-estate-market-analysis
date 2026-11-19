"use client";

import { addDays, hebrewDate, shortDate } from "@/lib/dates";
import { DONE, type Status, type Task } from "@/lib/types";
import { TaskList, TaskRow } from "./TaskRow";

type Handlers = { onStatus: (t: Task, s: Status) => void; onOpen: (t: Task) => void };

export function sortTasks(a: Task, b: Task): number {
  const doneA = a.status === DONE ? 1 : 0;
  const doneB = b.status === DONE ? 1 : 0;
  if (doneA !== doneB) return doneA - doneB;
  const hiA = a.priority === "גבוהה" ? 0 : 1;
  const hiB = b.priority === "גבוהה" ? 0 : 1;
  if (hiA !== hiB) return hiA - hiB;
  return (a.due ?? "9999").localeCompare(b.due ?? "9999");
}

const openCount = (list: Task[]) => list.filter((t) => t.status !== DONE).length;

function Group({ title, extra, tone, count, children }: { title: string; extra?: string; tone?: "danger"; count: number; children: React.ReactNode }) {
  return (
    <section className="group">
      <h2 className={tone === "danger" ? "danger" : ""}>
        {title}
        {extra && <span className="muted"> · {extra}</span>}
        <span className="count">{count}</span>
      </h2>
      {children}
    </section>
  );
}

export function TodayView({ tasks, today, ...h }: { tasks: Task[]; today: string } & Handlers) {
  const tomorrow = addDays(today, 1);
  const overdue = tasks.filter((t) => t.due && t.due < today && t.status !== DONE).sort(sortTasks);
  const todayList = tasks.filter((t) => t.due === today).sort(sortTasks);
  const tomorrowList = tasks.filter((t) => t.due === tomorrow).sort(sortTasks);
  return (
    <>
      {overdue.length > 0 && (
        <Group title="באיחור" tone="danger" count={overdue.length}>
          <TaskList tasks={overdue} showDate dateDanger {...h} />
        </Group>
      )}
      <Group title="היום" count={openCount(todayList)}>
        <TaskList tasks={todayList} {...h} />
      </Group>
      <Group title="מחר" extra={shortDate(tomorrow)} count={openCount(tomorrowList)}>
        <TaskList tasks={tomorrowList} {...h} />
      </Group>
    </>
  );
}

export function WeekView({ tasks, today, ...h }: { tasks: Task[]; today: string } & Handlers) {
  const days = Array.from({ length: 7 }, (_, i) => addDays(today, i));
  return (
    <>
      {days.map((d, i) => {
        const list = tasks.filter((t) => t.due === d).sort(sortTasks);
        const name = i === 0 ? "היום" : i === 1 ? "מחר" : hebrewDate(d).split(",")[0];
        return (
          <Group key={d} title={name} extra={shortDate(d)} count={openCount(list)}>
            <TaskList tasks={list} {...h} />
          </Group>
        );
      })}
    </>
  );
}

export function CourseView({ tasks, today, ...h }: { tasks: Task[]; today: string } & Handlers) {
  const open = tasks.filter((t) => t.status !== DONE);
  const groups = new Map<string, Task[]>();
  for (const t of open) {
    const keys = t.courses.length ? t.courses : ["ללא קורס"];
    for (const k of keys) groups.set(k, [...(groups.get(k) ?? []), t]);
  }
  const names = [...groups.keys()].sort((a, b) =>
    a === "ללא קורס" ? 1 : b === "ללא קורס" ? -1 : a.localeCompare(b, "he"),
  );
  if (!names.length) return <p className="empty muted top-gap">אין משימות פתוחות</p>;
  return (
    <>
      {names.map((n) => {
        const list = groups.get(n)!.sort((a, b) => (a.due ?? "9999").localeCompare(b.due ?? "9999"));
        return (
          <Group key={n} title={n} count={list.length}>
            <ul className="list">
              {list.map((t) => (
                <TaskListItem key={t.id} task={t} today={today} {...h} />
              ))}
            </ul>
          </Group>
        );
      })}
    </>
  );
}

function TaskListItem({ task, today, ...h }: { task: Task; today: string } & Handlers) {
  return <TaskRow task={task} showCourse={false} showDate dateDanger={!!task.due && task.due < today} {...h} />;
}
