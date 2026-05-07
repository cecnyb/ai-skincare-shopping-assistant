"use client";

import { useMemo, useState, useEffect, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import ProductCard from "@/components/ProductCard";
import ProductModal from "@/components/ProductModal";
import ReviewToggle from "@/components/ReviewToggle";
import type { Product } from "@/types";

export default function ProductGrid({ products }: { products: Product[] }) {
  const [selected, setSelected] = useState<Product | null>(null);
  const params = useSearchParams();
  const router = useRouter();

  const byId = useMemo(() => {
    const m = new Map<string, Product>();
    products.forEach((p) => m.set(String(p.id), p));
    return m;
  }, [products]);

  // Open by product ID helper (used by deep link + chat event)
  const openById = useCallback(
    (pid: string | number) => {
      const key = String(pid);
      const p = byId.get(key);
      if (!p) return;
      // Update URL param (no scroll) and open modal
      const url = new URL(window.location.href);
      url.searchParams.set("product", key);
      router.replace(`${url.pathname}?${url.searchParams.toString()}`, { scroll: false });
      setSelected(p);
    },
    [byId, router]
  );

  // Deep-link open: /client?product=ID
  useEffect(() => {
    const pid = params.get("product");
    if (pid && byId.has(pid)) {
      // avoid re-setting if same product is already selected
      if (!selected || String(selected.id) !== pid) openById(pid);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params, byId]);

  // Listen for "open-product" events from Chat
  useEffect(() => {
    const onOpenProduct = (e: Event) => {
      const ce = e as CustomEvent<{ pid: string | number }>;
      if (ce?.detail?.pid != null) openById(ce.detail.pid);
    };
    window.addEventListener("open-product", onOpenProduct as EventListener);
    return () => window.removeEventListener("open-product", onOpenProduct as EventListener);
  }, [openById]);

  const openModal = useCallback(
    (p: Product) => {
      const key = String(p.id);
      const url = new URL(window.location.href);
      url.searchParams.set("product", key);
      router.replace(`${url.pathname}?${url.searchParams.toString()}`, { scroll: false });
      setSelected(p);
    },
    [router]
  );

  const closeModal = useCallback(() => {
    setSelected(null);
    const url = new URL(window.location.href);
    url.searchParams.delete("product");
    const qs = url.searchParams.toString();
    router.replace(qs ? `${url.pathname}?${qs}` : url.pathname, { scroll: false });
  }, [router]);

  return (
    <>
      <div className="row g-4" id="products">
        {products.map((p) => (
          <div
            className="col-md-4"
            key={String(p.id)}
            style={{ cursor: "pointer" }}
            onClick={() => openModal(p)}
          >
            <ProductCard
              p={p}
              footer={
                // Prevent footer clicks (reviews) from opening the modal
                <div onClick={(e) => e.stopPropagation()}>
                  <ReviewToggle pid={p.id} />
                </div>
              }
            />
          </div>
        ))}
      </div>

      {selected && <ProductModal product={selected} onClose={closeModal} />}
    </>
  );
}
