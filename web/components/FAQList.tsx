import type { FAQItem } from "@/types";

export default function FAQList({ items }: { items: FAQItem[] }) {
  return (
    <div id="faq" className="d-grid gap-3">
      {items.map((f, i) => (
        <details key={String(f.id ?? i)} className="border rounded p-3 bg-white">
          <summary className="fw-semibold" style={{ cursor: "pointer" }}>
            {f.question}
          </summary>
          <div className="mt-2">{f.answer}</div>
        </details>
      ))}
    </div>
  );
}
