"""
AUTONOMOUS ORCHESTRATOR — Chinese Killer Level
Улучшения:
- Parallel execution всех агентов (asyncio)
- Decision tree (автоматические решения)
- Dynamic wordlist generation
- Auto-reporting
- Persistent memory между циклами
"""
import asyncio, concurrent.futures, time, json
from pathlib import Path
from typing import Dict, List, Any
from pentest_db import PentestDB
from payload_generator import PayloadGenerator
from agents.scout import ScoutAgent
from agents.analyzer import AnalyzerAgent
from agents.attacker import AttackerAgent
from agents.enumerator import EnumerationAgent
from agents.persistence import PersistenceAgent

class AutonomousOrchestrator:
    def __init__(self, workspace: Path, db_path: Path, attacker_ip: str = "10.10.10.10", attacker_port: int = 4444):
        self.workspace = workspace
        self.db = PentestDB(db_path)
        self.payload_gen = PayloadGenerator(attacker_ip, attacker_port)
        
        # Initialize agents
        self.scout = ScoutAgent(workspace)
        self.analyzer = AnalyzerAgent(workspace)
        self.attacker = AttackerAgent(workspace)
        self.enumerator = EnumerationAgent(workspace, workspace.parent / "config" / "api_keys.json")
        self.persistence = PersistenceAgent(workspace, attacker_ip, attacker_port)
        
        self.state = {
            "current_phase": "idle",
            "completed_phases": [],
            "target_id": None,
            "findings": [],
            "exploited": [],
            "pivot_targets": [],
            "credentials": [],
            "access_gained": False
        }
        
        self.cycle_count = 0
        self.max_cycles = 3
        self.decision_log = []
    
    async def execute_autonomous_scan(self, target: str) -> Dict:
        """
        ГЛАВНЫЙ АВТОНОМНЫЙ ЦИКЛ
        """
        print(f"\n{'='*70}")
        print(f"🔥 REX35 AUTONOMOUS PENTEST — CHINESE KILLER LEVEL")
        print(f"Target: {target}")
        print(f"{'='*70}\n")
        
        start_time = time.time()
        
        # PHASE 0: INITIALIZATION
        target_id = self.db.add_target(target, "Autonomous scan initiated")
        self.state["target_id"] = target_id
        scan_id = self.db.start_scan(target_id, "autonomous_full")
        
        # MAIN LOOP
        while self.cycle_count < self.max_cycles:
            self.cycle_count += 1
            print(f"\n{'━'*70}")
            print(f"🔄 CYCLE {self.cycle_count}/{self.max_cycles}")
            print(f"{'━'*70}\n")
            
            # PARALLEL EXECUTION: Scout + Enumerator
            await self.phase_parallel_recon(target)
            
            # ANALYZE: Tech stack + Vulns
            await self.phase_analyze()
            
            # DECISION TREE: What to attack?
            attack_plan = self.build_attack_plan()
            
            # EXECUTE ATTACKS
            await self.phase_execute_attacks(attack_plan)
            
            # POST-EXPLOITATION: If access gained
            if self.state["access_gained"]:
                await self.phase_post_exploitation()
            
            # PIVOT: Look for new targets
            pivot_targets = await self.phase_pivot()
            
            if not pivot_targets and not self.state["access_gained"]:
                print("\n✓ No new pivot targets and no access gained. Ending cycle.")
                break
        
        # FINALIZE
        duration = int(time.time() - start_time)
        findings_count = len(self.state["findings"])
        self.db.finish_scan(scan_id, findings_count)
        
        # GENERATE REPORT
        await self.generate_final_report(target, duration)
        
        stats = self.db.get_target_stats(target_id)
        
        print(f"\n{'='*70}")
        print(f"✅ AUTONOMOUS PENTEST COMPLETE")
        print(f"Duration: {duration}s")
        print(f"Cycles: {self.cycle_count}")
        print(f"Findings: {findings_count}")
        print(f"Access gained: {'YES' if self.state['access_gained'] else 'NO'}")
        print(f"{'='*70}\n")
        
        return {
            "target": target,
            "duration": duration,
            "cycles": self.cycle_count,
            "stats": stats,
            "findings": self.state["findings"],
            "exploited": self.state["exploited"],
            "access_gained": self.state["access_gained"]
        }
    
    async def phase_parallel_recon(self, target: str):
        """
        PARALLEL RECONNAISSANCE
        Scout + Enumerator run simultaneously
        """
        print(f"[PHASE 1] 🔍 PARALLEL RECONNAISSANCE")
        self.state["current_phase"] = "recon"
        
        loop = asyncio.get_event_loop()
        
        # Run Scout and Enumerator in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            scout_future = loop.run_in_executor(executor, self.scout.execute, target)
            enum_future = loop.run_in_executor(executor, self.enumerator.execute, target, None)
            
            scout_results, enum_results = await asyncio.gather(scout_future, enum_future)
        
        # Store results
        self.state["scout_data"] = scout_results
        self.state["enum_data"] = enum_results
        
        # Save to DB
        for subdomain in scout_results.get("subdomains", []):
            subdomain_id = self.db.add_subdomain(self.state["target_id"], subdomain)
        
        for host in scout_results.get("live_hosts", []):
            subdomain_id = self.db.add_subdomain(
                self.state["target_id"], 
                host.get("url", ""),
                is_live=True,
                status_code=host.get("status"),
                tech_stack=json.dumps(host.get("tech", []))
            )
        
        for endpoint in scout_results.get("endpoints", []):
            self.db.add_endpoint(subdomain_id if subdomain_id else 1, endpoint)
        
        # Certificate transparency subdomains
        cert_domains = enum_results.get("cert_transparency", [])
        if cert_domains:
            print(f"  → Adding {len(cert_domains)} domains from cert transparency")
            for domain in cert_domains[:20]:  # Limit to 20
                self.db.add_subdomain(self.state["target_id"], domain)
        
        # Subdomain takeover findings
        for takeover in enum_results.get("subdomain_takeovers", []):
            subdomain_id = self.db.add_subdomain(self.state["target_id"], takeover["subdomain"])
            vuln_id = self.db.add_vulnerability(
                self.state["target_id"],
                subdomain_id,
                None,
                "subdomain_takeover",
                "HIGH",
                f"Subdomain Takeover via {takeover['service']}",
                f"Subdomain {takeover['subdomain']} is vulnerable to takeover via {takeover['service']}",
                takeover.get("status_code", "")
            )
            self.state["findings"].append({
                "type": "subdomain_takeover",
                "severity": "HIGH",
                "details": takeover
            })
        
        print(f"✓ Reconnaissance complete")
        print(f"  - Subdomains: {len(scout_results.get('subdomains', []))}")
        print(f"  - Live hosts: {len(scout_results.get('live_hosts', []))}")
        print(f"  - Endpoints: {len(scout_results.get('endpoints', []))}")
        print(f"  - Cert transparency: {len(cert_domains)}")
        print(f"  - Subdomain takeovers: {len(enum_results.get('subdomain_takeovers', []))}")
    
    async def phase_analyze(self):
        """
        ANALYSIS PHASE
        Tech detection + Vulnerability scanning
        """
        print(f"\n[PHASE 2] 🔬 ANALYSIS & VULN SCANNING")
        self.state["current_phase"] = "analyze"
        
        scout_data = self.state.get("scout_data", {})
        target = list(scout_data.get("live_hosts", [{}]))[0].get("url", "")
        
        if not target:
            print("  ⚠ No live hosts found, skipping analysis")
            return
        
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            analyzer_results = await loop.run_in_executor(
                executor, self.analyzer.execute, scout_data, target
            )
        
        self.state["analyzer_data"] = analyzer_results
        
        # Save vulnerabilities to DB
        for vuln in analyzer_results.get("vulnerabilities", []):
            vuln_id = self.db.add_vulnerability(
                self.state["target_id"],
                None,
                None,
                vuln.get("template", "unknown"),
                vuln.get("severity", "medium"),
                vuln.get("name", "Unknown"),
                "",
                vuln.get("matched_at", "")
            )
            self.state["findings"].append({
                "type": "vulnerability",
                "severity": vuln.get("severity"),
                "details": vuln
            })
        
        print(f"✓ Analysis complete")
        print(f"  - Frameworks: {len(analyzer_results.get('frameworks', []))}")
        print(f"  - Services: {len(analyzer_results.get('services', []))}")
        print(f"  - WAF: {analyzer_results.get('waf', 'None')}")
        print(f"  - Vulnerabilities: {len(analyzer_results.get('vulnerabilities', []))}")
    
    def build_attack_plan(self) -> List[Dict]:
        """
        DECISION TREE
        Построение плана атаки на основе найденных уязвимостей
        """
        print(f"\n[DECISION TREE] 🧠 Building attack plan...")
        
        analyzer_data = self.state.get("analyzer_data", {})
        scout_data = self.state.get("scout_data", {})
        enum_data = self.state.get("enum_data", {})
        
        vulnerabilities = analyzer_data.get("vulnerabilities", [])
        endpoints = scout_data.get("endpoints", [])
        waf = analyzer_data.get("waf")
        
        plan = []
        
        # Rule 1: SQLi found → exploit with sqlmap
        sqli_vulns = [v for v in vulnerabilities if "sql" in v.get("name", "").lower()]
        if sqli_vulns:
            plan.append({
                "action": "exploit_sqli",
                "target": sqli_vulns[0].get("matched_at"),
                "payload": "sqlmap",
                "priority": 1,
                "reason": "SQL injection detected - high impact"
            })
            self.log_decision("SQLi detected → launching sqlmap")
        
        # Rule 2: XSS found + login page → steal cookies
        xss_vulns = [v for v in vulnerabilities if "xss" in v.get("name", "").lower()]
        login_endpoints = [e for e in endpoints if any(kw in e.lower() for kw in ["login", "auth", "signin"])]
        if xss_vulns and login_endpoints:
            plan.append({
                "action": "xss_cookie_steal",
                "target": xss_vulns[0].get("matched_at"),
                "priority": 2,
                "reason": "XSS + login page → cookie stealing opportunity"
            })
            self.log_decision("XSS + login endpoint → attempting cookie theft")
        
        # Rule 3: Upload endpoint found → attempt webshell
        upload_endpoints = [e for e in endpoints if "upload" in e.lower() or "file" in e.lower()]
        if upload_endpoints:
            plan.append({
                "action": "upload_webshell",
                "target": upload_endpoints[0],
                "priority": 1,
                "reason": "File upload endpoint detected"
            })
            self.log_decision("Upload endpoint → attempting webshell injection")
        
        # Rule 4: Open cloud buckets → attempt data exfiltration
        open_buckets = [b for b in enum_data.get("cloud_buckets", []) if b.get("accessible")]
        if open_buckets:
            plan.append({
                "action": "enumerate_bucket",
                "target": open_buckets[0].get("url"),
                "priority": 3,
                "reason": "Open cloud bucket found"
            })
            self.log_decision(f"Open {open_buckets[0]['provider']} bucket → enumerating")
        
        # Rule 5: LFI + SSRF → RCE chain
        lfi_vulns = [v for v in vulnerabilities if "lfi" in v.get("name", "").lower() or "traversal" in v.get("name", "").lower()]
        ssrf_vulns = [v for v in vulnerabilities if "ssrf" in v.get("name", "").lower()]
        if lfi_vulns and ssrf_vulns:
            plan.append({
                "action": "chain_lfi_ssrf",
                "targets": [lfi_vulns[0].get("matched_at"), ssrf_vulns[0].get("matched_at")],
                "priority": 1,
                "reason": "LFI + SSRF detected → RCE chain possible"
            })
            self.log_decision("LFI + SSRF → attempting exploit chain to RCE")
        
        # Rule 6: No specific vulns → directory brute-force
        if not plan:
            plan.append({
                "action": "directory_bruteforce",
                "target": scout_data.get("live_hosts", [{}])[0].get("url", ""),
                "priority": 5,
                "reason": "No obvious vulns → brute-forcing directories"
            })
            self.log_decision("No clear vulnerabilities → falling back to directory brute-force")
        
        # Sort by priority
        plan.sort(key=lambda x: x["priority"])
        
        print(f"✓ Attack plan built: {len(plan)} actions")
        for i, action in enumerate(plan, 1):
            print(f"  {i}. {action['action']} → {action['reason']}")
        
        return plan
    
    async def phase_execute_attacks(self, attack_plan: List[Dict]):
        """
        EXECUTE ATTACKS
        """
        print(f"\n[PHASE 3] 💥 EXECUTING ATTACKS")
        self.state["current_phase"] = "attack"
        
        analyzer_data = self.state.get("analyzer_data", {})
        
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Run attacker agent
            target = attack_plan[0].get("target", "") if attack_plan else ""
            attacker_results = await loop.run_in_executor(
                executor, 
                self.attacker.execute, 
                analyzer_data,
                target
            )
        
        self.state["attacker_data"] = attacker_results
        
        # Check if we gained access
        if attacker_results.get("sqli_found") or attacker_results.get("directories"):
            self.state["access_gained"] = True
            print("  🎯 ACCESS GAINED!")
        
        # Mark exploited vulnerabilities
        for sqli in attacker_results.get("sqli_found", []):
            self.state["exploited"].append({
                "type": "sqli",
                "url": sqli["url"],
                "waf_bypassed": sqli.get("waf_bypassed", False)
            })
        
        print(f"✓ Attack execution complete")
        print(f"  - SQLi exploited: {len(attacker_results.get('sqli_found', []))}")
        print(f"  - XSS found: {len(attacker_results.get('xss_found', []))}")
        print(f"  - Directories: {len(attacker_results.get('directories', []))}")
        print(f"  - Exploit chains: {len(attacker_results.get('exploited', []))}")
    
    async def phase_post_exploitation(self):
        """
        POST-EXPLOITATION
        Deploy persistence mechanisms
        """
        print(f"\n[PHASE 4] 🚀 POST-EXPLOITATION")
        self.state["current_phase"] = "post_exploit"
        
        target_info = {
            "os_type": "linux",  # TODO: detect from tech stack
            "url": self.state.get("scout_data", {}).get("live_hosts", [{}])[0].get("url", ""),
            "upload_path": "/var/www/html"
        }
        
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            persistence_results = await loop.run_in_executor(
                executor,
                self.persistence.execute,
                target_info,
                "rce"
            )
        
        self.state["persistence_data"] = persistence_results
        
        # Save payloads to file
        self.persistence.save_payloads_to_file()
        
        print(f"✓ Post-exploitation complete")
        print(f"  - Webshells: {len(persistence_results.get('webshells', []))}")
        print(f"  - Persistence mechanisms: {len(persistence_results.get('cron_jobs', []))+ len(persistence_results.get('services', []))}")
    
    async def phase_pivot(self) -> List[str]:
        """
        PIVOT PHASE
        """
        print(f"\n[PHASE 5] 🔄 PIVOT & LATERAL MOVEMENT")
        self.state["current_phase"] = "pivot"
        
        pivot_targets = []
        
        # Check for credentials in DB
        creds = self.db.get_credentials(self.state["target_id"])
        if creds:
            print(f"  → Found {len(creds)} credentials")
            self.state["credentials"].extend(creds)
        
        # TODO: Parse internal IPs from responses
        # TODO: Try credentials on other services
        
        return pivot_targets
    
    async def generate_final_report(self, target: str, duration: int):
        """
        AUTO-REPORTING
        Generate Markdown report
        """
        print(f"\n[REPORTING] 📊 Generating final report...")
        
        report_file = self.workspace / f"report_{target.replace('://', '_').replace('/', '_')}.md"
        
        stats = self.db.get_target_stats(self.state["target_id"])
        
        report = []
        report.append(f"# REX35 Penetration Test Report")
        report.append(f"\n**Target**: {target}")
        report.append(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Duration**: {duration}s ({duration//60}m {duration%60}s)")
        report.append(f"**Cycles**: {self.cycle_count}")
        report.append(f"**Access Gained**: {'✅ YES' if self.state['access_gained'] else '❌ NO'}")
        
        report.append(f"\n## Executive Summary")
        report.append(f"Autonomous penetration test completed with {len(self.state['findings'])} findings.")
        report.append(f"Total vulnerabilities: {sum(stats['vulnerabilities'].values())}")
        report.append(f"Exploited: {len(self.state['exploited'])}")
        
        report.append(f"\n## Statistics")
        report.append(f"- **Subdomains**: {stats['subdomains']['total']} (live: {stats['subdomains']['live']})")
        report.append(f"- **Endpoints**: {stats['endpoints']}")
        report.append(f"- **Vulnerabilities by severity**:")
        for severity, count in stats['vulnerabilities'].items():
            report.append(f"  - {severity.upper()}: {count}")
        report.append(f"- **Credentials found**: {stats['credentials']}")
        report.append(f"- **Exploit chains**: {stats['exploit_chains']}")
        
        report.append(f"\n## Decision Log")
        for i, decision in enumerate(self.decision_log, 1):
            report.append(f"{i}. {decision}")
        
        report.append(f"\n## Findings")
        for i, finding in enumerate(self.state['findings'], 1):
            report.append(f"\n### Finding #{i}: {finding['type'].upper()}")
            report.append(f"**Severity**: {finding['severity']}")
            report.append(f"**Details**: {json.dumps(finding['details'], indent=2)}")
        
        report.append(f"\n## Exploited Vulnerabilities")
        for i, exploit in enumerate(self.state['exploited'], 1):
            report.append(f"{i}. **{exploit['type'].upper()}** at {exploit.get('url', 'N/A')}")
        
        report.append(f"\n---")
        report.append(f"*Generated by REX35 Autonomous Pentest Framework*")
        
        with open(report_file, 'w') as f:
            f.write('\n'.join(report))
        
        print(f"✓ Report saved to {report_file}")
    
    def log_decision(self, decision: str):
        """Log decision for reporting"""
        self.decision_log.append(decision)
    
    def cleanup(self):
        """Cleanup resources"""
        self.db.close()



# ━━━ CLI ENTRY POINT ━━━
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <target>")
        sys.exit(1)
    
    target = sys.argv[1]
    workspace = Path("./workspace")
    db_path = workspace / "pentest.db"
    
    workspace.mkdir(exist_ok=True)
    
    orchestrator = AutonomousOrchestrator(workspace, db_path)
    
    try:
        result = asyncio.run(orchestrator.execute_autonomous_scan(target))
        print("\n✅ SCAN COMPLETE")
        print(json.dumps({k: v for k, v in result.items() if k not in ['findings', 'exploited']}, indent=2))
    finally:
        orchestrator.cleanup()
