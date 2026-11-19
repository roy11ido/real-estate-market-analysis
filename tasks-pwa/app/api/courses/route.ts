import { NextResponse } from "next/server";
import { getCourses } from "@/lib/notion";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    return NextResponse.json(await getCourses(), { headers: { "Cache-Control": "private, no-store" } });
  } catch (e) {
    console.error("courses failed", e);
    return NextResponse.json({ error: "שגיאה בטעינת קורסים" }, { status: 502 });
  }
}
