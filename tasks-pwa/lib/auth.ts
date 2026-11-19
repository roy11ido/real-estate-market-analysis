export const AUTH_COOKIE = "tp_auth";
export const AUTH_MAX_AGE = 60 * 60 * 24 * 30; // 30 days

const enc = new TextEncoder();

/** Cookie value = HMAC(NOTION_TOKEN, "v1:" + APP_PIN). Changing the PIN invalidates all sessions. */
export async function expectedToken(): Promise<string | null> {
  const pin = process.env.APP_PIN;
  const secret = process.env.NOTION_TOKEN;
  if (!pin || !secret) return null;
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, [
    "sign",
  ]);
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(`v1:${pin}`));
  return Array.from(new Uint8Array(sig), (b) => b.toString(16).padStart(2, "0")).join("");
}

export function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export async function isAuthed(cookieValue: string | undefined): Promise<boolean> {
  if (!cookieValue) return false;
  const exp = await expectedToken();
  return !!exp && safeEqual(cookieValue, exp);
}
