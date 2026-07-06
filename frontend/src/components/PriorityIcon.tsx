import { Minus, SignalHigh, SignalLow, SignalMedium, TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";

// Ported from the Linear clone's priority-icon, mapped to our severity scale.
const config: Record<string, { icon: typeof Minus; className: string }> = {
  critical: { icon: TriangleAlert, className: "text-orange-500" },
  high: { icon: SignalHigh, className: "text-foreground" },
  medium: { icon: SignalMedium, className: "text-muted-foreground" },
  low: { icon: SignalLow, className: "text-muted-foreground/70" },
};

export function PriorityIcon({ severity, className }: { severity: string; className?: string }) {
  const c = config[severity] ?? { icon: Minus, className: "text-muted-foreground/50" };
  const Icon = c.icon;
  return <Icon className={cn("size-4 shrink-0", c.className, className)} />;
}
