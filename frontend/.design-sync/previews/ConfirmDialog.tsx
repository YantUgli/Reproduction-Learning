import { ConfirmDialog } from "reproduction-learning-engine-frontend";

// Pengganti window.confirm — presentasional, bertema, aksesibel. Overlay: dirender
// dalam keadaan terbuka (cardMode single).
export function Danger() {
  return (
    <ConfirmDialog
      open
      title="Kode belum dijalankan"
      description="Kode yang kamu tulis di editor belum dijalankan dan akan hilang saat pindah level. Tetap pindah?"
      confirmLabel="Pindah, buang kode"
      cancelLabel="Tetap di sini"
      tone="danger"
      onConfirm={() => {}}
      onCancel={() => {}}
    />
  );
}
