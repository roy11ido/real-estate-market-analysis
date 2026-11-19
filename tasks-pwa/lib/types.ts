export const STATUSES = ["לא התחלתי", "בתהליך", "הושלם"] as const;
export type Status = (typeof STATUSES)[number];
export const DONE: Status = "הושלם";

export type Task = {
  id: string;
  title: string;
  status: Status;
  type: string | null;
  priority: string | null;
  due: string | null; // YYYY-MM-DD (date part of start)
  courses: string[]; // course names
  url: string;
};

export type TodayPayload = {
  today: string;
  tomorrow: string;
  overdue: Task[];
  todayTasks: Task[];
  tomorrowTasks: Task[];
  fetchedAt: number;
};

export function nextStatus(s: Status): Status {
  return STATUSES[(STATUSES.indexOf(s) + 1) % STATUSES.length];
}
