// components/ProductModal.tsx
"use client";
import type { Product } from "@/types";
import ReviewToggle from "@/components/ReviewToggle";

export default function ProductModal({
  product,
  onClose,
}: {
  product: Product;
  onClose: () => void;
}) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`${product.title} details`}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.45)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 20,
        zIndex: 5000,
      }}
    >
      <div
        onMouseDown={(e) => e.stopPropagation()}
        style={{
          background: "#fff",
          borderRadius: 12,
          width: "min(720px, 96vw)",
          maxHeight: "90vh",
          overflowY: "auto",
          boxShadow: "0 20px 60px rgba(0,0,0,0.4)",
          padding: 20,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
          <h3 style={{ margin: 0 }}>{product.title}</h3>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "1px solid #ddd",
              borderRadius: 8,
              padding: "6px 10px",
              cursor: "pointer",
            }}
          >
            ✕
          </button>
        </div>

        {product.image && (
          <img
            src={product.image}
            alt={product.title}
            style={{
              width: "100%",
              maxHeight: 360,
              objectFit: "contain",
              margin: "14px 0",
              borderRadius: 10,
            }}
          />
        )}

        {product.description && (
          <p style={{ whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{product.description}</p>
        )}

        {product.price_display && (
          <p style={{ fontWeight: 600, fontSize: 18, marginTop: 8 }}>{product.price_display}</p>
        )}

        {/* Reviews inside modal */}
        <div style={{ marginTop: 18 }}>
          <ReviewToggle pid={product.id} />
        </div>

        {/* CTA row */}
        <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
          <button
            onClick={() => alert("Add to cart TBD")}
            style={{
              border: "1px solid #111",
              background: "#111",
              color: "#fff",
              borderRadius: 10,
              padding: "10px 12px",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Add to Cart
          </button>
          <button
            onClick={onClose}
            style={{
              border: "1px solid #ddd",
              background: "#fff",
              color: "#111",
              borderRadius: 10,
              padding: "10px 12px",
              cursor: "pointer",
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
