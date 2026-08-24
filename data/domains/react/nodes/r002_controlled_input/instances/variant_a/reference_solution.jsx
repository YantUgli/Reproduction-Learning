import { useState } from "react";

export default function Greeter() {
  const [name, setName] = useState("");

  return (
    <div>
      <input aria-label="nama" value={name} onChange={(e) => setName(e.target.value)} />
      <p>Halo, {name === "" ? "tamu" : name}!</p>
    </div>
  );
}
