import { useNavigate } from "react-router-dom";
import { UserCheck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { WORKLOADS, WORKLOAD_ORDER, tint, ACCENT, WARN, type WorkloadKey } from "@/lib/theme";
import { timeAgo } from "@/lib/utils";
import type { Job } from "@/lib/api";

function mostActive(jobs: Job[], key: WorkloadKey): Job | null {
  const active = jobs
    .filter((j) => j.workload === key && ["queued", "dispatched", "running", "needs_attention"].includes(j.status))
    .sort((a, b) => (b.dispatched_at ?? b.created_at) - (a.dispatched_at ?? a.created_at));
  return active[0] ?? null;
}

function stage(job: Job): { title: string; sub?: string; waiting: boolean; pct: number } {
  const d = job.details ?? {};
  if (job.workload === "security") {
    if (job.status === "needs_attention") return { title: "Awaiting review", waiting: true, pct: 90 };
    const title = job.devin_status_detail || (job.status === "running" ? "Running tests" : job.status === "dispatched" ? "Devin dispatched" : "Queued");
    return { title, sub: d.package ? `Fixing ${d.package}` : undefined, waiting: false, pct: job.status === "running" ? 65 : job.status === "dispatched" ? 35 : 10 };
  }
  if (job.workload === "governance") {
    const blocker = (job.policies ?? []).find((p) => p.needs_human_approval && p.status === "needs_approval");
    if (blocker) return { title: "Waiting for approval", sub: blocker.name.replace(/_/g, " "), waiting: true, pct: 90 };
    const title = job.status === "running" || job.status === "dispatched" ? "Drafting artifacts" : "Queued";
    return { title, sub: d.tier ? `Tier ${String(d.tier).replace(/[^0-9]/g, "") || d.tier}` : undefined, waiting: false, pct: 45 };
  }
  // incident
  if (d.suspect_commit && !job.pr_url) return { title: "Preparing rollback", sub: `Commit ${String(d.suspect_commit).slice(0, 8)}`, waiting: false, pct: 75 };
  if (job.status === "needs_attention") return { title: "Awaiting merge", sub: d.service, waiting: true, pct: 90 };
  const title = job.status === "running" ? "Bisecting deploys" : job.status === "dispatched" ? "Devin dispatched" : "Queued";
  return { title, sub: d.service, waiting: false, pct: job.status === "running" ? 55 : 20 };
}

function OperationCard({ workloadKey, job, onSelect }: { workloadKey: WorkloadKey; job: Job | null; onSelect: (j: Job) => void }) {
  const nav = useNavigate();
  const w = WORKLOADS[workloadKey];
  const s = job ? stage(job) : null;

  const accent = s ? (s.waiting ? WARN : ACCENT) : null;
  return (
    <button
      onClick={() => (job ? onSelect(job) : nav(`/w/${workloadKey}`))}
      className="hover-lift flex w-full flex-col gap-2 rounded-lg border px-3.5 py-3 text-left"
      style={{
        borderColor: accent ? tint(accent, 0.35) : "hsl(var(--border))",
        background: accent ? `linear-gradient(135deg, ${tint(accent, 0.1)}, transparent 72%)` : "hsl(var(--card))",
      }}
    >
      <div className="flex items-center gap-2">
        <div className="grid size-6 shrink-0 place-items-center rounded-md" style={{ background: tint(w.hex, 0.14), color: w.hex }}>
          <w.icon className="size-3.5" />
        </div>
        <span className="text-[12px] font-semibold" style={{ color: w.hex }}>{w.label}</span>
        {job && <span className="ml-auto text-[10.5px] tabular-nums text-muted-foreground">{timeAgo(job.dispatched_at)}</span>}
      </div>

      {s ? (
        <>
          <div className="flex items-center gap-1.5">
            {s.waiting && <UserCheck className="size-3.5 shrink-0" style={{ color: WARN }} />}
            <span className="truncate text-[13px] font-medium" style={s.waiting ? { color: WARN } : undefined}>
              {s.title}
            </span>
          </div>
          {s.sub && <div className="truncate text-[11px] text-muted-foreground">{s.sub}</div>}
          <div className="h-1 w-full overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full transition-all" style={{ width: `${s.pct}%`, background: accent ?? ACCENT }} />
          </div>
        </>
      ) : (
        <div className="text-[12px] text-muted-foreground">No active work</div>
      )}
    </button>
  );
}

export function CurrentOperations({ jobs, onSelect }: { jobs: Job[]; onSelect: (j: Job) => void }) {
  return (
    <Card className="p-4">
      <div className="mb-3 flex items-baseline justify-between">
        <span className="section-eyebrow">Current operations</span>
        <span className="text-[11px] text-muted-foreground">live</span>
      </div>
      <div className="flex flex-col gap-2">
        {WORKLOAD_ORDER.map((k) => (
          <OperationCard key={k} workloadKey={k} job={mostActive(jobs, k)} onSelect={onSelect} />
        ))}
      </div>
    </Card>
  );
}
