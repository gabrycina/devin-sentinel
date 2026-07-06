import { useMemo, useState } from "react";
import { useParams, Navigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { JobTable } from "@/components/JobTable";
import { JobDrawer } from "@/components/JobDrawer";
import { Skeleton } from "@/components/ui/skeleton";
import { usePoll, type Job } from "@/lib/api";
import { WORKLOADS, tint, type WorkloadKey } from "@/lib/theme";

const STATUS_FILTERS = [
  { key: "all", label: "All" },
  { key: "active", label: "In progress" },
  { key: "delivered", label: "Delivered" },
  { key: "failed", label: "Failed" },
];

export function Workload() {
  const { key } = useParams<{ key: WorkloadKey }>();
  const { data: jobs } = usePoll<Job[]>("/api/jobs", 5000);
  const [selected, setSelected] = useState<Job | null>(null);
  const [filter, setFilter] = useState("all");

  if (!key || !WORKLOADS[key]) return <Navigate to="/" replace />;
  const w = WORKLOADS[key];
  const Icon = w.icon;

  const mine = useMemo(() => (jobs ?? []).filter((j) => j.workload === key), [jobs, key]);
  const filtered = useMemo(() => {
    if (filter === "active") return mine.filter((j) => ["queued", "dispatched", "running"].includes(j.status));
    if (filter === "delivered") return mine.filter((j) => ["succeeded", "pr_open", "needs_attention"].includes(j.status) || j.pr_url);
    if (filter === "failed") return mine.filter((j) => j.status === "failed");
    return mine;
  }, [mine, filter]);

  const delivered = mine.filter((j) => ["succeeded", "pr_open", "needs_attention"].includes(j.status) || j.pr_url).length;
  const running = mine.filter((j) => ["queued", "dispatched", "running"].includes(j.status)).length;
  const hours = mine.filter((j) => j.pr_url || ["succeeded", "pr_open", "needs_attention"].includes(j.status))
    .reduce((s, j) => s + j.eng_minutes_saved, 0) / 60;

  return (
    <div className="space-y-6">
      <header className="flex items-start gap-4">
        <div className="grid size-11 place-items-center rounded-xl" style={{ background: tint(w.hex, 0.12), color: w.hex }}>
          <Icon className="size-6" />
        </div>
        <div className="flex-1">
          <h1 className="text-[22px] font-semibold tracking-tight">{w.label}</h1>
          <p className="mt-0.5 text-[14px] text-muted-foreground">{w.tagline}</p>
        </div>
        <div className="flex gap-6 pt-1">
          <HeaderStat label="Total" value={mine.length} />
          <HeaderStat label="Delivered" value={delivered} color="#059669" />
          <HeaderStat label="In progress" value={running} color={running ? w.hex : undefined} />
          <HeaderStat label="Eng. saved" value={`${hours.toFixed(1)}h`} />
        </div>
      </header>

      <Card className="overflow-hidden">
        <div className="flex items-center gap-1 border-b border-border px-3 py-2">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={
                "rounded-md px-2.5 py-1 text-[12.5px] font-medium transition-colors " +
                (filter === f.key ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground")
              }
            >
              {f.label}
            </button>
          ))}
        </div>
        {!jobs ? (
          <div className="space-y-2 p-4">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-12" />)}</div>
        ) : (
          <JobTable jobs={filtered} onSelect={setSelected} showWorkload={false} />
        )}
      </Card>

      <JobDrawer job={selected} onClose={() => setSelected(null)} />
    </div>
  );
}

const HeaderStat = ({ label, value, color }: { label: string; value: string | number; color?: string }) => (
  <div className="text-right">
    <div className="text-[10.5px] uppercase tracking-wide text-muted-foreground">{label}</div>
    <div className="mt-0.5 text-[18px] font-semibold tabular-nums" style={color ? { color } : undefined}>
      {value}
    </div>
  </div>
);
