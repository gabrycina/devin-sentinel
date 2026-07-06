import { Check, ExternalLink, X } from "lucide-react";
import { WORKLOADS, tint, type WorkloadKey } from "@/lib/theme";
import { timeAgo } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { Job } from "@/lib/api";

type Step = {
  label: string;
  sub?: string;
  state: "done" | "current" | "pending" | "failed";
  href?: string;
  at?: number | null;
};

function security(job: Job): Step[] {
  const d = job.details ?? {};
  const dispatched = !!job.dispatched_at;
  const running = job.status === "running" || job.status === "dispatched";
  const testState: Step["state"] =
    job.tests_passed === true ? "done" : job.tests_passed === false ? "failed" : dispatched ? "pending" : "pending";
  return [
    { label: "Issue detected", sub: `${job.severity} · ${d.cve || "finding"} in ${d.package || "code"}`, state: "done", at: job.created_at },
    { label: "Devin dispatched", sub: d.fixed_version ? `Strategy: upgrade to ${d.fixed_version}` : "Session investigates the fix", state: dispatched ? "done" : "pending", href: job.session_url, at: job.dispatched_at },
    { label: "Tests passed", state: running && job.tests_passed == null ? "current" : testState },
    { label: "Pull request opened", sub: "Fix delivered for review", state: job.pr_url ? "done" : job.status === "failed" ? "failed" : "pending", href: job.pr_url, at: job.completed_at },
  ];
}

function governance(job: Job): Step[] {
  const d = job.details ?? {};
  const needsApproval = (job.policies ?? []).filter((p) => p.needs_human_approval);
  const steps: Step[] = [
    { label: "Pull request opened", sub: `Change proposed${job.issue_number ? ` in #${job.issue_number}` : ""}`, state: "done", href: job.issue_url, at: job.created_at },
    { label: `Classified ${d.tier || job.severity}`, sub: Array.isArray(d.required_artifacts) && d.required_artifacts.length ? `Requires ${d.required_artifacts.map((a: string) => a.replace(/_/g, " ")).join(", ")}` : undefined, state: "done", at: job.dispatched_at },
    { label: "Devin drafts artifacts", sub: "Changelog, risk notes, tests", state: job.dispatched_at ? "done" : "pending", href: job.session_url },
  ];
  if (needsApproval.length) {
    steps.push({
      label: "Human review",
      sub: `Sign-off required: ${needsApproval.map((p) => p.name.replace(/_/g, " ")).join(", ")}`,
      state: job.status === "needs_attention" ? "current" : job.status === "succeeded" ? "done" : "pending",
    });
  }
  steps.push({ label: "Governed & merged", sub: "Compliant change delivered", state: job.status === "succeeded" ? "done" : job.status === "failed" ? "failed" : "pending", at: job.completed_at });
  return steps;
}

function incident(job: Job): Step[] {
  const d = job.details ?? {};
  return [
    { label: "Incident alert", sub: `${d.service || "service"} — ${d.alert || job.title}`, state: "done", at: job.created_at },
    { label: "Devin investigating", sub: "Correlating deploys & bisecting", state: job.dispatched_at ? "done" : "pending", href: job.session_url, at: job.dispatched_at },
    { label: "Root cause identified", sub: d.root_cause ? String(d.root_cause) : undefined, state: d.root_cause ? "done" : job.status === "running" ? "current" : "pending" },
    { label: "Rollback PR opened", sub: "Immediate mitigation shipped", state: job.pr_url ? "done" : "pending", href: job.pr_url },
    {
      label: job.status === "needs_attention" ? "Awaiting merge" : "RCA filed",
      sub: d.rca_issue_url ? "Post-mortem issue opened for the team" : undefined,
      state: job.status === "succeeded" ? "done" : job.status === "needs_attention" ? "current" : "pending",
      href: d.rca_issue_url,
      at: job.completed_at,
    },
  ];
}

function buildSteps(job: Job): Step[] {
  if (job.workload === "security") return security(job);
  if (job.workload === "governance") return governance(job);
  return incident(job);
}

export function JobTimeline({ job }: { job: Job }) {
  const w = WORKLOADS[job.workload as WorkloadKey];
  const steps = buildSteps(job);

  return (
    <div className="flex flex-col">
      {steps.map((s, i) => {
        const last = i === steps.length - 1;
        const content = (
          <>
            <div
              className={cn(
                "relative z-10 grid size-6 shrink-0 place-items-center rounded-full border",
                s.state === "done" && "border-transparent",
                s.state === "current" && "border-amber-500/50 bg-amber-500/10",
                s.state === "pending" && "border-border bg-card",
                s.state === "failed" && "border-rose-500/50 bg-rose-500/10"
              )}
              style={s.state === "done" ? { background: w.hex } : undefined}
            >
              {s.state === "done" && <Check className="size-3.5 text-white" />}
              {s.state === "current" && <span className="size-2 animate-pulse-dot rounded-full bg-amber-500" />}
              {s.state === "failed" && <X className="size-3.5 text-rose-600" />}
              {s.state === "pending" && <span className="size-1.5 rounded-full bg-border" />}
            </div>
            <div className="min-w-0 flex-1 pb-4 pt-0.5 last:pb-0">
              <div className="flex items-center justify-between gap-2">
                <span className={cn("text-[13px] font-medium", s.state === "pending" && "text-muted-foreground")}>
                  {s.label}
                </span>
                <div className="flex shrink-0 items-center gap-1.5">
                  {s.at && <span className="text-[11px] tabular-nums text-muted-foreground">{timeAgo(s.at)}</span>}
                  {s.href && <ExternalLink className="size-3 text-muted-foreground" />}
                </div>
              </div>
              {s.sub && <div className="mt-0.5 text-[12px] leading-snug text-muted-foreground">{s.sub}</div>}
              {s.state === "current" && (
                <div className="mt-1 inline-flex items-center rounded-full bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium text-amber-600">
                  in progress
                </div>
              )}
            </div>
          </>
        );
        return (
          <div key={i} className="relative flex gap-3">
            {!last && <span className="absolute left-[11px] top-6 h-[calc(100%-10px)] w-px bg-border" aria-hidden />}
            {s.href ? (
              <a href={s.href} target="_blank" rel="noreferrer" className="group flex flex-1 gap-3 rounded-md transition-colors hover:bg-muted/50">
                {content}
              </a>
            ) : (
              <div className="flex flex-1 gap-3">{content}</div>
            )}
          </div>
        );
      })}
    </div>
  );
}
