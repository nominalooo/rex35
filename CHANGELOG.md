# REX35 Changelog

## [v2.0.0] - Ultimate Edition - 2024-10-20

### 🔥 Major Additions

#### 1. Full Installation Script (`install.sh`)
- Автоматическая установка всех инструментов
- masscan, rustscan, amass, ffuf, feroxbuster, nuclei
- gau, paramspider, arjun, XSStrike, commix
- LinPEAS, WinPEAS, pspy
- Playwright browser automation
- Go, Rust, Python tools

#### 2. API Intelligence Integration (`agents/enumerator.py`)
- **Shodan API** — поиск уязвимых сервисов, CVE detection
- **Censys API** — IoT и открытые порты
- **VirusTotal API** — domain reputation + passive DNS + subdomains
- **SecurityTrails API** — DNS history + subdomain enumeration
- **GitHub Dorking** — leaked credentials, API keys, config files
- **Certificate Transparency** — subdomain discovery via crt.sh
- **Cloud Bucket Enumeration** — AWS S3, Azure Blob, GCP Storage
- **Subdomain Takeover Detection** — 11+ service signatures

#### 3. Professional Reporting System (`reporting/report_generator.py`)
- **HTML Dashboard**:
  - Real-time vulnerability statistics
  - Color-coded severity (Critical/High/Medium/Low)
  - Professional warm color design (#F6F1E8 palette)
  - Interactive charts
- **Markdown Report**:
  - Executive summary
  - Detailed findings with reproduction steps
  - Technical recommendations
  - Full asset inventory
- **JSON Export** — machine-readable format for integrations

#### 4. Browser Automation Agent (`agents/browser_agent.py`)
- **Playwright integration** — headless Chromium
- **SPA Crawling** — JavaScript-heavy targets, dynamic content
- **XSS Testing** — browser-based alert/console detection
- **Cookie Stealing** — extract cookies, localStorage, sessionStorage
- **Session Hijacking** — replay stolen sessions
- **Form Fuzzing** — automated input field testing

#### 5. Enhanced Orchestrator V3 (`agents/orchestrator_v3.py`)
- **Enhanced Decision Tree**:
  - AI-powered attack prioritization
  - Exploit chaining (XSS → cookie steal → session hijack)
  - Severity-based targeting
- **Parallel Execution** — Scout + Enumerator run simultaneously
- **Automatic Reporting** — generates reports after each scan
- **Better State Management** — tracks vulnerabilities, access level, pivots
- **Improved Attack Logic**:
  - Subdomain takeover exploitation
  - Open cloud bucket access
  - CVE exploitation from Shodan
  - Web app attacks (SQLi, XSS, IDOR, CMDI)

#### 6. Expanded Payload Library
- **XSS**: 75 payloads (was 49) — SVG, polyglots, obfuscation
- **SQLi**: 86 payloads (was 56) — UNION, time-based, error-based
- **LFI**: 104 payloads (was 80) — PHP wrappers, log poisoning
- **JWT Secrets**: 36 common secrets for JWT brute-force
- **Cloud Buckets**: patterns for S3/Azure/GCP enumeration

#### 7. Configuration Management
- `config/api_keys.json` — centralized API key storage
- Template with placeholder keys
- Easy setup for Shodan, Censys, VirusTotal, SecurityTrails, GitHub

#### 8. Comprehensive Documentation
- **README.md**: 
  - Full feature list
  - Installation guide
  - Usage examples (Web UI + CLI + Programmatic)
  - Architecture diagram
  - Workflow explanation
  - Legal disclaimer
- **CHANGELOG.md**: This file
- **Inline code comments**: Russian + English

---

### 🚀 Improvements

#### Dependencies (`requirements.txt`)
- Added `playwright==1.48.0` — browser automation
- Added `shodan==1.31.0` — Shodan API client
- Added `censys==2.2.12` — Censys API client
- Added `aiohttp`, `beautifulsoup4`, `lxml` — additional utilities

#### Existing Agents
- **EnumeratorAgent**: Full rewrite with API integrations
- **Orchestrator**: V3 replaces V2 with better decision-making

---

### 📊 Statistics

**Before:**
- Basic reconnaissance
- Manual exploitation
- No API intelligence
- No browser automation
- Simple reporting

**After:**
- Multi-source intelligence (5 APIs)
- Autonomous exploitation with chaining
- Browser-based attacks
- Professional HTML/Markdown/JSON reports
- 100+ new payloads
- 15+ critical tools auto-installed

---

### 🎯 Capabilities Unlocked

| Feature | v1.0 | v2.0 Ultimate |
|---------|------|---------------|
| Subdomain enumeration | ✅ | ✅✅ (crt.sh + SecurityTrails + VirusTotal) |
| Shodan integration | ❌ | ✅ |
| Censys integration | ❌ | ✅ |
| GitHub dorking | ❌ | ✅ |
| Subdomain takeover | Basic | Advanced (11 services) |
| Cloud bucket enum | ❌ | ✅ (S3/Azure/GCP) |
| Browser automation | ❌ | ✅ (Playwright) |
| XSS with browser | ❌ | ✅ |
| Cookie stealing | ❌ | ✅ |
| Session hijacking | ❌ | ✅ |
| HTML reporting | Basic | Professional |
| Parallel execution | ❌ | ✅ (asyncio) |
| Decision tree | Simple | Enhanced AI-powered |
| Exploit chaining | ❌ | ✅ |
| Auto-install script | ❌ | ✅ |

---

### 🔧 Breaking Changes

None — fully backwards compatible.

New features are opt-in via:
- API keys (if not provided, skips API calls)
- Orchestrator V3 (V2 still available)
- Browser agent (separate module)

---

### 🐛 Bug Fixes

- Fixed enumerator API key validation
- Improved error handling in browser agent
- Better async/await in orchestrator V3

---

### 📝 TODO (Future Versions)

- [ ] Metasploit integration (auto-exploit with msfconsole)
- [ ] WAF bypass engine
- [ ] Credential stuffing module
- [ ] JWT manipulation attacks
- [ ] GraphQL fuzzing
- [ ] Kubernetes/Docker enumeration
- [ ] Active Directory exploitation
- [ ] Network graph visualization (D3.js)
- [ ] Machine learning for vulnerability prediction
- [ ] Integration with Burp Suite / ZAP

---

### 🙏 Credits

Built with:
- Claude 3.5 Sonnet (Anthropic)
- Playwright (Microsoft)
- Nuclei (ProjectDiscovery)
- OWASP Amass
- Community security tools

**Status:** CHINESE KILLER LEVEL UNLOCKED 🔥

---

### 📞 Support

Issues: https://github.com/nominalooo/rex35/issues
Telegram: @nominalooo (probably)

**Remember:** Only use on authorized targets. Illegal use = prison time.
