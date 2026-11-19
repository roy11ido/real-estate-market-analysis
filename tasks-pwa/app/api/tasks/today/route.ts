import { NextResponse, type NextRequest } from "next/server";
import { getToday } from "@/lib/notion";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  try {
    const data = await getToday(req.nextUrl.searchParams.get("fresh") === "1");
    return NextResponse.json(data, { headers: { "Cache-Control": "private, no-store" } });
  } catch (e) {
    console.error("today failed", e);
    return NextResponse.json({ error: "שגיאה בטעינה מ-Notion" }, { status: 502 });
  }
}
