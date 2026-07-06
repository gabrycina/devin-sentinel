import { CornerDownRight, FileCode2, UserCheck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { usePoll, type Rules as RulesData } from "@/lib/api";
import { SEVERITY } from "@/lib/theme";

const TIER_COLOR: Record<string, string> = {
  critical: SEVERITY.critical,
  standard: "#4f46e5",
  low: SEVERITY.low,
};

export function Rules() {
  const { data } = usePoll<RulesData>("/api/rules", 30000);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-[22px] font-semibold tracking-tight">Rules engine</h1>
        <p className="mt-1 max-w-2xl text-[14px] text-muted-foreground">
          Change-governance policy as code. When a pull request opens, the engine matches it to the
          highest tier below and requires those engineering artifacts before merge. Devin produces
          them; items marked <span className="font-medium text-foreground">needs approval</span> still
          require a human sign-off.
        </p>
      </header>

      {!data ? (
        <div className="space-y-4">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-40" />)}</div>
      ) : (
        <div className="space-y-4">
          {data.tiers.map((tier, idx) => {
            const color = TIER_COLOR[tier.name] ?? "#4f46e5";
            return (
              <Card key={tier.name} className="overflow-hidden">
                <div className="flex items-center gap-3 border-b border-border px-5 py-3.5">
                  <span className="grid size-6 place-items-center rounded-md text-[12px] font-semibold text-muted-foreground">
                    {idx + 1}
                  </span>
                  <span
                    className="rounded-full px-2.5 py-0.5 text-[12px] font-semibold capitalize"
                    style={{ color, background: `color-mix(in srgb, ${color} 12%, transparent)` }}
                  >
                    {tier.name}
                  </span>
                  <span className="text-[13px] text-muted-foreground">{tier.description}</span>
                </div>

                <div className="grid gap-5 px-5 py-4 md:grid-cols-2">
                  <div>
                    <div className="mb-2 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                      <FileCode2 className="size-3.5" /> When a PR touches
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {tier.match_paths.map((p) => (
                        <code
                          key={p}
                          className="rounded-md border border-border bg-muted/60 px-2 py-0.5 font-mono text-[11.5px] text-foreground/80"
                        >
                          {p}
                        </code>
                      ))}
                    </div>
                  </div>

                  <div>
                    <div className="mb-2 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                      <CornerDownRight className="size-3.5" /> Devin must produce
                    </div>
                    <div className="flex flex-col gap-1.5">
                      {tier.require.map((a) => {
                        const needsApproval = data.human_approval_required.includes(a);
                        return (
                          <div key={a} className="flex items-center gap-2 text-[13px]">
                            <span className="size-1.5 rounded-full" style={{ background: color }} />
                            <span className="capitalize">{a.replace(/_/g, " ")}</span>
                            {needsApproval && (
                              <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-1.5 py-0.5 text-[10.5px] font-medium text-amber-600">
                                <UserCheck className="size-3" /> needs approval
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
