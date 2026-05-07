export type Product = {
  id: number | string;
  title: string;
  brand?: string;
  price_value?: number;
  currency?: string;
  price_display?: string;
  description?: string;
  image?: string;
  category?: string;
  rating?: number | null;
  availability?: string;
};

export type Review = {
  id?: number | string;
  product_id: number | string;
  text: string;
  author?: string;
  rating?: number;
  createdAt?: string;
};

export type FAQItem = { id?: number | string; question: string; answer: string };
