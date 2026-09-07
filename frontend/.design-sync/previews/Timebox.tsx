import { Timebox } from "reproduction-learning-engine-frontend";

// Hitung mundur timebox (batas waktu BERPIKIR di L0). Slot lebar tetap (tak menggeser
// layout). running=false di preview → deterministik, tak berdetak/memicu onExpire.
export function Tones() {
  return (
    <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
      <Timebox seconds={1200} running={false} onExpire={() => {}} />
      <Timebox seconds={90} running={false} onExpire={() => {}} />
      <Timebox seconds={20} running={false} onExpire={() => {}} />
    </div>
  );
}
