import { Shield, ScrollText, Siren, type LucideIcon } from "lucide-react";

export type WorkloadKey = "security" | "governance" | "incident";

export const WORKLOADS: Record<
  WorkloadKey,
  { key: WorkloadKey; label: string; tagline: string; hex: string; icon: LucideIcon; verb: string }
> = {
  security: {
    key: "security",
    label: "Prevent",
    tagline: "Security & dependency remediation",
    hex: "#2563eb",
    icon: Shield,
    verb: "remediated",
  },
  governance: {
    key: "governance",
    label: "Govern",
    tagline: "Change-governance artifacts",
    hex: "#0d9488",
    icon: ScrollText,
    verb: "governed",
  },
  incident: {
    key: "incident",
    label: "Respond",
    tagline: "Autonomous incident response",
    hex: "#ea580c",
    icon: Siren,
    verb: "mitigated",
  },
};

export const WORKLOAD_ORDER: WorkloadKey[] = ["security", "governance", "incident"];

export const STATUS: Record<string, { label: string; hex: string }> = {
  queued: { label: "Queued", hex: "#64748b" },
  dispatched: { label: "Dispatched", hex: "#2563eb" },
  running: { label: "Running", hex: "#2563eb" },
  needs_attention: { label: "Needs approval", hex: "#d97706" },
  pr_open: { label: "PR open", hex: "#0d9488" },
  succeeded: { label: "Succeeded", hex: "#059669" },
  failed: { label: "Failed", hex: "#e11d48" },
};

export const EVENT_LABELS: Record<string, string> = {
  security_finding: "Security finding",
  dependency_update: "Dependency update",
  failed_ci: "Failed CI",
  policy_violation: "Policy violation",
  pull_request: "Pull request",
  incident_alert: "Incident alert",
};

export const POLICY: Record<string, { label: string; hex: string; glyph: string }> = {
  auto_satisfied: { label: "Auto-satisfied", hex: "#059669", glyph: "✓" },
  needs_approval: { label: "Needs approval", hex: "#d97706", glyph: "⏳" },
  pending: { label: "Pending", hex: "#94a3b8", glyph: "○" },
  failed: { label: "Failed", hex: "#e11d48", glyph: "✕" },
};

export const SEVERITY: Record<string, string> = {
  critical: "#e11d48",
  high: "#ea580c",
  medium: "#d97706",
  low: "#64748b",
};

/** tint a hex color to a translucent background */
export const tint = (hex: string, alpha = 0.1) =>
  `color-mix(in srgb, ${hex} ${alpha * 100}%, transparent)`;
