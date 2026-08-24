import { useState } from "react";

export default function TodoList() {
  const [text, setText] = useState("");
  const [items, setItems] = useState([]);

  function add() {
    const trimmed = text.trim();
    if (trimmed === "") return;
    setItems([...items, trimmed]);
    setText("");
  }

  return (
    <div>
      <input aria-label="tugas" value={text} onChange={(e) => setText(e.target.value)} />
      <button onClick={add}>Tambah</button>
      {items.length === 0 ? (
        <p>Belum ada tugas</p>
      ) : (
        <ul>
          {items.map((item, i) => (
            <li key={`${item}-${i}`}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
