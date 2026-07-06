import { CircleDashed, Circle, CircleDot, CircleEllipsis, CircleCheck, CircleX } from "lucide-react";
import { cn } from "@/lib/utils";

// Ported from the Linear clone's status-icon, mapped to our job lifecycle.
const config: Record<string, { icon: typeof Circle; className: string; live?: boolean }> = {
  queued: { icon: CircleDashed, className: "text-muted-foreground" },
  dispatched: { icon: Circle, className: "text-blue-400" },
  running: { icon: CircleDot, className: "text-yellow-500", live: true },
  needs_attention: { icon: CircleEllipsis, className: "text-amber-500" },
  pr_open: { icon: CircleCheck, className: "text-teal-400" },
  succeeded: { icon: CircleCheck, className: "text-emerald-500" },
  failed: { icon: CircleX, className: "text-rose-500" },
};

export function StatusIcon({ status, className }: { status: string; className?: string }) {
  const c = config[status] ?? { icon: Circle, className: "text-muted-foreground" };
  const Icon = c.icon;
  return <Icon className={cn("size-4 shrink-0", c.className, c.live && "animate-pulse", className)} />;
}
