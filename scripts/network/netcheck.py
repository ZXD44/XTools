#!/usr/bin/env python3
"""XTools Network Check — เช็ค Public IP, DNS, Ping และพอร์ตที่เปิด"""

import socket
import subprocess
import urllib.request

CYAN, GREEN, RED, DIM, BOLD, RESET = "\033[96m", "\033[92m", "\033[91m", "\033[90m", "\033[1m", "\033[0m"


def main() -> None:
    print(f"{BOLD}{CYAN}┌── [ Network Diagnostics — ตรวจสอบเครือข่าย ] ────────┐{RESET}")
    print(f"  Hostname  : {socket.gethostname()}")
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
        print(f"  Local IP  : {local_ip}")
    except Exception:
        pass
    try:
        pub = urllib.request.urlopen("https://api.ipify.org", timeout=3).read().decode().strip()
        print(f"  Public IP : {GREEN}{pub}{RESET}")
    except Exception:
        print(f"  Public IP : {RED}ไม่สามารถเชื่อมต่อได้{RESET}")

    host = input("\n  เช็คพอร์ต/Ping ปลายทาง (เช่น 127.0.0.1:8080 หรือ google.com): ").strip()
    if not host:
        return
    if ":" in host:
        h, p = host.rsplit(":", 1)
        try:
            with socket.create_connection((h, int(p)), timeout=2):
                print(f"  {GREEN}[OPEN]{RESET} {h}:{p}")
        except Exception:
            print(f"  {RED}[CLOSED]{RESET} {h}:{p}")
    else:
        subprocess.run(["ping", "-n" if hasattr(subprocess, "CREATE_NO_WINDOW") else "-c", "2", host], check=False)


if __name__ == "__main__":
    main()
