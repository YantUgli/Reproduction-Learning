import { PageHeader, Button } from "reproduction-learning-engine-frontend";

// Header halaman konsisten: link balik + judul + subjudul + slot aksi.
export function WithSubtitle() {
  return (
    <div style={{ maxWidth: 720 }}>
      <PageHeader
        title="Placement — menemukan lantai"
        subtitle="Tantangan turun dari yang paling jauh di hilir ke yang paling primitif. Sesi berhenti di node pertama yang berhasil kamu produksi."
      />
    </div>
  );
}

export function WithActions() {
  return (
    <div style={{ maxWidth: 720 }}>
      <PageHeader
        title="Library"
        subtitle="Diukur dari yang sudah kamu produksi ulang tanpa AI — bukan yang dibaca."
        actions={<Button variant="secondary">Jalankan placement</Button>}
      />
    </div>
  );
}
