import { Button, IconArrowRight } from "reproduction-learning-engine-frontend";

// Satu aksi primer per layar — di produk ini "Jalankan & Verifikasi".
export function Variants() {
  return (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
      <Button variant="primary">Jalankan &amp; Verifikasi</Button>
      <Button variant="secondary">Coba lagi</Button>
      <Button variant="ghost">Library</Button>
      <Button variant="danger">Tolak</Button>
    </div>
  );
}

export function Sizes() {
  return (
    <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
      <Button variant="primary" size="sm">
        Kecil
      </Button>
      <Button variant="primary" size="md">
        Sedang
      </Button>
    </div>
  );
}

export function LoadingAndDisabled() {
  return (
    <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
      <Button variant="primary" loading>
        Menjalankan…
      </Button>
      <Button variant="secondary" disabled>
        Nonaktif
      </Button>
    </div>
  );
}

export function WithIcon() {
  return (
    <Button variant="primary">
      Lanjut (pudarkan scaffold) <IconArrowRight size={15} />
    </Button>
  );
}
