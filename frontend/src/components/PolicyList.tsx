import { POLICY } from "@/lib/theme";
import type { Policy } from "@/lib/api";
import { tint } from "@/lib/theme";

export function PolicyList({ policies, compact = false }: { policies: Policy[]; compact?: boolean }) {
  if (!policies?.length) return null;
  if (compact) {
    return (
      <div className="flex flex-wrap gap-1.5">
        {policies.map((p) => {
          const s = POLICY[p.status] ?? POLICY.pending;
          return (
            <span
              key={p.name}
              className="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px]"
              style={{ color: s.hex, borderColor: tint(s.hex, 0.28) }}
              title={s.label}
            >
              <span style={{ color: s.hex }}>{s.glyph}</span>
              {p.name.replace(/_/g, " ")}
            </span>
          );
        })}
      </div>
    );
  }
  return (
    <div className="flex flex-col divide-y divide-border rounded-lg border border-border">
      {policies.map((p) => {
        const s = POLICY[p.status] ?? POLICY.pending;
        return (
          <div key={p.name} className="flex items-start gap-3 px-3.5 py-2.5">
            <span
              className="mt-0.5 grid size-5 shrink-0 place-items-center rounded-full text-[12px]"
              style={{ color: s.hex, background: tint(s.hex, 0.12) }}
            >
              {s.glyph}
            </span>
            <div className="min-w-0 flex-1">
              <div className="text-[13px] font-medium capitalize">{p.name.replace(/_/g, " ")}</div>
              {p.description && <div className="text-[12px] text-muted-foreground">{p.description}</div>}
            </div>
            <span className="shrink-0 text-[11px] font-medium" style={{ color: s.hex }}>
              {s.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
