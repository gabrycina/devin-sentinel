/** Tiny dependency-free SVG charts, tuned to the app's restrained aesthetic. */

export function AreaTrend({
  values,
  color,
  height = 96,
}: {
  values: number[];
  color: string;
  height?: number;
}) {
  const W = 520;
  const H = height;
  const pad = 6;
  const pts = values.length ? values : [0, 0];
  const max = Math.max(...pts, 1);
  const stepX = (W - pad * 2) / Math.max(pts.length - 1, 1);
  const x = (i: number) => pad + i * stepX;
  const y = (v: number) => H - pad - (v / max) * (H - pad * 2);

  const line = pts.map((v, i) => `${i === 0 ? "M" : "L"} ${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(" ");
  const area = `${line} L ${x(pts.length - 1).toFixed(1)} ${H - pad} L ${x(0).toFixed(1)} ${H - pad} Z`;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" preserveAspectRatio="none">
      <defs>
        <linearGradient id={`grad-${color.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.22" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#grad-${color.replace("#", "")})`} />
      <path d={line} fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
      {pts.length > 0 && (
        <circle cx={x(pts.length - 1)} cy={y(pts[pts.length - 1])} r={3.2} fill={color} />
      )}
    </svg>
  );
}

export function WorkloadBars({
  rows,
}: {
  rows: { label: string; value: number; total: number; color: string }[];
}) {
  const max = Math.max(...rows.map((r) => r.total), 1);
  return (
    <div className="flex flex-col gap-3">
      {rows.map((r) => (
        <div key={r.label} className="flex items-center gap-3">
          <span className="w-16 text-[12.5px] text-muted-foreground">{r.label}</span>
          <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-muted">
            <div
              className="absolute inset-y-0 left-0 rounded-full"
              style={{ width: `${(r.value / max) * 100}%`, background: r.color, transition: "width .5s cubic-bezier(0.4,0,0.2,1)" }}
            />
          </div>
          <span className="w-6 text-right text-[13px] font-medium tabular-nums">{r.value}</span>
        </div>
      ))}
    </div>
  );
}
