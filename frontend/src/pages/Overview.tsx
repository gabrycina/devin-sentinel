import { useState } from "react";
import { DecisionFeed } from "@/components/DecisionFeed";
import { JobTable } from "@/components/JobTable";
import { JobDrawer } from "@/components/JobDrawer";
import { Donut, AreaTrend } from "@/components/charts";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { usePoll, type Metrics, type Job } from "@/lib/api";

// Representative operating figures for the demo (real counts stay live below).
const MOCK = {
  successRate: 94,
  criticalClosed: 3,
  meanRemediation: "22m",
  policyCompliance: 89,
  waitingOnApproval: "34m",
  rollbackTime: "8m",
  waitTrend: [46, 52, 39, 34, 41, 30, 34],
};

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
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-56" />)}</div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const needsAttention = jobs.filter((j) => j.status === "needs_attention").length;
  const queue = [...jobs].sort(
    (a, b) => (b.completed_at ?? b.dispatched_at ?? b.created_at) - (a.completed_at ?? a.dispatched_at ?? a.created_at)
  );

  return (
    <div className="space-y-6">
      <header className="animate-fade-up">
        <h1 className="text-[22px] font-semibold tracking-tight">Engineering control plane</h1>
        <p className="mt-1 text-[13.5px] font-medium" style={{ color: needsAttention > 0 ? "#d97706" : "#059669" }}>
          {needsAttention > 0 ? `${needsAttention} item${needsAttention > 1 ? "s" : ""} need your review` : "All systems operational"}
        </p>

        <div className="mt-5 flex flex-wrap items-end gap-x-8 gap-y-4">
          <div>
            <div className="text-[42px] font-semibold leading-none tabular-nums tracking-tight">{MOCK.successRate}%</div>
            <div className="mt-1.5 text-[12.5px] text-muted-foreground">Autonomous success rate</div>
          </div>
          <div className="flex flex-wrap items-end gap-x-6 gap-y-4">
            <SecondaryKpi value={String(MOCK.criticalClosed)} label="Critical vulns closed" />
            <SecondaryKpi value={String(m.prs_produced)} label="PRs generated" />
            <SecondaryKpi value={MOCK.meanRemediation} label="Mean remediation time" />
            <SecondaryKpi value={`${MOCK.policyCompliance}%`} label="Policy compliance" />
            <SecondaryKpi value={String(needsAttention)} label="Human interventions" />
            <SecondaryKpi value={MOCK.rollbackTime} label="Deployment rollback time" />
          </div>
        </div>
      </header>

      <section className="grid animate-fade-up grid-cols-1 gap-4 lg:grid-cols-3" style={{ animationDelay: "60ms" }}>
        <div className="lg:col-span-2">
          <DecisionFeed jobs={jobs} onSelect={setSelected} />
        </div>

        <div className="flex flex-col gap-4">
          <Card className="p-5">
            <div className="mb-4 text-[13px] font-semibold">Policy compliance</div>
            <div className="flex items-center gap-5">
              <Donut value={MOCK.policyCompliance} color="#16a34a" sub="auto-met" />
              <div className="flex flex-col gap-2 text-[12.5px]">
                <Legend color="#16a34a" label="Auto-satisfied" value={m.policies_auto} />
                <Legend color="#d97706" label="Needs approval" value={m.policies_need_approval} />
                <Legend color="#94a3b8" label="Pending" value={m.policies_pending} />
              </div>
            </div>
          </Card>

          <Card className="p-5">
            <div className="flex items-baseline justify-between">
              <span className="text-[13px] font-semibold">Time waiting on approval</span>
              <span className="text-[13px] font-semibold tabular-nums" style={{ color: "#d97706" }}>{MOCK.waitingOnApproval}</span>
            </div>
            <p className="mb-2 text-[11.5px] text-muted-foreground">avg across {needsAttention} awaiting sign-off</p>
            <AreaTrend values={MOCK.waitTrend} color="#d97706" height={64} />
          </Card>
        </div>
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

function Legend({ color, label, value }: { color: string; label: string; value: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="size-2 rounded-full" style={{ background: color }} />
      <span className="text-muted-foreground">{label}</span>
      <span className="ml-auto font-medium tabular-nums">{value}</span>
    </div>
  );
}
