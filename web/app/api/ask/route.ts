import { NextResponse } from "next/server";

const AGENT_URL = process.env.AGENT_URL!; // e.g. http://127.0.0.1:9001

export async function POST(req: Request) {
  const body = await req.json();

  // ✅ Extract the user ID (and optionally session ID)
  const userId = req.headers.get("x-user-id") ?? "anonymous";
  const sessionId = req.headers.get("x-session-id") ?? null;

  const r = await fetch(`${AGENT_URL}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": userId,             // ✅ forward to Python
      ...(sessionId ? { "X-Session-Id": sessionId } : {}), // ✅ optional session
    },
    body: JSON.stringify(body),
  });

  if (!r.ok) {
    const text = await r.text();
    return NextResponse.json({ error: `Agent ${r.status}: ${text}` }, { status: 502 });
  }

  const data = await r.json();
  return NextResponse.json(data);
}
