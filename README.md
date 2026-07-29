# NetRecon - A lightweight network reconnaissance CLI tool

**NetRecon** is a lightweight, dependency-light network reconnaissance toolkit written in Python. It bundles two small utilities — a threaded TCP port scanner and an HTTP directory/file brute-forcer — behind a single CLI, plus an optional local web portal with a live radar-style visualization of results.
It's built for sysadmins, security learners, and anyone doing authorized testing who wants a simple, readable, hackable alternative to reaching for a full nmap/gobuster install.

---


## Key Features
• **Threaded TCP port scanner** — scan common ports, a range, or a custom list with configurable thread count and timeout.
• **HTTP directory/file brute-forcer** — walk a wordlist against a target URL, with optional file extensions (.php, .html, etc.) and a bundled starter wordlist.
• **Single CLI, two subcommands** — netrecon.py portscan and netrecon.py dirbrute, no separate binaries to manage.
• **Local web portal** — a Flask app with a browser UI: mode toggle, live radar sweep animation, and a scrolling terminal-style log of results.
• **Minimal dependencies** — the port scanner uses only the Python standard library; requests and flask are only needed for HTTP brute-forcing and the web UI respectively.
• **Sane defaults, tunable everything** — thread counts and timeouts are capped and configurable so scans stay predictable on a laptop or a small VM.

---

## 🚀 How to Run
After completed installation or cloning, navigate to the directory and run the application:

### From your root directory Navigate to the `netrecon`:
cd netrecon

### Run the application
python3 netrecon.py

---

## 🛠️ Usage Guide
**CLI: Port scan**
# Scan the most common ports (default)
python netrecon.py portscan 192.168.1.10

# Scan a custom range
python netrecon.py portscan example.com -p 1-1000

# Scan specific ports with more threads
python netrecon.py portscan 10.0.0.5 -p 22,80,443,8080 -t 500
Flag	Description	Default
-p, --ports	common, a range 1-1000, or a list 22,80,443	common
-t, --threads	Number of worker threads	200
--timeout	Per-connection timeout (seconds)	1.0
CLI: Directory brute-force
# Use the bundled wordlist
python netrecon.py dirbrute https://example.com

# Use your own wordlist and check extensions
python netrecon.py dirbrute https://example.com -w /path/to/wordlist.txt -x php,html,txt
Flag	Description	Default
-w, --wordlist	Path to a newline-delimited wordlist	wordlists/common.txt
-x, --extensions	Comma-separated extensions to also try	none
-t, --threads	Number of worker threads	30
--timeout	Per-request timeout (seconds)	5.0
For real engagements, point -w at a larger list such as one from SecLists.
Web portal
pip install -r requirements.txt
cd web
python app.py
# open http://127.0.0.1:5000
This runs the same scanning code as the CLI, triggered from a form instead of arguments — same output, plus a live radar view. It's a local, unauthenticated dev server: don't expose it to the internet or an untrusted network.
Example output
[*] NetRecon port scan starting
[*] Target: example.com (93.184.216.34)
[*] Ports: 20 total
[*] Threads: 200  Timeout: 1.0s

[+] 80/tcp open	HTTP
[+] 443/tcp open	HTTPS


## 📜 License
Distributed under the MIT License. See LICENSE for more information.

---


## 🚀 Installation & Setup

### Option 1: Automated 1-Line Installer (Kali Linux)
Open your Kali Linux terminal and execute the following command to automatically download, install dependencies, create desktop shortcuts, and launch the tool:

```bash
git clone https://github.com/Syedhoque/netrecon.git ~/netrecon && cd ~/netrecon && chmod +x install.sh && sudo ./install.sh
