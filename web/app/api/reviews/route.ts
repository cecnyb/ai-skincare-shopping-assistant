export const runtime = "nodejs";
import { NextResponse } from "next/server";
const BASE = process.env.SERVER_URL!;

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const product_id = searchParams.get("product_id");
  const r = await fetch(`${BASE}/api/reviews?product_id=${encodeURIComponent(product_id ?? "")}`, { cache: "no-store" });
  const txt = await r.text();
  if (!r.ok) return NextResponse.json({ error: txt }, { status: 502 });
  return NextResponse.json(JSON.parse(txt)); // { reviews: [...] }
}
