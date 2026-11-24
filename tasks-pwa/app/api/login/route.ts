import { NextResponse, type NextRequest } from "next/server";
import { AUTH_COOKIE, AUTH_MAX_AGE, expectedToken, safeEqual } from "@/lib/auth";

// Best-effort brute-force protection (per warm instance): 5 failures → 10 min lock per IP.
const attempts = new Map<string, { n: number; until: number }>();

export async function POST(req: NextRequest) {
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "unknown";
  const now = Date.now();
  const a = attempts.get(ip);
  if (a && a.until > now) {
    return NextResponse.json({ error: "יותר מדי ניסיונות. נסה שוב בעוד כמה דקות." }, { status: 429 });
  }

  const body = (await req.json().catch(() => ({}))) as { pin?: unknown };
  const pin = typeof body.pin === "string" ? body.pin : "";
  const appPin = process.env.APP_PIN;
  if (!appPin) return NextResponse.json({ error: "APP_PIN לא מוגדר בשרת" }, { status: 500 });

  if (!safeEqual(pin, appPin)) {
    const n = (a?.n ?? 0) + 1;
    attempts.set(ip, { n: n >= 5 ? 0 : n, until: n >= 5 ? now + 10 * 60_000 : 0 });
    await new Promise((r) => setTimeout(r, 400));
    return NextResponse.json({ error: "קוד שגוי" }, { status: 401 });
  }

  attempts.delete(ip);
  const res = NextResponse.json({ ok: true });
  res.cookies.set(AUTH_COOKIE, (await expectedToken())!, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: AUTH_MAX_AGE,
  });
  return res;
}
