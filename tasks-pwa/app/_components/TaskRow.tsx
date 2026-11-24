"use client";

import { useRef, useState } from "react";
import { shortDate } from "@/lib/dates";
import { DONE, nextStatus, type Status, type Task } from "@/lib/types";

const SWIPE = 80;

export function TaskRow({
  task,
  onStatus,
  onOpen,
  showCourse = true,
  showDate = false,
  dateDanger = false,
}: {
  task: Task;
  onStatus: (t: Task, s: Status) => void;
  onOpen: (t: Task) => void;
  showCourse?: boolean;
  showDate?: boolean;
  dateDanger?: boolean;
}) {
  const [dx, setDx] = useState(0);
  const start = useRef<{ x: number; y: number; lock: "h" | "v" | null } | null>(null);
  const done = task.status === DONE;

  const onTouchStart = (e: React.TouchEvent) => {
    start.current = { x: e.touches[0].clientX, y: e.touches[0].clientY, lock: null };
  };
  const onTouchMove = (e: React.TouchEvent) => {
    const s = start.current;
    if (!s) return;
    const mx = e.touches[0].clientX - s.x;
    const my = e.touches[0].clientY - s.y;
    if (!s.lock && (Math.abs(mx) > 8 || Math.abs(my) > 8)) s.lock = Math.abs(mx) > Math.abs(my) ? "h" : "v";
    if (s.lock === "h") {
      e.stopPropagation(); // don't trigger pull-to-refresh
      setDx(Math.max(Math.min(mx, 0), -140)); // swipe left only
    }
  };
  const onTouchEnd = (e: React.TouchEvent) => {
    if (start.current?.lock === "h") e.stopPropagation();
    if (dx <= -SWIPE) onStatus(task, done ? "לא התחלתי" : DONE);
    start.current = null;
    setDx(0);
  };

  const statusClass = done ? "s-done" : task.status === "בתהליך" ? "s-progress" : "s-todo";

  return (
    <li className="row-wrap">
      <div className={`swipe-bg ${done ? "undo" : ""} ${dx <= -SWIPE ? "armed" : ""}`}>
        <span>{done ? "בטל השלמה" : "הושלם ✓"}</span>
      </div>
      <div
        className={`row ${done ? "is-done" : ""}`}
        style={{ transform: `translateX(${dx}px)`, transition: dx === 0 ? "transform .2s ease" : "none" }}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
      >
        <button
          className={`status ${statusClass}`}
          onClick={() => onStatus(task, nextStatus(task.status))}
          aria-label={`סטטוס: ${task.status}. לחץ לשינוי`}
        >
          {done ? "✓" : ""}
        </button>
        <button className="row-body" onClick={() => onOpen(task)}>
          <div className="row-title">
            {task.priority === "גבוהה" && <span className="prio">!</span>}
            {task.title}
          </div>
          <div className="row-meta">
            {showCourse && task.courses.length > 0 && <span>{task.courses.join(", ")}</span>}
            {task.type && <span className="chip">{task.type}</span>}
            {task.status === "בתהליך" && <span className="chip chip-blue">בתהליך</span>}
            {task.files.length > 0 && <span>📎 {task.files.length}</span>}
            {showDate && task.due && <span className={dateDanger ? "danger" : ""}>{shortDate(task.due)}</span>}
          </div>
        </button>
      </div>
    </li>
  );
}

export function TaskList(props: {
  tasks: Task[];
  onStatus: (t: Task, s: Status) => void;
  onOpen: (t: Task) => void;
  showCourse?: boolean;
  showDate?: boolean;
  dateDanger?: boolean;
  empty?: string;
}) {
  const { tasks, empty = "אין משימות", ...rest } = props;
  if (tasks.length === 0) return <p className="empty muted">{empty}</p>;
  return (
    <ul className="list">
      {tasks.map((t) => (
        <TaskRow key={t.id} task={t} {...rest} />
      ))}
    </ul>
  );
}
