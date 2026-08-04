#!/usr/bin/env python3
"""Generate a polished patch report for LLE hosts using inventory files."""

from __future__ import annotations

import argparse
import html
import re
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


WORKDIR = Path(__file__).resolve().parent
DEFAULT_INVENTORY_FILES = [
    "/backup/patching/monthly/LWR/QTS_RHEL_LWR.ini",
    "/backup/patching/monthly/LWR/OLS_ATL_LWR.ini",
    "/backup/patching/monthly/LWR/OLS_QTS_LWR.ini",
    "/backup/patching/monthly/LWR/QTS_OEL_LWR.ini",
]
DEFAULT_INVENTORY_DIR = Path("/inventory")

ENVIRONMENT_CONFIG = {
    "LLE": {
        "title": "LLE Patch Status Report",
        "subnets": ["10.42.", "10.44."],
        "output_name": "lle_patch_report.html",
    },
    "CAT3": {
        "title": "CAT3 Patch Status Report",
        "subnets": ["10.40.", "10.140.", "10.190.", "10.83.", "10.82."],
        "output_name": "cat3_patch_report.html",
    },
    "FCV_DMZ": {
        "title": "FCV DMZ Patch Status Report",
        "subnets": ["10.41.", "10.40.98.", "10.40.99.", "10.141.", "10.191.", "10.86."],
        "output_name": "fcv_dmz_patch_report.html",
    },
}


def parse_inventory_file(path: Path) -> List[Dict[str, str]]:
    hosts: List[Dict[str, str]] = []
    section = "default"
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            continue
        if "ansible_host=" not in line:
            continue
        match = re.match(r"^(?P<host>[^\s]+)\s+ansible_host=(?P<ip>[^\s]+)", line)
        if match:
            hosts.append(
                {
                    "hostname": match.group("host"),
                    "ip": match.group("ip"),
                    "source": path.name,
                    "section": section,
                }
            )
        else:
            hosts.append({"hostname": line.split()[0], "ip": "", "source": path.name, "section": section})
    return hosts


def discover_host_files(inventory_dir: Optional[Path] = None) -> List[Path]:
    base_dir = inventory_dir or DEFAULT_INVENTORY_DIR
    if not base_dir.exists():
        return []
    return sorted([p for p in base_dir.iterdir() if p.is_file() and not p.name.startswith(".")])


def discover_hosts(inventory_files: Optional[List[str]] = None) -> List[Dict[str, str]]:
    files = inventory_files or DEFAULT_INVENTORY_FILES
    hosts: List[Dict[str, str]] = []
    for path_str in files:
        path = Path(path_str)
        if path.exists():
            hosts.extend(parse_inventory_file(path))
    return hosts


def filter_hosts_for_environment(hosts: List[Dict[str, str]], environment: str) -> List[Dict[str, str]]:
    config = ENVIRONMENT_CONFIG.get(environment.upper())
    if not config:
        return hosts

    def matches_ip(ip: str) -> bool:
        return any(ip.startswith(prefix) for prefix in config["subnets"])

    return [host for host in hosts if host.get("ip") and matches_ip(host["ip"])]


def parse_collected_host_file(path: Path) -> Optional[Dict[str, str]]:
    if not path.exists():
        return None
    try:
        content = path.read_text(encoding="utf-8", errors="ignore").strip()
    except OSError:
        return None
    if not content:
        return None

    parts = [p.strip() for p in content.split(",")]
    while len(parts) > 6 and parts[-1] == "":
        parts.pop()
    if len(parts) < 6:
        return None

    hostname = parts[0]
    ip = parts[1] if len(parts) > 1 else ""
    patch_date = parts[2] if len(parts) > 2 else ""
    last_reboot = parts[3] if len(parts) > 3 else ""

    def looks_like_date(text: str) -> bool:
        return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", text))

    reported_date = ""
    os_release = ""
    kernel = ""
    remarks = ""

    if len(parts) >= 8:
        reported_date = parts[4]
        os_release = parts[5]
        kernel = parts[6]
        remarks = ",".join(parts[7:]).strip()
    elif len(parts) == 7:
        if looks_like_date(parts[4]):
            reported_date = parts[4]
            os_release = parts[5]
            kernel = parts[6]
        else:
            os_release = parts[4]
            kernel = parts[5]
            remarks = parts[6]
    else:
        os_release = parts[4]
        kernel = parts[5]

    return {
        "hostname": hostname,
        "ip": ip,
        "patch_date": patch_date,
        "last_reboot": last_reboot,
        "os_release": os_release,
        "patch_status": "Assessed",
        "notes": remarks,
        "source": path.name,
        "kernel": kernel,
        "reported_date": reported_date,
    }


def collect_host_data(host: Dict[str, str]) -> Dict[str, str]:
    hostname = host["hostname"]
    ip = host.get("ip", "") or "Unknown"

    result = {
        "hostname": hostname,
        "ip": ip,
        "patch_date": "Not found",
        "last_reboot": "Not found",
        "os_release": "Not found",
        "patch_status": "Not assessed",
        "notes": "No copied host data found in /inventory",
        "source": host.get("source", "inventory"),
    }

    host_file = DEFAULT_INVENTORY_DIR / hostname
    if not host_file.exists():
        host_file = DEFAULT_INVENTORY_DIR / host.get("hostname", "")
    parsed = parse_collected_host_file(host_file) if host_file.exists() else None
    if parsed:
        result.update(parsed)
        result["patch_status"] = "Assessed"
        result["notes"] = parsed.get("notes", "")
        return result

    return result


def summarize_reboot_counts(rows: List[Dict[str, str]]) -> Dict[str, int]:
    counts = {
        "Reboot should not be necessary": 0,
        "Reboot is probably not necessary": 0,
        "Reboot is required to fully utilize these updates": 0,
    }
    for row in rows:
        notes = (row.get("notes") or "").strip().lower()
        if "required" in notes and ("fully utilize" in notes or "these updates" in notes or "required" in notes):
            counts["Reboot is required to fully utilize these updates"] += 1
        elif "probably not necessary" in notes:
            counts["Reboot is probably not necessary"] += 1
        elif "should not be necessary" in notes:
            counts["Reboot should not be necessary"] += 1
    return counts


def build_reboot_inventory(rows: List[Dict[str, str]]) -> str:
    lines: List[str] = []
    for row in rows:
        notes = (row.get("notes") or "").strip().lower()
        if "required" in notes and ("fully utilize" in notes or "these updates" in notes or "required" in notes):
            hostname = row.get("hostname", "").strip()
            ip = row.get("ip", "").strip()
            if hostname and ip:
                lines.append(f"{hostname} ansible_host={ip}")
    return "\n".join(lines) + ("\n" if lines else "")


def build_html_report(rows: List[Dict[str, str]], issues: List[Dict[str, str]], title: str = "LLE Patch Status Report", reboot_inventory_filename: Optional[str] = None, reboot_inventory_content: Optional[str] = None) -> str:
    rows_html = []
    for row in rows:
        rows_html.append(
            "<tr>"
            f"<td>{html.escape(row.get('hostname',''))}</td>"
            f"<td>{html.escape(row.get('ip',''))}</td>"
            f"<td>{html.escape(row.get('patch_date',''))}</td>"
            f"<td>{html.escape(row.get('last_reboot',''))}</td>"
            f"<td>{html.escape(row.get('os_release',''))}</td>"
            f"<td>{html.escape(row.get('patch_status',''))}</td>"
            f"<td>{html.escape(row.get('notes',''))}</td>"
            f"<td>{html.escape(row.get('source',''))}</td>"
            "</tr>"
        )

    issues_html = []
    for issue in issues:
        issues_html.append(
            "<tr>"
            f"<td>{html.escape(issue.get('hostname',''))}</td>"
            f"<td>{html.escape(issue.get('ip',''))}</td>"
            f"<td>{html.escape(issue.get('issue',''))}</td>"
            f"<td>{html.escape(issue.get('source',''))}</td>"
            "</tr>"
        )

    counts = summarize_reboot_counts(rows)
    reboot_count = counts['Reboot is required to fully utilize these updates']
    download_link = ""
    if reboot_inventory_filename and reboot_inventory_content:
        href = f"data:text/plain;charset=utf-8,{urllib.parse.quote(reboot_inventory_content, safe='')}"
        download_link = (
            f"<div class=\"summary-card\" style=\"grid-column: span 3; text-align: center;\">"
            f"<a href=\"{href}\" download=\"{html.escape(reboot_inventory_filename)}\" style=\"text-decoration:none;color:#1d4ed8;font-weight:600;\">"
            f"Download reboot inventory ({reboot_count} host{'s' if reboot_count != 1 else ''}): {html.escape(reboot_inventory_filename)}"
            f"</a></div>"
        )
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2937; }}
    .report-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 12px; }}
    .report-header h1 {{ margin: 0; font-size: 28px; color: #0f172a; }}
    .report-header img {{ max-height: 48px; object-fit: contain; }}
    h2 {{ color: #0f172a; }}
    .meta {{ color: #475569; margin-bottom: 18px; }}
    .summary {{ background: #f8fafc; padding: 12px; border-left: 4px solid #2563eb; margin-bottom: 20px; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; margin-top: 8px; }}
    .summary-card {{ background: white; border: 1px solid #dbeafe; padding: 8px 10px; border-radius: 6px; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 24px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: left; font-size: 12px; }}
    th {{ background: #e2e8f0; cursor: pointer; }}
    th:hover {{ background: #dbeafe; }}
    .footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid #cbd5e1; color: #475569; font-size: 13px; }}
  </style>
</head>
<body>
  <div class="report-header">
    <h1>{title}</h1>
    <img src="https://www.incomm.com/wp-content/uploads/2022/04/incomm_payments_logo_hrz.png__1200x372_q85_subsampling-2-2.png" alt="InComm Payments logo">
  </div>
  <div class=\"meta\">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
  <div class=\"summary\">
    <strong>Summary:</strong> {len(rows)} assessed server entries and {len(issues)} issue entries.
    <div class=\"summary-grid\">
      <div class=\"summary-card\"><strong>Reboot should not be necessary:</strong> {counts['Reboot should not be necessary']}</div>
      <div class=\"summary-card\"><strong>Reboot is probably not necessary:</strong> {counts['Reboot is probably not necessary']}</div>
      <div class=\"summary-card\"><strong>Reboot is required to fully utilize these updates:</strong> {counts['Reboot is required to fully utilize these updates']}</div>
      {download_link}
    </div>
  </div>

  <h2>Primary Report</h2>
  <table id=\"primary-report\">
    <thead>
      <tr>
        <th data-sort=\"hostname\">Hostname</th>
        <th data-sort=\"ip\">IP Address</th>
        <th data-sort=\"patch_date\">Patch Date</th>
        <th data-sort=\"last_reboot\">Last Reboot Date</th>
        <th data-sort=\"os_release\">OS Release</th>
        <th data-sort=\"patch_status\">Patch Status</th>
        <th data-sort=\"notes\">Notes</th>
        <th data-sort=\"source\">Source</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows_html) if rows_html else '<tr><td colspan="8">No data available.</td></tr>'}
    </tbody>
  </table>

  <h2>Secondary Report - Issues</h2>
  <table>
    <thead>
      <tr>
        <th>Hostname</th>
        <th>IP Address</th>
        <th>Issue</th>
        <th>Source</th>
      </tr>
    </thead>
    <tbody>
      {''.join(issues_html) if issues_html else '<tr><td colspan="4">No issues recorded.</td></tr>'}
    </tbody>
  </table>
  <script>
    const table = document.getElementById('primary-report');
    if (table) {{
      const headers = table.querySelectorAll('th[data-sort]');
      headers.forEach((header) => {{
        header.addEventListener('click', () => {{
          const tbody = table.querySelector('tbody');
          const rows = Array.from(tbody.querySelectorAll('tr'));
          const key = header.getAttribute('data-sort');
          const ascending = header.dataset.order !== 'asc';
          header.dataset.order = ascending ? 'asc' : 'desc';
          rows.sort((a, b) => {{
            const aText = a.cells[Array.from(headers).indexOf(header)].textContent.trim().toLowerCase();
            const bText = b.cells[Array.from(headers).indexOf(header)].textContent.trim().toLowerCase();
            return aText.localeCompare(bText) * (ascending ? 1 : -1);
          }});
          rows.forEach((row) => tbody.appendChild(row));
        }});
      }});
    }}
  </script>
  <div class="footer">This report was generated by an automation created by Unix team. Report any mismatch to apetrocino@incomm.com</div>
</body>
</html>
"""


def write_report(output_path: Path, html_content: str) -> None:
    output_path.write_text(html_content, encoding="utf-8")


def build_reports(
    inventory_files: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
    max_hosts: Optional[int] = None,
    environment: str = "LLE",
) -> Tuple[Path, List[Dict[str, str]], List[Dict[str, str]]]:
    output_dir = output_dir or WORKDIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    hosts = discover_hosts(inventory_files)
    hosts = filter_hosts_for_environment(hosts, environment)
    if max_hosts is not None:
        hosts = hosts[:max_hosts]
    rows: List[Dict[str, str]] = []
    issues: List[Dict[str, str]] = []
    for host in hosts:
        info = collect_host_data(host)
        if info.get("patch_status") == "Assessed":
            rows.append(info)
        else:
            issues.append({
                "hostname": info["hostname"],
                "ip": info["ip"],
                "issue": info.get("notes", "Not assessed"),
                "source": info.get("source", "inventory"),
            })
    config = ENVIRONMENT_CONFIG.get(environment.upper(), ENVIRONMENT_CONFIG["LLE"])
    reboot_inventory_filename = f"{environment}_to_reboot.ini"
    reboot_inventory_content = build_reboot_inventory(rows)
    html_report = build_html_report(
        rows,
        issues,
        title=config["title"],
        reboot_inventory_filename=reboot_inventory_filename,
        reboot_inventory_content=reboot_inventory_content,
    )
    timestamp = datetime.now().strftime("%Y%m%d")
    stem = Path(config["output_name"]).stem
    output_name = f"{stem}_{timestamp}.html"
    output_path = output_dir / output_name
    write_report(output_path, html_report)
    return output_path, rows, issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a polished patch report for specific environments")
    parser.add_argument("--inventory", action="append", dest="inventories", help="Inventory file to include")
    parser.add_argument("--output-dir", default=str(WORKDIR / "output"), help="Directory for generated report")
    parser.add_argument("--max-hosts", type=int, default=None, help="Limit the number of hosts processed for testing")
    parser.add_argument(
        "--environment",
        choices=sorted(ENVIRONMENT_CONFIG.keys()),
        default="LLE",
        help="Environment to report on (LLE, CAT3, FCV_DMZ)",
    )
    args = parser.parse_args()

    output_path, _, _ = build_reports(
        args.inventories,
        Path(args.output_dir),
        max_hosts=args.max_hosts,
        environment=args.environment,
    )
    print(output_path)


if __name__ == "__main__":
    main()
