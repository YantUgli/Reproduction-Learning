import { useState } from "react";

export default function Stock() {
  const [stock, setStock] = useState(10);

  return (
    <div>
      <p>Stok: {stock}</p>
      <button onClick={() => setStock((s) => Math.max(0, s - 1))}>Ambil</button>
      <button onClick={() => setStock(10)}>Isi ulang</button>
    </div>
  );
}
