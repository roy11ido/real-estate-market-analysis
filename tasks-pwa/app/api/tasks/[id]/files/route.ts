import { NextResponse, type NextRequest } from "next/server";
import { addFile } from "@/lib/notion";
import { MAX_UPLOAD_BYTES } from "@/lib/types";
import { ID_RE } from "@/lib/validate";

export const maxDuration = 60;

export async function POST(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  if (!ID_RE.test(id)) return NextResponse.json({ error: "bad id" }, { status: 400 });
  const form = await req.formData().catch(() => null);
  const file = form?.get("file");
  if (!(file instanceof File) || file.size === 0) return NextResponse.json({ error: "לא נבחר קובץ" }, { status: 400 });
  if (file.size > MAX_UPLOAD_BYTES) return NextResponse.json({ error: "הקובץ גדול מ-4MB" }, { status: 413 });
  try {
    return NextResponse.json(await addFile(id, file));
  } catch (e) {
    console.error("upload failed", e);
    const msg = e instanceof Error && /size|large|limit/i.test(e.message) ? "Notion דחה את הקובץ (גודל)" : "ההעלאה ל-Notion נכשלה";
    return NextResponse.json({ error: msg }, { status: 502 });
  }
}
