"""Report generation — pure logic, no QGIS imports."""

import csv
import html
from io import StringIO

from .models import DiffResult


def _esc(value: object) -> str:
    """HTML-escape arbitrary values for safe rendering."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def to_html(result: DiffResult, title: str = "Layer Diff Report", summary_only: bool = False) -> str:
    """Generate an HTML report from a DiffResult.

    All user-supplied values are HTML-escaped to prevent XSS in field values.
    If summary_only is True, only the summary counts are included (no per-feature details).
    """
    s = result.summary
    safe_title = _esc(title)
    detail_section = ""
    if not summary_only:
        added_section = ""
        if result.added:
            added_section = f"""
    <h2>Added Features</h2>
    <table>
        <tr><th>Key</th></tr>
        {chr(10).join(f"<tr><td>{_esc(r.key)}</td></tr>" for r in result.added)}
    </table>"""
        removed_section = ""
        if result.removed:
            removed_section = f"""
    <h2>Removed Features</h2>
    <table>
        <tr><th>Key</th></tr>
        {chr(10).join(f"<tr><td>{_esc(r.key)}</td></tr>" for r in result.removed)}
    </table>"""
        modified_section = f"""
    <h2>Modified Features</h2>
    <table>
        <tr><th>Key</th><th>Field</th><th>Old</th><th>New</th></tr>
        {_modified_rows(result)}
    </table>"""
        warnings_section = ""
        if result.warnings:
            warnings_section = f"""
    <div class="warnings">
        <h2>Warnings</h2>
        <ul>
            {chr(10).join(f"<li>{_esc(w)}</li>" for w in result.warnings)}
        </ul>
    </div>"""
        detail_section = f"{added_section}{removed_section}{modified_section}{warnings_section}"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{safe_title}</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 2rem auto; }}
        .summary {{ display: flex; gap: 1rem; margin: 1rem 0; }}
        .summary div {{ padding: 1rem; border-radius: 8px; color: white; }}
        .added {{ background: #4caf50; }}
        .removed {{ background: #f44336; }}
        .modified {{ background: #ff9800; }}
        .unchanged {{ background: #9e9e9e; }}
        .warnings {{ background: #fff3e0; padding: 1rem; border-radius: 8px; margin-top: 1rem; }}
        .warnings ul {{ margin: 0.5rem 0; padding-left: 1.5rem; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        th, td {{ padding: 0.5rem; border-bottom: 1px solid #ddd; text-align: left; }}
    </style>
</head>
<body>
    <h1>{safe_title}</h1>
    <div class="summary">
        <div class="added">+{s['added']} Added</div>
        <div class="removed">-{s['removed']} Removed</div>
        <div class="modified">~{s['modified']} Modified</div>
        <div class="unchanged">{s['unchanged']} Unchanged</div>
    </div>{detail_section}
</body>
</html>"""


def _modified_rows(result: DiffResult) -> str:
    rows = []
    for m in result.modified:
        if m.geometry_changed:
            rows.append(
                f"<tr><td>{_esc(m.key)}</td><td><em>geometry</em></td><td colspan='2'>Changed</td></tr>"
            )
        for fc in m.field_changes:
            rows.append(
                f"<tr><td>{_esc(m.key)}</td><td>{_esc(fc.field)}</td>"
                f"<td>{_esc(fc.old)}</td><td>{_esc(fc.new)}</td></tr>"
            )
    return "\n".join(rows)


def to_csv(result: DiffResult) -> str:
    """Generate a CSV report from a DiffResult using proper CSV formatting."""
    output = StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    
    # Header
    writer.writerow(["type", "key", "field", "old_value", "new_value"])

    # Added features
    for rec in result.added:
        writer.writerow(["added", rec.key, "", "", ""])

    # Removed features
    for rec in result.removed:
        writer.writerow(["removed", rec.key, "", "", ""])

    # Modified features
    for m in result.modified:
        if m.geometry_changed:
            writer.writerow(["modified", m.key, "geometry", "Changed", "Changed"])
        for fc in m.field_changes:
            old = str(fc.old) if fc.old is not None else ""
            new = str(fc.new) if fc.new is not None else ""
            writer.writerow(["modified", m.key, fc.field, old, new])

    return output.getvalue()
