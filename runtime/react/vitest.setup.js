import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

/**
 * Bersihkan DOM setelah tiap test.
 *
 * Tanpa ini, render kedua menumpuk di dokumen yang sama dan query seperti
 * `getByRole("button")` gagal karena menemukan DUA tombol — kegagalan yang tak ada
 * hubungannya dengan kemampuan pengarang node. Auto-cleanup bawaan
 * @testing-library/react hanya aktif kalau `globals: true`; kita memilih `globals:
 * false` (import eksplisit di hidden test, lebih mudah dibaca) jadi teardown-nya
 * dipasang di sini — sekali, untuk semua node.
 */
afterEach(() => {
  cleanup();
});
