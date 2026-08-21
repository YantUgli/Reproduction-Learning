"use client";

import { useEffect, useState } from "react";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export default function Home() {
  const [status, setStatus] = useState<string>("…memuat");

  useEffect(() => {
    fetch(`${BACKEND_URL}/health`)
      .then((res) => res.json())
      .then((data) => setStatus(data.status ?? "tak dikenal"))
      .catch(() => setStatus("gagal terhubung ke backend"));
  }, []);

  return (
    <main>
      <h1>Reproduction Learning Engine</h1>
      <p>M0 alive.</p>
      <p>
        Status backend: <strong>{status}</strong>
      </p>
    </main>
  );
}
