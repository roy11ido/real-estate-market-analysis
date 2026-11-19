export const STATUSES = ["לא התחלתי", "בתהליך", "הושלם"] as const;
export type Status = (typeof STATUSES)[number];
export const DONE: Status = "הושלם";

export const TYPES = ["שיעורי בית", "עבודה", "קריאה", "מבחן", "בוחן"] as const;
export const PRIORITIES = ["גבוהה", "רגילה"] as const;

export type TaskFile = { name: string; url: string; image: boolean };

export type Task = {
  id: string;
  title: string;
  status: Status;
  type: string | null;
  priority: string | null;
  due: string | null; // YYYY-MM-DD (date part of start)
  courseIds: string[];
  courses: string[]; // course names
  files: TaskFile[];
  url: string;
};

export type Course = { id: string; name: string };

export type TasksPayload = {
  today: string;
  tasks: Task[];
  fetchedAt: number;
};

export function nextStatus(s: Status): Status {
  return STATUSES[(STATUSES.indexOf(s) + 1) % STATUSES.length];
}

export const MAX_UPLOAD_BYTES = 4_300_000; // Vercel request body limit is 4.5MB
