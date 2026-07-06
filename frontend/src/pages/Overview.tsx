import { useState } from "react";
import { CurrentOperations } from "@/components/CurrentOperations";
import { DecisionFeed } from "@/components/DecisionFeed";
import { JobTable } from "@/components/JobTable";
import { JobDrawer } from "@/components/JobDrawer";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { tint, ACCENT, WARN } from "@/lib/theme";
import { usePoll, type Metrics, type Job } from "@/lib/api";

const isDelivered = (j: Job) =>
  !!j.pr_url || ["succeeded", "pr_open", "needs_attention"].includes(j.status);

function duration(mins: number): string {
  if (!mins || mins <= 0) return "—";
  if (mins < 60) return `${Math.round(mins)}m`;
  return `${(mins / 60).toFixed(1)}h`;
}

function avgMinutes(jobs: Job[], from: (j: Job) => number | null, to: (j: Job) => number | null): number {
  const durations = jobs.map((j) => {
    const a = from(j);
    const b = to(j);
    return a && b && b > a ? (b - a) / 60 : null;
  }).filter((n): n is number => n != null);
  if (!durations.length) return 0;
  return durations.reduce((s, n) => s + n, 0) / durations.length;
}

function Kpi({ value, label, accent }: { value: string; label: string; accent?: string }) {
  return (
    <div className="rounded-lg border border-border bg-card px-4 py-3.5 shadow-xs">
      <div
        className="text-[21px] font-semibold leading-none tabular-nums tracking-tight"
        style={accent ? { color: accent } : undefined}
      >
        {value}
      </div>
      <div className="section-eyebrow mt-2 text-[10.5px]">{label}</div>
    </div>
  );
}

export function Overview() {
  const { data: m } = usePoll<Metrics>("/api/metrics", 5000);
  const { data: jobs } = usePoll<Job[]>("/api/jobs", 5000);
  const [selected, setSelected] = useState<Job | null>(null);

  if (!m || !jobs) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full" />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">{[0, 1].map((i) => <Skeleton key={i} className="h-56" />)}</div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const needsAttention = jobs.filter((j) => j.status === "needs_attention").length;
  const now = Date.now() / 1000;

  const queue = [...jobs].sort((a, b) => (b.completed_at ?? b.dispatched_at ?? b.created_at) - (a.completed_at ?? a.dispatched_at ?? a.created_at));

  const security = jobs.filter((j) => j.workload === "security");
  const incidents = jobs.filter((j) => j.workload === "incident");
  const waitingJobs = jobs.filter((j) => j.status === "needs_attention");

  const criticalClosed = security.filter((j) => j.severity === "critical" && isDelivered(j)).length;
  const meanRemediation = duration(avgMinutes(security.filter(isDelivered), (j) => j.created_at, (j) => j.completed_at));
  const policyTotal = m.policies_auto + m.policies_need_approval + m.policies_pending;
  const policyCompliance = policyTotal > 0 ? Math.round((m.policies_auto / policyTotal) * 100) : 100;
  const waitingOnApproval = duration(avgMinutes(waitingJobs, (j) => j.dispatched_at ?? j.created_at, () => now));
  const rollbackTime = duration(avgMinutes(incidents.filter(isDelivered), (j) => j.created_at, (j) => j.completed_at));

  const healthy = needsAttention === 0;
  const heroColor = healthy ? ACCENT : WARN;

  return (
    <div className="space-y-6">
      <header className="animate-fade-up">
        <h1 className="text-[24px] font-semibold tracking-tight">Engineering control plane</h1>
        <p className="mt-1 text-[13px] text-muted-foreground">
          Autonomous security, governance &amp; incident response — one control plane.
        </p>
      </header>

      <section className="grid animate-fade-up grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4" style={{ animationDelay: "40ms" }}>
        <div
          className="col-span-2 flex flex-col justify-between rounded-xl border p-5 shadow-sm"
          style={{ borderColor: tint(heroColor, 0.35), background: `linear-gradient(150deg, ${tint(heroColor, 0.1)}, ${tint(heroColor, 0.03)})` }}
        >
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full" style={{ background: heroColor }} />
            <span className="text-[12.5px] font-semibold" style={{ color: heroColor }}>
              {healthy ? "All systems operational" : `${needsAttention} item${needsAttention > 1 ? "s" : ""} need${needsAttention === 1 ? "s" : ""} your review`}
            </span>
          </div>
          <div className="mt-4">
            <div className="text-[46px] font-semibold leading-none tabular-nums tracking-tight" style={{ color: heroColor }}>
              {Math.round(m.success_rate)}%
            </div>
            <div className="mt-2 text-[12.5px] text-muted-foreground">
              Autonomous success rate across {jobs.length} job{jobs.length === 1 ? "" : "s"}
            </div>
          </div>
        </div>

        <Kpi value={String(criticalClosed)} label="Critical vulns closed" />
        <Kpi value={String(m.prs_produced)} label="PRs generated" accent={m.prs_produced > 0 ? ACCENT : undefined} />
        <Kpi value={meanRemediation} label="Mean remediation" />
        <Kpi value={`${policyCompliance}%`} label="Policy compliance" />
        <Kpi value={String(waitingJobs.length)} label="Human interventions" accent={waitingJobs.length > 0 ? WARN : undefined} />
        <Kpi value={waitingOnApproval} label="Waiting on approval" accent={waitingJobs.length > 0 ? WARN : undefined} />
        <Kpi value={rollbackTime} label="Rollback time" />
      </section>

      <section className="grid animate-fade-up grid-cols-1 gap-4 lg:grid-cols-2" style={{ animationDelay: "80ms" }}>
        <CurrentOperations jobs={jobs} onSelect={setSelected} />
        <DecisionFeed jobs={jobs} onSelect={setSelected} />
      </section>

      <Card className="animate-fade-up overflow-hidden p-0" style={{ animationDelay: "120ms" }}>
        <div className="flex items-center justify-between border-b border-border bg-subtle px-5 py-3">
          <span className="section-eyebrow">Engineering work queue</span>
          <span className="text-[11px] font-medium tabular-nums text-muted-foreground">{jobs.length} total</span>
        </div>
        <JobTable jobs={queue.slice(0, 12)} onSelect={setSelected} />
      </Card>

      <JobDrawer job={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
