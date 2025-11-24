#!/usr/bin/env python3

import os
import subprocess
import sys
import urllib.request

def run_command(command):
    """Run a shell command and exit on failure"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"Command failed: {command}")
        sys.exit(1)

def get_public_ip():
    """Fetch the instance's public IPv4 from EC2 metadata service"""
    try:
        with urllib.request.urlopen("http://169.254.169.254/latest/meta-data/public-ipv4", timeout=5) as response:
            return response.read().decode('utf-8').strip()
    except Exception as e:
        print(f"Could not retrieve public IP: {e}")
        sys.exit(1)

def main():
    # Update system and install Apache
    run_command("yum update -y")
    run_command("yum install httpd -y")

    # Start and enable httpd
    run_command("service httpd start")
    run_command("chkconfig httpd on")

    # Get public IP
    public_ip = get_public_ip()
    print(f"Public IP detected: {public_ip}")

    # Write content to web pages
    with open("/var/www/html/index.html", "w") as f:
        f.write(f"Manual instance with IP {public_ip}\n")

    with open("/var/www/html/health.html", "w") as f:
        f.write("ok\n")

    print("Web server configured successfully!")

if __name__ == "__main__":
    # Simple check to ensure we're running as root (required for yum/service)
    if os.geteuid() != 0:
        print("This script must be run as root!")
        sys.exit(1)

    main()
