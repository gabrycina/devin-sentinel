"""Central configuration, loaded from environment (.env in local dev)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # dotenv is optional at runtime (Docker passes env directly)
    pass


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # --- Devin ---
    devin_api_key: str = os.getenv("DEVIN_API_KEY", "")
    devin_org_id: str = os.getenv("DEVIN_ORG_ID", "")
    devin_base_url: str = os.getenv("DEVIN_BASE_URL", "https://api.devin.ai")
    # Every session we launch is tagged so the dashboard can isolate OUR fleet
    # from any other sessions in the org.
    fleet_tag: str = os.getenv("DEVIN_FLEET_TAG", "sentinel")
    # Cap spend per remediation so a runaway session can't drain the org budget.
    max_acu_per_session: int = int(os.getenv("DEVIN_MAX_ACU", "20"))

    # --- Target repository ---
    github_repo: str = os.getenv("GITHUB_REPO", "gabrycina/superset")
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    github_base_branch: str = os.getenv("GITHUB_BASE_BRANCH", "master")
    # Shared secret used to verify inbound GitHub webhook signatures.
    github_webhook_secret: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    # Only issues carrying this label are dispatched to Devin.
    trigger_label: str = os.getenv("TRIGGER_LABEL", "devin-fix")
    # Govern workload: run governance on every opened PR (or only labeled ones).
    govern_all_prs: bool = _bool("GOVERN_ALL_PRS", True)
    # Respond workload: the demo service repo that carries a planted regression.
    incident_repo: str = os.getenv("INCIDENT_REPO", "gabrycina/sentinel-demo-service")
    # Optional Slack incoming webhook for incident notifications.
    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")

    # --- Runtime ---
    db_path: str = os.getenv("DB_PATH", "data/sentinel.db")
    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))
    dry_run: bool = _bool("DRY_RUN", False)  # if true, never actually call Devin

    # --- ROI model (used purely for the observability dashboard) ---
    eng_hours_per_finding: float = float(os.getenv("ENG_HOURS_PER_FINDING", "2.5"))
    eng_hourly_cost: float = float(os.getenv("ENG_HOURLY_COST", "95"))
    acu_usd_cost: float = float(os.getenv("ACU_USD_COST", "2.25"))

    @property
    def sessions_url(self) -> str:
        return f"{self.devin_base_url}/v3/organizations/{self.devin_org_id}/sessions"

    def session_url(self, session_id: str) -> str:
        return f"{self.sessions_url}/{session_id}"

    def validate(self) -> list[str]:
        problems = []
        if not self.dry_run and not self.devin_api_key:
            problems.append("DEVIN_API_KEY is not set")
        if not self.dry_run and not self.devin_org_id:
            problems.append("DEVIN_ORG_ID is not set")
        if not self.github_repo:
            problems.append("GITHUB_REPO is not set")
        return problems


settings = Settings()

# Ensure the SQLite directory exists before anyone opens a connection.
Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
