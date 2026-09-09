"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  api,
  type LibraryCourse,
  type LibraryMaterial,
  type LibraryProgress,
} from "../../lib/api";
import Badge, { type BadgeTone, type BadgeVariant } from "../components/ui/Badge";
import Card from "../components/ui/Card";
import Container from "../components/ui/Container";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import PageHeader from "../components/ui/PageHeader";
import { IconArrowRight, IconCheck, IconInbox } from "../components/ui/Icon";

// Hatch "mapped · unproven" (§7.5): dukungan yang dipetakan tapi BELUM terbukti — dirender
// bergaris (bukan solid), Proof Law: hanya yang terbukti eksekusi yang solid. Token-based.
const HATCH =
  "repeating-linear-gradient(45deg, var(--neutral-bg) 0 4px, var(--surface) 4px 8px)";

/**
 * Halaman lajur Library (L5) — PENJAGA metrik, bukan katalog bacaan.
 *
 * Yang ditampilkan: berapa banyak materi yang sudah kamu PRODUKSI ULANG tanpa AI.
 * Yang sengaja TIDAK ditampilkan: persentase catatan yang sudah diisi. `note_status`
 * muncul hanya sebagai label netral per materi — tak pernah diakumulasi, tak pernah
 * jadi progress bar. Begitu "sudah dibaca" bisa naik jadi angka, lajur ini berubah
 * jadi consumption comfort yang §8 tolak.
 */
export default function LibraryPage() {
  const [data, setData] = useState<LibraryProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    api
      .getLibraryProgress()
      .then(setData)
      .catch((e) => setError(String(e)));
  };
  useEffect(load, []);

  return (
    <Container>
      <PageHeader
        back={null}
        title="Library"
        subtitle={
          <>
            Diukur dari{" "}
            <strong className="font-semibold text-fg">
              yang sudah kamu produksi ulang tanpa AI
            </strong>{" "}
            — bukan dari yang sudah dibaca atau dicatat. Course tampil berlubang sampai
            node-nya tertempa dan terbukti.
          </>
        }
      />

      {error && <ErrorState error={error} onRetry={load} />}

      {data && data.courses.length === 0 && (
        <EmptyState icon={<IconInbox />} title="Belum ada course di library/">
          Mulai dari skill <code className="font-mono">course-intake</code> (mirror course
          luar) atau <code className="font-mono">learn-intake</code> (peta belajar).
        </EmptyState>
      )}

      {data && data.courses.length > 0 && (
        <>
          <Card className="p-5">
            <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
              <div>
                <div className="font-mono text-[11px] font-semibold uppercase tracking-wide text-muted">
                  direproduksi
                </div>
                <div className="mt-1 flex items-baseline gap-2">
                  {/* Proof Law (§8): angka ini = yang TERBUKTI eksekusi → proof-green. */}
                  <span className="font-mono text-5xl font-bold leading-none tabular-nums text-success">
                    {pct(data.reproduced_pct, data.reproduced, data.total)}
                  </span>
                  <span className="inline-flex items-center gap-1.5 font-mono text-[11px] font-semibold text-success">
                    <span className="h-2 w-2 rounded-sm bg-success" aria-hidden="true" />
                    terbukti eksekusi
                  </span>
                </div>
              </div>
              <div className="min-w-[240px] flex-1">
                <p className="text-13 text-muted">
                  Menghitung hanya node yang terbukti di L0 — tak pernah materi yang kamu baca.
                  Ia <strong className="font-semibold text-fg">tak bisa 100%</strong> sampai
                  setiap node terpetakan terbukti; persen terakhir dihasilkan, bukan dibulatkan.
                </p>
                <div className="mt-2.5 inline-flex items-center gap-1.5 rounded-md border border-dashed border-border px-2.5 py-1 font-mono text-[11px] text-subtle tabular-nums">
                  ceiling 99% · {data.reproduced}/{data.total} terbukti
                </div>
              </div>
            </div>
          </Card>

          <BarLegend />

          <div className="mt-6 space-y-8">
            {data.courses.map((c) => (
              <CourseSection key={c.course} course={c} />
            ))}
          </div>
        </>
      )}
    </Container>
  );
}

/**
 * Pembulatan bisa berbohong: `Math.round(0.996)` = 100% padahal masih ada materi yang
 * belum terbukti — dan angka itulah yang paling ingin dipercaya. Selama `done < total`
 * hasilnya dibatasi 99%; selama masih ada yang terbukti hasilnya tak pernah 0%. Nilai
 * x/y selalu ditampilkan di sebelahnya.
 */
function pct(v: number | null, done?: number, total?: number): string {
  if (v === null) return "—";
  let p = Math.round(v * 100);
  if (done !== undefined && total !== undefined) {
    if (done < total && p >= 100) p = 99;
    if (done > 0 && p <= 0) p = 1;
  }
  return `${p}%`;
}

/** Legenda bar (§7.5): tiga keadaan, tiga bentuk berbeda — proven solid, unproven
 *  bergaris, unmapped lubang putus-putus. */
function BarLegend() {
  return (
    <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-13 text-muted">
      <span className="font-mono text-[11px] font-semibold uppercase tracking-wide text-subtle">
        legenda bar
      </span>
      <span className="inline-flex items-center gap-2">
        <span className="h-2.5 w-6 rounded-sm bg-success" aria-hidden="true" />
        direproduksi
      </span>
      <span className="inline-flex items-center gap-2">
        <span className="h-2.5 w-6 rounded-sm" style={{ background: HATCH }} aria-hidden="true" />
        tertempa · belum dibuktikan
      </span>
      <span className="inline-flex items-center gap-2">
        <span
          className="h-2.5 w-6 rounded-sm border border-dashed border-subtle bg-surface"
          aria-hidden="true"
        />
        belum tertempa — lubangnya
      </span>
    </div>
  );
}

function CourseSection({ course }: { course: LibraryCourse }) {
  const seg = (n: number) => (course.total > 0 ? (n / course.total) * 100 : 0);
  const repW = seg(course.reproduced);
  const mapW = seg(course.mapped_unproven);
  const unmapW = seg(course.unmapped);
  return (
    <section>
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2 className="text-lg font-semibold">{course.title}</h2>
        <span className="font-mono text-13 text-muted tabular-nums">
          {course.reproduced}/{course.total} direproduksi · {course.unmapped} belum
          tertempa
        </span>
      </div>

      {/* Bar TIGA segmen (§7.5): terbukti (solid green) · tertempa-belum-terbukti
          (bergaris — Proof Law: bukan solid) · belum-tertempa (LUBANG putus-putus, "the
          hole is the point"). Materi tanpa node ikut penyebut, jadi lubangnya nyata. */}
      <div className="mt-2 flex h-3 w-full overflow-hidden rounded-full border border-border-muted bg-surface-muted">
        {repW > 0 && <div className="h-full bg-success" style={{ width: `${repW}%` }} />}
        {mapW > 0 && (
          <div className="h-full" style={{ width: `${mapW}%`, background: HATCH }} />
        )}
        {unmapW > 0 && (
          <div
            className="h-full border-l border-dashed border-subtle"
            style={{ width: `${unmapW}%` }}
          />
        )}
      </div>
      <div className="mt-1.5 font-mono text-[11px] text-subtle tabular-nums">
        {Math.round(repW)}% direproduksi · {Math.round(mapW)}% tertempa-belum-terbukti ·{" "}
        {Math.round(unmapW)}% belum tertempa (lubang yang terlihat, bukan bug)
      </div>

      <div className="mt-4 space-y-4">
        {course.modules.map((m) => (
          <div key={m.module}>
            <h3 className="text-sm font-semibold text-muted">{m.title}</h3>
            <ul className="mt-2 space-y-2">
              {m.materials.map((mat) => (
                <li key={mat.path}>
                  <MaterialRow material={mat} />
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

// Proof Law (§8): hanya yang TERBUKTI eksekusi (`reproduced`) tampil solid; yang belum
// terbukti (unmapped/mapped_unproven) tampil outline/ghost — sejajar StatusBadge.
const STATE_LABEL: Record<
  LibraryMaterial["state"],
  { text: string; tone: BadgeTone; variant: BadgeVariant }
> = {
  unmapped: { text: "belum tertempa", tone: "neutral", variant: "outline" },
  mapped_unproven: { text: "tertempa, belum dibuktikan", tone: "warning", variant: "outline" },
  reproduced: { text: "direproduksi", tone: "success", variant: "solid" },
};

/** Penanda status (§7.5 / Proof Law): hanya `reproduced` yang dapat lingkaran terisi +
 *  centang (terbukti eksekusi). `mapped_unproven` = lingkaran putus-putus; `unmapped` =
 *  kotak putus-putus. Centang HANYA milik yang dibuktikan kode. */
function StateMarker({ state }: { state: LibraryMaterial["state"] }) {
  if (state === "reproduced") {
    return (
      <span
        aria-hidden="true"
        className="flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-full bg-success text-accent-fg"
      >
        <IconCheck size={11} />
      </span>
    );
  }
  if (state === "mapped_unproven") {
    return (
      <span
        aria-hidden="true"
        className="h-4 w-4 shrink-0 rounded-full border-2 border-dashed border-subtle bg-surface"
      />
    );
  }
  return (
    <span
      aria-hidden="true"
      className="h-4 w-4 shrink-0 rounded-[3px] border border-dashed border-subtle bg-surface"
    />
  );
}

function MaterialRow({ material }: { material: LibraryMaterial }) {
  const label = STATE_LABEL[material.state];
  return (
    <Card className="flex flex-wrap items-center justify-between gap-2 p-3">
      <div className="flex min-w-0 items-center gap-3">
        <StateMarker state={material.state} />
        <div className="min-w-0">
          <div className="truncate font-medium">{material.title}</div>
          <div className="mt-0.5 truncate font-mono text-xs text-subtle">
            {material.node_ids.length > 0 ? material.node_ids.join(" · ") : "belum ada node"}
            {material.missing_node_ids.length > 0 && (
              <span className="text-danger">
                {" "}
                · node hilang: {material.missing_node_ids.join(", ")}
              </span>
            )}
          </div>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {/* Label catatan — netral, tak pernah diakumulasi (KUNCI 8). */}
        <span className="text-xs text-subtle">catatan: {material.note_status || "—"}</span>
        {material.decayed && <Badge tone="warning">meluruh</Badge>}
        {material.mastered && <Badge tone="info">dikuasai</Badge>}
        <Badge tone={label.tone} variant={label.variant}>
          {label.text}
        </Badge>
        {material.node_ids.length > 0 && material.missing_node_ids.length === 0 && (
          <Link
            href={`/node/${material.node_ids[0]}`}
            className="inline-flex items-center gap-1 text-sm text-accent hover:underline"
          >
            Buka node <IconArrowRight size={14} />
          </Link>
        )}
      </div>
    </Card>
  );
}
