// components/ReviewToggle.tsx
"use client";
import { useState } from "react";

type Review = { product_id: number | string; text: string };

export default function ReviewToggle({ pid }: { pid: number | string }) {
  const [open, setOpen] = useState(false);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function toggle() {
    if (open) {
      setOpen(false);
      return;
    }
    setLoading(true);
    setErr(null);
    try {
      const r = await fetch(`/api/reviews?product_id=${encodeURIComponent(String(pid))}`);
      const j = await r.json();
      const arr: Review[] = Array.isArray(j) ? j : j.reviews ?? [];
      setReviews(arr);
      setOpen(true);
    } catch (e: any) {
      setErr("Could not load reviews.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button
        className={`btn btn-sm ${open ? "btn-success" : "btn-outline-primary"}`}
        onClick={toggle}
        disabled={loading}
      >
        {loading ? "Loading…" : open ? "Hide reviews" : "Reviews"}
      </button>

      {open && (
        <div className="border rounded bg-light mt-2 small text-muted p-2" style={{ maxHeight: 140, overflowY: "auto" }}>
          <div className="fw-semibold mb-2">Customer feedback:</div>

          {err && <div className="text-danger">{err}</div>}

          {!err && reviews.length === 0 && <div>No reviews yet.</div>}

          {reviews.map((rev, i) => (
            <div key={i} className="mb-2">
              &quot;{rev.text}&quot;
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
