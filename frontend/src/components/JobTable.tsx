import { GitPullRequest, CircleAlert, ChevronRight } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { StatusBadge } from "@/components/StatusBadge";
import { EVENT_LABELS, SEVERITY } from "@/lib/theme";
import { timeAgo } from "@/lib/utils";
import type { Job } from "@/lib/api";

export function JobTable({ jobs, onSelect }: { jobs: Job[]; onSelect: (j: Job) => void }) {
  if (!jobs.length) {
    return (
      <div className="flex flex-col items-center justify-center gap-1 py-16 text-center">
        <div className="text-[14px] font-medium">No jobs yet</div>
        <div className="text-[13px] text-muted-foreground">
          Trigger an event and Devin sessions will appear here.
        </div>
      </div>
    );
  }
  return (
    <Table>
      <TableHeader>
        <TableRow className="hover:bg-transparent">
          <TableHead className="w-[140px]">Status</TableHead>
          <TableHead>Job</TableHead>
          <TableHead className="w-[150px]">Event</TableHead>
          <TableHead className="w-[90px]">Output</TableHead>
          <TableHead className="w-[110px] text-right">Eng. saved</TableHead>
          <TableHead className="w-[110px] text-right">Updated</TableHead>
          <TableHead className="w-8" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {jobs.map((j) => (
          <TableRow
            key={j.job_id}
            onClick={() => onSelect(j)}
            className="group cursor-pointer hover:bg-muted/50"
          >
            <TableCell><StatusBadge status={j.status} /></TableCell>
            <TableCell>
              <div className="flex items-center gap-2">
                <span
                  className="size-1.5 shrink-0 rounded-full"
                  style={{ background: SEVERITY[j.severity] ?? "#94a3b8" }}
                  title={j.severity}
                />
                <span className="line-clamp-1 text-[13.5px] font-medium">{j.title}</span>
              </div>
              <div className="mt-0.5 line-clamp-1 pl-3.5 text-[12px] text-muted-foreground">
                {j.reason.replace(/\*\*/g, "")}
              </div>
            </TableCell>
            <TableCell className="text-[12.5px] text-muted-foreground">
              {EVENT_LABELS[j.event_type] ?? j.event_type}
            </TableCell>
            <TableCell>
              {j.pr_url ? (
                <span className="inline-flex items-center gap-1 text-[12px] text-primary">
                  <GitPullRequest className="size-3.5" /> PR
                </span>
              ) : j.details?.rca_issue_url ? (
                <span className="inline-flex items-center gap-1 text-[12px] text-muted-foreground">
                  <CircleAlert className="size-3.5" /> RCA
                </span>
              ) : (
                <span className="text-[12px] text-muted-foreground">—</span>
              )}
            </TableCell>
            <TableCell className="text-right text-[13px] tabular-nums text-muted-foreground">
              {j.eng_minutes_saved ? `${(j.eng_minutes_saved / 60).toFixed(1)}h` : "—"}
            </TableCell>
            <TableCell className="text-right text-[12.5px] tabular-nums text-muted-foreground">
              {timeAgo(j.dispatched_at)}
            </TableCell>
            <TableCell>
              <ChevronRight className="size-4 text-muted-foreground/50 transition-transform group-hover:translate-x-0.5" />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
