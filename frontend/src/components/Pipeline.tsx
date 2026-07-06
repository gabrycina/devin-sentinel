import { useCallback, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { WORKLOADS, WORKLOAD_ORDER, EVENT_LABELS, tint } from "@/lib/theme";
import type { Metrics } from "@/lib/api";
import { cn } from "@/lib/utils";

const EVENTS = [
  { id: "security_finding", active: (m: Metrics) => (m.by_workload.security?.total ?? 0) > 0 },
  { id: "dependency_update", active: (m: Metrics) => (m.by_workload.security?.total ?? 0) > 0 },
  { id: "failed_ci", active: () => false },
  { id: "pull_request", active: (m: Metrics) => (m.by_workload.governance?.total ?? 0) > 0 },
  { id: "incident_alert", active: (m: Metrics) => (m.by_workload.incident?.total ?? 0) > 0 },
];

type Path = { d: string; color: string; active: boolean; from: string };

export function Pipeline({ m }: { m: Metrics }) {
  const nav = useNavigate();
  const wrap = useRef<HTMLDivElement>(null);
  const anchors = useRef<Map<string, HTMLElement>>(new Map());
  const [paths, setPaths] = useState<Path[]>([]);
  const [size, setSize] = useState({ w: 0, h: 0 });

  const setAnchor = useCallback((id: string) => (el: HTMLElement | null) => {
    if (el) anchors.current.set(id, el);
    else anchors.current.delete(id);
  }, []);

  const measure = useCallback(() => {
    const box = wrap.current?.getBoundingClientRect();
    const rules = anchors.current.get("rules");
    if (!box || !rules) return;
    setSize({ w: box.width, h: box.height });
    const rr = rules.getBoundingClientRect();
    const rl = { x: rr.left - box.left, y: rr.top - box.top + rr.height / 2 };
    const rrr = { x: rr.right - box.left, y: rr.top - box.top + rr.height / 2 };

    const next: Path[] = [];
    const curve = (ax: number, ay: number, bx: number, by: number) => {
      const dx = Math.max(28, (bx - ax) * 0.5);
      return `M ${ax} ${ay} C ${ax + dx} ${ay}, ${bx - dx} ${by}, ${bx} ${by}`;
    };
    EVENTS.forEach((e) => {
      const el = anchors.current.get(`ev-${e.id}`);
      if (!el) return;
      const r = el.getBoundingClientRect();
      const ax = r.right - box.left;
      const ay = r.top - box.top + r.height / 2;
      next.push({ d: curve(ax, ay, rl.x, rl.y), color: "#94a3b8", active: e.active(m), from: e.id });
    });
    WORKLOAD_ORDER.forEach((k) => {
      const el = anchors.current.get(`wl-${k}`);
      if (!el) return;
      const r = el.getBoundingClientRect();
      const bx = r.left - box.left;
      const by = r.top - box.top + r.height / 2;
      const active = (m.by_workload[k]?.total ?? 0) > 0;
      next.push({ d: curve(rrr.x, rrr.y, bx, by), color: WORKLOADS[k].hex, active, from: `wl-${k}` });
    });
    setPaths(next);
  }, [m]);

  useLayoutEffect(() => {
    measure();
    const ro = new ResizeObserver(measure);
    if (wrap.current) ro.observe(wrap.current);
    window.addEventListener("resize", measure);
    return () => { ro.disconnect(); window.removeEventListener("resize", measure); };
  }, [measure]);

  return (
    <div ref={wrap} className="relative grid grid-cols-[minmax(150px,1fr)_auto_minmax(200px,1.1fr)] items-center gap-x-10 md:gap-x-16">
      <svg className="pointer-events-none absolute inset-0 h-full w-full" width={size.w} height={size.h}>
        {paths.map((p, i) => (
          <g key={i}>
            <path d={p.d} fill="none" stroke={p.color} strokeOpacity={p.active ? 0.55 : 0.18} strokeWidth={1.5} />
            {p.active && (
              <path
                d={p.d}
                fill="none"
                stroke={p.color}
                strokeWidth={1.5}
                strokeDasharray="3 13"
                className="animate-flow-dash"
                strokeLinecap="round"
              />
            )}
          </g>
        ))}
      </svg>

      {/* Events */}
      <div className="relative z-10 flex flex-col gap-2">
        <ColLabel>Events</ColLabel>
        {EVENTS.map((e) => {
          const active = e.active(m);
          return (
            <div
              key={e.id}
              ref={setAnchor(`ev-${e.id}`)}
              className={cn(
                "flex items-center gap-2 rounded-md border bg-card px-2.5 py-1.5 text-[12.5px] shadow-xs transition-colors",
                active ? "border-border text-foreground" : "border-dashed border-border/70 text-muted-foreground"
              )}
            >
              <span
                className={cn("size-1.5 rounded-full", active && "animate-pulse-dot")}
                style={{ background: active ? "#059669" : "#cbd5e1" }}
              />
              {EVENT_LABELS[e.id]}
            </div>
          );
        })}
      </div>

      {/* Rules engine */}
      <div className="relative z-10 flex flex-col items-center">
        <ColLabel>Rules engine</ColLabel>
        <button
          ref={setAnchor("rules") as any}
          onClick={() => nav("/rules")}
          className="group w-[168px] rounded-xl border border-primary/25 bg-primary/[0.04] px-4 py-4 text-center shadow-sm transition-all hover:border-primary/40 hover:shadow-md"
        >
          <div className="mx-auto mb-2 grid size-8 place-items-center rounded-lg bg-primary/10 text-primary">
            <SlidersIcon />
          </div>
          <div className="text-[13px] font-semibold">Policy engine</div>
          <div className="mt-0.5 text-[11px] leading-tight text-muted-foreground">
            classify · require · dispatch
          </div>
          <div className="mt-2 inline-flex items-center gap-1 text-[11px] font-medium text-primary opacity-0 transition-opacity group-hover:opacity-100">
            configure <ArrowRight className="size-3" />
          </div>
        </button>
      </div>

      {/* Workloads */}
      <div className="relative z-10 flex flex-col gap-2.5">
        <ColLabel>Workloads</ColLabel>
        {WORKLOAD_ORDER.map((k) => {
          const w = WORKLOADS[k];
          const wm = m.by_workload[k] ?? { total: 0, delivered: 0, running: 0 };
          const Icon = w.icon;
          return (
            <button
              key={k}
              ref={setAnchor(`wl-${k}`) as any}
              onClick={() => nav(`/w/${k}`)}
              className="group flex items-center gap-3 rounded-lg border border-border bg-card px-3 py-2.5 text-left shadow-xs transition-all hover:shadow-md"
              style={{ borderColor: wm.total ? tint(w.hex, 0.35) : undefined }}
            >
              <div className="grid size-8 place-items-center rounded-lg" style={{ background: tint(w.hex, 0.12), color: w.hex }}>
                <Icon className="size-[17px]" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-[13.5px] font-semibold">{w.label}</div>
                <div className="truncate text-[11px] text-muted-foreground">{w.tagline}</div>
              </div>
              <div className="text-right">
                <div className="text-[15px] font-semibold tabular-nums leading-none">{wm.total}</div>
                {wm.running > 0 && (
                  <div className="mt-1 flex items-center justify-end gap-1 text-[10.5px]" style={{ color: w.hex }}>
                    <span className="size-1.5 animate-pulse-dot rounded-full" style={{ background: w.hex }} />
                    {wm.running} live
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

const ColLabel = ({ children }: { children: ReactNode }) => (
  <div className="mb-1.5 text-[10.5px] font-medium uppercase tracking-wider text-muted-foreground/70">
    {children}
  </div>
);

const SlidersIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <line x1="4" y1="21" x2="4" y2="14" /><line x1="4" y1="10" x2="4" y2="3" />
    <line x1="12" y1="21" x2="12" y2="12" /><line x1="12" y1="8" x2="12" y2="3" />
    <line x1="20" y1="21" x2="20" y2="16" /><line x1="20" y1="12" x2="20" y2="3" />
    <line x1="1" y1="14" x2="7" y2="14" /><line x1="9" y1="8" x2="15" y2="8" /><line x1="17" y1="16" x2="23" y2="16" />
  </svg>
);
