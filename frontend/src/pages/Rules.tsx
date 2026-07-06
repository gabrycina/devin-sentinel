import { useEffect, useMemo, useState } from "react";
import { Play, Plus, Trash2, UserCheck, FileCode2, CornerDownRight, Check } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { Rules as RulesData, Rule } from "@/lib/api";
import { SEVERITY, INFO } from "@/lib/theme";
import { cn } from "@/lib/utils";

const TIER_COLOR = (name: string) =>
  ({ critical: SEVERITY.critical, standard: INFO, low: SEVERITY.low }[name] ?? INFO);

type Sim = {
  tier: string;
  tier_description: string;
  matched_paths: string[];
  required_artifacts: string[];
  human_approval: string[];
};

export function Rules() {
  const [policy, setPolicy] = useState<RulesData | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [paths, setPaths] = useState("superset/security/manager.py\nrequirements/base.txt");
  const [sim, setSim] = useState<Sim | null>(null);

  useEffect(() => {
    fetch("/api/rules").then((r) => r.json()).then(setPolicy);
  }, []);

  const allArtifacts = useMemo(() => Object.keys(policy?.artifacts ?? {}), [policy]);

  const mutate = (fn: (p: RulesData) => RulesData) => {
    setPolicy((p) => (p ? fn(JSON.parse(JSON.stringify(p))) : p));
    setDirty(true);
  };
  const setTier = (i: number, patch: Partial<Rule>) =>
    mutate((p) => { p.tiers[i] = { ...p.tiers[i], ...patch }; return p; });
  const toggleArtifact = (i: number, art: string) =>
    mutate((p) => {
      const req = new Set(p.tiers[i].require);
      req.has(art) ? req.delete(art) : req.add(art);
      p.tiers[i].require = allArtifacts.filter((a) => req.has(a));
      return p;
    });
  const toggleApproval = (art: string) =>
    mutate((p) => {
      const s = new Set(p.human_approval_required);
      s.has(art) ? s.delete(art) : s.add(art);
      p.human_approval_required = [...s];
      return p;
    });
  const addRule = () =>
    mutate((p) => {
      p.tiers.splice(p.tiers.length - 1, 0, {
        name: "new-rule", description: "Describe when this applies",
        match_paths: ["**/*"], require: ["changelog"],
      });
      return p;
    });
  const removeRule = (i: number) => mutate((p) => { p.tiers.splice(i, 1); return p; });

  const save = async () => {
    if (!policy) return;
    setSaving(true);
    const { repo, ...body } = policy;
    await fetch("/api/rules", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    setDirty(false); setSaving(false);
    runSim();
  };
  const runSim = async () => {
    const r = await fetch("/api/rules/simulate", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ paths }),
    }).then((r) => r.json());
    setSim(r);
  };
  useEffect(() => { if (policy) runSim(); /* eslint-disable-next-line */ }, [!!policy]);

  if (!policy) {
    return <div className="space-y-4">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-40" />)}</div>;
  }

  return (
    <div className="space-y-6">
      <header className="flex items-start gap-4">
        <div className="flex-1">
          <h1 className="text-[22px] font-semibold tracking-tight">Rules engine</h1>
          <p className="mt-1 max-w-2xl text-[14px] text-muted-foreground">
            Change-governance policy as code. Edit the tiers below — toggle required artifacts,
            mark which need human sign-off, or add a rule — then test it against a pull request.
          </p>
        </div>
        {dirty && (
          <div className="flex shrink-0 items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => { setDirty(false); fetch("/api/rules").then((r) => r.json()).then(setPolicy); }}>
              Discard
            </Button>
            <Button size="sm" onClick={save} disabled={saving}>
              <Check className="size-4" /> {saving ? "Saving…" : "Save changes"}
            </Button>
          </div>
        )}
      </header>

      {/* Live simulator */}
      <Card className="overflow-hidden border-primary/25">
        <div className="grid gap-0 md:grid-cols-[1fr_1.1fr]">
          <div className="border-b border-border p-5 md:border-b-0 md:border-r">
            <div className="mb-2 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              <Play className="size-3.5" /> Test a pull request
            </div>
            <textarea
              value={paths}
              onChange={(e) => setPaths(e.target.value)}
              spellCheck={false}
              rows={4}
              className="w-full resize-none rounded-md border border-border bg-muted/40 px-3 py-2 font-mono text-[12.5px] outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/15"
              placeholder="one changed file path per line…"
            />
            <Button size="sm" className="mt-2.5" onClick={runSim}>
              <Play className="size-3.5" /> Run classification
            </Button>
            {dirty && <p className="mt-2 text-[11.5px] text-[#cbb173]">Save changes to test the edited rules.</p>}
          </div>
          <div className="p-5">
            <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Result</div>
            {sim ? (
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[13px] text-muted-foreground">Classified</span>
                  <span
                    className="rounded-full px-2.5 py-0.5 text-[12px] font-semibold capitalize"
                    style={{ color: TIER_COLOR(sim.tier), background: `color-mix(in srgb, ${TIER_COLOR(sim.tier)} 12%, transparent)` }}
                  >
                    {sim.tier}
                  </span>
                </div>
                <div className="mt-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  Devin would produce
                </div>
                <div className="mt-1.5 flex flex-col gap-1">
                  {sim.required_artifacts.map((a) => (
                    <div key={a} className="flex items-center gap-2 text-[13px]">
                      <span className="size-1.5 rounded-full" style={{ background: TIER_COLOR(sim.tier) }} />
                      <span className="capitalize">{a.replace(/_/g, " ")}</span>
                      {sim.human_approval.includes(a) && (
                        <span className="inline-flex items-center gap-1 whitespace-nowrap text-[11px] font-medium text-[#cbb173]">
                          <UserCheck className="size-3" /> needs approval
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-[13px] text-muted-foreground">Run a classification to see the effect.</div>
            )}
          </div>
        </div>
      </Card>

      {/* Editable tiers */}
      <div className="space-y-4">
        {policy.tiers.map((tier, idx) => {
          const color = TIER_COLOR(tier.name);
          return (
            <Card key={idx} className="overflow-hidden">
              <div className="flex items-center gap-3 border-b border-border px-5 py-3">
                <span className="grid size-6 place-items-center text-[12px] font-semibold text-muted-foreground">{idx + 1}</span>
                <input
                  value={tier.name}
                  onChange={(e) => setTier(idx, { name: e.target.value })}
                  className="w-28 rounded-md px-2 py-0.5 text-[12.5px] font-semibold capitalize outline-none focus:bg-muted"
                  style={{ color }}
                />
                <input
                  value={tier.description}
                  onChange={(e) => setTier(idx, { description: e.target.value })}
                  className="flex-1 rounded-md px-2 py-0.5 text-[13px] text-muted-foreground outline-none focus:bg-muted"
                />
                <button
                  onClick={() => removeRule(idx)}
                  className="rounded-md p-1.5 text-muted-foreground/60 hover:bg-muted hover:text-[#d68f8f]"
                  title="Remove rule"
                >
                  <Trash2 className="size-4" />
                </button>
              </div>

              <div className="grid gap-5 px-5 py-4 md:grid-cols-2">
                <div>
                  <div className="mb-2 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                    <FileCode2 className="size-3.5" /> When a PR touches
                  </div>
                  <input
                    value={tier.match_paths.join(", ")}
                    onChange={(e) => setTier(idx, { match_paths: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })}
                    spellCheck={false}
                    className="w-full rounded-md border border-border bg-muted/40 px-3 py-2 font-mono text-[12px] outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/15"
                  />
                </div>

                <div>
                  <div className="mb-2 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                    <CornerDownRight className="size-3.5" /> Devin must produce
                  </div>
                  <div className="flex flex-col gap-1">
                    {allArtifacts.map((art) => {
                      const on = tier.require.includes(art);
                      const approval = policy.human_approval_required.includes(art);
                      return (
                        <div key={art} className="flex items-center gap-2">
                          <button
                            onClick={() => toggleArtifact(idx, art)}
                            className={cn(
                              "flex flex-1 items-center gap-2 rounded-md px-2 py-1 text-left text-[13px] transition-colors",
                              on ? "font-medium" : "text-muted-foreground/60 hover:bg-muted"
                            )}
                          >
                            <span
                              className={cn("grid size-4 place-items-center rounded border transition-colors")}
                              style={on ? { background: color, borderColor: color } : { borderColor: "hsl(var(--border))" }}
                            >
                              {on && <Check className="size-3 text-[#12140f]" />}
                            </span>
                            <span className="capitalize">{art.replace(/_/g, " ")}</span>
                          </button>
                          {on && (
                            <button
                              onClick={() => toggleApproval(art)}
                              className={cn(
                                "inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-[10.5px] font-medium transition-colors",
                                approval
                                  ? "border-[#cbb173]/40 bg-[#cbb173]/10 text-[#cbb173]"
                                  : "border-border text-muted-foreground/60 hover:text-foreground"
                              )}
                              title="Toggle human approval requirement"
                            >
                              <UserCheck className="size-3" /> {approval ? "needs approval" : "auto"}
                            </button>
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

        <Button variant="outline" onClick={addRule} className="w-full border-dashed">
          <Plus className="size-4" /> Add rule
        </Button>
      </div>
    </div>
  );
}
