"""Report generation — pure logic, no QGIS imports."""

from .models import DiffResult


def to_html(result: DiffResult, title: str = "Layer Diff Report") -> str:
    """Generate an HTML report from a DiffResult."""
    s = result.summary
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 2rem auto; }}
        .summary {{ display: flex; gap: 1rem; margin: 1rem 0; }}
        .summary div {{ padding: 1rem; border-radius: 8px; color: white; }}
        .added {{ background: #4caf50; }}
        .removed {{ background: #f44336; }}
        .modified {{ background: #ff9800; }}
        .unchanged {{ background: #9e9e9e; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        th, td {{ padding: 0.5rem; border-bottom: 1px solid #ddd; text-align: left; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="summary">
        <div class="added">+{s['added']} Added</div>
        <div class="removed">-{s['removed']} Removed</div>
        <div class="modified">~{s['modified']} Modified</div>
        <div class="unchanged">{s['unchanged']} Unchanged</div>
    </div>
    <h2>Modified Features</h2>
    <table>
        <tr><th>Key</th><th>Field</th><th>Old</th><th>New</th></tr>
        {_modified_rows(result)}
    </table>
</body>
</html>"""


def _modified_rows(result: DiffResult) -> str:
    rows = []
    for m in result.modified:
        if m.geometry_changed:
            rows.append(f"<tr><td>{m.key}</td><td><em>geometry</em></td><td colspan='2'>Changed</td></tr>")
        for fc in m.field_changes:
            rows.append(f"<tr><td>{m.key}</td><td>{fc.field}</td><td>{fc.old}</td><td>{fc.new}</td></tr>")
    return "\n".join(rows)


def to_csv(result: DiffResult) -> str:
    """Generate a CSV report from a DiffResult."""
    lines = ["type,key,field,old_value,new_value"]

    for rec in result.added:
        lines.append(f"added,{rec.key},,,,")

    for rec in result.removed:
        lines.append(f"removed,{rec.key},,,,")

    for m in result.modified:
        if m.geometry_changed:
            lines.append(f"modified,{m.key},geometry,Changed,Changed")
        for fc in m.field_changes:
            old = str(fc.old).replace(",", "\\,") if fc.old is not None else ""
            new = str(fc.new).replace(",", "\\,") if fc.new is not None else ""
            lines.append(f"modified,{m.key},{fc.field},{old},{new}")

    return "\n".join(lines)
