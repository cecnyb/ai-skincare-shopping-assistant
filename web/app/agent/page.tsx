// app/agent/page.tsx
"use client";
import Chat from "@/components/Chat";

export default function AgentPage() {
  return (
    <main style={{ padding: 16, maxWidth: 720, margin: "0 auto" }}>
      <h2>Chat with Agent</h2>
      <Chat />
    </main>
  );
}
