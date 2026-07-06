import { NavLink } from "react-router-dom";
import { LayoutGrid, GitBranch, Activity, SlidersHorizontal } from "lucide-react";
import { WORKLOADS, WORKLOAD_ORDER } from "@/lib/theme";
import { usePoll, type Metrics } from "@/lib/api";
import { cn } from "@/lib/utils";

type Config = { mode: string; repo: string; incident_repo: string };

function Item({
  to,
  icon: Icon,
  label,
  count,
  dot,
  end,
}: {
  to: string;
  icon?: any;
  label: string;
  count?: number;
  dot?: string;
  end?: boolean;
}) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          "group flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13.5px] transition-colors",
          isActive
            ? "bg-primary/10 text-primary font-medium"
            : "text-foreground/70 hover:bg-muted hover:text-foreground"
        )
      }
    >
      {Icon && <Icon className="size-[15px] opacity-80" />}
      {dot && <span className="size-2 rounded-full" style={{ background: dot }} />}
      <span className="truncate">{label}</span>
      {count !== undefined && count > 0 && (
        <span className="ml-auto text-xs tabular-nums text-muted-foreground">{count}</span>
      )}
    </NavLink>
  );
}

export function Sidebar() {
  const { data: m } = usePoll<Metrics>("/api/metrics", 5000);
  const { data: cfg } = usePoll<Config>("/api/config", 30000);

  return (
    <div className="flex h-full flex-col px-3 py-4">
      <div className="mb-5 flex items-center gap-2.5 px-2">
        <div className="grid size-7 place-items-center rounded-lg bg-foreground text-[13px] font-bold text-background">
          S
        </div>
        <div className="leading-tight">
          <div className="text-[14px] font-semibold tracking-tight">Sentinel</div>
          <div className="text-[11px] text-muted-foreground">{cfg?.repo?.split("/")[0] ?? "control plane"}</div>
        </div>
      </div>

      <nav className="flex flex-col gap-0.5">
        <Item to="/" icon={LayoutGrid} label="Overview" end />
        <Item to="/rules" icon={SlidersHorizontal} label="Rules engine" count={m ? m.policies_auto + m.policies_need_approval : 0} />
        <Item to="/activity" icon={Activity} label="Activity" />
      </nav>

      <div className="mb-1.5 mt-5 px-2.5 text-[10.5px] font-medium uppercase tracking-wider text-muted-foreground/70">
        Workloads
      </div>
      <nav className="flex flex-col gap-0.5">
        {WORKLOAD_ORDER.map((k) => (
          <Item
            key={k}
            to={`/w/${k}`}
            dot={WORKLOADS[k].hex}
            label={WORKLOADS[k].label}
            count={m?.by_workload?.[k]?.total ?? 0}
          />
        ))}
      </nav>

      <div className="mt-auto flex items-center gap-2 px-2 pt-4 text-[11px] text-muted-foreground">
        <GitBranch className="size-3.5" />
        <span className="truncate font-mono">{cfg?.repo ?? "…"}</span>
      </div>
    </div>
  );
}
