# 🔥 REX35 — Autonomous Penetration Testing System

**Ultimate Edition — Chinese Killer Level**

REX35 is a fully autonomous penetration testing framework that combines reconnaissance, enumeration, vulnerability analysis, exploitation, and post-exploitation into a single orchestrated system.

---

## ✨ Features

### Core Capabilities
- ✅ **Fully Autonomous** — Runs complete pentest cycles without human intervention
- ✅ **Multi-Agent Architecture** — Scout, Analyzer, Attacker, Enumerator, Persistence, Browser
- ✅ **API Intelligence** — Shodan, Censys, VirusTotal, SecurityTrails, GitHub integration
- ✅ **Browser Automation** — Playwright for JS-heavy targets, XSS testing, cookie stealing
- ✅ **Decision Tree** — AI-powered attack prioritization and exploit chaining
- ✅ **Professional Reporting** — HTML dashboard + Markdown + JSON exports
- ✅ **Parallel Execution** — Asyncio-based concurrent scanning

### Attack Vectors
- SQL Injection (SQLi)
- Cross-Site Scripting (XSS)
- Insecure Direct Object Reference (IDOR)
- Command Injection (RCE)
- Server-Side Request Forgery (SSRF)
- Subdomain Takeover
- Open Cloud Storage (S3/Azure/GCP)
- Authentication Bypass
- Session Hijacking

### Intelligence Sources
- Shodan (vulnerable services)
- Censys (IoT and open ports)
- VirusTotal (domain reputation + passive DNS)
- SecurityTrails (DNS history + subdomains)
- GitHub Dorking (leaked credentials)
- Certificate Transparency logs
- Cloud bucket enumeration

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/nominalooo/rex35
cd rex35

# Install system dependencies + tools
chmod +x install.sh
./install.sh

# Install Python dependencies
pip3 install -r requirements.txt

# Install browser automation
playwright install chromium
```

### 2. Configuration

Edit `config/api_keys.json` with your API keys:

```json
{
  "shodan": "YOUR_SHODAN_API_KEY",
  "censys_id": "YOUR_CENSYS_ID",
  "censys_secret": "YOUR_CENSYS_SECRET",
  "virustotal": "YOUR_VIRUSTOTAL_KEY",
  "securitytrails": "YOUR_SECURITYTRAILS_KEY",
  "github": "YOUR_GITHUB_TOKEN"
}
```

### 3. Run Server

```bash
# Set required environment variables
export ANTHROPIC_API_KEY="your_anthropic_api_key"
export EXA_API_KEY="your_exa_api_key"
export FIRECRAWL_API_KEY="your_firecrawl_api_key"

# Start server
python3 main.py
```

Navigate to `http://localhost:8000`

---

## 📖 Usage

### Web Interface

1. Open `http://localhost:8000` in your browser
2. Enter target domain
3. Select scan type (Fast / Deep / Autonomous)
4. View real-time results in dashboard

### Programmatic Usage

```python
from agents.orchestrator_v3 import AutonomousOrchestratorV3
from pathlib import Path
import asyncio

# Initialize
workspace = Path("workspace")
db_path = workspace / "pentest.db"
orchestrator = AutonomousOrchestratorV3(workspace, db_path)

# Run autonomous scan
async def main():
    results = await orchestrator.execute_autonomous_scan(
        target="example.com",
        deep_mode=True
    )
    print(f"Found {len(results['vulnerabilities'])} vulnerabilities")

asyncio.run(main())
```

### CLI Tools

Individual agents can be used standalone:

```bash
# Enumerator
python -c "from agents.enumerator import EnumerationAgent; from pathlib import Path; agent = EnumerationAgent(Path('workspace')); agent.execute('example.com')"

# Browser Agent
python -c "from agents.browser_agent import BrowserAgent; import asyncio; from pathlib import Path; agent = BrowserAgent(Path('workspace')); asyncio.run(agent.crawl_spa('https://example.com'))"
```

---

## 🏗️ Architecture

```
REX35/
├── agents/
│   ├── scout.py              # Reconnaissance (subdomains, ports, endpoints)
│   ├── enumerator.py         # API intelligence (Shodan, Censys, etc.)
│   ├── analyzer.py           # Tech stack detection + known CVEs
│   ├── attacker.py           # Exploitation (SQLi, XSS, IDOR, etc.)
│   ├── persistence.py        # Post-exploitation persistence
│   ├── browser_agent.py      # Browser automation (Playwright)
│   ├── orchestrator_v3.py    # Main orchestration engine
│
├── payloads/
│   ├── wordlists/
│   │   ├── sqli.txt          # SQL injection payloads
│   │   ├── xss.txt           # XSS vectors
│   │   ├── lfi.txt           # Local File Inclusion
│   │   ├── ssrf.txt          # SSRF bypasses
│   │   ├── command_injection.txt
│   │   ├── api_endpoints.txt # Common API paths
│   │   └── jwt_secrets.txt   # JWT brute-force wordlist
│   │
│   └── post_exploit/
│       ├── linpeas.sh        # Linux privilege escalation
│       ├── winPEASx64.exe    # Windows privilege escalation
│       └── pspy64            # Process monitoring
│
├── reporting/
│   └── report_generator.py   # HTML + Markdown + JSON reports
│
├── config/
│   └── api_keys.json         # API credentials
│
├── knowledge/
│   ├── frameworks.json       # Framework fingerprints
│   ├── services.json         # Service signatures
│   └── waf_bypasses.json     # WAF bypass techniques
│
├── main.py                   # FastAPI server
├── pentest_db.py             # SQLite database
├── payload_generator.py      # Dynamic payload generation
├── install.sh                # Full installation script
└── requirements.txt
```

---

## 🎯 Workflow

### Autonomous Scan Cycle

```
1. RECONNAISSANCE (Parallel)
   ├─ Scout: Subdomains, ports, endpoints
   └─ Enumerator: Shodan, Censys, VirusTotal, GitHub

2. ANALYSIS
   ├─ Tech stack detection
   ├─ Framework version identification
   └─ Known CVE lookup

3. DECISION TREE
   ├─ Prioritize attacks by severity
   ├─ Build exploit chains
   └─ Select optimal payloads

4. EXPLOITATION
   ├─ SQL Injection → Database access
   ├─ XSS → Cookie stealing → Session hijacking
   ├─ IDOR → Unauthorized data access
   ├─ Command Injection → Shell access
   └─ Subdomain Takeover

5. POST-EXPLOITATION (if access gained)
   ├─ Deploy persistence mechanisms
   ├─ Privilege escalation
   ├─ Lateral movement
   └─ Data exfiltration

6. PIVOT
   ├─ Discover internal networks
   ├─ Find new subdomains
   └─ Loop to step 1 with new targets

7. REPORTING
   ├─ Generate HTML dashboard
   ├─ Create Markdown report
   └─ Export JSON for integrations
```

---

## 📊 Reporting

REX35 generates comprehensive reports:

### HTML Dashboard
- Real-time vulnerability statistics
- Color-coded severity levels (Critical/High/Medium/Low)
- Interactive charts
- Professional design (warm color palette)

### Markdown Report
- Executive summary
- Detailed findings with reproduction steps
- Technical recommendations
- Full asset inventory

### JSON Export
- Machine-readable format
- Integration with other security tools
- Complete raw data

Reports are saved in `workspace/reports/`

---

## 🛡️ Installed Tools

REX35 includes these industry-standard tools:

**Network Scanning:**
- masscan
- nmap
- rustscan

**Subdomain Enumeration:**
- amass
- subfinder
- crt.sh integration

**Fuzzing:**
- ffuf
- feroxbuster
- gobuster

**Vulnerability Scanning:**
- nuclei (13,000+ templates)
- XSStrike
- commix
- sqlmap

**Endpoint Discovery:**
- gau (GetAllURLs)
- waybackurls
- paramspider
- arjun

**Post-Exploitation:**
- LinPEAS
- WinPEAS
- pspy

**Password Cracking:**
- hydra
- john
- hashcat

**Browser Automation:**
- Playwright (Chromium headless)

---

## 🔑 API Keys

### Free Tier Available
- [Shodan](https://account.shodan.io/register) — 100 queries/month free
- [VirusTotal](https://www.virustotal.com/gui/join-us) — 4 requests/min free
- [GitHub](https://github.com/settings/tokens) — Free with account
- [crt.sh](https://crt.sh) — No API key required

### Paid Services
- [Censys](https://censys.io/pricing) — $99/month
- [SecurityTrails](https://securitytrails.com/pricing) — $99/month

**Note:** REX35 works without API keys but will skip those integrations.

---

## ⚠️ Legal Disclaimer

REX35 is intended for:
- ✅ Authorized penetration testing
- ✅ Bug bounty programs
- ✅ Red team exercises
- ✅ Educational purposes on your own infrastructure

**Unauthorized use against systems you do not own or have explicit permission to test is ILLEGAL.**

Always obtain written authorization before testing.

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional exploit modules
- New API integrations
- Machine learning for attack prioritization
- Improved stealth techniques
- Better evasion methods

---

## 📝 License

MIT License — See LICENSE file

---

## 🙏 Credits

Built by **rex** with autonomous AI assistance.

Powered by:
- Claude (Anthropic)
- Playwright
- Nuclei (ProjectDiscovery)
- OWASP Amass
- And many open-source security tools

---

## 🔥 Chinese Killer Level Unlocked

*REX35 doesn't just find vulnerabilities — it chains them into full exploitation paths.*

**Status:** READY FOR DOMINATION
