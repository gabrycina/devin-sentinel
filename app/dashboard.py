"""Server-rendered observability dashboard (no build step, no JS framework).

Auto-refreshes so an engineering leader can leave it on a wall monitor and watch
the fleet of Devin sessions move findings from 'queued' to 'merged PR'.
"""
from __future__ import annotations

import html
import time
from typing import Any

from .config import settings
from .models import Remediation, Status

_STATUS_STYLE = {
    Status.QUEUED.value: ("#8b93a7", "queued"),
    Status.DISPATCHED.value: ("#3b82f6", "dispatched"),
    Status.RUNNING.value: ("#3b82f6", "running"),
    Status.NEEDS_ATTENTION.value: ("#f59e0b", "needs attention"),
    Status.PR_OPEN.value: ("#a855f7", "PR open"),
    Status.SUCCEEDED.value: ("#22c55e", "succeeded"),
    Status.FAILED.value: ("#ef4444", "failed"),
}
_SEV_COLOR = {"critical": "#ef4444", "high": "#f97316", "medium": "#eab308", "low": "#64748b"}


def _esc(s: Any) -> str:
    return html.escape(str(s if s is not None else ""))


def _badge(status: str) -> str:
    color, label = _STATUS_STYLE.get(status, ("#8b93a7", status))
    return f'<span class="badge" style="background:{color}22;color:{color};border:1px solid {color}55">{label}</span>'


def _ago(ts: float | None) -> str:
    if not ts:
        return "—"
    d = time.time() - ts
    if d < 60:
        return f"{int(d)}s ago"
    if d < 3600:
        return f"{int(d/60)}m ago"
    return f"{int(d/3600)}h ago"


def _kpi(label: str, value: str, sub: str = "", accent: str = "#e5e7eb") -> str:
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""<div class="kpi">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value" style="color:{accent}">{value}</div>
      {sub_html}
    </div>"""


def _row(r: Remediation) -> str:
    sev_c = _SEV_COLOR.get(r.severity, "#64748b")
    session = (
        f'<a href="{_esc(r.session_url)}" target="_blank">session ↗</a>' if r.session_url else "—"
    )
    pr = f'<a href="{_esc(r.pr_url)}" target="_blank">PR ↗</a>' if r.pr_url else "—"
    issue = (
        f'<a href="{_esc(r.issue_url)}" target="_blank">#{r.issue_number}</a>'
        if r.issue_number else "—"
    )
    tests = "✅" if r.tests_passed else ("❌" if r.tests_passed is False else "—")
    detail = _esc(r.devin_status_detail or r.summary or "")[:90]
    return f"""<tr>
      <td><div class="fid">{_esc(r.finding_id)}</div><div class="ftitle">{_esc(r.title)}</div></td>
      <td><span class="sev" style="color:{sev_c}">{_esc(r.severity.upper())}</span></td>
      <td>{_badge(r.status)}<div class="detail">{detail}</div></td>
      <td>{issue}</td>
      <td>{session}</td>
      <td>{pr}</td>
      <td style="text-align:center">{tests}</td>
      <td style="text-align:right">{r.acus_consumed:.1f}</td>
      <td class="muted">{_ago(r.dispatched_at)}</td>
    </tr>"""


def _funnel(m: dict[str, Any]) -> str:
    stages = [
        ("Findings", m["total"], "#8b93a7"),
        ("In progress", m["running"], "#3b82f6"),
        ("PR open", m["pr_open"], "#a855f7"),
        ("Succeeded", m["succeeded"], "#22c55e"),
        ("Failed", m["failed"], "#ef4444"),
    ]
    total = max(m["total"], 1)
    bars = ""
    for label, val, color in stages:
        pct = int(val / total * 100)
        bars += f"""<div class="fn-row">
          <div class="fn-label">{label}</div>
          <div class="fn-track"><div class="fn-fill" style="width:{max(pct,2)}%;background:{color}"></div></div>
          <div class="fn-val">{val}</div>
        </div>"""
    return bars


def _events(events: list[dict[str, Any]]) -> str:
    if not events:
        return '<div class="muted">No events yet — trigger a scan.</div>'
    out = ""
    for e in events:
        out += f"""<div class="ev">
          <span class="ev-kind">{_esc(e['kind'])}</span>
          <span class="ev-msg">{_esc(e['message'])}</span>
          <span class="ev-ts muted">{_ago(e['ts'])}</span>
        </div>"""
    return out


def render_dashboard(
    m: dict[str, Any], rows: list[Remediation], events: list[dict[str, Any]]
) -> str:
    net = m["net_value_usd"]
    net_color = "#22c55e" if net >= 0 else "#ef4444"
    table = "".join(_row(r) for r in rows) or (
        '<tr><td colspan="9" class="muted" style="padding:28px">'
        "No remediations yet. POST /api/scan or add the "
        f"<code>{settings.trigger_label}</code> label to an issue.</td></tr>"
    )
    mode = "DRY RUN" if settings.dry_run else "LIVE"
    mode_color = "#f59e0b" if settings.dry_run else "#22c55e"

    return f"""<!doctype html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="8">
<title>Devin Sentinel</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:#0b0e14; color:#e5e7eb;
    font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
  a {{ color:#60a5fa; text-decoration:none; }} a:hover {{ text-decoration:underline; }}
  .wrap {{ max-width:1240px; margin:0 auto; padding:28px 22px 60px; }}
  header {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:22px; }}
  .brand {{ display:flex; align-items:center; gap:12px; }}
  .logo {{ width:34px; height:34px; border-radius:8px;
    background:linear-gradient(135deg,#6366f1,#a855f7); display:grid; place-items:center;
    font-size:18px; }}
  h1 {{ font-size:19px; margin:0; letter-spacing:.2px; }}
  .sub {{ color:#8b93a7; font-size:12.5px; }}
  .pill {{ font-size:11px; font-weight:600; padding:4px 10px; border-radius:999px;
    background:{mode_color}22; color:{mode_color}; border:1px solid {mode_color}55; }}
  .grid {{ display:grid; grid-template-columns:repeat(6,1fr); gap:12px; margin-bottom:20px; }}
  .kpi {{ background:#141925; border:1px solid #1f2635; border-radius:12px; padding:14px 16px; }}
  .kpi-label {{ font-size:11px; text-transform:uppercase; letter-spacing:.6px; color:#8b93a7; }}
  .kpi-value {{ font-size:26px; font-weight:700; margin-top:6px; }}
  .kpi-sub {{ font-size:11.5px; color:#8b93a7; margin-top:2px; }}
  .cols {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:20px; }}
  .card {{ background:#141925; border:1px solid #1f2635; border-radius:12px; padding:16px 18px; }}
  .card h2 {{ font-size:13px; text-transform:uppercase; letter-spacing:.6px; color:#8b93a7;
    margin:0 0 14px; }}
  .fn-row {{ display:flex; align-items:center; gap:12px; margin:9px 0; }}
  .fn-label {{ width:92px; font-size:12.5px; color:#c3c9d6; }}
  .fn-track {{ flex:1; height:9px; background:#0b0e14; border-radius:6px; overflow:hidden; }}
  .fn-fill {{ height:100%; border-radius:6px; transition:width .4s; }}
  .fn-val {{ width:28px; text-align:right; font-variant-numeric:tabular-nums; color:#c3c9d6; }}
  .ev {{ display:flex; gap:10px; align-items:baseline; padding:5px 0; border-bottom:1px solid #1a2030; font-size:12.5px; }}
  .ev-kind {{ font-family:ui-monospace,monospace; font-size:11px; color:#a855f7; min-width:96px; }}
  .ev-msg {{ flex:1; color:#c3c9d6; }}
  table {{ width:100%; border-collapse:collapse; }}
  th {{ text-align:left; font-size:11px; text-transform:uppercase; letter-spacing:.5px;
    color:#8b93a7; padding:10px 12px; border-bottom:1px solid #1f2635; }}
  td {{ padding:12px; border-bottom:1px solid #161c28; vertical-align:top; }}
  .fid {{ font-family:ui-monospace,monospace; font-size:11.5px; color:#8b93a7; }}
  .ftitle {{ font-size:13px; color:#e5e7eb; margin-top:2px; max-width:360px; }}
  .badge {{ font-size:11px; font-weight:600; padding:3px 9px; border-radius:999px; white-space:nowrap; }}
  .sev {{ font-weight:700; font-size:11.5px; }}
  .detail {{ font-size:11px; color:#6b7280; margin-top:4px; max-width:220px; }}
  .muted {{ color:#6b7280; }}
  .table-card {{ background:#141925; border:1px solid #1f2635; border-radius:12px; overflow:hidden; }}
  .table-head {{ padding:14px 18px; border-bottom:1px solid #1f2635; display:flex;
    justify-content:space-between; align-items:center; }}
  code {{ background:#0b0e14; padding:1px 6px; border-radius:5px; font-size:12px; }}
  @media (max-width:900px) {{ .grid{{grid-template-columns:repeat(2,1fr)}} .cols{{grid-template-columns:1fr}} }}
</style></head><body><div class="wrap">
  <header>
    <div class="brand">
      <div class="logo">🛡️</div>
      <div>
        <h1>Devin Sentinel</h1>
        <div class="sub">Autonomous security &amp; dependency remediation · {_esc(settings.github_repo)}</div>
      </div>
    </div>
    <span class="pill">● {mode}</span>
  </header>

  <div class="grid">
    {_kpi("Findings tracked", str(m["total"]))}
    {_kpi("PRs produced", str(m["prs_produced"]), "autonomous", "#a855f7")}
    {_kpi("Success rate", f"{m['success_rate']}%", f"{m['succeeded']}/{m['resolved']} resolved", "#22c55e")}
    {_kpi("In progress", str(m["running"]), "live sessions", "#3b82f6")}
    {_kpi("Devin spend", f"${m['devin_spend_usd']}", f"{m['total_acus']} ACUs", "#e5e7eb")}
    {_kpi("Net value", f"${net:,.0f}", f"{m['eng_hours_saved']}h eng saved", net_color)}
  </div>

  <div class="cols">
    <div class="card"><h2>Remediation funnel</h2>{_funnel(m)}</div>
    <div class="card"><h2>Live activity</h2>{_events(events)}</div>
  </div>

  <div class="table-card">
    <div class="table-head">
      <h2 style="margin:0;font-size:13px;text-transform:uppercase;letter-spacing:.6px;color:#8b93a7">Remediations</h2>
      <span class="muted" style="font-size:12px">auto-refresh 8s</span>
    </div>
    <table>
      <thead><tr>
        <th>Finding</th><th>Sev</th><th>Status</th><th>Issue</th>
        <th>Devin</th><th>PR</th><th>Tests</th><th>ACUs</th><th>Dispatched</th>
      </tr></thead>
      <tbody>{table}</tbody>
    </table>
  </div>
</div></body></html>"""
