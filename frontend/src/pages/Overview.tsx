import { GitPullRequest, ShieldCheck, Clock, TrendingUp } from "lucide-react";
import { Pipeline } from "@/components/Pipeline";
import { AreaTrend, WorkloadBars } from "@/components/charts";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { usePoll, type Metrics, type Job } from "@/lib/api";
import { money } from "@/lib/utils";
import { WORKLOADS, WORKLOAD_ORDER } from "@/lib/theme";

function Stat({ icon: Icon, label, value, sub, color }: { icon: any; label: string; value: string; sub: string; color: string }) {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Icon className="size-4" style={{ color }} />
        <span className="text-[11.5px] font-medium uppercase tracking-wide">{label}</span>
      </div>
      <div className="mt-2 text-[26px] font-semibold leading-none tracking-tight tabular-nums">{value}</div>
      <div className="mt-1.5 text-[12px] text-muted-foreground">{sub}</div>
    </Card>
  );
}

const isDelivered = (j: Job) =>
  !!j.pr_url || ["succeeded", "pr_open", "needs_attention"].includes(j.status);

export function Overview() {
  const { data: m } = usePoll<Metrics>("/api/metrics", 5000);
  const { data: jobs } = usePoll<Job[]>("/api/jobs", 5000);

  if (!m) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-[260px] w-full" />
        <div className="grid grid-cols-4 gap-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}</div>
      </div>
    );
  }

  const delivered = (jobs ?? [])
    .filter(isDelivered)
    .sort((a, b) => (a.dispatched_at ?? a.created_at) - (b.dispatched_at ?? b.created_at));
  let acc = 0;
  const series = [0, ...delivered.map((j) => { acc += j.eng_minutes_saved / 60; return +acc.toFixed(1); })];

  const wlRows = WORKLOAD_ORDER.map((k) => ({
    label: WORKLOADS[k].label,
    value: m.by_workload[k]?.delivered ?? 0,
    total: m.by_workload[k]?.total ?? 0,
    color: WORKLOADS[k].hex,
  }));

  return (
    <div className="space-y-7">
      <header className="animate-fade-up">
        <h1 className="text-[22px] font-semibold tracking-tight">Control plane</h1>
        <p className="mt-1 text-[14px] text-muted-foreground">
          {m.running > 0 ? (
            <><span className="font-medium text-foreground">{m.running} Devin session{m.running > 1 ? "s" : ""}</span> working across your workloads.</>
          ) : (
            <>All workloads idle. {m.total} jobs processed to date.</>
          )}{" "}
          Click any node to drill in.
        </p>
      </header>

      <Card className="animate-fade-up p-6 md:p-8" style={{ animationDelay: "60ms" }}>
        <Pipeline m={m} />
      </Card>

      <section className="grid animate-fade-up grid-cols-2 gap-4 lg:grid-cols-4" style={{ animationDelay: "120ms" }}>
        <Stat icon={GitPullRequest} label="PRs produced" value={String(m.prs_produced)} sub="fixes + rollbacks, autonomous" color="#2563eb" />
        <Stat icon={ShieldCheck} label="Policies auto-met" value={String(m.policies_auto)} sub="no human required" color="#059669" />
        <Stat icon={Clock} label="Awaiting human" value={String(m.policies_need_approval + m.needs_attention)} sub="held for sign-off, by policy" color="#d97706" />
        <Stat icon={TrendingUp} label="Net value" value={money(m.net_value_usd)} sub={`${m.eng_hours_saved}h engineering saved`} color="#059669" />
      </section>

      <section className="grid animate-fade-up grid-cols-1 gap-4 lg:grid-cols-3" style={{ animationDelay: "180ms" }}>
        <Card className="p-5 lg:col-span-2">
          <div className="mb-1 flex items-baseline justify-between">
            <span className="text-[13px] font-semibold">Engineering hours saved</span>
            <span className="text-[13px] tabular-nums text-muted-foreground">
              {m.eng_hours_saved}h cumulative
            </span>
          </div>
          <p className="mb-3 text-[12px] text-muted-foreground">Accrued as each autonomous job delivers.</p>
          <AreaTrend values={series} color="#2563eb" />
        </Card>

        <Card className="p-5">
          <div className="mb-1 text-[13px] font-semibold">Workload distribution</div>
          <p className="mb-4 text-[12px] text-muted-foreground">Delivered jobs by workload.</p>
          <WorkloadBars rows={wlRows} />
        </Card>
      </section>
    </div>
  );
}
