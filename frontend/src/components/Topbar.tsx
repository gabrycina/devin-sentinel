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

  return (
    <header className="flex h-14 items-center gap-3 border-b border-border bg-background/80 px-6 py-3 backdrop-blur">
      <div className="text-[13.5px] text-muted-foreground">
        <span className="font-medium text-foreground">Engineering Control Plane</span>
        <span className="mx-1.5 text-border">/</span>
        {crumb(pathname)}
      </div>
      <div className="ml-auto flex items-center gap-3 text-[12px] text-muted-foreground">
        <span className="hidden items-center gap-1.5 sm:flex">
          <span className="size-1.5 animate-pulse-dot rounded-full bg-emerald-500" />
          auto-refresh
        </span>
        <span
          className="flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold"
          style={{
            color: live ? "#059669" : "#d97706",
            borderColor: live ? "#05966933" : "#d9770633",
            background: live ? "#05966912" : "#d9770612",
          }}
        >
          <span className="size-1.5 rounded-full" style={{ background: live ? "#059669" : "#d97706" }} />
          {cfg?.mode ?? "LIVE"}
        </span>
      </div>
    </header>
  );
}
