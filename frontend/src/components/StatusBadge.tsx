import { STATUS } from "@/lib/theme";
import { Badge } from "@/components/ui/badge";

export function StatusBadge({ status }: { status: string }) {
  const s = STATUS[status] ?? { label: status, hex: "#64748b" };
  const animate = status === "running" || status === "dispatched";
  return (
    <Badge color={s.hex} className="font-medium">
      <span
        className={animate ? "animate-pulse-dot" : ""}
        style={{
          width: 6,
          height: 6,
          borderRadius: 999,
          background: s.hex,
          display: "inline-block",
        }}
      />
      {s.label}
    </Badge>
  );
}
