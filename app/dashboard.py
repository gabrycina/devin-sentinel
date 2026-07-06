"""Server-rendered control-plane dashboard, styled to feel native to Devin.

Light theme, left sidebar, generous whitespace, one restrained blue accent,
monospace for refs. Shows multiple event types flowing into a central
orchestrator, and for each job: WHY it exists, which policies were satisfied
automatically vs. still need a human, and estimated engineer-time saved.
"""
from __future__ import annotations

import html
import time
from typing import Any

from .config import settings
from .models import Job, PolicyStatus, Status, Workload

# --- Devin-like design tokens ------------------------------------------------
BLUE = "#2f6feb"
WORKLOAD = {
    Workload.SECURITY.value:   ("Prevent", "#2f6feb", "🛡️", "Security & dependency remediation"),
    Workload.GOVERNANCE.value: ("Govern", "#7c3aed", "📋", "Change-governance artifacts"),
    Workload.INCIDENT.value:   ("Respond", "#ea580c", "🚨", "Autonomous incident response"),
}
STATUS = {
    Status.QUEUED.value: ("#6b7280", "Queued"),
    Status.DISPATCHED.value: ("#2f6feb", "Dispatched"),
    Status.RUNNING.value: ("#2f6feb", "Running"),
    Status.NEEDS_ATTENTION.value: ("#d97706", "Needs approval"),
    Status.PR_OPEN.value: ("#7c3aed", "PR open"),
    Status.SUCCEEDED.value: ("#16a34a", "Succeeded"),
    Status.FAILED.value: ("#dc2626", "Failed"),
}
EVENT_LABEL = {
    "security_finding": "Security finding",
    "dependency_update": "Dependency update",
    "failed_ci": "Failed CI",
    "policy_violation": "Policy violation",
    "pull_request": "Pull request",
    "incident_alert": "Incident alert",
}
POLICY_MARK = {
    PolicyStatus.AUTO_SATISFIED.value: ("✓", "#16a34a", "auto"),
    PolicyStatus.NEEDS_APPROVAL.value: ("⏳", "#d97706", "needs approval"),
    PolicyStatus.PENDING.value: ("○", "#9ca3af", "pending"),
    PolicyStatus.FAILED.value: ("✕", "#dc2626", "failed"),
}


def _e(s: Any) -> str:
    return html.escape(str(s if s is not None else ""))


def _ago(ts: float | None) -> str:
    if not ts:
        return "—"
    d = time.time() - ts
    if d < 60:
        return f"{int(d)}s ago"
    if d < 3600:
        return f"{int(d/60)}m ago"
    return f"{int(d/3600)}h ago"


def _status_pill(status: str) -> str:
    color, label = STATUS.get(status, ("#6b7280", status))
    return (f'<span class="pill" style="color:{color};background:{color}14;'
            f'border-color:{color}33">{label}</span>')


def _md_bold(text: str) -> str:
    # tiny **bold** renderer for reason strings
    out, i = "", 0
    parts = _e(text).split("**")
    for idx, p in enumerate(parts):
        out += f"<strong>{p}</strong>" if idx % 2 else p
    return out


def _policies(job: Job) -> str:
    if not job.policies:
        return ""
    chips = ""
    for p in job.policies:
        mark, color, _ = POLICY_MARK.get(p.get("status", "pending"), ("○", "#9ca3af", ""))
        chips += (f'<span class="chip" style="color:{color};border-color:{color}33">'
                  f'<b style="color:{color}">{mark}</b> {_e(p["name"].replace("_"," "))}</span>')
    return f'<div class="chips">{chips}</div>'


def _links(job: Job) -> str:
    out = []
    if job.session_url:
        out.append(f'<a href="{_e(job.session_url)}" target="_blank">Devin session ↗</a>')
    if job.pr_url:
        label = "Rollback PR ↗" if job.workload == "incident" else "PR ↗"
        out.append(f'<a href="{_e(job.pr_url)}" target="_blank">{label}</a>')
    rca = job.details.get("rca_issue_url")
    if rca:
        out.append(f'<a href="{_e(rca)}" target="_blank">RCA issue ↗</a>')
    if job.issue_url and job.workload != "incident":
        lbl = "Governed PR ↗" if job.workload == "governance" else f"Issue #{job.issue_number} ↗"
        out.append(f'<a href="{_e(job.issue_url)}" target="_blank">{lbl}</a>')
    return ' <span class="dot">·</span> '.join(out) or '<span class="muted">—</span>'


def _job_row(job: Job) -> str:
    _, wcolor, _, _ = WORKLOAD.get(job.workload, ("", "#6b7280", "", ""))
    event = EVENT_LABEL.get(job.event_type, job.event_type)
    saved = f"{job.eng_minutes_saved/60:.1f}h saved" if job.eng_minutes_saved else ""
    acu = f"{job.acus_consumed:.1f} ACU" if job.acus_consumed else ""
    meta = " · ".join(x for x in [saved, acu, _ago(job.dispatched_at)] if x)
    return f"""<div class="job">
      <div class="job-main">
        <div class="job-top">
          <span class="etype" style="color:{wcolor};background:{wcolor}12">{_e(event)}</span>
          <span class="job-title">{_e(job.title)}</span>
        </div>
        <div class="job-why">{_md_bold(job.reason)}</div>
        {_policies(job)}
        <div class="job-links">{_links(job)}</div>
      </div>
      <div class="job-side">
        {_status_pill(job.status)}
        <div class="job-meta">{_e(meta)}</div>
      </div>
    </div>"""


def _workload_section(wl: str, jobs: list[Job]) -> str:
    name, color, icon, desc = WORKLOAD.get(wl, (wl, "#6b7280", "•", ""))
    rows = "".join(_job_row(j) for j in jobs) or (
        f'<div class="empty">No {name.lower()} jobs yet.</div>'
    )
    return f"""<section class="wl">
      <div class="wl-head">
        <span class="wl-badge" style="background:{color}14;color:{color}">{icon} {name}</span>
        <span class="wl-desc">{_e(desc)}</span>
        <span class="wl-count">{len(jobs)}</span>
      </div>
      {rows}
    </section>"""


def _kpi(label: str, value: str, sub: str = "", accent: str = "#1f1f1f") -> str:
    sub = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (f'<div class="kpi"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value" style="color:{accent}">{value}</div>{sub}</div>')


def _nav_item(label: str, count: int | None = None, color: str = "", active: bool = False) -> str:
    badge = f'<span class="nav-count">{count}</span>' if count is not None else ""
    dot = f'<span class="nav-dot" style="background:{color}"></span>' if color else ""
    cls = "nav-item active" if active else "nav-item"
    return f'<div class="{cls}">{dot}<span>{label}</span>{badge}</div>'


def _flow() -> str:
    events = ["Security finding", "Dependency update", "Failed CI", "Policy violation", "Incident alert"]
    ev = "".join(f'<span class="flow-ev">{e}</span>' for e in events)
    wls = "".join(
        f'<span class="flow-wl" style="color:{c};border-color:{c}44;background:{c}0c">{i} {n}</span>'
        for n, c, i, _ in WORKLOAD.values()
    )
    return f"""<div class="flow">
      <div class="flow-col"><div class="flow-h">Events</div><div class="flow-items">{ev}</div></div>
      <div class="flow-arrow">→</div>
      <div class="flow-col"><div class="flow-h">Rules engine</div>
        <div class="flow-orch">classify · require artifacts · dispatch Devin</div></div>
      <div class="flow-arrow">→</div>
      <div class="flow-col"><div class="flow-h">Workloads</div><div class="flow-items">{wls}</div></div>
    </div>"""


def _events(events: list[dict[str, Any]]) -> str:
    if not events:
        return '<div class="empty">No activity yet.</div>'
    out = ""
    for e in events:
        out += (f'<div class="ev"><span class="ev-kind">{_e(e["kind"])}</span>'
                f'<span class="ev-msg">{_e(e["message"])}</span>'
                f'<span class="muted ev-ts">{_ago(e["ts"])}</span></div>')
    return out


def render_dashboard(m: dict[str, Any], jobs: list[Job], events: list[dict[str, Any]]) -> str:
    net = m["net_value_usd"]
    by_wl = m["by_workload"]
    grouped = {w.value: [j for j in jobs if j.workload == w.value] for w in Workload}
    sections = "".join(
        _workload_section(w, grouped[w]) for w in [
            Workload.SECURITY.value, Workload.GOVERNANCE.value, Workload.INCIDENT.value]
    )
    mode = "DRY RUN" if settings.dry_run else "LIVE"
    mode_color = "#d97706" if settings.dry_run else "#16a34a"

    nav_workloads = "".join(
        _nav_item(WORKLOAD[w][0], by_wl.get(w, {}).get("total", 0), WORKLOAD[w][1])
        for w in [Workload.SECURITY.value, Workload.GOVERNANCE.value, Workload.INCIDENT.value]
    )

    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="8">
<title>Sentinel · Engineering Control Plane</title>
<style>
  * {{ box-sizing:border-box; }}
  :root {{ color-scheme:light; }}
  body {{ margin:0; background:#fbfbfa; color:#1f1f1f;
    font:13.5px/1.55 -apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Roboto,sans-serif;
    -webkit-font-smoothing:antialiased; }}
  a {{ color:{BLUE}; text-decoration:none; }} a:hover {{ text-decoration:underline; }}
  .muted {{ color:#9a9a9a; }}
  .layout {{ display:grid; grid-template-columns:236px 1fr; min-height:100vh; }}

  /* sidebar */
  .side {{ background:#fbfbfa; border-right:1px solid #ededed; padding:16px 12px; }}
  .brand {{ display:flex; align-items:center; gap:9px; padding:6px 8px 14px; }}
  .logo {{ width:26px; height:26px; border-radius:7px; background:#1f1f1f; color:#fff;
    display:grid; place-items:center; font-weight:700; font-size:14px; }}
  .brand-name {{ font-weight:600; font-size:14px; }}
  .brand-org {{ font-size:11.5px; color:#9a9a9a; }}
  .nav-sec {{ font-size:10.5px; text-transform:uppercase; letter-spacing:.7px;
    color:#a3a3a3; padding:14px 8px 6px; }}
  .nav-item {{ display:flex; align-items:center; gap:8px; padding:6px 8px; border-radius:7px;
    color:#3d3d3d; font-size:13px; cursor:default; }}
  .nav-item:hover {{ background:#f0f0ef; }}
  .nav-item.active {{ background:#eef1f6; color:{BLUE}; font-weight:500; }}
  .nav-dot {{ width:7px; height:7px; border-radius:50%; }}
  .nav-count {{ margin-left:auto; font-size:11.5px; color:#9a9a9a; }}
  .side-foot {{ margin-top:18px; padding:10px 8px; border-top:1px solid #ededed; font-size:11.5px; color:#9a9a9a; }}

  /* main */
  .main {{ min-width:0; }}
  .topbar {{ display:flex; align-items:center; gap:10px; padding:14px 26px;
    border-bottom:1px solid #ededed; background:#fff; }}
  .crumb {{ font-size:13px; color:#5a5a5a; }}
  .crumb b {{ color:#1f1f1f; }}
  .top-right {{ margin-left:auto; display:flex; align-items:center; gap:12px; font-size:12px; color:#9a9a9a; }}
  .mode {{ font-weight:600; padding:3px 9px; border-radius:999px; font-size:11px;
    color:{mode_color}; background:{mode_color}14; border:1px solid {mode_color}33; }}
  .content {{ padding:24px 26px 60px; max-width:1180px; }}
  h1 {{ font-size:20px; margin:0 0 3px; letter-spacing:-.2px; }}
  .subtitle {{ color:#8a8a8a; font-size:13px; margin-bottom:20px; }}

  .kpis {{ display:grid; grid-template-columns:repeat(6,1fr); gap:10px; margin-bottom:18px; }}
  .kpi {{ background:#fff; border:1px solid #ededed; border-radius:10px; padding:12px 14px; }}
  .kpi-label {{ font-size:10.5px; text-transform:uppercase; letter-spacing:.5px; color:#a3a3a3; }}
  .kpi-value {{ font-size:23px; font-weight:650; margin-top:5px; letter-spacing:-.5px; }}
  .kpi-sub {{ font-size:11px; color:#9a9a9a; margin-top:1px; }}

  .flow {{ display:flex; align-items:stretch; gap:10px; background:#fff; border:1px solid #ededed;
    border-radius:10px; padding:14px 16px; margin-bottom:22px; }}
  .flow-col {{ flex:1; }}
  .flow-arrow {{ display:grid; place-items:center; color:#c9c9c9; font-size:18px; }}
  .flow-h {{ font-size:10.5px; text-transform:uppercase; letter-spacing:.6px; color:#a3a3a3; margin-bottom:8px; }}
  .flow-items {{ display:flex; flex-wrap:wrap; gap:5px; }}
  .flow-ev {{ font-size:11.5px; color:#5a5a5a; background:#f4f4f3; border:1px solid #eaeaea;
    padding:3px 8px; border-radius:6px; }}
  .flow-wl {{ font-size:11.5px; padding:3px 8px; border-radius:6px; border:1px solid; }}
  .flow-orch {{ font-size:12px; color:#5a5a5a; background:#f7f5ff; border:1px dashed #d9ccf5;
    padding:8px 10px; border-radius:8px; }}

  .wl {{ background:#fff; border:1px solid #ededed; border-radius:10px; margin-bottom:14px; overflow:hidden; }}
  .wl-head {{ display:flex; align-items:center; gap:10px; padding:12px 16px; border-bottom:1px solid #f0f0f0; }}
  .wl-badge {{ font-size:12.5px; font-weight:600; padding:3px 10px; border-radius:7px; }}
  .wl-desc {{ font-size:12px; color:#9a9a9a; }}
  .wl-count {{ margin-left:auto; font-size:12px; color:#9a9a9a; }}
  .job {{ display:flex; gap:16px; padding:14px 16px; border-bottom:1px solid #f4f4f3; }}
  .job:last-child {{ border-bottom:none; }}
  .job-main {{ flex:1; min-width:0; }}
  .job-top {{ display:flex; align-items:center; gap:9px; margin-bottom:4px; }}
  .etype {{ font-size:10.5px; font-weight:600; padding:2px 7px; border-radius:5px; white-space:nowrap; }}
  .job-title {{ font-size:13.5px; font-weight:550; color:#1f1f1f; overflow:hidden;
    text-overflow:ellipsis; white-space:nowrap; }}
  .job-why {{ font-size:12.5px; color:#6e6e6e; margin-bottom:8px; }}
  .chips {{ display:flex; flex-wrap:wrap; gap:5px; margin-bottom:9px; }}
  .chip {{ font-size:11px; padding:2px 8px; border:1px solid; border-radius:999px; background:#fff; }}
  .job-links {{ font-size:12px; }}
  .job-links .dot {{ color:#d0d0d0; }}
  .job-side {{ text-align:right; white-space:nowrap; }}
  .pill {{ font-size:11px; font-weight:600; padding:3px 10px; border-radius:999px; border:1px solid; }}
  .job-meta {{ font-size:11px; color:#a3a3a3; margin-top:6px; }}
  .empty {{ padding:18px 16px; color:#b0b0b0; font-size:12.5px; }}

  .grid2 {{ display:grid; grid-template-columns:2fr 1fr; gap:14px; align-items:start; }}
  .card {{ background:#fff; border:1px solid #ededed; border-radius:10px; padding:4px 0; }}
  .card h2 {{ font-size:11px; text-transform:uppercase; letter-spacing:.6px; color:#a3a3a3;
    margin:0; padding:14px 16px 8px; }}
  .ev {{ display:flex; gap:9px; align-items:baseline; padding:7px 16px; border-top:1px solid #f4f4f3; font-size:12px; }}
  .ev-kind {{ font-family:ui-monospace,"SF Mono",monospace; font-size:10.5px; color:#7c3aed; min-width:92px; }}
  .ev-msg {{ flex:1; color:#5a5a5a; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
  .ev-ts {{ font-size:11px; }}
  @media (max-width:920px) {{ .layout{{grid-template-columns:1fr}} .side{{display:none}}
    .kpis{{grid-template-columns:repeat(2,1fr)}} .flow{{flex-direction:column}} .grid2{{grid-template-columns:1fr}} }}
</style></head><body><div class="layout">

  <aside class="side">
    <div class="brand">
      <div class="logo">S</div>
      <div><div class="brand-name">Sentinel</div><div class="brand-org">{_e(settings.github_repo.split('/')[0])}</div></div>
    </div>
    {_nav_item("Overview", active=True)}
    {_nav_item("Automations")}
    {_nav_item("Activity")}
    <div class="nav-sec">Workloads</div>
    {nav_workloads}
    <div class="nav-sec">Governance</div>
    {_nav_item("Policies", m["policies_auto"] + m["policies_need_approval"])}
    <div class="side-foot">Repo · <code>{_e(settings.github_repo)}</code></div>
  </aside>

  <div class="main">
    <div class="topbar">
      <div class="crumb"><b>Engineering Control Plane</b> <span class="muted">/ overview</span></div>
      <div class="top-right">
        <span>updated {_ago(time.time()-1)} · auto-refresh 8s</span>
        <span class="mode">● {mode}</span>
      </div>
    </div>
    <div class="content">
      <h1>Engineering Control Plane</h1>
      <div class="subtitle">Events become governed, autonomous engineering work — with a full audit trail.</div>

      <div class="kpis">
        {_kpi("Autonomous jobs", str(m["total"]), f"{m['running']} in progress")}
        {_kpi("PRs produced", str(m["prs_produced"]), "security + rollback", "#2f6feb")}
        {_kpi("Policies auto-met", str(m["policies_auto"]), "no human needed", "#16a34a")}
        {_kpi("Needs approval", str(m["policies_need_approval"] + m["needs_attention"]), "awaiting human", "#d97706")}
        {_kpi("Devin spend", f"${m['devin_spend_usd']}", f"{m['total_acus']} ACUs")}
        {_kpi("Net value", f"${net:,.0f}", f"{m['eng_hours_saved']}h eng saved", "#16a34a" if net>=0 else "#dc2626")}
      </div>

      {_flow()}

      {sections}

      <div class="card" style="margin-top:8px"><h2>Live activity</h2>{_events(events)}</div>
    </div>
  </div>
</div></body></html>"""
