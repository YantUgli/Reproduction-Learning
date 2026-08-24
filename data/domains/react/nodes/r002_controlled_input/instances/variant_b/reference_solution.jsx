import { useState } from "react";

const LIMIT = 20;

export default function MessageBox() {
  const [text, setText] = useState("");

  return (
    <div>
      <input
        aria-label="pesan"
        value={text}
        onChange={(e) => setText(e.target.value.slice(0, LIMIT))}
      />
      <p>Sisa: {LIMIT - text.length}</p>
    </div>
  );
}
