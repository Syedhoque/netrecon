#!/usr/bin/env python3
"""
NetRecon - A lightweight network reconnaissance CLI tool.

Includes:
  - portscan: threaded TCP port scanner
  - dirbrute: threaded HTTP directory/file brute-forcer

LEGAL NOTICE:
Only use this tool against systems you own or have explicit written
authorization to test. Unauthorized scanning or brute-forcing of systems
you do not control may violate laws such as the U.S. Computer Fraud and
Abuse Act (CFAA), the UK Computer Misuse Act, or equivalent legislation
elsewhere. You are solely responsible for how you use this tool.
"""

import argparse
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None


COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 111: "RPCbind", 135: "MSRPC",
    139: "NetBIOS", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    993: "IMAPS", 995: "POP3S", 1723: "PPTP", 3306: "MySQL",
    3389: "RDP", 5900: "VNC", 8080: "HTTP-Alt", 8443: "HTTPS-Alt",
}


# --------------------------------------------------------------------------
# Port scanner
# --------------------------------------------------------------------------

def scan_port(target, port, timeout):
    """Attempt a TCP connect to a single port. Returns port if open, else None."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((target, port))
            if result == 0:
                return port
    except socket.error:
        return None
    return None


def parse_ports(port_spec):
    """Parse a port spec like '22,80,443' or '1-1000' or 'common' into a list of ints."""
    if port_spec == "common":
        return sorted(COMMON_PORTS.keys())

    ports = set()
    for part in port_spec.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-")
            ports.update(range(int(start), int(end) + 1))
        elif part:
            ports.add(int(part))
    return sorted(ports)


def resolve_target(target):
    try:
        return socket.gethostbyname(target)
    except socket.gaierror:
        print(f"[!] Could not resolve host: {target}")
        sys.exit(1)


def run_portscan(args):
    ip = resolve_target(args.target)
    ports = parse_ports(args.ports)

    print(f"[*] NetRecon port scan starting")
    print(f"[*] Target: {args.target} ({ip})")
    print(f"[*] Ports: {len(ports)} total")
    print(f"[*] Threads: {args.threads}  Timeout: {args.timeout}s")
    print(f"[*] Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    open_ports = []
    start = time.time()

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {
            executor.submit(scan_port, ip, port, args.timeout): port
            for port in ports
        }
        for future in as_completed(futures):
            port = futures[future]
            result = future.result()
            if result:
                service = COMMON_PORTS.get(port, "unknown")
                print(f"[+] {port}/tcp open\t{service}")
                open_ports.append(port)

    elapsed = time.time() - start
    print(f"\n[*] Scan complete in {elapsed:.2f}s. {len(open_ports)} open port(s) found.")
    if open_ports:
        print(f"[*] Open ports: {sorted(open_ports)}")


# --------------------------------------------------------------------------
# Directory / file brute-forcer
# --------------------------------------------------------------------------

DEFAULT_STATUS_CODES = {200, 204, 301, 302, 307, 401, 403}


def check_path(base_url, word, timeout, extensions):
    if requests is None:
        return []

    candidates = [word] + [f"{word}.{ext.lstrip('.')}" for ext in extensions]
    hits = []
    for candidate in candidates:
        url = f"{base_url.rstrip('/')}/{candidate.lstrip('/')}"
        try:
            resp = requests.get(url, timeout=timeout, allow_redirects=False)
            if resp.status_code in DEFAULT_STATUS_CODES:
                hits.append((url, resp.status_code, len(resp.content)))
        except requests.RequestException:
            continue
    return hits


def run_dirbrute(args):
    if requests is None:
        print("[!] The 'requests' package is required for dirbrute. Install with:")
        print("    pip install requests")
        sys.exit(1)

    with open(args.wordlist) as f:
        words = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    extensions = args.extensions.split(",") if args.extensions else []

    print(f"[*] NetRecon directory brute-force starting")
    print(f"[*] Target: {args.url}")
    print(f"[*] Wordlist: {args.wordlist} ({len(words)} words)")
    print(f"[*] Extensions: {extensions if extensions else 'none'}")
    print(f"[*] Threads: {args.threads}  Timeout: {args.timeout}s")
    print(f"[*] Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    found = []
    start = time.time()

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {
            executor.submit(check_path, args.url, word, args.timeout, extensions): word
            for word in words
        }
        for future in as_completed(futures):
            hits = future.result()
            for url, status, size in hits:
                print(f"[+] {status}\t{size:>8} bytes\t{url}")
                found.append((url, status, size))

    elapsed = time.time() - start
    print(f"\n[*] Scan complete in {elapsed:.2f}s. {len(found)} result(s) found.")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="netrecon",
        description="NetRecon - lightweight network reconnaissance CLI tool. "
                     "Only use against systems you own or are authorized to test.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("portscan", help="Threaded TCP port scanner")
    p_scan.add_argument("target", help="Target hostname or IP address")
    p_scan.add_argument(
        "-p", "--ports", default="common",
        help="Ports to scan: 'common', '1-1000', or '22,80,443' (default: common)"
    )
    p_scan.add_argument("-t", "--threads", type=int, default=200, help="Number of threads (default: 200)")
    p_scan.add_argument("--timeout", type=float, default=1.0, help="Socket timeout in seconds (default: 1.0)")
    p_scan.set_defaults(func=run_portscan)

    p_dir = sub.add_parser("dirbrute", help="Threaded HTTP directory/file brute-forcer")
    p_dir.add_argument("url", help="Base URL, e.g. https://example.com")
    p_dir.add_argument(
        "-w", "--wordlist", default="wordlists/common.txt",
        help="Path to wordlist file (default: wordlists/common.txt)"
    )
    p_dir.add_argument("-x", "--extensions", default="", help="Comma-separated extensions, e.g. php,html,txt")
    p_dir.add_argument("-t", "--threads", type=int, default=30, help="Number of threads (default: 30)")
    p_dir.add_argument("--timeout", type=float, default=5.0, help="Request timeout in seconds (default: 5.0)")
    p_dir.set_defaults(func=run_dirbrute)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
