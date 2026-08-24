/** Lebar baca konsisten antar-halaman (820px, atau 980px untuk halaman authoring). */
export default function Container({
  wide = false,
  children,
}: {
  wide?: boolean;
  children: React.ReactNode;
}) {
  return (
    <main className={`mx-auto w-full ${wide ? "max-w-wide" : "max-w-content"}`}>
      {children}
    </main>
  );
}
