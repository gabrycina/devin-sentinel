import { StatusIcon } from "@/components/StatusIcon";
import { WORKLOADS, tint, type WorkloadKey } from "@/lib/theme";
import { timeAgo } from "@/lib/utils";
import type { Job } from "@/lib/api";

type Step = { label: string; value: string; flag?: "approval" | "outcome" };

function outcomeText(job: Job): string {
  if (job.status === "needs_attention") return "Awaiting human sign-off";
  if (job.status === "failed") return job.error || "Failed";
  if (job.pr_url) return job.workload === "incident" ? "Rollback PR opened" : "Pull request opened";
  if (job.status === "succeeded") return "Resolved";
  if (job.status === "running" || job.status === "dispatched") return "Devin working…";
  return "Queued";
}

function buildChain(job: Job): Step[] {
  const d = job.details ?? {};
  const w = WORKLOADS[job.workload as WorkloadKey];

  if (job.workload === "security") {
    return [
      { label: "Dispatched", value: w.label },
      { label: "Reason", value: `${job.severity} ${d.cve ?? "finding"} in ${d.package ?? "code"}` },
      { label: "Outcome", value: outcomeText(job), flag: "outcome" },
    ];
  }

  if (job.workload === "governance") {
    const needsApproval = (job.policies ?? []).filter((p) => p.needs_human_approval);
    const steps: Step[] = [
      { label: "Risk tier", value: String(d.tier ?? job.severity) },
      {
        label: "Required",
        value: Array.isArray(d.required_artifacts) && d.required_artifacts.length
          ? d.required_artifacts.map((a: string) => a.replace(/_/g, " ")).join(", ")
          : "governance artifacts",
      },
    ];
    if (needsApproval.length) {
      steps.push({ label: "Needs human", value: needsApproval.map((p) => p.name.replace(/_/g, " ")).join(", "), flag: "approval" });
    }
    steps.push({ label: "Outcome", value: outcomeText(job), flag: "outcome" });
    return steps;
  }

  // incident
  return [
    { label: "Dispatched", value: w.label },
    {
      label: d.suspect_commit ? "Root cause" : "Investigating",
      value: d.suspect_commit ? `Commit ${String(d.suspect_commit).slice(0, 8)}` : d.service ?? "Correlating deploys",
    },
    { label: "Outcome", value: outcomeText(job), flag: "outcome" },
  ];
}

function DecisionCard({ job, onSelect }: { job: Job; onSelect: (j: Job) => void }) {
  const w = WORKLOADS[job.workload as WorkloadKey];
  const chain = buildChain(job);

  return (
    <button
      onClick={() => onSelect(job)}
      className="group flex w-full flex-col gap-2 border-b border-border/70 px-1 py-3 text-left last:border-0 hover:bg-muted/40"
    >
      <div className="flex items-center gap-2">
        <span className="w-9 shrink-0 text-[11px] tabular-nums text-muted-foreground">{timeAgo(job.created_at)}</span>
        <StatusIcon status={job.status} />
        <span
          className="grid size-5 shrink-0 place-items-center rounded"
          style={{ background: tint(w.hex, 0.12), color: w.hex }}
          title={w.label}
        >
          <w.icon className="size-3" />
        </span>
        <span className="min-w-0 flex-1 truncate text-[12.5px] font-medium">{job.title}</span>
      </div>
      <div className="ml-9 flex flex-col gap-1 border-l border-border pl-3">
        {chain.map((s, i) => (
          <div key={i} className="text-[11.5px] leading-snug">
            <span className="mr-1.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground/70">{s.label}</span>
            <span
              className={
                s.flag === "approval" ? "font-medium text-amber-600" : s.flag === "outcome" ? "font-medium text-foreground" : "text-foreground/80"
              }
            >
              {s.value}
            </span>
          </div>
        ))}
      </div>
    </button>
  );
}

export function DecisionFeed({ jobs, onSelect }: { jobs: Job[]; onSelect: (j: Job) => void }) {
  const recent = [...jobs].sort((a, b) => (b.created_at ?? 0) - (a.created_at ?? 0)).slice(0, 3);

  return (
    <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
      <div className="mb-0.5 section-eyebrow">Autonomous decisions</div>
      <p className="mb-2 text-[11.5px] text-muted-foreground">How the policy engine and Devin reasoned through each job.</p>
      {recent.length === 0 ? (
        <div className="py-8 text-center text-[13px] text-muted-foreground">No decisions yet.</div>
      ) : (
        <div className="flex flex-col">
          {recent.map((j) => <DecisionCard key={j.job_id} job={j} onSelect={onSelect} />)}
        </div>
      )}
    </div>
  );
}
