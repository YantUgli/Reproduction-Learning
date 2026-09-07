import { Badge } from "reproduction-learning-engine-frontend";

// Proof Law: yang DIBUKTIKAN eksekusi tampil solid; yang belum terbukti tampil outline.
export function Solid() {
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
      <Badge tone="neutral">neutral</Badge>
      <Badge tone="info">info</Badge>
      <Badge tone="success">acquired</Badge>
      <Badge tone="warning">mastered</Badge>
      <Badge tone="danger">lapsed</Badge>
      <Badge tone="ember">scaffold</Badge>
    </div>
  );
}

export function Outline() {
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
      <Badge tone="neutral" variant="outline">
        terkunci
      </Badge>
      <Badge tone="info" variant="outline">
        tersedia
      </Badge>
      <Badge tone="ember" variant="outline">
        belum ditempa
      </Badge>
    </div>
  );
}

// Ember = peran identitas baru (brief §8): kehangatan scaffold yang memudar ke L0.
export function Ember() {
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
      <Badge tone="ember">L3 · contoh dikerjakan</Badge>
      <Badge tone="ember" variant="outline">
        dukungan memudar
      </Badge>
    </div>
  );
}
