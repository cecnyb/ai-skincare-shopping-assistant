// app/client/page.tsx
import type { Product, FAQItem } from "@/types";
import ProductCard from "@/components/ProductCard";
import ReviewToggle from "@/components/ReviewToggle";
import FAQList from "@/components/FAQList";
import ProductGrid from "@/components/ProductGrid";


const BASE = process.env.SERVER_URL!; // e.g. http://127.0.0.1:9001

async function getProducts(): Promise<Product[]> {
  const r = await fetch(`${BASE}/api/products`, { cache: "no-store" });
  if (!r.ok) return [];
  const j = await r.json(); // { products: [...] }
  return j.products ?? [];
}

async function getFAQ(): Promise<FAQItem[]> {
  const r = await fetch(`${BASE}/api/faq`, { cache: "no-store" });
  if (!r.ok) return [];
  const j = await r.json(); // array
  return Array.isArray(j) ? j : [];
}

export default async function ClientPage() {
  const [products, faq] = await Promise.all([getProducts(), getFAQ()]);

  return (
    <main className="container">
      {/* Products grid */}
      <ProductGrid products={products} />

      {/* FAQ */}
      <section className="mt-5" id="faq">
        <h2 className="mb-3">FAQ</h2>
        <FAQList items={faq} />
      </section>
    </main>
  );
}