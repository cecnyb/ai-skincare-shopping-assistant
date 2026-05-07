import ClientHeader from "@/components/ClientHeader";
import Footer from "@/components/Footer";
import FloatingChat from "@/components/FloatingChat";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <section>
      <ClientHeader />
      {children}
      <Footer />
      <FloatingChat />
    </section>
  );
}
