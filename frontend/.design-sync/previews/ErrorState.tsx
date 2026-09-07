import { ErrorState } from "reproduction-learning-engine-frontend";

// Error yang bisa ditindaklanjuti — mendeteksi backend mati (kasus dev paling umum).
export function BackendDown() {
  return (
    <div style={{ maxWidth: 560 }}>
      <ErrorState error="TypeError: Failed to fetch" onRetry={() => {}} />
    </div>
  );
}

export function GenericError() {
  return (
    <div style={{ maxWidth: 560 }}>
      <ErrorState error="500: node n042 tidak ditemukan di jadwal" onRetry={() => {}} />
    </div>
  );
}
