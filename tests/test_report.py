import json

from cloudcost.report import render_report, write_report


def test_render_report_sorts_findings_and_escapes_html() -> None:
    findings = [
        {
            "severity": "low",
            "provider": "azure",
            "service_name": "Storage <Account>",
            "policy_name": "small-impact",
            "resource_id": "r1",
            "estimated_impact": 5.0,
            "recommended_action": "Review",
            "status": "open",
        },
        {
            "severity": "high",
            "provider": "aws",
            "service_name": "EC2",
            "policy_name": "large-impact",
            "resource_id": "r2",
            "estimated_impact": 25.0,
            "recommended_action": "Stop",
            "status": "open",
        },
    ]

    html = render_report(findings)

    assert html.index("large-impact") < html.index("small-impact")
    assert "$30.00" in html
    assert "Storage &lt;Account&gt;" in html
    assert "<script>" not in html


def test_write_report_creates_parent_directory_and_valid_html(tmp_path) -> None:
    findings_path = tmp_path / "findings.json"
    output_path = tmp_path / "reports" / "weekly.html"
    findings_path.write_text(json.dumps([{"estimated_impact": 12.5, "status": "open"}]))

    destination = write_report(findings_path, output_path)

    assert destination == output_path
    assert output_path.exists()
    assert "<title>CloudCost Findings Report</title>" in output_path.read_text()
