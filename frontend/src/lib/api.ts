import { useCallback, useEffect, useRef, useState } from "react";

export type Policy = {
  name: string;
  description?: string;
  status: "auto_satisfied" | "needs_approval" | "pending" | "failed";
  needs_human_approval?: boolean;
  path?: string;
};

export type Job = {
  job_id: string;
  workload: "security" | "governance" | "incident";
  event_type: string;
  severity: string;
  title: string;
  reason: string;
  source: string;
  repo: string;
  issue_number: number | null;
  issue_url: string;
  session_id: string;
  session_url: string;
  devin_status: string;
  devin_status_detail: string;
  acus_consumed: number;
  status: string;
  pr_url: string;
  tests_passed: boolean | null;
  summary: string;
  error: string;
  policies: Policy[];
  details: Record<string, any>;
  eng_minutes_saved: number;
  created_at: number;
  dispatched_at: number | null;
  completed_at: number | null;
};

export type Metrics = {
  total: number;
  by_status: Record<string, number>;
  by_workload: Record<string, { total: number; delivered: number; running: number }>;
  running: number;
  needs_attention: number;
  succeeded: number;
  failed: number;
  resolved: number;
  prs_produced: number;
  success_rate: number;
  total_acus: number;
  avg_cycle_min: number;
  policies_auto: number;
  policies_need_approval: number;
  policies_pending: number;
  eng_hours_saved: number;
  labor_value_usd: number;
  devin_spend_usd: number;
  net_value_usd: number;
};

export type Rule = {
  name: string;
  description: string;
  match_paths: string[];
  require: string[];
};
export type Rules = {
  tiers: Rule[];
  human_approval_required: string[];
  artifacts: Record<string, string>;
  repo: string;
};

export type EventLog = { id: number; ts: number; kind: string; job_id: string; message: string };

async function get<T>(path: string): Promise<T> {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
}

/** Poll a JSON endpoint on an interval; returns latest data + loading state. */
export function usePoll<T>(path: string, intervalMs = 5000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<number | null>(null);

  const tick = useCallback(() => {
    get<T>(path)
      .then((d) => { setData(d); setError(null); })
      .catch((e) => setError(String(e)));
  }, [path]);

  useEffect(() => {
    tick();
    timer.current = window.setInterval(tick, intervalMs);
    return () => { if (timer.current) window.clearInterval(timer.current); };
  }, [tick, intervalMs]);

  return { data, error, refetch: tick };
}

export const post = (path: string) => fetch(path, { method: "POST" });
