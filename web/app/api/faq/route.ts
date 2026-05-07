export const runtime = "nodejs";
import { NextResponse } from "next/server";
const BASE = process.env.SERVER_URL!;

export async function GET() {
  const r = await fetch(`${BASE}/api/faq`, { cache: "no-store" });
  const txt = await r.text();
  if (!r.ok) return NextResponse.json({ error: txt }, { status: 502 });
  return NextResponse.json(JSON.parse(txt)); // FAQ array
}
