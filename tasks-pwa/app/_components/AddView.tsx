"use client";

import { useEffect, useState } from "react";
import { addDays, israelToday } from "@/lib/dates";
import { PRIORITIES, TYPES, type Course, type Task } from "@/lib/types";

export function AddView({ onCreated, onError }: { onCreated: (t: Task) => void; onError: (m: string) => void }) {
  const [courses, setCourses] = useState<Course[] | null>(null);
  const [title, setTitle] = useState("");
  const [courseId, setCourseId] = useState("");
  const [type, setType] = useState<string | null>(null);
  const [due, setDue] = useState(() => addDays(israelToday(), 1));
  const [priority, setPriority] = useState<string>("רגילה");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetch("/api/courses")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setCourses)
      .catch(() => setCourses([]));
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || busy) return;
    setBusy(true);
    const res = await fetch("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: title.trim(), courseId: courseId || null, type, due: due || null, priority }),
    }).catch(() => null);
    const json = await res?.json().catch(() => null);
    setBusy(false);
    if (!res?.ok) {
      onError(json?.error ?? "ההוספה נכשלה");
      return;
    }
    onCreated(json as Task);
    // Keep course/type/date for adding several tasks in a row; clear the name.
    setTitle("");
  }

  return (
    <form className="add-form" onSubmit={submit}>
      <div className="field">
        <label htmlFor="title">שם המשימה</label>
        <input id="title" className="input" value={title} onChange={(e) => setTitle(e.target.value)} autoComplete="off" enterKeyHint="done" />
      </div>

      <div className="field">
        <label htmlFor="course">קורס</label>
        <select id="course" className="input" value={courseId} onChange={(e) => setCourseId(e.target.value)}>
          <option value="">{courses === null ? "טוען…" : "ללא קורס"}</option>
          {courses?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label>סוג</label>
        <div className="chips">
          {TYPES.map((t) => (
            <button type="button" key={t} className={type === t ? "on" : ""} onClick={() => setType(type === t ? null : t)}>
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <label htmlFor="add-due">תאריך יעד</label>
        <input id="add-due" type="date" className="input" value={due} onChange={(e) => setDue(e.target.value)} />
      </div>

      <div className="field">
        <label>עדיפות</label>
        <div className="segmented">
          {PRIORITIES.map((p) => (
            <button type="button" key={p} className={priority === p ? "on" : ""} onClick={() => setPriority(p)}>
              {p}
            </button>
          ))}
        </div>
      </div>

      <button className="primary" type="submit" disabled={!title.trim() || busy}>
        {busy ? "מוסיף…" : "הוסף משימה"}
      </button>
    </form>
  );
}
