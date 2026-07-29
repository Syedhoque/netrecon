# NetRecon - A lightweight network reconnaissance CLI tool

**NetRecon** is a lightweight, dependency-light network reconnaissance toolkit written in Python. It bundles two small utilities — a threaded TCP port scanner and an HTTP directory/file brute-forcer — behind a single CLI, plus an optional local web portal with a live radar-style visualization of results.
It's built for sysadmins, security learners, and anyone doing authorized testing who wants a simple, readable, hackable alternative to reaching for a full nmap/gobuster install.

---

## ⚡ Key Features
• **Native Desktop GUI** — Built with Tkinter for a seamless, dark-themed native experience on Kali Linux without requiring an external web browser.
• **Threaded TCP Port Scanner** — Quickly scan common ports, custom ranges, or specific ports with multi-threading and timeout controls.
• **HTTP Directory Brute-Forcer** — Enumerate web directories using standard Kali wordlists (e.g., SecLists, DIRB) with support for custom file extensions (`.php`, `.html`, `.txt`).
• **Live Stop Functionality** — Abort active scanning threads instantly using the built-in Stop button.
• **Export Results** — Export live console findings directly into clean `.txt` log files with a single click.
• **Persistent History Logs** — Track and view prior scan sessions through a dedicated Popup History Manager.
• **Cyber Typewriter About Section** — Includes built-in developer credentials and ethical usage notices.

---

## 🛠️ Requirements & Dependencies
Ensure Python 3, Tkinter, and Requests are installed on your system:

**bash command
sudo apt update && sudo apt install -y python3 python3-tk python3-requests

---

## 🚀 How to Run
After completed installation or cloning, navigate to the directory and run the application:

### From your root directory Navigate to the `netrecon`:
cd netrecon

### Run the application
python netrecon.py

---

## 📖 Usage Guide
**Select Mode**: Choose between PORT SCAN and DIR BRUTE using the top sidebar toggle.

###Target Input:
**Port Scan**: Enter an IP address or hostname (e.g., 127.0.0.1 or example.com).

**Dir Brute**: Enter a target URL (e.g., http://example.com).

**Parameters**:

**Ports**: Enter common, ranges (1-1000), or lists (22,80,443).

**Extensions**: Specify extensions for web brute-forcing (e.g., php,html,txt).

**Threads & Timeout**: Fine-tune execution speed and connection timeout.

**Execute & Control**:

**Click** ▶ RUN SCAN to begin.

**Click** ⏹ STOP to interrupt an ongoing scan at any time.

**Click** 💾 EXPORT (.TXT) to save the current terminal log.

**Click** 📜 SCAN HISTORY to view or clear session logs.

**Click** ℹ ABOUT SOFTWARE to view developer info and compliance notices.


## 📜 License
Distributed under the MIT License. See LICENSE for more information.

---


## 🚀 Installation & Setup

### Option 1: Automated 1-Line Installer (Kali Linux)
Open your Kali Linux terminal and execute the following command to automatically download, install dependencies, create desktop shortcuts, and launch the tool:

```bash
git clone https://github.com/Syedhoque/netrecon.git ~/netrecon && cd ~/netrecon && chmod +x install.sh && sudo ./install.sh
