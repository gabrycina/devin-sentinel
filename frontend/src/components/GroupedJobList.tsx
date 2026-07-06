import type { ReactNode } from "react";
import { JobRow } from "@/components/JobRow";
import { StatusIcon } from "@/components/StatusIcon";
import { STATUS } from "@/lib/theme";
import type { Job } from "@/lib/api";

// Order jobs are grouped into sections (Linear grouped-list style).
const ORDER = ["running", "dispatched", "needs_attention", "pr_open", "queued", "succeeded", "failed"];

// Adapted from the Linear clone's GroupedIssueList.
export function GroupedJobList({
  jobs,
  onSelect,
  showWorkload = true,
  emptyState,
}: {
  jobs: Job[];
  onSelect: (j: Job) => void;
  showWorkload?: boolean;
  emptyState?: ReactNode;
}) {
  if (!jobs.length) {
    return (
      <>{emptyState ?? (
        <div className="py-16 text-center text-[13px] text-muted-foreground">No jobs in this view.</div>
      )}</>
    );
  }

  const grouped = ORDER.map((status) => ({
    status,
    jobs: jobs
      .filter((j) => j.status === status)
      .sort((a, b) => (b.dispatched_at ?? b.created_at) - (a.dispatched_at ?? a.created_at)),
  })).filter((g) => g.jobs.length > 0);

  return (
    <>
      {grouped.map(({ status, jobs: groupJobs }) => (
        <section key={status}>
          <div className="flex h-9 items-center gap-2 border-b border-border bg-muted/40 px-4 text-sm">
            <StatusIcon status={status} />
            <span className="font-medium">{STATUS[status]?.label ?? status}</span>
            <span className="text-xs text-muted-foreground">{groupJobs.length}</span>
          </div>
          {groupJobs.map((j) => (
            <JobRow key={j.job_id} job={j} onSelect={onSelect} showWorkload={showWorkload} />
          ))}
        </section>
      ))}
    </>
  );
}
