const TZ = "Asia/Jerusalem";

/** YYYY-MM-DD in Israel time */
export function israelToday(now = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: TZ }).format(now);
}

export function addDays(ymd: string, days: number): string {
  const d = new Date(`${ymd}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

export function hebrewDate(ymd: string): string {
  return new Intl.DateTimeFormat("he-IL", {
    weekday: "long",
    day: "numeric",
    month: "long",
    timeZone: "UTC",
  }).format(new Date(`${ymd}T00:00:00Z`));
}

export function shortDate(ymd: string): string {
  return new Intl.DateTimeFormat("he-IL", { day: "numeric", month: "numeric", timeZone: "UTC" }).format(
    new Date(`${ymd}T00:00:00Z`),
  );
}
