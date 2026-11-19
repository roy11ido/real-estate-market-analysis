"use client";

export type Tab = "today" | "week" | "courses" | "add";

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  {
    id: "today",
    label: "היום",
    icon: <path d="M12 3v2M12 19v2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M3 12h2M19 12h2M5.6 18.4 7 17M17 7l1.4-1.4M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z" />,
  },
  {
    id: "week",
    label: "השבוע",
    icon: <path d="M4 6h16v14H4zM4 10h16M8 3v4M16 3v4" />,
  },
  {
    id: "courses",
    label: "קורסים",
    icon: <path d="M4 5h6a2 2 0 0 1 2 2v13a2 2 0 0 0-2-2H4zM20 5h-6a2 2 0 0 0-2 2v13a2 2 0 0 1 2-2h6z" />,
  },
  {
    id: "add",
    label: "הוספה",
    icon: <path d="M12 5v14M5 12h14" />,
  },
];

export function TabBar({ tab, onTab }: { tab: Tab; onTab: (t: Tab) => void }) {
  return (
    <nav className="tabbar">
      {TABS.map((t) => (
        <button key={t.id} className={tab === t.id ? "on" : ""} onClick={() => onTab(t.id)}>
          <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            {t.icon}
          </svg>
          <span>{t.label}</span>
        </button>
      ))}
    </nav>
  );
}
