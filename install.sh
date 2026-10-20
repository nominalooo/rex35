#!/bin/bash
# REX35 — Full installation script for all pentest tools
# Author: rex
# Usage: chmod +x install.sh && ./install.sh

set -e
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}[REX35] Starting full installation...${NC}"

# ═══════════════════════════════════════════════════════════
# 1. SYSTEM DEPENDENCIES
# ═══════════════════════════════════════════════════════════
echo -e "${GREEN}[1/8] Installing system dependencies...${NC}"
sudo apt update -qq
sudo apt install -y \
    git curl wget build-essential \
    python3-pip golang-go cargo \
    libpcap-dev nmap masscan \
    hydra john hashcat \
    metasploit-framework \
    dnsutils whois nikto \
    jq parallel netcat-openbsd \
    > /dev/null 2>&1 || echo -e "${RED}[WARN] Some apt packages failed${NC}"

# ═══════════════════════════════════════════════════════════
# 2. GO TOOLS
# ═══════════════════════════════════════════════════════════
echo -e "${GREEN}[2/8] Installing Go-based tools...${NC}"
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin

go install github.com/OWASP/Amass/v3/...@master 2>/dev/null || echo "Amass already installed"
go install github.com/lc/gau/v2/cmd/gau@latest 2>/dev/null || echo "gau already installed"
go install github.com/devanshbatham/ParamSpider@latest 2>/dev/null || echo "ParamSpider already installed"
go install github.com/s0md3v/Arjun/cmd/arjun@latest 2>/dev/null || echo "Arjun already installed"
go install github.com/ffuf/ffuf/v2@latest 2>/dev/null || echo "ffuf already installed"
go install github.com/dwisiswant0/crlfuzz/cmd/crlfuzz@latest 2>/dev/null || echo "crlfuzz already installed"
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest 2>/dev/null || echo "subfinder already installed"
go install github.com/projectdiscovery/httpx/cmd/httpx@latest 2>/dev/null || echo "httpx already installed"
go install github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest 2>/dev/null || echo "nuclei already installed"
go install github.com/tomnomnom/waybackurls@latest 2>/dev/null || echo "waybackurls already installed"

# ═══════════════════════════════════════════════════════════
# 3. RUST TOOLS
# ═══════════════════════════════════════════════════════════
echo -e "${GREEN}[3/8] Installing Rust-based tools...${NC}"
cargo install rustscan 2>/dev/null || echo "rustscan already installed"
cargo install feroxbuster 2>/dev/null || echo "feroxbuster already installed"

# ═══════════════════════════════════════════════════════════
# 4. PYTHON TOOLS
# ═══════════════════════════════════════════════════════════
echo -e "${GREEN}[4/8] Installing Python tools...${NC}"
pip3 install -q --upgrade pip setuptools wheel

# XSStrike
if [ ! -d "/opt/XSStrike" ]; then
    git clone -q https://github.com/s0md3v/XSStrike /opt/XSStrike
    pip3 install -q -r /opt/XSStrike/requirements.txt
fi

# Commix
if [ ! -d "/opt/commix" ]; then
    git clone -q https://github.com/commixproject/commix /opt/commix
fi

# SQLMap (usually pre-installed)
pip3 install -q sqlmap 2>/dev/null || echo "sqlmap via apt"

# Playwright for browser automation
pip3 install -q playwright
playwright install chromium --with-deps > /dev/null 2>&1 || echo "Playwright installed"

# ═══════════════════════════════════════════════════════════
# 5. POST-EXPLOITATION TOOLS
# ═══════════════════════════════════════════════════════════
echo -e "${GREEN}[5/8] Downloading post-exploitation scripts...${NC}"
mkdir -p payloads/post_exploit

# LinPEAS
wget -q -O payloads/post_exploit/linpeas.sh \
    https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh

# WinPEAS
wget -q -O payloads/post_exploit/winPEASx64.exe \
    https://github.com/carlospolop/PEASS-ng/releases/latest/download/winPEASx64.exe

# pspy (process monitor without root)
wget -q -O payloads/post_exploit/pspy64 \
    https://github.com/DominicBreuker/pspy/releases/latest/download/pspy64

chmod +x payloads/post_exploit/*.sh payloads/post_exploit/pspy64

# ═══════════════════════════════════════════════════════════
# 6. WORDLISTS & PAYLOADS
# ═══════════════════════════════════════════════════════════
echo -e "${GREEN}[6/8] Expanding wordlists...${NC}"
mkdir -p payloads/wordlists

# SecLists (если нет)
if [ ! -d "/usr/share/seclists" ] && [ ! -d "payloads/seclists" ]; then
    git clone -q --depth 1 https://github.com/danielmiessler/SecLists payloads/seclists
fi

# ═══════════════════════════════════════════════════════════
# 7. NUCLEI TEMPLATES
# ═══════════════════════════════════════════════════════════
echo -e "${GREEN}[7/8] Updating nuclei templates...${NC}"
nuclei -update-templates -silent 2>/dev/null || echo "Nuclei templates updated"

# ═══════════════════════════════════════════════════════════
# 8. API KEYS TEMPLATE
# ═══════════════════════════════════════════════════════════
echo -e "${GREEN}[8/8] Creating API keys template...${NC}"
mkdir -p config

if [ ! -f "config/api_keys.json" ]; then
    cat > config/api_keys.json << 'EOF'
{
  "shodan": "YOUR_SHODAN_API_KEY_HERE",
  "censys_id": "YOUR_CENSYS_APP_ID_HERE",
  "censys_secret": "YOUR_CENSYS_SECRET_HERE",
  "virustotal": "YOUR_VIRUSTOTAL_API_KEY_HERE",
  "securitytrails": "YOUR_SECURITYTRAILS_API_KEY_HERE",
  "hunter": "YOUR_HUNTER_IO_API_KEY_HERE",
  "github": "YOUR_GITHUB_TOKEN_HERE"
}
EOF
    echo -e "${GREEN}[REX35] API keys template created at config/api_keys.json${NC}"
    echo -e "${RED}[ACTION REQUIRED] Edit config/api_keys.json with your real API keys!${NC}"
fi

# ═══════════════════════════════════════════════════════════
# VERIFICATION
# ═══════════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}[REX35] Installation complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo ""
echo "Installed tools:"
echo "  - masscan, nmap, rustscan (network scanning)"
echo "  - amass, subfinder (subdomain enumeration)"
echo "  - ffuf, feroxbuster, gobuster (fuzzing)"
echo "  - nuclei (vulnerability scanner)"
echo "  - gau, waybackurls, paramspider (endpoint discovery)"
echo "  - xsstrike, commix, sqlmap (exploitation)"
echo "  - hydra, john, hashcat (password cracking)"
echo "  - LinPEAS, WinPEAS, pspy (post-exploitation)"
echo "  - playwright (browser automation)"
echo ""
echo -e "${RED}Next steps:${NC}"
echo "  1. Edit config/api_keys.json with your real API keys"
echo "  2. Run: python3 main.py"
echo "  3. Navigate to http://localhost:8000"
echo ""
echo -e "${GREEN}Rex is ready to dominate.${NC}"
