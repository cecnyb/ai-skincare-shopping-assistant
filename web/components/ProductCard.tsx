// components/ProductCard.tsx
import type { Product } from "@/types";

function firstSentence(text?: string) {
  if (!text) return "";
  const i = text.indexOf(".");
  return i !== -1 ? text.slice(0, i + 1) : text;
}

export default function ProductCard({
  p,
  footer,
}: { p: Product; footer?: React.ReactNode }) {
  return (
    <div className="card h-100">
      {p.image && (
        <img
          src={p.image}
          alt={p.title}
          className="card-img-top"
          style={{ height: 500, objectFit: "contain", padding: 8 }}
        />
      )}
      <div className="card-body">
        <h5 className="card-title">{p.title}</h5>
        <p className="card-text">{firstSentence(p.description)}</p>
        <p className="fw-bold">{p.price_display}</p>
      </div>

      {/* footer goes INSIDE the card */}
      {footer && (
      <div
        className="card-footer bg-white"
        style={{ borderTop: "none", paddingTop: 0 }}
      >
        
        {footer}
      </div>
    )}
    </div>
  );
}
