import { Container, Card } from "reproduction-learning-engine-frontend";

// Lebar baca konsisten: 820px (default) atau 980px (wide, halaman authoring).
export function Default() {
  return (
    <div style={{ background: "var(--canvas)", padding: 16 }}>
      <Container>
        <Card className="p-4">
          <div style={{ fontWeight: 600 }}>Lebar konten (820px)</div>
          <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 4 }}>
            Membungkus konten sesi node & review agar baris teks tak terlalu lebar.
          </div>
        </Card>
      </Container>
    </div>
  );
}
