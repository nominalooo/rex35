"""
EnumerationAgent — advanced enumeration with API integrations
Задачи:
- Shodan integration (поиск уязвимых сервисов)
- Censys integration (IoT и открытые порты)
- VirusTotal (domain/IP reputation + passive DNS)
- SecurityTrails (DNS history + subdomains)
- Subdomain takeover detection
- S3/Azure/GCP bucket enumeration
- GitHub dork scanning
- Certificate transparency logs
"""
import subprocess, json, os, re, requests
from pathlib import Path
from typing import Dict, List, Optional
import time

class EnumerationAgent:
    def __init__(self, workspace: Path, config_path: Optional[Path] = None):
        self.workspace = workspace
        self.config_path = config_path or Path("config/api_keys.json")
        self.results = {
            "shodan_results": [],
            "censys_results": [],
            "virustotal_results": {},
            "securitytrails_results": {},
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
        if "shodan" in self.api_keys and self.api_keys["shodan"] != "YOUR_SHODAN_API_KEY_HERE":
            self.search_shodan(target)
        
        # 2. Censys search
        if "censys_id" in self.api_keys and self.api_keys["censys_id"] != "YOUR_CENSYS_APP_ID_HERE":
            self.search_censys(target)
        
        # 3. VirusTotal
        if "virustotal" in self.api_keys and self.api_keys["virustotal"] != "YOUR_VIRUSTOTAL_API_KEY_HERE":
            self.search_virustotal(target)
        
        # 4. SecurityTrails
        if "securitytrails" in self.api_keys and self.api_keys["securitytrails"] != "YOUR_SECURITYTRAILS_API_KEY_HERE":
            self.search_securitytrails(target)
        
        # 5. Subdomain takeover detection
        if subdomains:
            self.detect_subdomain_takeovers(subdomains)
        
        # 6. Cloud bucket enumeration
        self.enumerate_cloud_buckets(target)
        
        # 7. GitHub dorks
        if "github" in self.api_keys and self.api_keys["github"] != "YOUR_GITHUB_TOKEN_HERE":
            self.search_github_leaks(target)
        
        # 8. Certificate transparency
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
            elif response.status_code == 401:
                print(f"[ENUM] Shodan API: Invalid API key")
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
            elif response.status_code == 401:
                print(f"[ENUM] Censys API: Invalid credentials")
            else:
                print(f"[ENUM] Censys API error: {response.status_code}")
        except Exception as e:
            print(f"[ENUM] Error in Censys search: {e}")
    
    def search_virustotal(self, target: str):
        """VirusTotal domain + passive DNS lookup"""
        try:
            api_key = self.api_keys.get("virustotal")
            headers = {"x-apikey": api_key}
            
            # Domain report
            url_domain = f"https://www.virustotal.com/api/v3/domains/{target}"
            response = requests.get(url_domain, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json().get("data", {}).get("attributes", {})
                
                self.results["virustotal_results"] = {
                    "reputation": data.get("reputation", 0),
                    "last_analysis_stats": data.get("last_analysis_stats", {}),
                    "categories": data.get("categories", {}),
                    "last_dns_records": data.get("last_dns_records", []),
                    "subdomains": []
                }
                
                print(f"[ENUM] VirusTotal reputation: {data.get('reputation', 0)}")
                
                # Get subdomains from VT
                url_subdomains = f"https://www.virustotal.com/api/v3/domains/{target}/subdomains?limit=40"
                resp_sub = requests.get(url_subdomains, headers=headers, timeout=30)
                if resp_sub.status_code == 200:
                    subdomains_data = resp_sub.json().get("data", [])
                    self.results["virustotal_results"]["subdomains"] = [
                        sub.get("id") for sub in subdomains_data
                    ]
                    print(f"[ENUM] VirusTotal found {len(subdomains_data)} subdomains")
            elif response.status_code == 401:
                print(f"[ENUM] VirusTotal API: Invalid API key")
            else:
                print(f"[ENUM] VirusTotal API error: {response.status_code}")
        except Exception as e:
            print(f"[ENUM] Error in VirusTotal search: {e}")
    
    def search_securitytrails(self, target: str):
        """SecurityTrails DNS history + subdomain enumeration"""
        try:
            api_key = self.api_keys.get("securitytrails")
            headers = {"APIKEY": api_key, "Content-Type": "application/json"}
            
            # Get subdomains
            url_subs = f"https://api.securitytrails.com/v1/domain/{target}/subdomains"
            response = requests.get(url_subs, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                subdomains = data.get("subdomains", [])
                full_subs = [f"{sub}.{target}" for sub in subdomains]
                
                self.results["securitytrails_results"]["subdomains"] = full_subs
                print(f"[ENUM] SecurityTrails found {len(full_subs)} subdomains")
                
                # Get DNS history
                url_history = f"https://api.securitytrails.com/v1/history/{target}/dns/a"
                resp_hist = requests.get(url_history, headers=headers, timeout=30)
                
                if resp_hist.status_code == 200:
                    history = resp_hist.json().get("records", [])
                    self.results["securitytrails_results"]["dns_history"] = history[:10]
                    print(f"[ENUM] SecurityTrails DNS history: {len(history)} records")
            elif response.status_code == 401:
                print(f"[ENUM] SecurityTrails API: Invalid API key")
            else:
                print(f"[ENUM] SecurityTrails API error: {response.status_code}")
        except Exception as e:
            print(f"[ENUM] Error in SecurityTrails search: {e}")
    
    def detect_subdomain_takeovers(self, subdomains: List[str]):
        """Детектим subdomain takeover vulnerabilities"""
        print(f"[ENUM] Checking {len(subdomains)} subdomains for takeover...")
        
        # Signatures для subdomain takeover
        takeover_signatures = {
            "github": ["There isn't a GitHub Pages site here"],
            "heroku": ["No such app", "herokucdn.com/error-pages/no-such-app"],
            "aws_s3": ["NoSuchBucket", "The specified bucket does not exist"],
            "azure": ["404 Web Site not found", "ErrorCode: BlobNotFound"],
            "shopify": ["Sorry, this shop is currently unavailable"],
            "zendesk": ["Help Center Closed"],
            "tumblr": ["There's nothing here", "Whatever you were looking for doesn't currently exist"],
            "wordpress": ["Do you want to register"],
            "pantheon": ["404 error unknown site"],
            "surge": ["project not found"],
            "bitbucket": ["Repository not found"]
        }
        
        for subdomain in subdomains[:100]:  # Check first 100
            try:
                # Quick HTTP check
                response = requests.get(f"http://{subdomain}", timeout=5, allow_redirects=True)
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
                        break
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
            f"{base}-uploads", f"{base}-static", f"{base}-media",
            f"prod-{base}", f"backup-{base}", f"staging-{base}"
        ]
        
        # AWS S3
        for pattern in patterns[:15]:  # First 15 patterns
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
                    status = "🔓 OPEN" if response.status_code == 200 else "🔒 EXISTS"
                    print(f"  💾 S3 bucket {status}: {bucket_url}")
            except:
                pass
        
        # Azure Blob Storage
        for pattern in patterns[:15]:
            azure_url = f"https://{pattern}.blob.core.windows.net"
            try:
                response = requests.head(azure_url, timeout=5)
                if response.status_code in [200, 403, 400]:
                    self.results["cloud_buckets"].append({
                        "provider": "Azure Blob",
                        "bucket": pattern,
                        "url": azure_url,
                        "accessible": response.status_code == 200
                    })
                    print(f"  💾 Azure Blob found: {azure_url}")
            except:
                pass
        
        # Google Cloud Storage
        for pattern in patterns[:15]:
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
        
        print(f"[ENUM] Found {len(self.results['cloud_buckets'])} cloud storage buckets")
    
    def search_github_leaks(self, target: str):
        """GitHub code search для утечек (API keys, credentials, config files)"""
        print(f"[ENUM] Searching GitHub for {target} leaks...")
        
        try:
            token = self.api_keys.get("github")
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Dorking patterns
            dorks = [
                f'"{target}" password',
                f'"{target}" api_key',
                f'"{target}" secret',
                f'"{target}" credentials',
                f'"{target}" token',
                f'"{target}" aws_access_key_id',
                f'"{target}" .env',
                f'"{target}" config.json',
                f'"{target}" database'
            ]
            
            for dork in dorks[:5]:  # Limit to 5 dorks to avoid rate limit
                url = f"https://api.github.com/search/code?q={dork}&per_page=10"
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    
                    for item in items:
                        self.results["github_leaks"].append({
                            "repo": item.get("repository", {}).get("full_name"),
                            "path": item.get("path"),
                            "url": item.get("html_url"),
                            "query": dork
                        })
                        print(f"  🔍 GitHub leak: {item.get('repository', {}).get('full_name')} - {item.get('path')}")
                
                time.sleep(2)  # Rate limiting
            
            print(f"[ENUM] Found {len(self.results['github_leaks'])} potential GitHub leaks")
        except Exception as e:
            print(f"[ENUM] Error in GitHub search: {e}")
    
    def search_cert_transparency(self, target: str):
        """Certificate Transparency logs для поиска subdomains"""
        print(f"[ENUM] Searching certificate transparency logs...")
        
        try:
            url = f"https://crt.sh/?q=%.{target}&output=json"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                subdomains = set()
                
                for cert in data:
                    name = cert.get("name_value", "")
                    # Parse multiple domains from certificate
                    for domain in name.split('\n'):
                        domain = domain.strip()
                        if domain and target in domain:
                            subdomains.add(domain.replace('*.', ''))
                
                self.results["cert_transparency"] = list(subdomains)[:100]  # Limit to 100
                print(f"[ENUM] Certificate transparency found {len(self.results['cert_transparency'])} subdomains")
        except Exception as e:
            print(f"[ENUM] Error in cert transparency search: {e}")
    
    def save_results(self, output_file: Path = None):
        """Сохранение результатов"""
        if output_file is None:
            output_file = self.workspace / "enumeration_results.json"
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"[ENUM] Results saved to {output_file}")
        return output_file
