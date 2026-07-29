#!/usr/bin/env python3
# ===================================================================
# Project Name : NetRecon - Automated Kali Linux Installer
# Author       : Syed Hoque
# GitHub       : https://github.com/Syedhoque/netrecon.git
# ===================================================================

import os
import socket
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# GUI Libraries
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

try:
    import requests
except ImportError:
    requests = None


# Common Services Mapping
COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 111: "RPCbind", 135: "MSRPC",
    139: "NetBIOS", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    993: "IMAPS", 995: "POP3S", 1723: "PPTP", 3306: "MySQL",
    3389: "RDP", 5900: "VNC", 8080: "HTTP-Alt", 8443: "HTTPS-Alt",
}

# Standard Wordlists for Kali Linux
COMMON_WORDLIST_PATHS = [
    "/usr/share/seclists/Discovery/Web-Content/common.txt",
    "/usr/share/wordlists/dirb/common.txt",
    "/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt",
    "wordlists/common.txt",
    "/opt/netrecon/wordlists/common.txt"
]


def find_default_wordlist():
    for path in COMMON_WORDLIST_PATHS:
        if os.path.isfile(path):
            return path
    return None


# --------------------------------------------------------------------------
# Scanning Logic Engine
# --------------------------------------------------------------------------

def scan_port(target, port, timeout):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            if sock.connect_ex((target, port)) == 0:
                return port
    except Exception:
        pass
    return None


def parse_ports(port_spec):
    if port_spec.strip().lower() == "common":
        return sorted(COMMON_PORTS.keys())
    ports = set()
    for part in port_spec.split(","):
        part = part.strip()
        if "-" in part:
            s, e = part.split("-")
            ports.update(range(int(s), int(e) + 1))
        elif part.isdigit():
            ports.add(int(part))
    return sorted(ports)


def resolve_target(target):
    try:
        return socket.gethostbyname(target)
    except socket.gaierror:
        return None


def check_path(base_url, word, timeout, extensions):
    if requests is None:
        return []
    candidates = [word] + [f"{word}.{ext.lstrip('.')}" for ext in extensions]
    hits = []
    for candidate in candidates:
        url = f"{base_url.rstrip('/')}/{candidate.lstrip('/')}"
        try:
            resp = requests.get(url, timeout=timeout, allow_redirects=False)
            if resp.status_code in {200, 204, 301, 302, 307, 401, 403}:
                hits.append((url, resp.status_code, len(resp.content)))
        except Exception:
            continue
    return hits


# --------------------------------------------------------------------------
# Native Desktop GUI Application
# --------------------------------------------------------------------------

class NetReconGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("NetRecon - Security & Reconnaissance Suite")
        self.geometry("980x700")
        self.configure(bg="#0b0f19")

        self.active_mode = "portscan"
        self.is_scanning = False
        self.stop_requested = False
        self.scan_history = []

        # Fix native dialog colors globally
        self.option_add("*Dialog.msg.font", "Consolas 10")
        self.option_add("*FileDialog*Entry.background", "#ffffff")
        self.option_add("*FileDialog*Entry.foreground", "#000000")

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        
        self.style.configure(".", background="#0b0f19", foreground="#f3f4f6", font=("Consolas", 10))
        self.style.configure("TFrame", background="#0b0f19")
        self.style.configure("Card.TFrame", background="#111827", relief="solid", borderwidth=1)
        
        self.style.configure("TLabel", background="#111827", foreground="#9ca3af", font=("Consolas", 10))
        self.style.configure("Header.TLabel", background="#111827", foreground="#f97316", font=("Consolas", 14, "bold"))
        self.style.configure("SubHeader.TLabel", background="#111827", foreground="#6b7280", font=("Consolas", 8))
        self.style.configure("Counter.TLabel", background="#111827", foreground="#ffffff", font=("Consolas", 32, "bold"))

    def _build_ui(self):
        main_container = ttk.Frame(self, padding=15)
        main_container.pack(fill=tk.BOTH, expand=True)

        # ---------------- LEFT PANEL (Sidebar Controls) ----------------
        sidebar = ttk.Frame(main_container, style="Card.TFrame", padding=15)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        sidebar.config(width=340)

        # Header Title
        title_lbl = ttk.Label(sidebar, text="🟠 NETRECON", style="Header.TLabel")
        title_lbl.pack(anchor=tk.W)
        sub_lbl = ttk.Label(sidebar, text="// authorized targets only", style="SubHeader.TLabel")
        sub_lbl.pack(anchor=tk.W, pady=(0, 15))

        # Mode Selector Buttons
        btn_frame = ttk.Frame(sidebar, style="Card.TFrame")
        btn_frame.pack(fill=tk.X, pady=(0, 12))

        self.btn_port = tk.Button(
            btn_frame, text="PORT SCAN", bg="#f97316", fg="#000000", font=("Consolas", 9, "bold"),
            relief=tk.FLAT, activebackground="#f97316", command=lambda: self._set_mode("portscan")
        )
        self.btn_port.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)

        self.btn_dir = tk.Button(
            btn_frame, text="DIR BRUTE", bg="#1f2937", fg="#9ca3af", font=("Consolas", 9, "bold"),
            relief=tk.FLAT, activebackground="#1f2937", command=lambda: self._set_mode("dirbrute")
        )
        self.btn_dir.pack(side=tk.RIGHT, fill=tk.X, expand=True, ipady=5)

        # Form Inputs
        self.target_lbl = ttk.Label(sidebar, text="Target Host or IP")
        self.target_lbl.pack(anchor=tk.W, pady=(2, 2))
        
        self.entry_target = tk.Entry(sidebar, bg="#000000", fg="#ffffff", insertbackground="#ffffff", font=("Consolas", 10), relief=tk.SOLID, bd=1)
        self.entry_target.insert(0, "127.0.0.1")
        self.entry_target.pack(fill=tk.X, pady=(0, 10), ipady=4)

        self.dynamic_lbl = ttk.Label(sidebar, text="Ports ('common', 1-1000, 22,80)")
        self.dynamic_lbl.pack(anchor=tk.W, pady=(2, 2))

        self.entry_dynamic = tk.Entry(sidebar, bg="#000000", fg="#ffffff", insertbackground="#ffffff", font=("Consolas", 10), relief=tk.SOLID, bd=1)
        self.entry_dynamic.insert(0, "common")
        self.entry_dynamic.pack(fill=tk.X, pady=(0, 10), ipady=4)

        # Threads & Timeout
        params_frame = ttk.Frame(sidebar, style="Card.TFrame")
        params_frame.pack(fill=tk.X, pady=(0, 10))

        lbl_threads = ttk.Label(params_frame, text="Threads")
        lbl_threads.grid(row=0, column=0, sticky=tk.W)
        self.entry_threads = tk.Entry(params_frame, bg="#000000", fg="#ffffff", insertbackground="#ffffff", font=("Consolas", 10), relief=tk.SOLID, bd=1, width=10)
        self.entry_threads.insert(0, "200")
        self.entry_threads.grid(row=1, column=0, sticky=tk.W, pady=(2, 0), ipady=3)

        lbl_timeout = ttk.Label(params_frame, text="Timeout (s)")
        lbl_timeout.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        self.entry_timeout = tk.Entry(params_frame, bg="#000000", fg="#ffffff", insertbackground="#ffffff", font=("Consolas", 10), relief=tk.SOLID, bd=1, width=10)
        self.entry_timeout.insert(0, "1.0")
        self.entry_timeout.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(2, 0), ipady=3)

        # Action Buttons (Run / Stop)
        act_btn_frame = ttk.Frame(sidebar, style="Card.TFrame")
        act_btn_frame.pack(fill=tk.X, pady=(10, 15))

        self.btn_run = tk.Button(
            act_btn_frame, text="▶ RUN SCAN", bg="#f97316", fg="#000000", font=("Consolas", 10, "bold"),
            relief=tk.FLAT, activebackground="#ea580c", command=self._start_scan_thread
        )
        self.btn_run.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 4))

        self.btn_stop = tk.Button(
            act_btn_frame, text="⏹ STOP", bg="#dc2626", fg="#ffffff", font=("Consolas", 10, "bold"),
            relief=tk.FLAT, activebackground="#b91c1c", state=tk.DISABLED, command=self._stop_scan
        )
        self.btn_stop.pack(side=tk.RIGHT, fill=tk.X, expand=True, ipady=6, padx=(4, 0))

        # Bottom Utility Buttons (History & About)
        self.btn_history = tk.Button(
            sidebar, text="📜 SCAN HISTORY", bg="#0284c7", fg="#ffffff", font=("Consolas", 9, "bold"),
            relief=tk.FLAT, activebackground="#0369a1", command=self._show_history_popup
        )
        self.btn_history.pack(fill=tk.X, pady=(0, 8), ipady=5)

        self.btn_about = tk.Button(
            sidebar, text="ℹ ABOUT SOFTWARE", bg="#1e293b", fg="#f3f4f6", font=("Consolas", 9, "bold"),
            relief=tk.FLAT, activebackground="#334155", command=self._show_about_popup
        )
        self.btn_about.pack(fill=tk.X, ipady=5)

        # ---------------- RIGHT PANEL (Visual Display & Logs) ----------------
        display_panel = ttk.Frame(main_container)
        display_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Counter Dashboard Box
        counter_box = ttk.Frame(display_panel, style="Card.TFrame", padding=12)
        counter_box.pack(fill=tk.X, pady=(0, 10))

        self.console_title = ttk.Label(counter_box, text="Port scan console", style="Header.TLabel")
        self.console_title.pack(anchor=tk.W)

        self.lbl_counter = ttk.Label(counter_box, text="0", style="Counter.TLabel")
        self.lbl_counter.pack(anchor=tk.CENTER, pady=2)
        
        lbl_subtext = ttk.Label(counter_box, text="DISCOVERED RESULTS", style="SubHeader.TLabel")
        lbl_subtext.pack(anchor=tk.CENTER)

        # Console Header with Export Button
        console_header = ttk.Frame(display_panel)
        console_header.pack(fill=tk.X, pady=(0, 5))

        lbl_output = ttk.Label(console_header, text="TERMINAL OUTPUT", style="SubHeader.TLabel")
        lbl_output.pack(side=tk.LEFT, anchor=tk.W)

        self.btn_export = tk.Button(
            console_header, text="💾 EXPORT (.TXT)", bg="#2563eb", fg="#ffffff", font=("Consolas", 8, "bold"),
            relief=tk.FLAT, activebackground="#1d4ed8", command=self._export_results
        )
        self.btn_export.pack(side=tk.RIGHT)

        # Scrolling Console Terminal Output
        console_box = ttk.Frame(display_panel, style="Card.TFrame", padding=10)
        console_box.pack(fill=tk.BOTH, expand=True)

        self.txt_output = scrolledtext.ScrolledText(
            console_box, bg="#000000", fg="#00ff66", insertbackground="#00ff66",
            font=("Consolas", 9), relief=tk.FLAT, bd=0
        )
        self.txt_output.pack(fill=tk.BOTH, expand=True)
        self.txt_output.insert(tk.END, "$ System ready for reconnaissance scan...\n")

    def _show_about_popup(self):
        notice_text = (
            "===========================================================\n"
            "               NETRECON DIAGNOSTIC UTILITY                 \n"
            "===========================================================\n\n"
            "[+] DEVELOPER : Syed Hoque\n"
            "[+] ROLE      : Penetration Tester & Security Consultant\n"
            "[+] GITHUB    : https://github.com/Syedhoque/netrecon.git\n"
            "----------------------- ETHICAL NOTICE ---------------------\n"
            "NetRecon is designed for defensive cybersecurity,\n"
            "authorized Web Application Penetration Testing, and Recon.\n\n"
            "Always secure explicit permission before auditing target systems.\n"
            "==========================================================="
        )

        popup = tk.Toplevel(self)
        popup.title("About NetRecon")
        popup.geometry("580x360")
        popup.configure(bg="#050811")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()

        frame = tk.Frame(popup, bg="#0d1117", bd=1, relief=tk.SOLID)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        txt_about = tk.Text(
            frame, bg="#000000", fg="#00ff66", font=("Consolas", 9, "bold"),
            relief=tk.FLAT, bd=0, wrap=tk.WORD
        )
        txt_about.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def type_text(index=0):
            if index < len(notice_text):
                txt_about.insert(tk.END, notice_text[index])
                txt_about.see(tk.END)
                popup.after(10, type_text, index + 1)

        type_text()

        btn_close = tk.Button(
            frame, text="CLOSE", bg="#1f2937", fg="#ffffff", font=("Consolas", 9, "bold"),
            relief=tk.FLAT, activebackground="#374151", command=popup.destroy
        )
        btn_close.pack(pady=(0, 10), ipadx=15, ipady=3)

    def _show_history_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Scan History Logs")
        popup.geometry("620x400")
        popup.configure(bg="#0b0f19")
        popup.transient(self)
        popup.grab_set()

        frame = tk.Frame(popup, bg="#111827", bd=1, relief=tk.SOLID)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        lbl_title = tk.Label(frame, text="📜 RECONNAISSANCE SCAN HISTORY", bg="#111827", fg="#38bdf8", font=("Consolas", 11, "bold"))
        lbl_title.pack(anchor=tk.W, padx=10, pady=(10, 5))

        lst_box = tk.Listbox(
            frame, bg="#000000", fg="#38bdf8", selectbackground="#1e293b", selectforeground="#ffffff",
            font=("Consolas", 9), relief=tk.FLAT, bd=0
        )
        lst_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        if not self.scan_history:
            lst_box.insert(tk.END, " No scan history recorded yet.")
        else:
            for item in self.scan_history:
                lst_box.insert(tk.END, f" {item}")

        btn_bar = tk.Frame(frame, bg="#111827")
        btn_bar.pack(fill=tk.X, padx=10, pady=10)

        def clear_hist():
            self.scan_history.clear()
            lst_box.delete(0, tk.END)
            lst_box.insert(tk.END, " No scan history recorded yet.")

        btn_clear = tk.Button(btn_bar, text="CLEAR HISTORY", bg="#dc2626", fg="#ffffff", font=("Consolas", 8, "bold"), relief=tk.FLAT, command=clear_hist)
        btn_clear.pack(side=tk.LEFT, ipady=3, ipadx=10)

        btn_close = tk.Button(btn_bar, text="CLOSE", bg="#1f2937", fg="#ffffff", font=("Consolas", 8, "bold"), relief=tk.FLAT, command=popup.destroy)
        btn_close.pack(side=tk.RIGHT, ipady=3, ipadx=10)

    def _set_mode(self, mode):
        if self.is_scanning:
            return
        self.active_mode = mode
        if mode == "portscan":
            self.btn_port.config(bg="#f97316", fg="#000000")
            self.btn_dir.config(bg="#1f2937", fg="#9ca3af")
            self.target_lbl.config(text="Target Host or IP")
            self.dynamic_lbl.config(text="Ports ('common', 1-1000, 22,80)")
            self.entry_dynamic.delete(0, tk.END)
            self.entry_dynamic.insert(0, "common")
            self.entry_threads.delete(0, tk.END)
            self.entry_threads.insert(0, "200")
            self.console_title.config(text="Port scan console")
        else:
            self.btn_dir.config(bg="#f97316", fg="#000000")
            self.btn_port.config(bg="#1f2937", fg="#9ca3af")
            self.target_lbl.config(text="Target Base URL")
            self.dynamic_lbl.config(text="Extensions (e.g. php,html,txt)")
            self.entry_dynamic.delete(0, tk.END)
            self.entry_threads.delete(0, tk.END)
            self.entry_threads.insert(0, "30")
            self.console_title.config(text="Directory brute console")

    def _log(self, text):
        self.txt_output.insert(tk.END, text + "\n")
        self.txt_output.see(tk.END)

    def _stop_scan(self):
        if self.is_scanning:
            self.stop_requested = True
            self._log("\n[!] Stopping scan upon user request... Please wait.")
            self.btn_stop.config(state=tk.DISABLED, bg="#4b5563")

    def _start_scan_thread(self):
        if self.is_scanning:
            messagebox.showwarning("Warning", "A scan is already in progress.")
            return

        target = self.entry_target.get().strip()
        if not target:
            messagebox.showerror("Error", "Please provide a valid target host or URL.")
            return

        self.is_scanning = True
        self.stop_requested = False
        
        self.btn_run.config(state=tk.DISABLED, bg="#4b5563")
        self.btn_stop.config(state=tk.NORMAL, bg="#dc2626")
        self.lbl_counter.config(text="0")
        self.txt_output.delete(1.0, tk.END)

        threading.Thread(target=self._execute_scan, args=(target,), daemon=True).start()

    def _execute_scan(self, target):
        try:
            threads = int(self.entry_threads.get().strip())
            timeout = float(self.entry_timeout.get().strip())
        except ValueError:
            self._log("[!] Invalid Threads or Timeout value.")
            self._reset_run_button()
            return

        dynamic_val = self.entry_dynamic.get().strip()
        time_str = datetime.now().strftime("%H:%M:%S")

        if self.active_mode == "portscan":
            self._log(f"[*] Starting NetRecon Port Scan on: {target}")
            ip = resolve_target(target)
            if not ip:
                self._log(f"[!] Error: Could not resolve target {target}")
                self._reset_run_button()
                return

            try:
                ports = parse_ports(dynamic_val)
            except Exception as e:
                self._log(f"[!] Error parsing ports: {e}")
                self._reset_run_button()
                return

            self._log(f"[*] Target IP: {ip}")
            self._log(f"[*] Scanning {len(ports)} port(s) with {threads} threads...\n")

            open_count = 0
            start_time = time.time()

            with ThreadPoolExecutor(max_workers=threads) as executor:
                futures = {executor.submit(scan_port, ip, p, timeout): p for p in ports}
                for future in as_completed(futures):
                    if self.stop_requested:
                        break
                    port = futures[future]
                    res = future.result()
                    if res:
                        open_count += 1
                        service = COMMON_PORTS.get(port, "unknown")
                        self._log(f"[+] {port}/tcp open\t{service}")
                        self.lbl_counter.config(text=str(open_count))

            elapsed = time.time() - start_time
            if self.stop_requested:
                self._log(f"\n[!] Scan stopped by user after {elapsed:.2f}s.")
            else:
                self._log(f"\n[*] Scan complete in {elapsed:.2f}s. Total open ports: {open_count}")

            self.scan_history.insert(0, f"[{time_str}] PORTS: {target} -> {open_count} open")

        else:
            if requests is None:
                self._log("[!] Error: Python 'requests' module not installed. Run: sudo apt install python3-requests")
                self._reset_run_button()
                return

            if not target.startswith("http://") and not target.startswith("https://"):
                target = f"http://{target}"

            wpath = find_default_wordlist()
            if not wpath:
                self._log("[!] Error: No standard wordlist found on host.")
                self._reset_run_button()
                return

            self._log(f"[*] Starting Directory Brute-force on: {target}")
            self._log(f"[*] Wordlist: {wpath}")

            try:
                with open(wpath, errors="ignore") as f:
                    words = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            except Exception as e:
                self._log(f"[!] Failed to read wordlist: {e}")
                self._reset_run_button()
                return

            exts = [e.strip() for e in dynamic_val.split(",") if e.strip()]
            self._log(f"[*] Loaded {len(words)} words. Threads: {threads}\n")

            hits_count = 0
            start_time = time.time()

            with ThreadPoolExecutor(max_workers=threads) as executor:
                futures = {executor.submit(check_path, target, w, timeout, exts): w for w in words}
                for future in as_completed(futures):
                    if self.stop_requested:
                        break
                    hits = future.result()
                    for url, status, size in hits:
                        hits_count += 1
                        self._log(f"[+] Status: {status}\tSize: {size:>8} B\tURL: {url}")
                        self.lbl_counter.config(text=str(hits_count))

            elapsed = time.time() - start_time
            if self.stop_requested:
                self._log(f"\n[!] Directory brute stopped by user after {elapsed:.2f}s.")
            else:
                self._log(f"\n[*] Directory brute complete in {elapsed:.2f}s. Discovered: {hits_count}")

            self.scan_history.insert(0, f"[{time_str}] DIR BRUTE: {target} -> {hits_count} hits")

        self._reset_run_button()

    def _export_results(self):
        content = self.txt_output.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("Warning", "No scan output available to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files (*.txt)", "*.txt"), ("All Files (*.*)", "*.*")],
            title="Export Scan Results"
        )

        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Scan results exported successfully to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def _reset_run_button(self):
        self.is_scanning = False
        self.stop_requested = False
        self.btn_run.config(state=tk.NORMAL, bg="#f97316")
        self.btn_stop.config(state=tk.DISABLED, bg="#4b5563")


if __name__ == "__main__":
    app = NetReconGUI()
    app.mainloop()