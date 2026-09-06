"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  api,
  type LibraryCourse,
  type LibraryMaterial,
  type LibraryProgress,
} from "../../lib/api";
import Badge, { type BadgeTone } from "../components/ui/Badge";
import Card from "../components/ui/Card";
import Container from "../components/ui/Container";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import PageHeader from "../components/ui/PageHeader";
import { IconArrowRight, IconInbox } from "../components/ui/Icon";

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
          <Card className="p-4">
            <div className="text-xs font-medium uppercase tracking-wide text-muted">
              materi direproduksi
            </div>
            <div className="mt-0.5 text-3xl font-bold leading-tight tabular-nums">
              {pct(data.reproduced_pct, data.reproduced, data.total)}
            </div>
            <div className="mt-0.5 text-xs text-muted tabular-nums">
              {data.reproduced}/{data.total} materi terbukti tanpa AI
            </div>
          </Card>

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

function CourseSection({ course }: { course: LibraryCourse }) {
  const width = Math.min(100, Math.round((course.reproduced_pct ?? 0) * 100));
  return (
    <section>
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2 className="text-lg font-semibold">{course.title}</h2>
        <span className="text-sm text-muted tabular-nums">
          {course.reproduced}/{course.total} direproduksi · {course.unmapped} belum
          tertempa
        </span>
      </div>

      {/* Bar = proporsi materi yang TERBUKTI. Materi tanpa node ikut penyebut, jadi
          lubangnya terlihat sebagai ruang kosong — itu memang maksudnya. */}
      <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-neutral-bg">
        <div className="h-full bg-success" style={{ width: `${width}%` }} />
      </div>

      <div className="mt-3 space-y-4">
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

const STATE_LABEL: Record<LibraryMaterial["state"], { text: string; tone: BadgeTone }> = {
  unmapped: { text: "belum tertempa", tone: "neutral" },
  mapped_unproven: { text: "tertempa, belum dibuktikan", tone: "warning" },
  reproduced: { text: "direproduksi", tone: "success" },
};

function MaterialRow({ material }: { material: LibraryMaterial }) {
  const label = STATE_LABEL[material.state];
  return (
    <Card className="flex flex-wrap items-center justify-between gap-2 p-3">
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
      <div className="flex flex-wrap items-center gap-2">
        {/* Label catatan — netral, tak pernah diakumulasi (KUNCI 8). */}
        <span className="text-xs text-subtle">catatan: {material.note_status || "—"}</span>
        {material.decayed && <Badge tone="warning">meluruh</Badge>}
        {material.mastered && <Badge tone="info">dikuasai</Badge>}
        <Badge tone={label.tone}>{label.text}</Badge>
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
