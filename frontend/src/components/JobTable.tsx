import { JobRow } from "@/components/JobRow";
import type { Job } from "@/lib/api";

export function JobTable({
  jobs,
  onSelect,
  showWorkload = true,
}: {
  jobs: Job[];
  onSelect: (j: Job) => void;
  showWorkload?: boolean;
}) {
  if (!jobs.length) {
    return (
      <div className="flex flex-col items-center justify-center gap-1 py-16 text-center">
        <div className="text-[14px] font-medium">No jobs yet</div>
        <div className="text-[13px] text-muted-foreground">Trigger an event and Devin sessions will appear here.</div>
      </div>
    );
  }
  return (
    <div className="flex flex-col">
      {jobs.map((j) => (
        <JobRow key={j.job_id} job={j} onSelect={onSelect} showWorkload={showWorkload} />
      ))}
    </div>
  );
}
