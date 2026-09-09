"use client";

/**
 * TEMPER LINE — tanda tangan produk (brief §8).
 *
 * Tangga scaffold L3·L2·L1·L0 digambar sebagai gradient dukungan horizontal yang
 * TERLIHAT mendingin: dari ember (L3, worked example yang tersokong penuh) ke baja
 * dingin (L0, verify telanjang). Ia menyandikan sesuatu yang benar — dukungan
 * memudar, hanya ujung dingin yang dihitung.
 *
 * PROOF LAW (§8) di sini: titik = **dilewati**, BUKAN terbukti. Tidak pernah ada
 * centang hijau di temper line; melewati scaffold hanyalah navigasi, tak ada test
 * yang jalan. Centang hijau = "terverifikasi eksekusi", dan itu hidup di panel hasil,
 * bukan di sini.
 */
export default function TemperLine({
  levels,
  activeIndex,
  onSelect,
}: {
  levels: string[];
  activeIndex: number;
  onSelect?: (index: number) => void;
}) {
  return (
    <div className="select-none">
      <div className="relative">
        {/* rel gradient — dukungan yang mendingin L3 → L0 */}
        <div
          aria-hidden="true"
          className="absolute left-3 right-3 top-2 h-[3px] rounded-full"
          style={{ background: "var(--temper-line)" }}
        />
        <ol className="relative flex justify-between">
          {levels.map((lv, i) => {
            const state: DotState =
              i === activeIndex ? "current" : i < activeIndex ? "visited" : "upcoming";
            const warm = i === 0; // ujung hangat (L3)
            const cold = i === levels.length - 1; // ujung dingin (L0)
            const caption =
              state === "current"
                ? "di sini"
                : state === "visited"
                  ? "dilewati"
                  : warm
                    ? "hangat"
                    : cold
                      ? "dingin"
                      : "";

            const dot = <Dot state={state} warm={warm} />;
            return (
              <li
                key={lv}
                className="z-[1] flex flex-col items-center gap-2"
                aria-current={state === "current" ? "step" : undefined}
              >
                {onSelect ? (
                  <button
                    type="button"
                    onClick={() => onSelect(i)}
                    title={
                      state === "current"
                        ? `Kamu di ${lv}`
                        : state === "visited"
                          ? `Kembali ke ${lv}`
                          : `Lompat ke ${lv}`
                    }
                    className="flex items-center justify-center rounded-full p-0.5"
                  >
                    {dot}
                  </button>
                ) : (
                  dot
                )}
                <div className="flex flex-col items-center">
                  <span
                    className={`font-mono text-xs font-semibold ${
                      state === "current"
                        ? warm
                          ? "text-ember"
                          : "text-accent"
                        : "text-subtle"
                    }`}
                  >
                    {lv}
                  </span>
                  {caption && (
                    <span
                      className={`-mt-0.5 font-mono text-[10px] ${
                        state === "current"
                          ? warm
                            ? "text-ember"
                            : "text-accent"
                          : "text-subtle"
                      }`}
                    >
                      {caption}
                    </span>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      </div>
      <div className="mt-3.5 flex items-center justify-between font-mono text-[11.5px] text-subtle">
        <span>temper line · dukungan memudar L3 → L0</span>
        <span>titik = dilewati, bukan terbukti</span>
      </div>
    </div>
  );
}

type DotState = "current" | "visited" | "upcoming";

function Dot({ state, warm }: { state: DotState; warm: boolean }) {
  if (state === "current") {
    // Split-circle "you are here": separuh warna, separuh putih — ring token di luar.
    const color = warm ? "var(--ember)" : "var(--accent)";
    const ring = warm ? "var(--ember-bg)" : "var(--info-bg)";
    return (
      <span
        aria-hidden="true"
        className="h-5 w-5 rounded-full border-[2.5px]"
        style={{
          background: `linear-gradient(90deg, ${color} 0 50%, var(--surface) 50% 100%)`,
          borderColor: color,
          boxShadow: `0 0 0 4px var(--surface), 0 0 0 6px ${ring}`,
        }}
      />
    );
  }
  if (state === "visited") {
    // Titik kecil terisi + border (netral/ember) — dilewati, tanpa centang.
    return (
      <span
        aria-hidden="true"
        className={`h-3.5 w-3.5 rounded-full border-2 bg-neutral-bg ${
          warm ? "border-ember" : "border-subtle"
        }`}
        style={{ boxShadow: "0 0 0 4px var(--surface)" }}
      />
    );
  }
  // upcoming — kosong, putus-putus (ghost, belum disentuh)
  return (
    <span
      aria-hidden="true"
      className="h-3.5 w-3.5 rounded-full border-2 border-dashed border-border bg-surface"
      style={{ boxShadow: "0 0 0 4px var(--surface)" }}
    />
  );
}
