export const runtime = "nodejs";
import { NextResponse } from "next/server";
const BASE = process.env.SERVER_URL!;

export async function GET(_: Request, { params }: { params: { pid: string } }) {
  const r = await fetch(`${BASE}/api/products/${params.pid}`, { cache: "no-store" });
  const txt = await r.text();
  if (!r.ok) return NextResponse.json({ error: txt }, { status: 502 });
  return NextResponse.json(JSON.parse(txt)); // { product: {...} } or {error}
}
