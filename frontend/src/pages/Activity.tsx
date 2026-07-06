import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { usePoll, type EventLog } from "@/lib/api";
import { timeAgo } from "@/lib/utils";
import { ACCENT, WARN, INFO } from "@/lib/theme";

const KIND_COLOR: Record<string, string> = {
  ingested: "#808781",
  dispatched: INFO,
  status_change: ACCENT,
  webhook: INFO,
  incident: WARN,
};

export function Activity() {
  const { data } = usePoll<EventLog[]>("/api/events", 4000);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-[22px] font-semibold tracking-tight">Activity</h1>
        <p className="mt-1 text-[14px] text-muted-foreground">
          Every event the control plane has processed, newest first.
        </p>
      </header>

      <Card>
        {!data ? (
          <div className="space-y-2 p-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-9" />)}</div>
        ) : data.length === 0 ? (
          <div className="py-16 text-center text-[13px] text-muted-foreground">No activity yet.</div>
        ) : (
          <div className="flex flex-col divide-y divide-border">
            {data.map((e) => (
              <div key={e.id} className="flex items-center gap-3 px-5 py-2.5">
                <span
                  className="w-[92px] shrink-0 font-mono text-[11px] font-medium"
                  style={{ color: KIND_COLOR[e.kind] ?? "#64748b" }}
                >
                  {e.kind}
                </span>
                <span className="flex-1 truncate text-[13px] text-foreground/80">
                  {e.message.replace(/\*\*/g, "")}
                </span>
                <span className="shrink-0 text-[11.5px] text-muted-foreground">{timeAgo(e.ts)}</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
