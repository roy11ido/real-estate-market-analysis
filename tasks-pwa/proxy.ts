import { NextResponse, type NextRequest } from "next/server";
import { AUTH_COOKIE, isAuthed } from "./lib/auth";

export async function proxy(req: NextRequest) {
  if (await isAuthed(req.cookies.get(AUTH_COOKIE)?.value)) return NextResponse.next();
  if (req.nextUrl.pathname.startsWith("/api/")) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  return NextResponse.redirect(new URL("/login", req.url));
}

export const config = {
  // Everything except login, static assets and PWA files
  matcher: [
    "/((?!login|api/login|_next/static|_next/image|manifest.webmanifest|icon-192.png|icon-512.png|apple-touch-icon.png|favicon.ico).*)",
  ],
};
