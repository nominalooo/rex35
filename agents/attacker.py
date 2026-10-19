"""
AttackerAgent — exploit validation & chaining
Задачи:
- SQLi testing (sqlmap)
- XSS testing (dalfox)
- Directory brute-force (gobuster/ffuf)
- Exploit chaining (если найдены LFI+SSRF → RCE)
"""
import subprocess, json, os
from pathlib import Path

class AttackerAgent:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.results = {
            "sqli_found": [],
            "xss_found": [],
            "directories": [],
            "exploited": []
        }
    
    def execute(self, analyzer_data: dict, target: str) -> dict:
        """Атакующее сканирование"""
        print(f"[ATTACKER] Starting exploitation on {target}")
        
        vulnerabilities = analyzer_data.get("vulnerabilities", [])
        waf = analyzer_data.get("waf")
        
        # 1. Directory brute-force
        self.bruteforce_directories(target)
        
        # 2. Если найдены SQLi индикаторы → запускаем sqlmap
        sqli_candidates = [v for v in vulnerabilities if "sql" in v.get("name", "").lower()]
        if sqli_candidates:
            self.test_sqli(sqli_candidates[0].get("matched_at", target), waf)
        
        # 3. Если найдены XSS индикаторы → запускаем dalfox
        xss_candidates = [v for v in vulnerabilities if "xss" in v.get("name", "").lower()]
        if xss_candidates:
            self.test_xss(xss_candidates[0].get("matched_at", target))
        
        # 4. Exploit chaining
        self.chain_exploits(vulnerabilities)
        
        return self.results
    
    def bruteforce_directories(self, target: str):
        """Брутфорс директорий через gobuster"""
        try:
            # Используем встроенный wordlist или создаём минимальный
            wordlist = "/usr/share/wordlists/dirb/common.txt"
            if not os.path.exists(wordlist):
                # Создаём минимальный wordlist
                wordlist = self.workspace / "dirs.txt"
                with open(wordlist, 'w') as f:
                    f.write("\n".join([
                        "admin", "api", "login", "dashboard", "config",
                        "backup", "test", "dev", "uploads", "files",
                        ".env", ".git", "phpinfo.php", "server-status"
                    ]))
            
            output_file = self.workspace / "gobuster_results.txt"
            cmd = f"gobuster dir -u {target} -w {wordlist} -q -o {output_file} --timeout 30s -t 20"
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            
            if output_file.exists():
                with open(output_file) as f:
                    for line in f:
                        if line.strip():
                            self.results["directories"].append(line.strip())
                print(f"[ATTACKER] Found {len(self.results['directories'])} directories")
        except Exception as e:
            print(f"[ATTACKER] Error in directory brute-force: {e}")
    
    def test_sqli(self, url: str, waf: str = None):
        """Тестирование SQLi через sqlmap"""
        try:
            output_file = self.workspace / "sqlmap_results.txt"
            
            # Базовая команда
            cmd = f"sqlmap -u '{url}' --batch --random-agent --level=1 --risk=1 --threads=5 --timeout=30 -o"
            
            # Если WAF детектнут → добавляем tamper scripts
            if waf:
                if "cloudflare" in waf.lower():
                    cmd += " --tamper=space2comment,between"
                elif "imperva" in waf.lower():
                    cmd += " --tamper=space2hash,apostrophemask"
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=180)
            
            if "injectable" in result.stdout.lower():
                self.results["sqli_found"].append({
                    "url": url,
                    "status": "VULNERABLE",
                    "waf_bypassed": waf is not None
                })
                print(f"[ATTACKER] ✓ SQLi confirmed at {url}")
        except Exception as e:
            print(f"[ATTACKER] Error testing SQLi: {e}")
    
    def test_xss(self, url: str):
        """Тестирование XSS через dalfox"""
        try:
            cmd = f"dalfox url {url} --silence --no-color --only-poc"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            
            if "POC" in result.stdout or "xss" in result.stdout.lower():
                self.results["xss_found"].append({
                    "url": url,
                    "status": "VULNERABLE"
                })
                print(f"[ATTACKER] ✓ XSS confirmed at {url}")
        except Exception as e:
            print(f"[ATTACKER] Error testing XSS: {e}")
    
    def chain_exploits(self, vulnerabilities: list):
        """Чейнинг эксплоитов"""
        vuln_types = [v.get("name", "").lower() for v in vulnerabilities]
        
        # LFI + SSRF → RCE potential
        if any("lfi" in v for v in vuln_types) and any("ssrf" in v for v in vuln_types):
            self.results["exploited"].append({
                "chain": "LFI + SSRF → RCE",
                "status": "POTENTIAL",
                "description": "LFI can be chained with SSRF to achieve RCE via /proc/self/environ or log poisoning"
            })
            print("[ATTACKER] ⚠ Exploit chain detected: LFI + SSRF → RCE")
        
        # Open Redirect + OAuth → Account Takeover
        if any("redirect" in v for v in vuln_types) and any("oauth" in v for v in vuln_types):
            self.results["exploited"].append({
                "chain": "Open Redirect + OAuth → Account Takeover",
                "status": "POTENTIAL"
            })
            print("[ATTACKER] ⚠ Exploit chain detected: Open Redirect + OAuth")
    
    def get_report(self) -> str:
        """Генерация текстового отчёта"""
        report = ["=== ATTACKER AGENT REPORT ===\n"]
        report.append(f"Directories found: {len(self.results['directories'])}")
        report.append(f"SQLi vulnerabilities: {len(self.results['sqli_found'])}")
        report.append(f"XSS vulnerabilities: {len(self.results['xss_found'])}")
        report.append(f"Exploit chains: {len(self.results['exploited'])}")
        
        if self.results["sqli_found"]:
            report.append("\n--- SQLi Findings ---")
            for sqli in self.results['sqli_found']:
                report.append(f"  ✓ {sqli['url']} (WAF bypass: {sqli.get('waf_bypassed', False)})")
        
        if self.results["exploited"]:
            report.append("\n--- Exploit Chains ---")
            for chain in self.results['exploited']:
                report.append(f"  ⚠ {chain['chain']} [{chain['status']}]")
                report.append(f"     {chain.get('description', '')}")
        
        return '\n'.join(report)
