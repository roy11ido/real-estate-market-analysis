import { NextResponse, type NextRequest } from "next/server";
import { updateTask } from "@/lib/notion";
import { STATUSES, type Status } from "@/lib/types";
import { DATE_RE, ID_RE } from "@/lib/validate";

export async function PATCH(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  if (!ID_RE.test(id)) return NextResponse.json({ error: "bad id" }, { status: 400 });
  const b = (await req.json().catch(() => ({}))) as { status?: unknown; due?: unknown };
  const patch: { status?: Status; due?: string | null } = {};
  if (b.status !== undefined) {
    if (typeof b.status !== "string" || !(STATUSES as readonly string[]).includes(b.status)) {
      return NextResponse.json({ error: "bad status" }, { status: 400 });
    }
    patch.status = b.status as Status;
  }
  if (b.due !== undefined) {
    if (b.due !== null && (typeof b.due !== "string" || !DATE_RE.test(b.due))) {
      return NextResponse.json({ error: "bad date" }, { status: 400 });
    }
    patch.due = b.due as string | null;
  }
  if (!Object.keys(patch).length) return NextResponse.json({ error: "nothing to update" }, { status: 400 });
  try {
    return NextResponse.json(await updateTask(id, patch));
  } catch (e) {
    console.error("update failed", e);
    return NextResponse.json({ error: "העדכון ב-Notion נכשל" }, { status: 502 });
  }
}
