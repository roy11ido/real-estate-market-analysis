"use client";

import { useState } from "react";

export default function LoginPage() {
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!pin || busy) return;
    setBusy(true);
    setError("");
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin }),
    }).catch(() => null);
    if (res?.ok) {
      window.location.replace("/");
      return;
    }
    const data = (await res?.json().catch(() => null)) as { error?: string } | null;
    setError(data?.error ?? "אין חיבור לשרת");
    setPin("");
    setBusy(false);
  }

  return (
    <main className="login">
      <form onSubmit={submit} className="login-card">
        <h1>משימות</h1>
        <p className="muted">הזן קוד כניסה</p>
        <input
          className="pin-input"
          type="password"
          inputMode="numeric"
          autoComplete="current-password"
          autoFocus
          value={pin}
          onChange={(e) => setPin(e.target.value.replace(/\D/g, ""))}
          aria-label="קוד כניסה"
        />
        {error && <p className="error">{error}</p>}
        <button className="primary" type="submit" disabled={!pin || busy}>
          {busy ? "בודק…" : "כניסה"}
        </button>
      </form>
    </main>
  );
}
