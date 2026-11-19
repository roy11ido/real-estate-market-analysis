import { NextResponse, type NextRequest } from "next/server";
import { setStatus } from "@/lib/notion";
import { STATUSES, type Status } from "@/lib/types";

const ID_RE = /^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$/i;

export async function PATCH(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  if (!ID_RE.test(id)) return NextResponse.json({ error: "bad id" }, { status: 400 });
  const body = (await req.json().catch(() => ({}))) as { status?: unknown };
  const status = body.status;
  if (typeof status !== "string" || !(STATUSES as readonly string[]).includes(status)) {
    return NextResponse.json({ error: "bad status" }, { status: 400 });
  }
  try {
    await setStatus(id, status as Status);
    return NextResponse.json({ ok: true });
  } catch (e) {
    console.error("status update failed", e);
    return NextResponse.json({ error: "העדכון ב-Notion נכשל" }, { status: 502 });
  }
}
