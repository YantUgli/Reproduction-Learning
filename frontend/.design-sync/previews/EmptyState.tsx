import { EmptyState, Button, IconInbox } from "reproduction-learning-engine-frontend";

// Empty state = undangan bertindak, bukan ruang kosong.
export function NothingDue() {
  return (
    <div style={{ maxWidth: 520 }}>
      <EmptyState icon={<IconInbox />} title="Tak ada yang jatuh tempo">
        Ambil node <b>tersedia</b> di bawah, atau jalankan placement kalau belum pernah
        menemukan lantai awal.
      </EmptyState>
    </div>
  );
}

export function WithAction() {
  return (
    <div style={{ maxWidth: 520 }}>
      <EmptyState
        icon={<IconInbox />}
        title="Belum ada course di library"
        action={<Button variant="primary">Mulai course-intake</Button>}
      >
        Mirror sebuah course luar, atau bangun peta belajar bersitasi.
      </EmptyState>
    </div>
  );
}
