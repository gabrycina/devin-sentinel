import type { ReactNode } from "react";
import { Sheet } from "@/components/ui/sheet";
import { StatusBadge } from "@/components/StatusBadge";
import { PolicyList } from "@/components/PolicyList";
import { JobTimeline } from "@/components/JobTimeline";
import { WORKLOADS, EVENT_LABELS, SEVERITY, tint, type WorkloadKey } from "@/lib/theme";
import { timeAgo } from "@/lib/utils";
import type { Job } from "@/lib/api";

function renderMdBold(text: string) {
  return text.split("**").map((p, i) => (i % 2 ? <strong key={i}>{p}</strong> : <span key={i}>{p}</span>));
}

export function JobDrawer({ job, onClose }: { job: Job | null; onClose: () => void }) {
  const open = !!job;
  const w = job ? WORKLOADS[job.workload as WorkloadKey] : null;

  return (
    <Sheet open={open} onClose={onClose}>
      {job && w && (
        <div className="flex flex-col">
          <div className="border-b border-border px-6 py-5" style={{ background: tint(w.hex, 0.04) }}>
            <div className="mb-3 flex items-center gap-3">
              <span
                className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-md px-2 py-0.5 text-[11px] font-semibold"
                style={{ color: w.hex, background: tint(w.hex, 0.12) }}
              >
                <w.icon className="size-3.5" /> {w.label}
              </span>
              <StatusBadge status={job.status} />
            </div>
            <h2 className="pr-8 text-[16px] font-semibold leading-snug">{job.title}</h2>
            <div className="mt-1.5 text-[11.5px] text-muted-foreground">
              {EVENT_LABELS[job.event_type] ?? job.event_type}
              <span className="mx-1.5 text-border">·</span>
              <span className="font-mono">{job.job_id}</span>
            </div>
          </div>

          <div className="flex flex-col gap-5 px-6 py-5">
            <Section label="Why this job exists">
              <p className="text-[13px] leading-relaxed text-foreground/80">{renderMdBold(job.reason)}</p>
            </Section>

            <Section label="Story">
              <JobTimeline job={job} />
            </Section>

            {job.summary && (
              <Section label="Devin's summary">
                <p className="text-[13px] leading-relaxed text-foreground/80">{job.summary}</p>
              </Section>
            )}

            {job.policies?.length > 0 && (
              <Section label="Policy requirements">
                <PolicyList policies={job.policies} />
              </Section>
            )}

            <div className="grid grid-cols-3 gap-3 rounded-lg border border-border bg-subtle/60 p-3.5">
              <Metric label="Severity" value={job.severity} color={SEVERITY[job.severity]} />
              <Metric label="Eng. saved" value={`${(job.eng_minutes_saved / 60).toFixed(1)}h`} />
              <Metric label="ACUs" value={job.acus_consumed ? job.acus_consumed.toFixed(1) : "—"} />
            </div>

            <div className="text-[11.5px] text-muted-foreground">
              Dispatched {timeAgo(job.dispatched_at)}
              {job.completed_at ? ` · completed ${timeAgo(job.completed_at)}` : ""}
              {job.devin_status ? ` · devin: ${job.devin_status}` : ""}
            </div>
          </div>
        </div>
      )}
    </Sheet>
  );
}

const Section = ({ label, children }: { label: string; children: ReactNode }) => (
  <div>
    <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
    {children}
  </div>
);

const Metric = ({ label, value, color }: { label: string; value: string; color?: string }) => (
  <div>
    <div className="text-[10.5px] uppercase tracking-wide text-muted-foreground">{label}</div>
    <div className="mt-0.5 text-[14px] font-semibold capitalize" style={color ? { color } : undefined}>
      {value}
    </div>
  </div>
);
