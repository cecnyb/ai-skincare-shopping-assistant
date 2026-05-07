export default function ClientHeader() {
  return (
    <nav className="navbar navbar-light bg-white shadow-sm mb-4">
      <div className="container d-flex w-100">
        <a className="navbar-brand" href="#">Seoulight Beauty Store</a>
        <nav className="d-flex gap-3 ms-auto">
          <a className="text-primary fw-semibold text-decoration-none" href="/client">Products</a>
          <a className="text-secondary text-decoration-none" href="/client#faq">FAQ</a>
        </nav>
      </div>
    </nav>
  );
}
