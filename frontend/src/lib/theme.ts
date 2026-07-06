import { Shield, ScrollText, Siren, type LucideIcon } from "lucide-react";

export type WorkloadKey = "security" | "governance" | "incident";

/* Cohesive, low-saturation palette. One sage accent for "good/active",
   restrained gold for "attention", muted rose for "failure"; everything
   else is neutral so the UI stays near-monochrome. */
export const ACCENT = "#a9c39a"; // sage — positive / active / primary
export const WARN = "#cbb173"; // muted gold — needs approval / in-progress attention
export const DANGER = "#d68f8f"; // muted rose — failure / critical
export const INFO = "#8f98a6"; // cool slate — dispatched / running
export const NEUTRAL = "#a6ada7"; // neutral — workloads & default chips

export const WORKLOADS: Record<
  WorkloadKey,
  { key: WorkloadKey; label: string; tagline: string; hex: string; icon: LucideIcon; verb: string }
> = {
  security: {
    key: "security",
    label: "Prevent",
    tagline: "Security & dependency remediation",
    hex: NEUTRAL,
    icon: Shield,
    verb: "remediated",
  },
  governance: {
    key: "governance",
    label: "Govern",
    tagline: "Change-governance artifacts",
    hex: NEUTRAL,
    icon: ScrollText,
    verb: "governed",
  },
  incident: {
    key: "incident",
    label: "Respond",
    tagline: "Autonomous incident response",
    hex: NEUTRAL,
    icon: Siren,
    verb: "mitigated",
  },
};

export const WORKLOAD_ORDER: WorkloadKey[] = ["security", "governance", "incident"];

export const STATUS: Record<string, { label: string; hex: string }> = {
  queued: { label: "Queued", hex: "#808781" },
  dispatched: { label: "Dispatched", hex: INFO },
  running: { label: "Running", hex: INFO },
  needs_attention: { label: "Needs approval", hex: WARN },
  pr_open: { label: "PR open", hex: ACCENT },
  succeeded: { label: "Succeeded", hex: ACCENT },
  failed: { label: "Failed", hex: DANGER },
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
  auto_satisfied: { label: "Auto-satisfied", hex: ACCENT, glyph: "✓" },
  needs_approval: { label: "Needs approval", hex: WARN, glyph: "⏳" },
  pending: { label: "Pending", hex: "#808781", glyph: "○" },
  failed: { label: "Failed", hex: DANGER, glyph: "✕" },
};

export const SEVERITY: Record<string, string> = {
  critical: DANGER,
  high: WARN,
  medium: NEUTRAL,
  low: "#6f756f",
};

/** tint a hex color to a translucent background */
export const tint = (hex: string, alpha = 0.1) =>
  `color-mix(in srgb, ${hex} ${alpha * 100}%, transparent)`;
