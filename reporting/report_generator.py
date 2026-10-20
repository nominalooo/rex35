"""
ReportGenerator — Professional pentest reporting
Создаёт:
- HTML dashboard с графиками
- Markdown отчёт
- JSON export для других инструментов
- Timeline атаки
- Network visualization
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class ReportGenerator:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.report_dir = workspace / "reports"
        self.report_dir.mkdir(exist_ok=True)
    
    def generate_full_report(self, results: Dict, target: str) -> Path:
        """Генерация полного отчёта (HTML + Markdown + JSON)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f"pentest_{target.replace('.', '_')}_{timestamp}"
        
        # 1. JSON export
        json_path = self.report_dir / f"{report_name}.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # 2. Markdown report
        md_path = self.generate_markdown(results, target, report_name)
        
        # 3. HTML dashboard
        html_path = self.generate_html_dashboard(results, target, report_name)
        
        print(f"[REPORT] Full report generated:")
        print(f"  - JSON: {json_path}")
        print(f"  - Markdown: {md_path}")
        print(f"  - HTML: {html_path}")
        
        return html_path
    
    def generate_markdown(self, results: Dict, target: str, report_name: str) -> Path:
        """Генерация Markdown отчёта"""
        md_path = self.report_dir / f"{report_name}.md"
        
        md_content = f"""# Penetration Test Report: {target}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Target:** `{target}`  
**Operator:** REX35 Autonomous Pentest System

---

## Executive Summary

This report contains findings from an automated penetration test performed against **{target}**.

### Key Statistics
- **Total Vulnerabilities Found:** {self._count_vulns(results)}
- **Critical Findings:** {self._count_critical(results)}
- **High Findings:** {self._count_high(results)}
- **Endpoints Tested:** {len(results.get('endpoints', []))}
- **Subdomains Discovered:** {len(results.get('subdomains', []))}

---

## 1. Reconnaissance

### 1.1 Subdomains Discovered
"""
        # Subdomains
        subdomains = results.get('subdomains', [])
        if subdomains:
            md_content += f"Found **{len(subdomains)}** subdomains:\n\n"
            for sub in subdomains[:50]:
                md_content += f"- `{sub}`\n"
        else:
            md_content += "*No subdomains discovered.*\n"
        
        # Enumeration results
        enum_results = results.get('enumeration', {})
        if enum_results:
            md_content += "\n### 1.2 API Intelligence\n\n"
            
            # Shodan
            shodan = enum_results.get('shodan_results', [])
            if shodan:
                md_content += f"#### Shodan Results ({len(shodan)} hosts)\n\n"
                for host in shodan[:10]:
                    md_content += f"- **{host.get('ip')}:{host.get('port')}** — {host.get('product', 'unknown')} {host.get('version', '')}\n"
                    if host.get('vulns'):
                        md_content += f"  - ⚠️ **CVEs:** {', '.join(host['vulns'])}\n"
            
            # Subdomain takeovers
            takeovers = enum_results.get('subdomain_takeovers', [])
            if takeovers:
                md_content += f"\n#### 🚨 Subdomain Takeover Vulnerabilities ({len(takeovers)})\n\n"
                for t in takeovers:
                    md_content += f"- **{t['subdomain']}** — Vulnerable via {t['service']} (HTTP {t['status_code']})\n"
            
            # Cloud buckets
            buckets = enum_results.get('cloud_buckets', [])
            if buckets:
                md_content += f"\n#### Cloud Storage Buckets ({len(buckets)})\n\n"
                for bucket in buckets:
                    access = "🔓 OPEN" if bucket['accessible'] else "🔒 EXISTS"
                    md_content += f"- {access} **{bucket['provider']}**: `{bucket['bucket']}`\n"
            
            # GitHub leaks
            github = enum_results.get('github_leaks', [])
            if github:
                md_content += f"\n#### 🔍 GitHub Leaks ({len(github)})\n\n"
                for leak in github[:10]:
                    md_content += f"- **{leak['repo']}** — {leak['path']} ([link]({leak['url']}))\n"
        
        # Endpoints
        md_content += "\n---\n\n## 2. Attack Surface\n\n### 2.1 Discovered Endpoints\n\n"
        endpoints = results.get('endpoints', [])
        if endpoints:
            md_content += f"Found **{len(endpoints)}** endpoints:\n\n"
            for ep in endpoints[:100]:
                md_content += f"- `{ep.get('method', 'GET')} {ep.get('url', ep.get('path', 'unknown'))}`"
                if ep.get('status_code'):
                    md_content += f" → HTTP {ep['status_code']}"
                md_content += "\n"
        
        # Vulnerabilities
        md_content += "\n---\n\n## 3. Vulnerabilities\n\n"
        
        vulns = results.get('vulnerabilities', [])
        if vulns:
            # Group by severity
            critical = [v for v in vulns if v.get('severity') == 'CRITICAL']
            high = [v for v in vulns if v.get('severity') == 'HIGH']
            medium = [v for v in vulns if v.get('severity') == 'MEDIUM']
            low = [v for v in vulns if v.get('severity') == 'LOW']
            
            if critical:
                md_content += "### 🔴 CRITICAL Vulnerabilities\n\n"
                for v in critical:
                    md_content += f"#### {v.get('type', 'Unknown')}\n"
                    md_content += f"- **Endpoint:** `{v.get('endpoint', 'N/A')}`\n"
                    md_content += f"- **Description:** {v.get('description', 'No description')}\n"
                    if v.get('payload'):
                        md_content += f"- **Payload:** `{v['payload']}`\n"
                    if v.get('evidence'):
                        md_content += f"- **Evidence:** {v['evidence']}\n"
                    md_content += "\n"
            
            if high:
                md_content += "### 🟠 HIGH Vulnerabilities\n\n"
                for v in high:
                    md_content += f"#### {v.get('type', 'Unknown')}\n"
                    md_content += f"- **Endpoint:** `{v.get('endpoint', 'N/A')}`\n"
                    md_content += f"- **Description:** {v.get('description', 'No description')}\n"
                    md_content += "\n"
            
            if medium:
                md_content += "### 🟡 MEDIUM Vulnerabilities\n\n"
                for v in medium[:10]:
                    md_content += f"- **{v.get('type')}** at `{v.get('endpoint')}`\n"
            
            if low:
                md_content += f"\n### 🟢 LOW Vulnerabilities ({len(low)})\n\n"
                md_content += "*See JSON report for full list.*\n"
        else:
            md_content += "*No vulnerabilities detected.*\n"
        
        # Recommendations
        md_content += "\n---\n\n## 4. Recommendations\n\n"
        md_content += self._generate_recommendations(results)
        
        # Footer
        md_content += "\n---\n\n## 5. Appendix\n\n"
        md_content += f"**Full JSON Report:** `{report_name}.json`\n\n"
        md_content += "*This report was generated automatically by REX35.*\n"
        
        with open(md_path, 'w') as f:
            f.write(md_content)
        
        return md_path
    
    def generate_html_dashboard(self, results: Dict, target: str, report_name: str) -> Path:
        """Генерация HTML dashboard с графиками"""
        html_path = self.report_dir / f"{report_name}.html"
        
        # Count vulnerabilities by severity
        vulns = results.get('vulnerabilities', [])
        critical_count = len([v for v in vulns if v.get('severity') == 'CRITICAL'])
        high_count = len([v for v in vulns if v.get('severity') == 'HIGH'])
        medium_count = len([v for v in vulns if v.get('severity') == 'MEDIUM'])
        low_count = len([v for v in vulns if v.get('severity') == 'LOW'])
        
        # Build HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pentest Report: {target}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #F6F1E8;
            color: #1F2421;
            padding: 2rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #FBF7EF;
            border-radius: 12px;
            padding: 2.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }}
        h1 {{
            font-family: 'DM Serif Display', Georgia, serif;
            font-size: 2.5rem;
            font-weight: 700;
            color: #1F2421;
            margin-bottom: 0.5rem;
        }}
        .subtitle {{
            color: #8A8A80;
            font-size: 1rem;
            margin-bottom: 2rem;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }}
        .stat-card {{
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            border: 2px solid #E2D9C8;
        }}
        .stat-card.critical {{ border-color: #DC2626; }}
        .stat-card.high {{ border-color: #EA580C; }}
        .stat-card.medium {{ border-color: #D97706; }}
        .stat-card.low {{ border-color: #16A34A; }}
        .stat-number {{
            font-size: 3rem;
            font-weight: 700;
            line-height: 1;
            margin-bottom: 0.5rem;
        }}
        .stat-card.critical .stat-number {{ color: #DC2626; }}
        .stat-card.high .stat-number {{ color: #EA580C; }}
        .stat-card.medium .stat-number {{ color: #D97706; }}
        .stat-card.low .stat-number {{ color: #16A34A; }}
        .stat-label {{
            color: #8A8A80;
            text-transform: uppercase;
            font-size: 0.875rem;
            letter-spacing: 0.05em;
            font-weight: 600;
        }}
        .section {{
            margin-bottom: 2.5rem;
        }}
        .section-title {{
            font-family: 'DM Serif Display', Georgia, serif;
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: #2A2723;
        }}
        .vuln-list {{
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            border: 1px solid #E2D9C8;
        }}
        .vuln-item {{
            padding: 1rem;
            border-left: 4px solid #E2D9C8;
            margin-bottom: 1rem;
            background: #F6F1E8;
            border-radius: 4px;
        }}
        .vuln-item.critical {{ border-left-color: #DC2626; }}
        .vuln-item.high {{ border-left-color: #EA580C; }}
        .vuln-item.medium {{ border-left-color: #D97706; }}
        .vuln-type {{
            font-weight: 700;
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }}
        .vuln-endpoint {{
            font-family: 'Courier New', monospace;
            background: #2A2723;
            color: #F6F1E8;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
            display: inline-block;
            margin: 0.5rem 0;
        }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .badge.critical {{ background: #FEE2E2; color: #DC2626; }}
        .badge.high {{ background: #FFEDD5; color: #EA580C; }}
        .badge.medium {{ background: #FEF3C7; color: #D97706; }}
        .badge.low {{ background: #D1FAE5; color: #16A34A; }}
        .footer {{
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 2px solid #E2D9C8;
            color: #8A8A80;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 Penetration Test Report</h1>
        <div class="subtitle">
            Target: <strong>{target}</strong> | 
            Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 
            Operator: REX35
        </div>
        
        <div class="stats-grid">
            <div class="stat-card critical">
                <div class="stat-number">{critical_count}</div>
                <div class="stat-label">Critical</div>
            </div>
            <div class="stat-card high">
                <div class="stat-number">{high_count}</div>
                <div class="stat-label">High</div>
            </div>
            <div class="stat-card medium">
                <div class="stat-number">{medium_count}</div>
                <div class="stat-label">Medium</div>
            </div>
            <div class="stat-card low">
                <div class="stat-number">{low_count}</div>
                <div class="stat-label">Low</div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">Discovered Assets</h2>
            <div class="vuln-list">
                <p><strong>Subdomains:</strong> {len(results.get('subdomains', []))}</p>
                <p><strong>Endpoints:</strong> {len(results.get('endpoints', []))}</p>
                <p><strong>Cloud Buckets:</strong> {len(results.get('enumeration', ).get('cloud_buckets', []))}</p>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">Vulnerabilities</h2>
            <div class="vuln-list">
"""
        
        # Add vulnerabilities
        if vulns:
            for vuln in vulns[:50]:  # Limit to 50 for HTML
                severity = vuln.get('severity', 'LOW').lower()
                html += f"""
                <div class="vuln-item {severity}">
                    <div class="vuln-type">
                        {vuln.get('type', 'Unknown')}
                        <span class="badge {severity}">{vuln.get('severity', 'LOW')}</span>
                    </div>
                    <div class="vuln-endpoint">{vuln.get('endpoint', 'N/A')}</div>
                    <p>{vuln.get('description', 'No description')}</p>
                </div>
"""
        else:
            html += "<p><em>No vulnerabilities detected.</em></p>"
        
        html += """
            </div>
        </div>
        
        <div class="footer">
            <p>This report was generated automatically by <strong>REX35</strong> autonomous pentest system.</p>
            <p>For full details, see the JSON and Markdown reports.</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(html_path, 'w') as f:
            f.write(html)
        
        return html_path
    
    def _count_vulns(self, results: Dict) -> int:
        return len(results.get('vulnerabilities', []))
    
    def _count_critical(self, results: Dict) -> int:
        vulns = results.get('vulnerabilities', [])
        return len([v for v in vulns if v.get('severity') == 'CRITICAL'])
    
    def _count_high(self, results: Dict) -> int:
        vulns = results.get('vulnerabilities', [])
        return len([v for v in vulns if v.get('severity') == 'HIGH'])
    
    def _generate_recommendations(self, results: Dict) -> str:
        """Генерация рекомендаций на основе найденных уязвимостей"""
        vulns = results.get('vulnerabilities', [])
        recommendations = []
        
        # Check for specific vulnerability types
        vuln_types = {v.get('type', '') for v in vulns}
        
        if 'SQL Injection' in vuln_types:
            recommendations.append("- **SQL Injection:** Use parameterized queries/prepared statements. Never concatenate user input into SQL.")
        
        if 'XSS' in vuln_types or 'Cross-Site Scripting' in vuln_types:
            recommendations.append("- **XSS:** Implement proper output encoding. Use Content-Security-Policy headers. Sanitize all user input.")
        
        if 'IDOR' in vuln_types or 'Insecure Direct Object Reference' in vuln_types:
            recommendations.append("- **IDOR:** Implement proper authorization checks. Use UUID/non-sequential IDs. Validate user permissions on every request.")
        
        if 'Command Injection' in vuln_types:
            recommendations.append("- **Command Injection:** Never execute user input. Use whitelisting for allowed commands. Run services with minimal privileges.")
        
        if 'SSRF' in vuln_types:
            recommendations.append("- **SSRF:** Validate and whitelist URLs. Block internal IP ranges. Use network segmentation.")
        
        # Check enumeration results
        enum_results = results.get('enumeration', {})
        if enum_results.get('subdomain_takeovers'):
            recommendations.append("- **Subdomain Takeover:** Remove DNS records for decommissioned services. Monitor for dangling CNAMEs.")
        
        if enum_results.get('cloud_buckets'):
            open_buckets = [b for b in enum_results['cloud_buckets'] if b.get('accessible')]
            if open_buckets:
                recommendations.append("- **Open Cloud Storage:** Restrict bucket permissions. Enable logging. Use IAM policies.")
        
        if enum_results.get('github_leaks'):
            recommendations.append("- **GitHub Leaks:** Rotate exposed credentials immediately. Use .gitignore for sensitive files. Implement pre-commit hooks.")
        
        if not recommendations:
            recommendations.append("- Continue regular security assessments")
            recommendations.append("- Implement Web Application Firewall (WAF)")
            recommendations.append("- Enable security logging and monitoring")
            recommendations.append("- Keep all software up to date")
        
        return "\n".join(recommendations)
