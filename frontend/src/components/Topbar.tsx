import { useLocation } from "react-router-dom";
import { usePoll } from "@/lib/api";
import { WORKLOADS, type WorkloadKey } from "@/lib/theme";

type Config = { mode: string; repo: string };

function crumb(path: string): string {
  if (path === "/") return "Overview";
  if (path === "/rules") return "Rules engine";
  if (path === "/activity") return "Activity";
  const k = path.split("/w/")[1] as WorkloadKey;
  return WORKLOADS[k] ? `${WORKLOADS[k].label} · ${WORKLOADS[k].tagline}` : "";
}

export function Topbar() {
  const { pathname } = useLocation();
  const { data: cfg } = usePoll<Config>("/api/config", 30000);
  const live = cfg?.mode !== "DRY RUN";
  const dot = live ? "#16a34a" : "#d97706";

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border px-6">
      <div className="text-[13.5px] text-muted-foreground">
        <span className="font-medium text-foreground">Engineering Control Plane</span>
        <span className="mx-1.5 text-border">/</span>
        {crumb(pathname)}
      </div>
      <div className="ml-auto flex items-center gap-2 text-[12px] text-muted-foreground">
        <span className="size-1.5 animate-pulse-dot rounded-full" style={{ background: dot }} />
        {live ? "auto-refresh" : "dry run"}
      </div>
    </header>
  );
}
