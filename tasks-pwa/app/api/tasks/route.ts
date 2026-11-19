import { NextResponse, type NextRequest } from "next/server";
import { createTask, getTasks } from "@/lib/notion";
import { PRIORITIES, TYPES } from "@/lib/types";
import { DATE_RE, ID_RE } from "@/lib/validate";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  try {
    const data = await getTasks(req.nextUrl.searchParams.get("fresh") === "1");
    return NextResponse.json(data, { headers: { "Cache-Control": "private, no-store" } });
  } catch (e) {
    console.error("tasks failed", e);
    return NextResponse.json({ error: "שגיאה בטעינה מ-Notion" }, { status: 502 });
  }
}

export async function POST(req: NextRequest) {
  const b = (await req.json().catch(() => ({}))) as Record<string, unknown>;
  const title = typeof b.title === "string" ? b.title.trim() : "";
  if (!title || title.length > 500) return NextResponse.json({ error: "חסר שם משימה" }, { status: 400 });
  const courseId = typeof b.courseId === "string" && ID_RE.test(b.courseId) ? b.courseId : null;
  const type = typeof b.type === "string" && (TYPES as readonly string[]).includes(b.type) ? b.type : null;
  const priority =
    typeof b.priority === "string" && (PRIORITIES as readonly string[]).includes(b.priority) ? b.priority : null;
  const due = typeof b.due === "string" && DATE_RE.test(b.due) ? b.due : null;
  try {
    const task = await createTask({ title, courseId, type, due, priority });
    return NextResponse.json(task);
  } catch (e) {
    console.error("create failed", e);
    return NextResponse.json({ error: "היצירה ב-Notion נכשלה" }, { status: 502 });
  }
}
