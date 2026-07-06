import { useState } from "react";
import { CurrentOperations } from "@/components/CurrentOperations";
import { DecisionFeed } from "@/components/DecisionFeed";
import { JobTable } from "@/components/JobTable";
import { JobDrawer } from "@/components/JobDrawer";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
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

function SecondaryKpi({ value, label }: { value: string; label: string }) {
  return (
    <div className="border-l border-border pl-5">
      <div className="text-[20px] font-semibold leading-none tabular-nums tracking-tight">{value}</div>
      <div className="mt-1 text-[11.5px] text-muted-foreground">{label}</div>
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

  return (
    <div className="space-y-6">
      <header className="animate-fade-up">
        <h1 className="text-[22px] font-semibold tracking-tight">Engineering control plane</h1>
        <p className="mt-1 text-[13.5px] font-medium" style={{ color: needsAttention > 0 ? "#d97706" : "#059669" }}>
          {needsAttention > 0 ? `${needsAttention} item${needsAttention > 1 ? "s" : ""} need your review` : "All systems operational"}
        </p>

        <div className="mt-5 flex flex-wrap items-end gap-x-8 gap-y-4">
          <div>
            <div className="text-[42px] font-semibold leading-none tabular-nums tracking-tight">{Math.round(m.success_rate)}%</div>
            <div className="mt-1.5 text-[12.5px] text-muted-foreground">Autonomous success rate</div>
          </div>
          <div className="flex flex-wrap items-end gap-x-6 gap-y-4">
            <SecondaryKpi value={String(criticalClosed)} label="Critical vulns closed" />
            <SecondaryKpi value={String(m.prs_produced)} label="PRs generated" />
            <SecondaryKpi value={meanRemediation} label="Mean remediation time" />
            <SecondaryKpi value={`${policyCompliance}%`} label="Policy compliance" />
            <SecondaryKpi value={String(waitingJobs.length)} label="Human interventions" />
            <SecondaryKpi value={waitingOnApproval} label="Time waiting on approval" />
            <SecondaryKpi value={rollbackTime} label="Deployment rollback time" />
          </div>
        </div>
      </header>

      <section className="grid animate-fade-up grid-cols-1 gap-4 lg:grid-cols-2" style={{ animationDelay: "60ms" }}>
        <CurrentOperations jobs={jobs} onSelect={setSelected} />
        <DecisionFeed jobs={jobs} onSelect={setSelected} />
      </section>

      <Card className="animate-fade-up overflow-hidden p-0" style={{ animationDelay: "100ms" }}>
        <div className="flex items-center justify-between border-b border-border px-5 py-3">
          <span className="text-[13px] font-semibold">Engineering work queue</span>
          <span className="text-[12px] text-muted-foreground">{jobs.length} total</span>
        </div>
        <JobTable jobs={queue.slice(0, 12)} onSelect={setSelected} />
      </Card>

      <JobDrawer job={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
