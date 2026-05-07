// app/agent/layout.tsx
export default function AgentLayout({ children }: { children: React.ReactNode }) {
  return (
    <section>
      <header style={{ padding: 16, borderBottom: "1px solid #eee" }}>
        <strong>Agent Console</strong>
      </header>
      {children}
    </section>
  );
}
