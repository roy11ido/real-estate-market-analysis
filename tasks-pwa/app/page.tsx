"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { hebrewDate, israelToday } from "@/lib/dates";
import type { Status, Task, TasksPayload } from "@/lib/types";
import { AddView } from "./_components/AddView";
import { TabBar, type Tab } from "./_components/TabBar";
import { TaskSheet } from "./_components/TaskSheet";
import { CourseView, TodayView, WeekView } from "./_components/views";

const TITLES: Record<Tab, string> = { today: "היום", week: "השבוע", courses: "לפי קורס", add: "משימה חדשה" };
const PULL_THRESHOLD = 70;

export default function App() {
  const [tab, setTab] = useState<Tab>("today");
  const [data, setData] = useState<TasksPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);
  const [pull, setPull] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const pullStart = useRef<number | null>(null);

  const load = useCallback(async (fresh = false) => {
    try {
      const res = await fetch(`/api/tasks${fresh ? "?fresh=1" : ""}`, { cache: "no-store" });
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

  // On resume: re-read (served from the 30s server cache). Also refreshes expiring Notion file URLs.
  useEffect(() => {
    const onVis = () => {
      if (document.visibilityState === "visible" && data && Date.now() - data.fetchedAt > 30_000) load();
    };
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, [data, load]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(""), 3000);
    return () => clearTimeout(t);
  }, [toast]);

  const replaceTask = useCallback((task: Task) => {
    setData((d) => {
      if (!d) return d;
      const exists = d.tasks.some((t) => t.id === task.id);
      return { ...d, tasks: exists ? d.tasks.map((t) => (t.id === task.id ? task : t)) : [...d.tasks, task] };
    });
  }, []);

  const patchTask = useCallback(
    async (task: Task, body: { status?: Status; due?: string | null }) => {
      replaceTask({ ...task, ...body });
      const res = await fetch(`/api/tasks/${task.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }).catch(() => null);
      if (!res?.ok) {
        replaceTask(task);
        setToast("העדכון נכשל — נסה שוב");
      }
    },
    [replaceTask],
  );

  const onStatus = useCallback(
    (task: Task, status: Status) => {
      if (navigator.vibrate) navigator.vibrate(10);
      patchTask(task, { status });
    },
    [patchTask],
  );
  const onDue = useCallback((task: Task, due: string | null) => patchTask(task, { due }), [patchTask]);
  const onOpen = useCallback((task: Task) => setOpenId(task.id), []);

  // Pull to refresh
  const onTouchStart = (e: React.TouchEvent) => {
    pullStart.current = tab !== "add" && !openId && window.scrollY <= 0 && !refreshing ? e.touches[0].clientY : null;
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

  const today = data?.today ?? israelToday();
  const openTask = openId ? data?.tasks.find((t) => t.id === openId) : undefined;
  const viewProps = { tasks: data?.tasks ?? [], today, onStatus, onOpen };

  return (
    <>
      <main className="with-tabbar" onTouchStart={onTouchStart} onTouchMove={onTouchMove} onTouchEnd={onTouchEnd}>
        <div className="ptr" style={{ height: pull }} aria-hidden>
          <div
            className={`ptr-spinner ${refreshing ? "spin" : ""}`}
            style={{ opacity: Math.min(pull / PULL_THRESHOLD, 1), transform: `rotate(${pull * 3}deg)` }}
          />
        </div>

        <header className="top">
          <h1>{TITLES[tab]}</h1>
          {tab === "today" && <p className="muted">{hebrewDate(today)}</p>}
        </header>

        {tab === "add" ? (
          <AddView
            onCreated={(t) => {
              replaceTask(t);
              setToast("נוסף ✓");
            }}
            onError={setToast}
          />
        ) : (
          <>
            {loading && !data && <p className="center muted">טוען…</p>}
            {error && (
              <div className="banner error-banner">
                {error}
                <button onClick={() => load(true)}>נסה שוב</button>
              </div>
            )}
            {data && tab === "today" && <TodayView {...viewProps} />}
            {data && tab === "week" && <WeekView {...viewProps} />}
            {data && tab === "courses" && <CourseView {...viewProps} />}
          </>
        )}
      </main>

      <TabBar
        tab={tab}
        onTab={(t) => {
          setTab(t);
          window.scrollTo(0, 0);
        }}
      />

      {openTask && (
        <TaskSheet
          task={openTask}
          onClose={() => setOpenId(null)}
          onStatus={onStatus}
          onDue={onDue}
          onUpdated={(t) => {
            // Merge only the files: a newer optimistic status/date must not be overwritten.
            setData((d) => d && { ...d, tasks: d.tasks.map((x) => (x.id === t.id ? { ...x, files: t.files } : x)) });
            setToast("הקובץ נוסף ✓");
          }}
          onError={setToast}
        />
      )}

      {toast && <div className="toast">{toast}</div>}
    </>
  );
}
