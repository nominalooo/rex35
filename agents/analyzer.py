"""
AnalyzerAgent — tech stack detection & vulnerability scanning
Задачи:
- Framework detection (из knowledge/frameworks.json)
- Service detection (из knowledge/services.json)
- WAF detection (из knowledge/waf_bypasses.json)
- Vulnerability scanning (nuclei)
"""
import subprocess, json, os
from pathlib import Path

class AnalyzerAgent:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.knowledge_dir = Path(__file__).parent.parent / "knowledge"
        self.results = {
            "frameworks": [],
            "services": [],
            "waf": None,
            "vulnerabilities": []
        }
        
        # Load knowledge bases
        self.load_knowledge()
    
    def load_knowledge(self):
        """Загрузка баз знаний"""
        try:
            with open(self.knowledge_dir / "frameworks.json") as f:
                self.frameworks_db = json.load(f).get("frameworks", [])
            with open(self.knowledge_dir / "services.json") as f:
                self.services_db = json.load(f).get("services", [])
            with open(self.knowledge_dir / "waf_bypasses.json") as f:
                self.waf_db = json.load(f).get("waf_vendors", [])
            print("[ANALYZER] Knowledge bases loaded")
        except Exception as e:
            print(f"[ANALYZER] Error loading knowledge: {e}")
            self.frameworks_db = []
            self.services_db = []
            self.waf_db = []
    
    def execute(self, scout_data: dict, target: str) -> dict:
        """Полный анализ цели"""
        print(f"[ANALYZER] Starting analysis on {target}")
        
        # 1. Detect frameworks
        self.detect_frameworks(scout_data)
        
        # 2. Detect services
        self.detect_services(scout_data)
        
        # 3. Detect WAF
        self.detect_waf(target)
        
        # 4. Run nuclei
        self.run_nuclei(target)
        
        return self.results
    
    def detect_frameworks(self, scout_data: dict):
        """Детектим фреймворки по сигнатурам"""
        live_hosts = scout_data.get("live_hosts", [])
        
        for host_info in live_hosts:
            tech = host_info.get("tech", [])
            url = host_info.get("url", "")
            
            for framework in self.frameworks_db:
                # Check tech stack keywords
                detection = framework.get("detection", {})
                keywords = detection.get("keywords", [])
                
                if any(kw.lower() in ' '.join(tech).lower() for kw in keywords):
                    self.results["frameworks"].append({
                        "name": framework["name"],
                        "url": url,
                        "confidence": "high"
                    })
                    print(f"[ANALYZER] Detected framework: {framework['name']} at {url}")
        
        # Deduplicate
        seen = set()
        unique = []
        for fw in self.results["frameworks"]:
            key = (fw["name"], fw["url"])
            if key not in seen:
                seen.add(key)
                unique.append(fw)
        self.results["frameworks"] = unique
    
    def detect_services(self, scout_data: dict):
        """Детектим сервисы по открытым портам"""
        ports = scout_data.get("ports", [])
        
        for service in self.services_db:
            service_ports = service.get("ports", [])
            if any(port in ports for port in service_ports):
                self.results["services"].append({
                    "name": service["name"],
                    "ports": [p for p in service_ports if p in ports],
                    "cves": service.get("cve_keywords", [])
                })
                print(f"[ANALYZER] Detected service: {service['name']} on ports {service_ports}")
    
    def detect_waf(self, target: str):
        """Детектим WAF через wafw00f"""
        try:
            cmd = f"wafw00f {target} -o /dev/null"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and result.stdout:
                # Простой парсинг вывода wafw00f
                for waf in self.waf_db:
                    if waf["name"].lower() in result.stdout.lower():
                        self.results["waf"] = waf["name"]
                        print(f"[ANALYZER] WAF detected: {waf['name']}")
                        break
        except Exception as e:
            print(f"[ANALYZER] Error in WAF detection: {e}")
    
    def run_nuclei(self, target: str):
        """Запуск nuclei на HIGH/CRITICAL уязвимости"""
        try:
            output_file = self.workspace / "nuclei_results.json"
            cmd = f"nuclei -u {target} -severity high,critical -json -o {output_file} -silent -timeout 60"
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            
            if output_file.exists():
                with open(output_file) as f:
                    for line in f:
                        try:
                            vuln = json.loads(line)
                            self.results["vulnerabilities"].append({
                                "template": vuln.get("template-id"),
                                "name": vuln.get("info", {}).get("name"),
                                "severity": vuln.get("info", ).get("severity"),
                                "matched_at": vuln.get("matched-at")
                            })
                        except:
                            pass
                print(f"[ANALYZER] Nuclei found {len(self.results['vulnerabilities'])} vulnerabilities")
        except Exception as e:
            print(f"[ANALYZER] Error running nuclei: {e}")
    
    def get_report(self) -> str:
        """Генерация текстового отчёта"""
        report = ["=== ANALYZER AGENT REPORT ===\n"]
        report.append(f"Frameworks detected: {len(self.results['frameworks'])}")
        for fw in self.results['frameworks']:
            report.append(f"  - {fw['name']} at {fw['url']}")
        
        report.append(f"\nServices detected: {len(self.results['services'])}")
        for svc in self.results['services']:
            report.append(f"  - {svc['name']} on ports {svc['ports']}")
        
        report.append(f"\nWAF: {self.results['waf'] or 'None detected'}")
        
        report.append(f"\nVulnerabilities: {len(self.results['vulnerabilities'])}")
        for vuln in self.results['vulnerabilities'][:10]:
            report.append(f"  [{vuln['severity'].upper()}] {vuln['name']} - {vuln['matched_at']}")
        
        return '\n'.join(report)
