export const runtime = "nodejs";
import { NextResponse } from "next/server";
const BASE = process.env.SERVER_URL!;

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const q = searchParams.get("q") ?? "";
  const top_k = searchParams.get("top_k") ?? "5";
  const r = await fetch(`${BASE}/api/products/match?q=${encodeURIComponent(q)}&top_k=${top_k}`, { cache: "no-store" });
  const txt = await r.text();
  if (!r.ok) return NextResponse.json({ error: txt }, { status: 502 });
  return NextResponse.json(JSON.parse(txt)); // { products: [...] }
}
