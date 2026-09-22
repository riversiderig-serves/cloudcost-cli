from __future__ import annotations
import html
import json
from pathlib import Path
from typing import Any

def load_findings(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array of findings in {path}")
    return [item for item in data if isinstance(item, dict)]

def _impact(f: dict[str, Any]) -> float:
    try:
        return float(f.get("estimated_impact") or 0)
    except (TypeError, ValueError):
        return 0.0

def _money(value: float) -> str:
    return f"${value:,.2f}"

def _esc(value: Any) -> str:
    return html.escape(str(value if value is not None else "N/A"))

def _chart(findings: list[dict[str, Any]]) -> str:
    totals: dict[str, float] = {}
    for f in findings:
        service = str(f.get("service_name") or "Unknown")
        totals[service] = totals.get(service, 0.0) + _impact(f)
    ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:8]
    if not ranked:
        return '<p class="muted">No impact data available.</p>'
    max_value = max(v for _, v in ranked) or 1.0
    bars = []
    for i, (service, value) in enumerate(ranked):
        y = i * 34 + 4
        width = max(2.0, value / max_value * 480)
        bars.append(f'<text x="0" y="{y + 15}" class="label">{_esc(service)[:30]}</text><rect x="190" y="{y}" width="{width:.1f}" height="20" rx="4" class="bar"/><text x="{190 + width + 8:.1f}" y="{y + 15}" class="value">{_money(value)}</text>')
    return f'<svg viewBox="0 0 720 {len(ranked) * 34 + 8}" role="img" aria-label="Estimated impact by service">{"".join(bars)}</svg>'

def render_report(findings: list[dict[str, Any]]) -> str:
    ranked = sorted(findings, key=_impact, reverse=True)
    total = sum(_impact(f) for f in findings)
    services = len({str(f.get("service_name") or "Unknown") for f in findings})
    open_count = sum(str(f.get("status", "open")).lower() == "open" for f in findings)
    rows = []
    for f in ranked:
        rows.append("<tr>" + f"<td>{_esc(f.get('severity', 'N/A')).upper()}</td><td>{_esc(f.get('provider'))}</td><td>{_esc(f.get('service_name'))}</td><td>{_esc(f.get('policy_name'))}</td><td>{_esc(f.get('resource_id'))}</td><td class='money'>{_money(_impact(f))}</td><td>{_esc(f.get('recommended_action'))}</td>" + "</tr>")
    table = "".join(rows) or '<tr><td colspan="7" class="muted">No findings in this report.</td></tr>'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CloudCost Findings Report</title>
<style>
body{{margin:0;background:#f5f7fa;color:#172033;font:14px system-ui,sans-serif}}main{{max-width:1280px;margin:auto;padding:32px 20px}}h1{{margin-bottom:4px}}.muted{{color:#667085}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0}}.card,section{{background:white;border:1px solid #e4e7ec;border-radius:12px;padding:18px}}.value{{font-size:26px;font-weight:700;margin-top:6px}}section{{margin-top:16px;overflow-x:auto}}table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;padding:10px 8px;border-bottom:1px solid #eaecf0;vertical-align:top}}.money{{white-space:nowrap}}svg{{width:100%;max-width:900px}}.label,.value{{font-size:12px;fill:#344054}}.bar{{fill:#2f6fed}}@media(max-width:800px){{.cards{{grid-template-columns:repeat(2,1fr)}}}}
</style></head><body><main>
<h1>CloudCost Findings Report</h1><p class="muted">Static summary of findings, sorted by estimated financial impact.</p>
<div class="cards"><div class="card">Total estimated impact<div class="value">{_money(total)}</div></div><div class="card">Findings<div class="value">{len(findings)}</div></div><div class="card">Open findings<div class="value">{open_count}</div></div><div class="card">Services affected<div class="value">{services}</div></div></div>
<section><h2>Impact by service</h2>{_chart(findings)}</section>
<section><h2>Findings</h2><table><thead><tr><th>Severity</th><th>Provider</th><th>Service</th><th>Policy</th><th>Resource</th><th>Impact</th><th>Recommended action</th></tr></thead><tbody>{table}</tbody></table></section>
</main></body></html>"""

def write_report(findings_path: str | Path, output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_report(load_findings(findings_path)), encoding="utf-8")
    return destination
