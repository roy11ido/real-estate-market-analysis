"use client";

import { useRef, useState } from "react";
import { fitForUpload } from "@/lib/compress";
import { MAX_UPLOAD_BYTES, STATUSES, type Status, type Task } from "@/lib/types";

export function TaskSheet({
  task,
  onClose,
  onStatus,
  onDue,
  onUpdated,
  onError,
}: {
  task: Task;
  onClose: () => void;
  onStatus: (t: Task, s: Status) => void;
  onDue: (t: Task, due: string | null) => void;
  onUpdated: (t: Task) => void;
  onError: (msg: string) => void;
}) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = e.target.files?.[0];
    e.target.value = "";
    if (!picked) return;
    setUploading(true);
    try {
      const file = await fitForUpload(picked);
      if (file.size > MAX_UPLOAD_BYTES) throw new Error("הקובץ גדול מ-4MB — העלה אותו ישירות ב-Notion");
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`/api/tasks/${task.id}/files`, { method: "POST", body: fd });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json.error || "ההעלאה נכשלה");
      onUpdated(json as Task);
    } catch (err) {
      onError(err instanceof Error ? err.message : "ההעלאה נכשלה");
    } finally {
      setUploading(false);
    }
  }

  const images = task.files.filter((f) => f.image);
  const others = task.files.filter((f) => !f.image);

  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
        <div className="sheet-handle" />
        <div className="sheet-head">
          <h3>{task.title}</h3>
          <button className="link-btn" onClick={onClose}>
            סגור
          </button>
        </div>
        <div className="row-meta sheet-meta">
          {task.courses.length > 0 && <span>{task.courses.join(", ")}</span>}
          {task.type && <span className="chip">{task.type}</span>}
          {task.priority === "גבוהה" && <span className="chip chip-red">עדיפות גבוהה</span>}
        </div>

        <div className="field">
          <label>סטטוס</label>
          <div className="segmented">
            {STATUSES.map((s) => (
              <button key={s} className={task.status === s ? "on" : ""} onClick={() => onStatus(task, s)}>
                {s}
              </button>
            ))}
          </div>
        </div>

        <div className="field">
          <label htmlFor="due">תאריך יעד</label>
          <input
            id="due"
            type="date"
            className="input"
            value={task.due ?? ""}
            onChange={(e) => onDue(task, e.target.value || null)}
          />
        </div>

        <div className="field">
          <label>קבצים ומדיה</label>
          {images.length > 0 && (
            <div className="thumbs">
              {images.map((f, i) => (
                <a key={i} href={f.url} target="_blank" rel="noreferrer" className="thumb">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={f.url} alt={f.name} loading="lazy" />
                </a>
              ))}
            </div>
          )}
          {others.length > 0 && (
            <ul className="file-list">
              {others.map((f, i) => (
                <li key={i}>
                  <a href={f.url} target="_blank" rel="noreferrer">
                    📄 <bdi>{f.name}</bdi>
                  </a>
                </li>
              ))}
            </ul>
          )}
          {task.files.length === 0 && <p className="muted small">אין קבצים</p>}
          <input ref={fileInput} type="file" hidden onChange={upload} />
          <button className="secondary" disabled={uploading} onClick={() => fileInput.current?.click()}>
            {uploading ? "מעלה…" : "+ הוסף קובץ"}
          </button>
        </div>

        <a className="primary block" href={task.url} target="_blank" rel="noreferrer">
          פתח ב-Notion
        </a>
      </div>
    </div>
  );
}
