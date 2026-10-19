"""
Orchestrator — координирует всех агентов
Workflow:
1. ScoutAgent → разведка
2. AnalyzerAgent → анализ (использует результаты Scout)
3. AttackerAgent → эксплуатация (использует результаты Analyzer)
4. Генерация финального отчёта
"""
import json, time
from pathlib import Path
from .scout import ScoutAgent
from .analyzer import AnalyzerAgent
from .attacker import AttackerAgent

class Orchestrator:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.scout = ScoutAgent(workspace)
        self.analyzer = AnalyzerAgent(workspace)
        self.attacker = AttackerAgent(workspace)
        
        self.final_report = {
            "target": "",
            "start_time": "",
            "end_time": "",
            "duration_seconds": 0,
            "summary": {},
            "scout_data": {},
            "analyzer_data": {},
            "attacker_data": {}
        }
    
    def execute(self, target: str) -> dict:
        """Полное автономное сканирование"""
        print(f"\n{'='*60}")
        print(f"🎯 AUTONOMOUS PENTEST INITIATED")
        print(f"Target: {target}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        self.final_report["target"] = target
        self.final_report["start_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # PHASE 1: SCOUT
            print("\n[PHASE 1/3] RECONNAISSANCE")
            scout_data = self.scout.execute(target)
            self.final_report["scout_data"] = scout_data
            print(self.scout.get_report())
            
            # PHASE 2: ANALYZER
            print("\n[PHASE 2/3] ANALYSIS & VULNERABILITY SCANNING")
            analyzer_data = self.analyzer.execute(scout_data, target)
            self.final_report["analyzer_data"] = analyzer_data
            print(self.analyzer.get_report())
            
            # PHASE 3: ATTACKER
            print("\n[PHASE 3/3] EXPLOITATION & VALIDATION")
            attacker_data = self.attacker.execute(analyzer_data, target)
            self.final_report["attacker_data"] = attacker_data
            print(self.attacker.get_report())
            
            # FINALIZE
            end_time = time.time()
            self.final_report["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.final_report["duration_seconds"] = int(end_time - start_time)
            
            self.generate_summary()
            self.save_report()
            
            print("\n" + "="*60)
            print("✅ PENTEST COMPLETE")
            print(f"Duration: {self.final_report['duration_seconds']}s")
            print(f"Report saved: {self.workspace}/pentest_report.json")
            print("="*60 + "\n")
            
            return self.final_report
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            self.final_report["error"] = str(e)
            return self.final_report
    
    def generate_summary(self):
        """Генерация краткой сводки"""
        scout = self.final_report["scout_data"]
        analyzer = self.final_report["analyzer_data"]
        attacker = self.final_report["attacker_data"]
        
        self.final_report["summary"] = {
            "subdomains_found": len(scout.get("subdomains", [])),
            "live_hosts": len(scout.get("live_hosts", [])),
            "endpoints_discovered": len(scout.get("endpoints", [])),
            "open_ports": len(scout.get("ports", [])),
            "frameworks_detected": len(analyzer.get("frameworks", [])),
            "services_detected": len(analyzer.get("services", [])),
            "waf_present": analyzer.get("waf") is not None,
            "vulnerabilities_found": len(analyzer.get("vulnerabilities", [])),
            "sqli_confirmed": len(attacker.get("sqli_found", [])),
            "xss_confirmed": len(attacker.get("xss_found", [])),
            "exploit_chains": len(attacker.get("exploited", [])),
            "severity": self.calculate_severity(analyzer, attacker)
        }
    
    def calculate_severity(self, analyzer: dict, attacker: dict) -> str:
        """Вычисление общей критичности"""
        vulns = analyzer.get("vulnerabilities", [])
        critical_count = sum(1 for v in vulns if v.get("severity") == "critical")
        high_count = sum(1 for v in vulns if v.get("severity") == "high")
        
        sqli = len(attacker.get("sqli_found", []))
        chains = len(attacker.get("exploited", []))
        
        if critical_count > 0 or sqli > 0 or chains > 0:
            return "CRITICAL"
        elif high_count > 3:
            return "HIGH"
        elif high_count > 0:
            return "MEDIUM"
        else:
            return "LOW"
    
    def save_report(self):
        """Сохранение отчёта в JSON"""
        report_path = self.workspace / "pentest_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.final_report, f, indent=2)
        
        # Также создаём markdown версию
        md_path = self.workspace / "pentest_report.md"
        with open(md_path, 'w') as f:
            f.write(self.generate_markdown_report())
    
    def generate_markdown_report(self) -> str:
        """Генерация markdown отчёта"""
        s = self.final_report["summary"]
        
        report = [
            f"# Penetration Test Report",
            f"",
            f"**Target:** {self.final_report['target']}  ",
            f"**Date:** {self.final_report['start_time']}  ",
            f"**Duration:** {self.final_report['duration_seconds']}s  ",
            f"**Overall Severity:** {s['severity']}  ",
            f"",
            f"## Executive Summary",
            f"",
            f"- Subdomains discovered: **{s['subdomains_found']}**",
            f"- Live hosts: **{s['live_hosts']}**",
            f"- Endpoints mapped: **{s['endpoints_discovered']}**",
            f"- Open ports: **{s['open_ports']}**",
            f"- Frameworks detected: **{s['frameworks_detected']}**",
            f"- Services identified: **{s['services_detected']}**",
            f"- WAF detected: **{'Yes' if s['waf_present'] else 'No'}**",
            f"- Vulnerabilities found: **{s['vulnerabilities_found']}**",
            f"- SQLi confirmed: **{s['sqli_confirmed']}**",
            f"- XSS confirmed: **{s['xss_confirmed']}**",
            f"- Exploit chains: **{s['exploit_chains']}**",
            f"",
            f"## Detailed Findings",
            f"",
            self.scout.get_report(),
            f"",
            self.analyzer.get_report(),
            f"",
            self.attacker.get_report(),
            f""
        ]
        
        return '\n'.join(report)
