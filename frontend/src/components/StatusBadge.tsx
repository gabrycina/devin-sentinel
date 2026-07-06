import { STATUS } from "@/lib/theme";
import { cn } from "@/lib/utils";

/** Status as a colored dot + label (GitHub/Linear style) — never wraps. */
export function StatusBadge({ status, className }: { status: string; className?: string }) {
  const s = STATUS[status] ?? { label: status, hex: "#64748b" };
  const animate = status === "running" || status === "dispatched";
  return (
    <span
      className={cn("inline-flex items-center gap-1.5 whitespace-nowrap text-[12.5px] font-medium", className)}
      style={{ color: s.hex }}
    >
      <span
        className={cn("size-1.5 shrink-0 rounded-full", animate && "animate-pulse-dot")}
        style={{ background: s.hex }}
      />
      {s.label}
    </span>
  );
}
