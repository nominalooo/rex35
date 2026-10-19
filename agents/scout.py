"""
ScoutAgent — reconnaissance & asset discovery
Задачи:
- Subdomain enumeration (subfinder)
- Active host discovery (httpx)
- Crawling & endpoint discovery (katana)
- Port scanning (nmap)
"""
import subprocess, json, os
from pathlib import Path

class ScoutAgent:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.results = {
            "subdomains": [],
            "live_hosts": [],
            "endpoints": [],
            "ports": []
        }
    
    def execute(self, target: str) -> dict:
        """Полное разведывательное сканирование цели"""
        print(f"[SCOUT] Starting reconnaissance on {target}")
        
        # 1. Subdomain enumeration
        self.find_subdomains(target)
        
        # 2. Check which hosts are live
        self.check_live_hosts()
        
        # 3. Crawl for endpoints
        if self.results["live_hosts"]:
            self.crawl_endpoints(self.results["live_hosts"][0])
        
        # 4. Port scan
        if self.results["live_hosts"]:
            self.port_scan(self.results["live_hosts"][0])
        
        return self.results
    
    def find_subdomains(self, domain: str):
        """Поиск поддоменов через subfinder"""
        try:
            cmd = f"subfinder -d {domain} -silent"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and result.stdout:
                subs = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                self.results["subdomains"] = subs
                print(f"[SCOUT] Found {len(subs)} subdomains")
            else:
                # Fallback: просто используем сам домен
                self.results["subdomains"] = [domain]
                print(f"[SCOUT] Subfinder failed, using target domain")
        except Exception as e:
            print(f"[SCOUT] Error in subdomain enum: {e}")
            self.results["subdomains"] = [domain]
    
    def check_live_hosts(self):
        """Проверка живых хостов через httpx"""
        if not self.results["subdomains"]:
            return
        
        try:
            # Сохраняем subdomains в файл
            subs_file = self.workspace / "subdomains.txt"
            with open(subs_file, 'w') as f:
                f.write('\n'.join(self.results["subdomains"]))
            
            cmd = f"httpx -l {subs_file} -silent -status-code -tech-detect -json"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            self.results["live_hosts"].append({
                                "url": data.get("url"),
                                "status": data.get("status_code"),
                                "tech": data.get("tech", [])
                            })
                        except:
                            pass
                print(f"[SCOUT] Found {len(self.results['live_hosts'])} live hosts")
        except Exception as e:
            print(f"[SCOUT] Error in live host check: {e}")
    
    def crawl_endpoints(self, target: str):
        """Crawling endpoints через katana"""
        try:
            url = target if isinstance(target, str) else target.get("url", "")
            if not url:
                return
            
            cmd = f"katana -u {url} -silent -jc -d 3 -timeout 60"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=90)
            
            if result.returncode == 0 and result.stdout:
                endpoints = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                self.results["endpoints"] = endpoints[:100]  # Лимит 100 endpoints
                print(f"[SCOUT] Found {len(self.results['endpoints'])} endpoints")
        except Exception as e:
            print(f"[SCOUT] Error in crawling: {e}")
    
    def port_scan(self, target: str):
        """Port scan через nmap (top 100 ports)"""
        try:
            url = target if isinstance(target, str) else target.get("url", "")
            if not url:
                return
            
            # Extract hostname from URL
            from urllib.parse import urlparse
            hostname = urlparse(url).netloc
            
            cmd = f"nmap -T4 -F --open {hostname} -oX -"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and result.stdout:
                # Простой парсинг XML вывода nmap
                import re
                ports = re.findall(r'portid="(\d+)".*?<state state="open"', result.stdout)
                self.results["ports"] = [int(p) for p in ports]
                print(f"[SCOUT] Found {len(self.results['ports'])} open ports")
        except Exception as e:
            print(f"[SCOUT] Error in port scan: {e}")

    def get_report(self) -> str:
        """Генерация текстового отчёта"""
        report = ["=== SCOUT AGENT REPORT ===\n"]
        report.append(f"Subdomains found: {len(self.results['subdomains'])}")
        report.append(f"Live hosts: {len(self.results['live_hosts'])}")
        report.append(f"Endpoints discovered: {len(self.results['endpoints'])}")
        report.append(f"Open ports: {self.results['ports']}")
        report.append("\n--- Live Hosts ---")
        for host in self.results['live_hosts'][:10]:
            report.append(f"  {host.get('url')} [{host.get('status')}] Tech: {', '.join(host.get('tech', []))}")
        return '\n'.join(report)
