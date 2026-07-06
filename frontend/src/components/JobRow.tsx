import { GitPullRequest, CircleAlert } from "lucide-react";
import { StatusIcon } from "@/components/StatusIcon";
import { PriorityIcon } from "@/components/PriorityIcon";
import { WORKLOADS, tint, type WorkloadKey } from "@/lib/theme";
import { timeAgo } from "@/lib/utils";
import type { Job } from "@/lib/api";

const KEY: Record<string, string> = { security: "PRV", governance: "GOV", incident: "INC" };

export function issueKey(j: Job): string {
  const prefix = KEY[j.workload] ?? "JOB";
  const n = j.issue_number ?? (Number(j.job_id.replace(/\D/g, "").slice(-3)) || 0);
  return `${prefix}-${n}`;
}

// Adapted from the Linear clone's IssueRow.
export function JobRow({
  job: j,
  onSelect,
  showWorkload = true,
}: {
  job: Job;
  onSelect: (j: Job) => void;
  showWorkload?: boolean;
}) {
  const w = WORKLOADS[j.workload as WorkloadKey];
  return (
    <button
      onClick={() => onSelect(j)}
      className="group flex h-10 w-full items-center gap-3 border-b border-border px-4 text-left text-sm transition-colors last:border-0 hover:bg-accent/60"
    >
      <PriorityIcon severity={j.severity} />
      <span className="w-16 shrink-0 font-mono text-xs text-muted-foreground">{issueKey(j)}</span>
      <StatusIcon status={j.status} />
      <span className="min-w-0 flex-1 truncate font-medium">{j.title}</span>

      {j.pr_url ? (
        <GitPullRequest className="size-3.5 shrink-0 text-muted-foreground" />
      ) : j.details?.rca_issue_url ? (
        <CircleAlert className="size-3.5 shrink-0 text-muted-foreground" />
      ) : null}

      {showWorkload && w && (
        <span
          className="grid size-5 shrink-0 place-items-center rounded"
          style={{ background: tint(w.hex, 0.16), color: w.hex }}
          title={w.label}
        >
          <w.icon className="size-3" />
        </span>
      )}

      <span className="hidden w-12 shrink-0 text-right text-xs tabular-nums text-muted-foreground sm:block">
        {j.eng_minutes_saved ? `${(j.eng_minutes_saved / 60).toFixed(1)}h` : "—"}
      </span>
      <span className="w-14 shrink-0 text-right text-xs tabular-nums text-muted-foreground">
        {timeAgo(j.dispatched_at)}
      </span>
    </button>
  );
}
