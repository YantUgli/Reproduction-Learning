import { useState } from "react";

export default function GuestList() {
  const [name, setName] = useState("");
  const [guests, setGuests] = useState([]);

  function invite() {
    const trimmed = name.trim();
    setName("");
    if (trimmed === "" || guests.includes(trimmed)) return;
    setGuests([...guests, trimmed]);
  }

  return (
    <div>
      <input aria-label="tamu" value={name} onChange={(e) => setName(e.target.value)} />
      <button onClick={invite}>Undang</button>
      {guests.length === 0 ? (
        <p>Daftar tamu kosong</p>
      ) : (
        <ul>
          {guests.map((guest) => (
            <li key={guest}>{guest}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
