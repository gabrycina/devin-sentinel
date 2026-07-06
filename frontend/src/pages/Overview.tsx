import { GitPullRequest, ShieldCheck, Clock, TrendingUp } from "lucide-react";
import { Pipeline } from "@/components/Pipeline";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { usePoll, type Metrics } from "@/lib/api";
import { money } from "@/lib/utils";

function Stat({
  icon: Icon,
  label,
  value,
  sub,
  color,
}: {
  icon: any;
  label: string;
  value: string;
  sub: string;
  color: string;
}) {
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

export function Overview() {
  const { data: m } = usePoll<Metrics>("/api/metrics", 5000);

  if (!m) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-[260px] w-full" />
        <div className="grid grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
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
        <Stat
          icon={GitPullRequest}
          label="PRs produced"
          value={String(m.prs_produced)}
          sub="fixes + rollbacks, autonomous"
          color="#4f46e5"
        />
        <Stat
          icon={ShieldCheck}
          label="Policies auto-met"
          value={String(m.policies_auto)}
          sub="no human required"
          color="#059669"
        />
        <Stat
          icon={Clock}
          label="Awaiting human"
          value={String(m.policies_need_approval + m.needs_attention)}
          sub="held for sign-off, by policy"
          color="#d97706"
        />
        <Stat
          icon={TrendingUp}
          label="Net value"
          value={money(m.net_value_usd)}
          sub={`${m.eng_hours_saved}h engineering saved`}
          color="#059669"
        />
      </section>
    </div>
  );
}
