"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { hebrewDate, israelToday, shortDate } from "@/lib/dates";
import { DONE, nextStatus, type Status, type Task, type TodayPayload } from "@/lib/types";

type Section = { key: "overdue" | "todayTasks" | "tomorrowTasks"; title: string; tone?: "danger" };

const SECTIONS: Section[] = [
  { key: "overdue", title: "באיחור", tone: "danger" },
  { key: "todayTasks", title: "היום" },
  { key: "tomorrowTasks", title: "מחר" },
];

const PULL_THRESHOLD = 70;

export default function TodayPage() {
  const [data, setData] = useState<TodayPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [pull, setPull] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const pullStart = useRef<number | null>(null);

  const load = useCallback(async (fresh = false) => {
    try {
      const res = await fetch(`/api/tasks/today${fresh ? "?fresh=1" : ""}`, { cache: "no-store" });
      if (res.status === 401) {
        window.location.replace("/login");
        return;
      }
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || "שגיאה");
      setData(json);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "שגיאה בטעינה");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // If the app is resumed on a new day, the lists are stale — reload.
  useEffect(() => {
    const onVis = () => {
      if (document.visibilityState === "visible" && data && data.today !== israelToday()) load();
    };
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, [data, load]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(""), 3000);
    return () => clearTimeout(t);
  }, [toast]);

  // Pull to refresh
  const onTouchStart = (e: React.TouchEvent) => {
    pullStart.current = window.scrollY <= 0 && !refreshing ? e.touches[0].clientY : null;
  };
  const onTouchMove = (e: React.TouchEvent) => {
    if (pullStart.current === null) return;
    const dy = e.touches[0].clientY - pullStart.current;
    setPull(dy > 0 ? Math.min(dy * 0.5, 110) : 0);
  };
  const onTouchEnd = async () => {
    if (pullStart.current === null) return;
    pullStart.current = null;
    if (pull >= PULL_THRESHOLD) {
      setRefreshing(true);
      setPull(PULL_THRESHOLD);
      await load(true);
      setRefreshing(false);
    }
    setPull(0);
  };

  const updateStatus = useCallback(
    async (task: Task, status: Status) => {
      const patch = (s: Status) =>
        setData((d) => {
          if (!d) return d;
          const map = (list: Task[]) => list.map((t) => (t.id === task.id ? { ...t, status: s } : t));
          return { ...d, overdue: map(d.overdue), todayTasks: map(d.todayTasks), tomorrowTasks: map(d.tomorrowTasks) };
        });
      patch(status);
      if (navigator.vibrate) navigator.vibrate(10);
      const res = await fetch(`/api/tasks/${task.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      }).catch(() => null);
      if (!res?.ok) {
        patch(task.status);
        setToast("העדכון נכשל — נסה שוב");
      }
    },
    [],
  );

  return (
    <main onTouchStart={onTouchStart} onTouchMove={onTouchMove} onTouchEnd={onTouchEnd}>
      <div className="ptr" style={{ height: pull }} aria-hidden>
        <div className={`ptr-spinner ${refreshing ? "spin" : ""}`} style={{ opacity: Math.min(pull / PULL_THRESHOLD, 1), transform: `rotate(${pull * 3}deg)` }} />
      </div>

      <header className="top">
        <h1>היום</h1>
        <p className="muted">{hebrewDate(data?.today ?? israelToday())}</p>
      </header>

      {loading && !data && <p className="center muted">טוען…</p>}
      {error && (
        <div className="banner error-banner">
          {error}
          <button onClick={() => load(true)}>נסה שוב</button>
        </div>
      )}

      {data &&
        SECTIONS.map((s) => {
          const list = data[s.key];
          if (s.key === "overdue" && list.length === 0) return null;
          return (
            <section key={s.key} className="group">
              <h2 className={s.tone === "danger" ? "danger" : ""}>
                {s.title}
                {s.key === "tomorrowTasks" && <span className="muted"> · {shortDate(data.tomorrow)}</span>}
                <span className="count">{list.filter((t) => t.status !== DONE).length}</span>
              </h2>
              {list.length === 0 ? (
                <p className="empty muted">אין משימות</p>
              ) : (
                <ul className="list">
                  {list.map((t) => (
                    <TaskRow key={t.id} task={t} overdue={s.key === "overdue"} onStatus={updateStatus} />
                  ))}
                </ul>
              )}
            </section>
          );
        })}

      {toast && <div className="toast">{toast}</div>}
    </main>
  );
}

function TaskRow({
  task,
  overdue,
  onStatus,
}: {
  task: Task;
  overdue: boolean;
  onStatus: (t: Task, s: Status) => void;
}) {
  const [dx, setDx] = useState(0);
  const start = useRef<{ x: number; y: number; lock: "h" | "v" | null } | null>(null);
  const done = task.status === DONE;
  const SWIPE = 80;

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

  const statusClass = task.status === DONE ? "s-done" : task.status === "בתהליך" ? "s-progress" : "s-todo";

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
          {task.status === DONE ? "✓" : ""}
        </button>
        <div className="row-body">
          <div className="row-title">
            {task.priority === "גבוהה" && <span className="prio">!</span>}
            {task.title}
          </div>
          <div className="row-meta">
            {task.courses.length > 0 && <span>{task.courses.join(", ")}</span>}
            {task.type && <span className="chip">{task.type}</span>}
            {task.status === "בתהליך" && <span className="chip chip-blue">בתהליך</span>}
            {overdue && task.due && <span className="danger">{shortDate(task.due)}</span>}
          </div>
        </div>
      </div>
    </li>
  );
}
