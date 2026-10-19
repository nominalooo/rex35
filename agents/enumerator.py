"""
EnumerationAgent — advanced enumeration with API integrations
Задачи:
- Shodan integration (поиск уязвимых сервисов)
- Censys integration (IoT и открытые порты)
- Subdomain takeover detection
- S3/Azure/GCP bucket enumeration
- GitHub dork scanning
- Certificate transparency logs
"""
import subprocess, json, os, re, requests
from pathlib import Path
from typing import Dict, List, Optional

class EnumerationAgent:
    def __init__(self, workspace: Path, config_path: Optional[Path] = None):
        self.workspace = workspace
        self.config_path = config_path or Path("config/api_keys.json")
        self.results = {
            "shodan_results": [],
            "censys_results": [],
            "subdomain_takeovers": [],
            "cloud_buckets": [],
            "github_leaks": [],
            "cert_transparency": []
        }
        self.api_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> Dict:
        """Загрузка API ключей"""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    keys = json.load(f)
                    print(f"[ENUM] Loaded API keys from {self.config_path}")
                    return keys
            except Exception as e:
                print(f"[ENUM] Error loading API keys: {e}")
        else:
            print(f"[ENUM] No API keys found at {self.config_path}, skipping API integrations")
        return {}
    
    def execute(self, target: str, subdomains: List[str] = None) -> Dict:
        """Полное перечисление активов"""
        print(f"[ENUM] Starting advanced enumeration on {target}")
        
        # 1. Shodan search
        if "shodan" in self.api_keys:
            self.search_shodan(target)
        
        # 2. Censys search
        if "censys_id" in self.api_keys and "censys_secret" in self.api_keys:
            self.search_censys(target)
        
        # 3. Subdomain takeover detection
        if subdomains:
            self.detect_subdomain_takeovers(subdomains)
        
        # 4. Cloud bucket enumeration
        self.enumerate_cloud_buckets(target)
        
        # 5. GitHub dorks
        if "github" in self.api_keys:
            self.search_github_leaks(target)
        
        # 6. Certificate transparency
        self.search_cert_transparency(target)
        
        return self.results
    
    def search_shodan(self, target: str):
        """Shodan API search"""
        try:
            api_key = self.api_keys.get("shodan")
            url = f"https://api.shodan.io/shodan/host/search?query=hostname:{target}&key={api_key}"
            
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                matches = data.get("matches", [])
                
                for match in matches[:20]:  # Limit to first 20
                    self.results["shodan_results"].append({
                        "ip": match.get("ip_str"),
                        "port": match.get("port"),
                        "product": match.get("product"),
                        "version": match.get("version"),
                        "os": match.get("os"),
                        "vulns": match.get("vulns", []),
                        "org": match.get("org")
                    })
                
                print(f"[ENUM] Shodan found {len(self.results['shodan_results'])} results")
                
                # Highlight critical findings
                for result in self.results["shodan_results"]:
                    if result.get("vulns"):
                        print(f"  ⚠️  {result['ip']}:{result['port']} has CVEs: {result['vulns']}")
            else:
                print(f"[ENUM] Shodan API error: {response.status_code}")
        except Exception as e:
            print(f"[ENUM] Error in Shodan search: {e}")
    
    def search_censys(self, target: str):
        """Censys API search"""
        try:
            api_id = self.api_keys.get("censys_id")
            api_secret = self.api_keys.get("censys_secret")
            
            url = "https://search.censys.io/api/v2/hosts/search"
            headers = {"Content-Type": "application/json"}
            payload = {"q": f"services.dns.names: {target}", "per_page": 20}
            
            response = requests.post(url, headers=headers, json=payload, 
                                   auth=(api_id, api_secret), timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                hits = data.get("result", {}).get("hits", [])
                
                for hit in hits:
                    self.results["censys_results"].append({
                        "ip": hit.get("ip"),
                        "services": hit.get("services", []),
                        "autonomous_system": hit.get("autonomous_system", {})
                    })
                
                print(f"[ENUM] Censys found {len(self.results['censys_results'])} results")
            else:
                print(f"[ENUM] Censys API error: {response.status_code}")
        except Exception as e:
            print(f"[ENUM] Error in Censys search: {e}")
    
    def detect_subdomain_takeovers(self, subdomains: List[str]):
        """Детектим subdomain takeover vulnerabilities"""
        print(f"[ENUM] Checking {len(subdomains)} subdomains for takeover...")
        
        # Signatures для subdomain takeover
        takeover_signatures = {
            "github": ["There isn't a GitHub Pages site here"],
            "heroku": ["No such app"],
            "aws_s3": ["NoSuchBucket", "The specified bucket does not exist"],
            "azure": ["404 Web Site not found"],
            "shopify": ["Sorry, this shop is currently unavailable"],
            "zendesk": ["Help Center Closed"],
            "tumblr": ["There's nothing here"],
            "wordpress": ["Do you want to register"]
        }
        
        for subdomain in subdomains[:50]:  # Check first 50
            try:
                # Quick HTTP check
                response = requests.get(f"http://{subdomain}", timeout=5, allow_redirects=False)
                content = response.text.lower()
                
                for service, signatures in takeover_signatures.items():
                    if any(sig.lower() in content for sig in signatures):
                        self.results["subdomain_takeovers"].append({
                            "subdomain": subdomain,
                            "service": service,
                            "status_code": response.status_code,
                            "severity": "HIGH"
                        })
                        print(f"  🚨 TAKEOVER: {subdomain} vulnerable via {service}")
            except:
                pass
        
        print(f"[ENUM] Found {len(self.results['subdomain_takeovers'])} potential takeovers")
    
    def enumerate_cloud_buckets(self, target: str):
        """Поиск облачных storage buckets (S3, Azure, GCP)"""
        print(f"[ENUM] Enumerating cloud buckets for {target}...")
        
        # Extract base domain without TLD
        base = target.split('.')[0]
        
        # Common patterns
        patterns = [
            base, f"{base}-prod", f"{base}-dev", f"{base}-staging",
            f"{base}-backup", f"{base}-assets", f"{base}-files",
            f"{base}-uploads", f"{base}-static", f"{base}-media"
        ]
        
        # AWS S3
        for pattern in patterns:
            bucket_url = f"https://{pattern}.s3.amazonaws.com"
            try:
                response = requests.head(bucket_url, timeout=5)
                if response.status_code in [200, 403]:
                    self.results["cloud_buckets"].append({
                        "provider": "AWS S3",
                        "bucket": pattern,
                        "url": bucket_url,
                        "accessible": response.status_code == 200
                    })
                    status = "OPEN" if response.status_code == 200 else "EXISTS"
                    print(f"  💾 S3 bucket {status}: {bucket_url}")
            except:
                pass
        
        # Azure Blob Storage
        for pattern in patterns:
            azure_url = f"https://{pattern}.blob.core.windows.net"
            try:
                response = requests.head(azure_url, timeout=5)
                if response.status_code in [200, 400]:
                    self.results["cloud_buckets"].append({
                        "provider": "Azure Blob",
                        "bucket": pattern,
                        "url": azure_url,
                        "accessible": response.status_code == 200
                    })
                    print(f"  💾 Azure bucket found: {azure_url}")
            except:
                pass
        
        # GCP Storage
        for pattern in patterns:
            gcp_url = f"https://storage.googleapis.com/{pattern}"
            try:
                response = requests.head(gcp_url, timeout=5)
                if response.status_code in [200, 403]:
                    self.results["cloud_buckets"].append({
                        "provider": "GCP Storage",
                        "bucket": pattern,
                        "url": gcp_url,
                        "accessible": response.status_code == 200
                    })
                    print(f"  💾 GCP bucket found: {gcp_url}")
            except:
                pass
        
        print(f"[ENUM] Found {len(self.results['cloud_buckets'])} cloud buckets")
    
    def search_github_leaks(self, target: str):
        """GitHub dork search for leaked credentials/keys"""
        try:
            api_key = self.api_keys.get("github")
            headers = {"Authorization": f"token {api_key}"}
            
            # Поисковые запросы
            dorks = [
                f"{target} password",
                f"{target} api_key",
                f"{target} secret",
                f"{target} credentials",
                f"{target} AWS_ACCESS_KEY_ID"
            ]
            
            for dork in dorks[:3]:  # Limit to 3 dorks to avoid rate limit
                url = f"https://api.github.com/search/code?q={dork}"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    
                    for item in items[:5]:  # First 5 results
                        self.results["github_leaks"].append({
                            "file": item.get("name"),
                            "path": item.get("path"),
                            "repo": item.get("repository", {}).get("full_name"),
                            "url": item.get("html_url")
                        })
                        print(f"  🔓 GitHub leak: {item.get('repository', {}).get('full_name')}/{item.get('path')}")
            
            print(f"[ENUM] Found {len(self.results['github_leaks'])} potential GitHub leaks")
        except Exception as e:
            print(f"[ENUM] Error in GitHub search: {e}")
    
    def search_cert_transparency(self, target: str):
        """Certificate Transparency logs for subdomains"""
        try:
            url = f"https://crt.sh/?q=%.{target}&output=json"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract unique domains
                domains = set()
                for entry in data:
                    name_value = entry.get("name_value", "")
                    # Split by newlines (some entries have multiple domains)
                    for domain in name_value.split('\n'):
                        domain = domain.strip()
                        if domain and target in domain:
                            domains.add(domain)
                
                self.results["cert_transparency"] = list(domains)
                print(f"[ENUM] Found {len(domains)} domains via Certificate Transparency")
                
                # Show first 10
                for domain in list(domains)[:10]:
                    print(f"  📜 {domain}")
        except Exception as e:
            print(f"[ENUM] Error in cert transparency search: {e}")
    
    def get_report(self) -> str:
        """Генерация текстового отчёта"""
        report = ["=== ENUMERATION AGENT REPORT ===\n"]
        
        report.append(f"Shodan results: {len(self.results['shodan_results'])}")
        for result in self.results['shodan_results'][:5]:
            vulns = result.get('vulns', [])
            vuln_str = f" [CVEs: {len(vulns)}]" if vulns else ""
            report.append(f"  - {result['ip']}:{result['port']} {result.get('product', 'unknown')}{vuln_str}")
        
        report.append(f"\nCensys results: {len(self.results['censys_results'])}")
        
        report.append(f"\nSubdomain takeovers: {len(self.results['subdomain_takeovers'])}")
        for takeover in self.results['subdomain_takeovers']:
            report.append(f"  🚨 {takeover['subdomain']} → {takeover['service']}")
        
        report.append(f"\nCloud buckets: {len(self.results['cloud_buckets'])}")
        for bucket in self.results['cloud_buckets']:
            access = "OPEN" if bucket['accessible'] else "EXISTS"
            report.append(f"  💾 [{access}] {bucket['provider']}: {bucket['url']}")
        
        report.append(f"\nGitHub leaks: {len(self.results['github_leaks'])}")
        for leak in self.results['github_leaks'][:5]:
            report.append(f"  🔓 {leak['repo']}/{leak['file']}")
        
        report.append(f"\nCert Transparency: {len(self.results['cert_transparency'])} domains")
        
        return '\n'.join(report)
