import { useState, type ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { LayoutGrid, SlidersHorizontal, Activity, ChevronDown, Search, Bot } from "lucide-react";
import { WORKLOADS, WORKLOAD_ORDER } from "@/lib/theme";
import { usePoll, type Metrics } from "@/lib/api";
import { cn } from "@/lib/utils";

type Config = { mode: string; repo: string; incident_repo: string };
const KEY: Record<string, string> = { security: "PRV", governance: "GOV", incident: "RSP" };

// Adapted from the Linear clone's app-sidebar NavLink.
function Item({
  to,
  icon,
  children,
  count,
  end,
}: {
  to: string;
  icon: ReactNode;
  children: ReactNode;
  count?: number;
  end?: boolean;
}) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          "flex h-7 items-center gap-2 rounded-md px-2 text-[13px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground",
          isActive && "bg-accent font-medium text-foreground"
        )
      }
    >
      {icon}
      <span className="truncate">{children}</span>
      {count !== undefined && count > 0 && (
        <span className="ml-auto text-xs tabular-nums text-muted-foreground">{count}</span>
      )}
    </NavLink>
  );
}

export function Sidebar() {
  const { data: m } = usePoll<Metrics>("/api/metrics", 5000);
  const { data: cfg } = usePoll<Config>("/api/config", 30000);
  const [opsOpen, setOpsOpen] = useState(true);

  return (
    <div className="flex h-full flex-col">
      {/* brand */}
      <div className="flex items-center gap-2.5 p-3">
        <div className="grid size-7 shrink-0 place-items-center rounded-lg bg-foreground text-[13px] font-bold text-background">
          S
        </div>
        <div className="min-w-0 leading-tight">
          <div className="truncate text-[13.5px] font-semibold tracking-tight">Sentinel</div>
          <div className="truncate text-[11px] text-muted-foreground">{cfg?.repo?.split("/")[0] ?? "control plane"}</div>
        </div>
      </div>

      {/* search */}
      <div className="px-3 pb-2">
        <button className="flex h-7 w-full items-center gap-2 rounded-md border border-border bg-card px-2 text-[13px] text-muted-foreground transition-colors hover:text-foreground">
          <Search className="size-3.5" />
          Search…
          <kbd className="ml-auto rounded border border-border bg-muted px-1 font-mono text-[10px]">⌘K</kbd>
        </button>
      </div>

      {/* nav */}
      <div className="flex-1 overflow-y-auto px-3">
        <nav className="flex flex-col gap-0.5 pb-2">
          <Item to="/" end icon={<LayoutGrid className="size-4" />}>Overview</Item>
          <Item to="/rules" icon={<SlidersHorizontal className="size-4" />} count={m ? m.policies_auto + m.policies_need_approval : 0}>Policies</Item>
          <Item to="/activity" icon={<Activity className="size-4" />}>Activity</Item>
        </nav>

        <div className="pb-4">
          <button
            onClick={() => setOpsOpen((v) => !v)}
            className="flex w-full items-center gap-1 py-1 text-xs font-medium text-muted-foreground hover:text-foreground"
          >
            Operations
            <ChevronDown className={cn("size-3 transition-transform", !opsOpen && "-rotate-90")} />
          </button>
          {opsOpen && (
            <nav className="flex flex-col gap-0.5 pt-1">
              {WORKLOAD_ORDER.map((k) => {
                const w = WORKLOADS[k];
                return (
                  <Item
                    key={k}
                    to={`/w/${k}`}
                    count={m?.by_workload?.[k]?.total ?? 0}
                    icon={
                      <span
                        className="flex size-4 items-center justify-center rounded text-[8px] font-bold"
                        style={{ background: `color-mix(in srgb, ${w.hex} 16%, transparent)`, color: w.hex }}
                      >
                        {KEY[k]?.slice(0, 2)}
                      </span>
                    }
                  >
                    {w.label}
                  </Item>
                );
              })}
            </nav>
          )}
        </div>
      </div>

      {/* footer */}
      <div className="flex items-center gap-2 border-t border-border p-3 text-[11px] text-muted-foreground">
        <Bot className="size-3.5" />
        <span className="truncate font-mono">{cfg?.repo ?? "…"}</span>
      </div>
    </div>
  );
}
