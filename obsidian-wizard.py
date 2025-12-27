#!/usr/bin/env python3
import os
import sys
import tty
import termios
import tempfile
import time
import subprocess
import shutil
import re

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DIM = '\033[2m'
    BRIGHT_WHITE = '\033[97m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_YELLOW = '\033[93m'

DEFAULT_MKOBSFS_CONTENT = """
:<<:
Packages can be programs or parts of your system.
$PACKAGES can be thought of as a mega-package in this situation that has everything needed for boot..
You may add on packages from https://archlinux.org/packages/ here.
Reccomended: add the `plasma` package to get a desktop.
:
PACKAGES="$PACKAGES"
:<<:
Some simple configuration:
TIMEZONE is your (olson) timezone
HOSTNAME is the name of your computer
SERVICES are services. If you added the `plasma` package, we highly reccomend you add `sddm` to services.
:
TIMEZONE=""
HOSTNAME="obsidianbtw"
SERVICES="$SERVICES"
:<<:
YAY_GET is close to packages, but from https://aur.archlinux.org/.
These are COMMUNITY MADE.
$YAY_GET is a bunch of obsidianOS tools that are needed.
: 
YAY_GET="$YAY_GET"
:<<:
This section creates a user that is not root.
root can do anything, but that also makes it unsafe.
We HIGHLY RECCOMEND you add a user.
If you dont know what dotfiles are, we reccomend you do NOT set these.
:
ADMIN_USER="user"
ADMIN_DOTFILES=""
ADMIN_DOTFILES_TYPE=""
"""

DEFAULT_PARTITION_SIZES = {
    "esp_size": "512M",
    "rootfs_size": "10G",
    "etc_size": "1G",
    "var_size": "5G"
}

IS_ARCHISO_REAL = os.path.isfile("/etc/system.sfs")
IS_ARCHISO = True
OBSIDIANCTL_PATH = "obsidianctl" if IS_ARCHISO else (shutil.which("obsidianctl") or "/tmp/obsidianctl/obsidianctl")

def get_current_slots():
    try:
        output = subprocess.check_output([OBSIDIANCTL_PATH, "status"], text=True).splitlines()
        slots = []
        for line in output:
            if "Slot" in line:
                match = re.search(r'Slot\s+([ab])', line)
                if match:
                    slots.append(match.group(1))
        return slots if slots else ["a", "b"]
    except:
        return ["a", "b"]

def get_next_slot():
    current_slots = get_current_slots()
    if not current_slots:
        return "a"
    current_slot = current_slots[0] if current_slots else "a"
    return "b" if current_slot == "a" else "a"

CURRENT_SLOT = get_current_slots()
NEXT_SLOT = get_next_slot()

def get_terminal_size():
    try:
        return os.get_terminal_size()
    except OSError:
        return 80, 24

def draw_box(text, width, style="single"):
    lines = text.split('\n')
    max_len = max(len(line) for line in lines) if lines else 0
    content_width = min(max_len + 4, width - 4)
    if style == "double":
        top = "╔" + "═" * (content_width - 2) + "╗"
        bottom = "╚" + "═" * (content_width - 2) + "╝"
        side = "║"
    else:
        top = "┌" + "─" * (content_width - 2) + "┐"
        bottom = "└" + "─" * (content_width - 2) + "┘"
        side = "│"
    
    result = [top]
    for line in lines:
        padding = content_width - len(line) - 2
        left_pad = padding // 2
        right_pad = padding - left_pad
        result.append(f"{side}{' ' * left_pad}{line}{' ' * right_pad}{side}")
    result.append(bottom)
    return '\n'.join(result)

def print_centered(text, color="", box_style=None):
    width, _ = get_terminal_size()
    if box_style:
        text = draw_box(text, width, box_style)
    
    lines = text.split('\n')
    for line in lines:
        padding = max(0, (width - len(line)) // 2)
        print(" " * padding + color + line + Colors.ENDC)

def strip_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def draw_header():
    width, _ = get_terminal_size()
    logo_lines = [
        Colors.HEADER,
        f" ██████╗ ██████╗ ███████╗██╗██████╗ ██╗ █████╗ ███╗   ██╗ ██████╗ ███████╗",
        f"██╔═══██╗██╔══██╗██╔════╝██║██╔══██╗██║██╔══██╗████╗  ██║██╔═══██╗██╔════╝",
        f"██║   ██║██████╔╝███████╗██║██║  ██║██║███████║██╔██╗ ██║██║   ██║███████╗",
        f"██║   ██║██╔══██╗╚════██║██║██║  ██║██║██╔══██║██║╚██╗██║██║   ██║╚════██║",
        f"╚██████╔╝██████╔╝███████║██║██████╔╝██║██║  ██║██║ ╚████║╚██████╔╝███████║",
        f" ╚═════╝ ╚═════╝ ╚══════╝╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝{Colors.ENDC}"
    ]
    
    print()
    for line in logo_lines:
        clean_length = len(strip_ansi(line))
        padding = max(0, (width - clean_length) // 2)
        print(" " * padding + line)
    print()

def draw_progress_bar(progress, width=40):
    filled = int(width * progress)
    bar = f"{Colors.BRIGHT_GREEN}{'█' * filled}{Colors.DIM}{'░' * (width - filled)}{Colors.ENDC}"
    percentage = f"{Colors.BRIGHT_WHITE}{int(progress * 100)}%{Colors.ENDC}"
    return f"[{bar}] {percentage}"

def print_menu_(title, options, selected_index, subtitle=""):
    clear_screen()
    width, height = get_terminal_size()
    draw_header()
    print()
    print_centered(title, Colors.BRIGHT_WHITE + Colors.BOLD)
    if subtitle:
        print_centered(subtitle, Colors.DIM)
    print("\n" * 2)
    menu_start = len(options) // 2
    for i, option in enumerate(options):
        color = Colors.DIM
        if i == selected_index:
            color = Colors.BRIGHT_WHITE + Colors.BOLD
        print_centered(f"  {option}  ", color)
        if i < len(options) - 1:
            print()
    
    print("\n" * 3)
    print_centered(f"{Colors.DIM}Use ↑↓ to navigate, Enter to select, Q to quit{Colors.ENDC}")

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            next_chars = sys.stdin.read(2)
            ch += next_chars
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def selection_menu(title, options, subtitle=""):
    selected_index = 0
    while True:
        print_menu_(title, options, selected_index, subtitle)
        key = get_key()
        if key == '\x1b[A':
            selected_index = (selected_index - 1) % len(options)
        elif key == '\x1b[B':
            selected_index = (selected_index + 1) % len(options)
        elif key == '\r':
            return options[selected_index]
        elif key == '\x03' or key.lower() == 'q':
            return None

def get_disks():
    try:
        output = subprocess.check_output(["lsblk", "-d", "-n", "-o", "NAME,SIZE,MODEL"], text=True).strip().split('\n')
        disks = []
        for line in output:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    size = parts[1]
                    model = ' '.join(parts[2:]) if len(parts) > 2 else "Unknown"
                    disks.append(f"/dev/{name} ({size}) - {model}")
        return disks
    except Exception:
        return []

def confirm(message, warning=False, summary=None, details=None):
    clear_screen()
    width, height = get_terminal_size()
    draw_header()
    print("\n" * 2)
    
    if warning:
        color = Colors.BRIGHT_YELLOW
        icon = "!"
    else:
        color = Colors.BRIGHT_CYAN
        icon = "?"
    
    print_centered(f"{icon} CONFIRMATION {icon}", color)
    print("\n")
    print_centered(message, color)
    
    if summary:
        print("\n")
        print_centered("Summary:", Colors.BRIGHT_WHITE + Colors.BOLD)
        print_centered(summary, Colors.BRIGHT_CYAN)
    
    if details:
        print("\n")
        print_centered("Details:", Colors.BRIGHT_WHITE + Colors.BOLD)
        for detail in details:
            print_centered(f"• {detail}", Colors.DIM)
    
    print("\n" * 2)
    
    options = ["Yes, Continue", "No, Go Back"]
    selected_index = 0
    
    while True:
        for i, option in enumerate(options):
            color = Colors.DIM
            if i == selected_index:
                color = Colors.BRIGHT_WHITE + Colors.BOLD
            print_centered(f"  {option}  ", color)
            if i < len(options) - 1:
                print()
        
        print("\n" * 2)
        print_centered(f"{Colors.DIM}Use ↑↓ to navigate, Enter to select, Q to quit{Colors.ENDC}")
        
        key = get_key()
        if key == '\x1b[A':
            selected_index = (selected_index - 1) % len(options)
            clear_screen()
            draw_header()
            print("\n" * 2)
            print_centered(f"{icon} CONFIRMATION {icon}", color)
            print("\n")
            print_centered(message, color)
            if summary:
                print("\n")
                print_centered("Summary:", Colors.BRIGHT_WHITE + Colors.BOLD)
                print_centered(summary, Colors.BRIGHT_CYAN)
            if details:
                print("\n")
                print_centered("Details:", Colors.BRIGHT_WHITE + Colors.BOLD)
                for detail in details:
                    print_centered(f"• {detail}", Colors.DIM)
            print("\n" * 2)
        elif key == '\x1b[B':
            selected_index = (selected_index + 1) % len(options)
            clear_screen()
            draw_header()
            print("\n" * 2)
            print_centered(f"{icon} CONFIRMATION {icon}", color)
            print("\n")
            print_centered(message, color)
            if summary:
                print("\n")
                print_centered("Summary:", Colors.BRIGHT_WHITE + Colors.BOLD)
                print_centered(summary, Colors.BRIGHT_CYAN)
            if details:
                print("\n")
                print_centered("Details:", Colors.BRIGHT_WHITE + Colors.BOLD)
                for detail in details:
                    print_centered(f"• {detail}", Colors.DIM)
            print("\n" * 2)
        elif key == '\r':
            return options[selected_index].startswith("Yes")
        elif key == '\x03' or key.lower() == 'q':
            return False

def select_system_image(action_type="install"):
    preconf_path = "/usr/preconf"
    mkobsfs_files = []
    sfs_files = []
    if os.path.exists(preconf_path):
        for f in os.listdir(preconf_path):
            if f.endswith(".mkobsfs"):
                mkobsfs_files.append(f)
            elif f.endswith(".sfs"):
                sfs_files.append(f)
    
    current_dir_files = []
    try:
        for f in os.listdir('.'):
            if f.endswith('.mkobsfs') or f.endswith('.sfs'):
                current_dir_files.append(f"[Current Dir] {f}")
    except:
        pass
    
    options = ["Create New Config"]
    if IS_ARCHISO_REAL:
        options.append("Default System Image")
        
    if mkobsfs_files:
        options.append("Pre-configured Images")
        for f in sorted(mkobsfs_files):
            options.append(f"  ├─ {f}")
    
    if sfs_files:
        options.append("System Images") 
        for f in sorted(sfs_files):
            options.append(f"  ├─ {f}")
    
    if current_dir_files:
        options.append("Local Directory")
        for f in current_dir_files:
            options.append(f"  ├─ {f}")
    while True:
        choice = selection_menu(
            f"Select System Image for {action_type.title()}", 
            options,
            "Choose your system configuration"
        )

        if choice is None:
            return None

        if choice.startswith("Default System Image"):
            if confirm(
                "Use default system image (/etc/system.sfs)?",
                summary="Default system image will be used",
                details=[
                    "Path: /etc/system.sfs",
                    "This is the standard system image for this installation media"
                ]
            ):
                return "/etc/system.sfs"
        elif choice.startswith("Create"):
            config_file_path = os.path.expanduser("~/config.mkobsfs")
            with open(config_file_path, "w") as f:
                f.write(DEFAULT_MKOBSFS_CONTENT)
            clear_screen()
            print_centered("Opening editor for new configuration...", Colors.BRIGHT_GREEN)
            print_centered("Save and exit when done", Colors.DIM)
            time.sleep(1)
            os.system(f"nano {config_file_path}")
            return config_file_path
        elif choice.startswith("  ├─"):
            filename = choice.split("├─ ")[1]
            if "[Current Dir]" in choice:
                filepath = filename.replace("[Current Dir] ", "")
            else:
                filepath = os.path.join(preconf_path, filename)
            if confirm(
                f"Use {filepath}?",
                summary=f"Selected file: {os.path.basename(filepath)}",
                details=[
                    f"Full path: {filepath}",
                    f"File type: {'Configuration' if filepath.endswith('.mkobsfs') else 'System Image'}",
                    "This file will be used for the installation process"
                ]
            ):
                return filepath

def show_status_screen(action, disk, image, slot=None, dual_boot=None, partition_sizes=None, file_system_type=None):
    clear_screen()
    width, height = get_terminal_size()
    draw_header()
    print("\n" * 2)
    
    print_centered(f"FINAL CONFIRMATION - {action.upper()}", Colors.BRIGHT_WHITE + Colors.BOLD)
    print_centered("Review your settings before proceeding", Colors.DIM)
    print("\n" * 2)
    
    status_info = [
        f"Action: {Colors.BRIGHT_CYAN}{action}{Colors.ENDC}",
        f"Target: {Colors.BRIGHT_GREEN}{disk}{Colors.ENDC}",
        f"Image: {Colors.BRIGHT_YELLOW}{os.path.basename(image)}{Colors.ENDC}"
    ]
    
    if slot:
        status_info.append(f"Slot: {Colors.BRIGHT_WHITE}{slot.upper()}{Colors.ENDC}")
    
    if dual_boot is not None:
        status_info.append(f"Dual Boot: {Colors.BRIGHT_GREEN if dual_boot else Colors.FAIL}{'Yes' if dual_boot else 'No'}{Colors.ENDC}")
    
    if file_system_type:
        status_info.append(f"File System: {Colors.BRIGHT_CYAN}{file_system_type.upper()}{Colors.ENDC}")
    
    for info in status_info:
        print_centered(info)
        print()
    
    if partition_sizes:
        print_centered("Partition Configuration:", Colors.BRIGHT_WHITE + Colors.BOLD)
        print_centered(f"ESP: {Colors.BRIGHT_CYAN}{partition_sizes['esp_size']}{Colors.ENDC} | Root: {Colors.BRIGHT_CYAN}{partition_sizes['rootfs_size']}{Colors.ENDC} | ETC: {Colors.BRIGHT_CYAN}{partition_sizes['etc_size']}{Colors.ENDC} | VAR: {Colors.BRIGHT_CYAN}{partition_sizes['var_size']}{Colors.ENDC}")
        print()
    
    print_centered("⚠️  WARNING ⚠️", Colors.BRIGHT_YELLOW + Colors.BOLD)
    print_centered("This action will modify your system!", Colors.BRIGHT_YELLOW)
    if action.lower() == "install":
        print_centered(f"All data on {disk} will be destroyed!", Colors.FAIL + Colors.BOLD)
    print()
    
    print_centered("Are you sure you want to proceed?", Colors.BRIGHT_WHITE)
    print("\n")
    
    options = ["Yes, Execute Now", "No, Cancel"]
    selected_index = 0
    
    while True:
        for i, option in enumerate(options):
            color = Colors.DIM
            if i == selected_index:
                color = Colors.BRIGHT_WHITE + Colors.BOLD
            print_centered(f"  {option}  ", color)
            if i < len(options) - 1:
                print()
        
        print("\n" * 2)
        print_centered(f"{Colors.DIM}Use ↑↓ to navigate, Enter to select, Q to quit{Colors.ENDC}")
        
        key = get_key()
        if key == '\x1b[A':
            selected_index = (selected_index - 1) % len(options)
            clear_screen()
            draw_header()
            print("\n" * 2)
            print_centered(f"FINAL CONFIRMATION - {action.upper()}", Colors.BRIGHT_WHITE + Colors.BOLD)
            print_centered("Review your settings before proceeding", Colors.DIM)
            print("\n" * 2)
            for info in status_info:
                print_centered(info)
                print()
            if partition_sizes:
                print_centered("Partition Configuration:", Colors.BRIGHT_WHITE + Colors.BOLD)
                print_centered(f"ESP: {Colors.BRIGHT_CYAN}{partition_sizes['esp_size']}{Colors.ENDC} | Root: {Colors.BRIGHT_CYAN}{partition_sizes['rootfs_size']}{Colors.ENDC} | ETC: {Colors.BRIGHT_CYAN}{partition_sizes['etc_size']}{Colors.ENDC} | VAR: {Colors.BRIGHT_CYAN}{partition_sizes['var_size']}{Colors.ENDC}")
                print()
            print_centered("⚠️  WARNING ⚠️", Colors.BRIGHT_YELLOW + Colors.BOLD)
            print_centered("This action will modify your system!", Colors.BRIGHT_YELLOW)
            if action.lower() == "install":
                print_centered(f"All data on {disk} will be destroyed!", Colors.FAIL + Colors.BOLD)
            print()
            print_centered("Are you sure you want to proceed?", Colors.BRIGHT_WHITE)
            print("\n")
        elif key == '\x1b[B':
            selected_index = (selected_index + 1) % len(options)
            clear_screen()
            draw_header()
            print("\n" * 2)
            print_centered(f"FINAL CONFIRMATION - {action.upper()}", Colors.BRIGHT_WHITE + Colors.BOLD)
            print_centered("Review your settings before proceeding", Colors.DIM)
            print("\n" * 2)
            for info in status_info:
                print_centered(info)
                print()
            if partition_sizes:
                print_centered("Partition Configuration:", Colors.BRIGHT_WHITE + Colors.BOLD)
                print_centered(f"ESP: {Colors.BRIGHT_CYAN}{partition_sizes['esp_size']}{Colors.ENDC} | Root: {Colors.BRIGHT_CYAN}{partition_sizes['rootfs_size']}{Colors.ENDC} | ETC: {Colors.BRIGHT_CYAN}{partition_sizes['etc_size']}{Colors.ENDC} | VAR: {Colors.BRIGHT_CYAN}{partition_sizes['var_size']}{Colors.ENDC}")
                print()
            print_centered("⚠️  WARNING ⚠️", Colors.BRIGHT_YELLOW + Colors.BOLD)
            print_centered("This action will modify your system!", Colors.BRIGHT_YELLOW)
            if action.lower() == "install":
                print_centered(f"All data on {disk} will be destroyed!", Colors.FAIL + Colors.BOLD)
            print()
            print_centered("Are you sure you want to proceed?", Colors.BRIGHT_WHITE)
            print("\n")
        elif key == '\r':
            return options[selected_index] == "Yes, Execute Now"
        elif key == '\x03' or key.lower() == 'q':
            return False

def run_command(command, description):
    clear_screen()
    width, height = get_terminal_size()
    print_centered(f"{Colors.BRIGHT_GREEN}EXECUTING {Colors.ENDC}")
    print("\n" * 2)
    print_centered(description, Colors.BRIGHT_WHITE)
    print_centered(command, Colors.DIM)
    print("\n" * 2)
    print_centered("Starting execution...", Colors.BRIGHT_CYAN)
    time.sleep(1)
    result = os.system(command)
    print("\n" * 2)
    if result == 0:
        print_centered("Command completed successfully!", Colors.BRIGHT_GREEN)
    else:
        print_centered("Command failed with errors!", Colors.FAIL)
    
    print("\n")
    print_centered("Press any key to continue...", Colors.DIM)
    get_key()

def is_laptop():
    """Detect if the system is running on a laptop."""
    try:
        # Method 1: Check for battery via sysfs
        if os.path.exists("/sys/class/power_supply/BAT0") or os.path.exists("/sys/class/power_supply/BAT1"):
            return True

        # Method 2: Check DMI chassis type
        result = subprocess.run(["dmidecode", "-s", "chassis-type"],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            chassis_type = result.stdout.strip().lower()
            # Common laptop chassis types: 8-12, 14 (notebook), 30 (tablet), 31 (convertible)
            laptop_types = ["8", "9", "10", "11", "12", "14", "30", "31", "notebook", "laptop", "portable"]
            if any(ltype in chassis_type for ltype in laptop_types):
                return True

        # Method 3: Check for lid switch
        if os.path.exists("/proc/acpi/button/lid"):
            return True

        return False
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        # Fallback: assume desktop if detection fails
        return False

def has_wired_connection():
    """Check if the system has an active wired internet connection."""
    try:
        # Check for default gateway
        result = subprocess.run(["ip", "route", "show", "default"],
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return False

        # Parse gateway IP
        lines = result.stdout.strip().split('\n')
        if not lines:
            return False

        gateway_line = lines[0]
        if 'via' not in gateway_line:
            return False

        gateway_ip = gateway_line.split('via')[1].split()[0]

        # Check if gateway is reachable
        ping_result = subprocess.run(["ping", "-c", "1", "-W", "2", gateway_ip],
                                   capture_output=True, timeout=3)
        if ping_result.returncode != 0:
            return False

        # Check if default interface is wired (not wireless)
        route_result = subprocess.run(["ip", "route", "get", gateway_ip],
                                    capture_output=True, text=True, timeout=5)
        if route_result.returncode == 0:
            # Look for interface name in output
            output = route_result.stdout.lower()
            # If output contains wlan, wlp, or similar wireless indicators, it's wireless
            wireless_indicators = ['wlan', 'wlp', 'wifi', 'wireless']
            if any(indicator in output for indicator in wireless_indicators):
                return False

        return True

    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError, IndexError):
        return False

def get_wifi_interfaces():
    """Get available wireless interfaces."""
    try:
        result = subprocess.run(["iwconfig"], capture_output=True, text=True, timeout=10)
        interfaces = []
        for line in result.stdout.split('\n'):
            if 'IEEE 802.11' in line or 'ESSID:' in line:
                interface = line.split()[0]
                if interface not in interfaces:
                    interfaces.append(interface)
        return interfaces
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return []

def scan_wifi_networks(interface):
    """Scan for available WiFi networks using iwlist."""
    try:
        result = subprocess.run(["iwlist", interface, "scan"],
                              capture_output=True, text=True, timeout=15)
        networks = []
        current_network = {}

        for line in result.stdout.split('\n'):
            line = line.strip()
            if line.startswith('Cell'):
                if current_network:
                    networks.append(current_network)
                current_network = {'cell': line.split()[1]}
            elif 'ESSID:' in line:
                essid = line.split('ESSID:')[1].strip().strip('"')
                current_network['essid'] = essid
            elif 'Encryption key:' in line:
                current_network['encrypted'] = 'on' in line.lower()
            elif 'Quality=' in line:
                quality_match = re.search(r'Quality=(\d+)/(\d+)', line)
                if quality_match:
                    current_network['quality'] = f"{quality_match.group(1)}/{quality_match.group(2)}"

        if current_network:
            networks.append(current_network)

        # Sort by quality (best first)
        networks.sort(key=lambda x: x.get('quality', '0/0').split('/')[0], reverse=True)
        return networks
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return []

def connect_wifi_iwctl(interface, ssid, password=None):
    """Connect to WiFi using iwctl (iwd)."""
    try:
        # Start iwd if not running
        subprocess.run(["systemctl", "start", "iwd"], capture_output=True, timeout=5)

        # Connect using iwctl
        if password:
            cmd = f"iwctl station {interface} connect '{ssid}' --passphrase '{password}'"
        else:
            cmd = f"iwctl station {interface} connect '{ssid}'"

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stderr if result.returncode != 0 else None
    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        return False, str(e)

def connect_wifi_nmcli(ssid, password=None):
    """Connect to WiFi using nmcli (NetworkManager)."""
    try:
        if password:
            cmd = ["nmcli", "device", "wifi", "connect", ssid, "password", password]
        else:
            cmd = ["nmcli", "device", "wifi", "connect", ssid]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stderr if result.returncode != 0 else None
    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        return False, str(e)

def connect_wifi_wpa(ssid, password=None):
    """Connect to WiFi using wpa_supplicant."""
    try:
        # Create temporary wpa_supplicant config
        config_content = f'network={{\n    ssid="{ssid}"\n'
        if password:
            config_content += f'    psk="{password}"\n'
        else:
            config_content += '    key_mgmt=NONE\n'
        config_content += '}\n'

        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write(config_content)
            config_file = f.name

        # Find wireless interface
        interfaces = get_wifi_interfaces()
        if not interfaces:
            return False, "No wireless interfaces found"

        interface = interfaces[0]

        # Connect using wpa_supplicant
        cmd = ["wpa_supplicant", "-B", "-i", interface, "-c", config_file]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        # Clean up config file
        os.unlink(config_file)

        if result.returncode == 0:
            # Wait for DHCP
            time.sleep(5)
            return True, None
        else:
            return False, result.stderr
    except (subprocess.SubprocessError, OSError) as e:
        return False, str(e)

def wifi_connection_menu():
    """Main WiFi connection menu for laptops."""
    if not is_laptop():
        return True  # Skip WiFi setup for desktops

    # Check if wired connection already exists
    if has_wired_connection():
        return True  # Skip WiFi setup if wired connection available

    clear_screen()
    draw_header()
    print("\n" * 2)
    print_centered("WiFi Network Setup", Colors.BRIGHT_WHITE + Colors.BOLD)
    print_centered("Connect to a wireless network for installation", Colors.DIM)
    print("\n" * 2)

    # Check available WiFi tools
    wifi_tools = []
    if shutil.which("iwctl"):
        wifi_tools.append("iwctl")
    if shutil.which("nmcli"):
        wifi_tools.append("nmcli")
    if shutil.which("wpa_supplicant"):
        wifi_tools.append("wpa_supplicant")

    if not wifi_tools:
        print_centered("No WiFi tools detected on this system", Colors.WARNING)
        print_centered("WiFi setup will be skipped", Colors.DIM)
        print("\n")
        print_centered("Press any key to continue...", Colors.DIM)
        get_key()
        return False  # Block installation if no WiFi tools available

    # Get wireless interfaces
    interfaces = get_wifi_interfaces()
    if not interfaces:
        print_centered("No wireless interfaces detected", Colors.WARNING)
        print_centered("WiFi setup will be skipped", Colors.DIM)
        print("\n")
        print_centered("Press any key to continue...", Colors.DIM)
        get_key()
        return False  # Block installation if no wireless interfaces

    interface = interfaces[0]  # Use first available interface

    # Main WiFi menu options
    options = [
        "Scan for Networks",
        "Manual Connection"
    ]

    while True:
        choice = selection_menu("WiFi Setup", options,
                              f"Using interface: {interface} | Tools: {', '.join(wifi_tools)}")

        if choice is None:
            return False  # User cancelled, block installation

        elif choice == "Scan for Networks":
            if not scan_and_connect_wifi(interface, wifi_tools):
                continue  # Try again
            return True

        elif choice == "Manual Connection":
            if not manual_wifi_connection(interface, wifi_tools):
                continue  # Try again
            return True

def scan_and_connect_wifi(interface, wifi_tools):
    """Scan for networks and allow user to select one."""
    clear_screen()
    draw_header()
    print("\n" * 2)
    print_centered("Scanning for WiFi Networks...", Colors.BRIGHT_CYAN)

    networks = scan_wifi_networks(interface)

    if not networks:
        print_centered("No networks found", Colors.WARNING)
        print("\n")
        print_centered("Press any key to continue...", Colors.DIM)
        get_key()
        return False

    # Create menu options
    network_options = []
    for i, network in enumerate(networks[:10]):  # Show top 10
        ssid = network.get('essid', 'Unknown')
        quality = network.get('quality', 'Unknown')
        encrypted = "🔒" if network.get('encrypted') else "📡"
        network_options.append(f"{encrypted} {ssid} (Quality: {quality})")

    network_options.append("Back to WiFi Menu")

    while True:
        choice = selection_menu("Available Networks", network_options,
                              "Select a network to connect to")

        if choice is None or choice == "Back to WiFi Menu":
            return False

        # Extract SSID from choice
        if "🔒" in choice or "📡" in choice:
            ssid = choice.split(' ', 2)[1]  # Skip emoji and get SSID
        else:
            ssid = choice.split(' ')[0]

        # Find network details
        selected_network = None
        for network in networks:
            if network.get('essid') == ssid:
                selected_network = network
                break

        encrypted = selected_network and selected_network.get('encrypted', False)

        # Get password if encrypted
        password = None
        if encrypted:
            clear_screen()
            draw_header()
            print("\n" * 2)
            print_centered(f"Connect to {ssid}", Colors.BRIGHT_WHITE + Colors.BOLD)
            print_centered("This network requires a password", Colors.DIM)
            print("\n" * 2)
            print_centered("Enter password (or leave empty to cancel):", Colors.BRIGHT_CYAN)
            print_centered("(Password will be hidden)", Colors.DIM)
            print("\n")

            try:
                password = input("Password: ").strip()
                if not password:
                    continue  # Back to network selection
            except (KeyboardInterrupt, EOFError):
                continue

        # Attempt connection
        success, error = attempt_wifi_connection(ssid, password, interface, wifi_tools)

        if success:
            print_centered("WiFi connection successful!", Colors.BRIGHT_GREEN)
            print("\n")
            print_centered("Press any key to continue...", Colors.DIM)
            get_key()
            return True
        else:
            print_centered("Connection failed", Colors.FAIL)
            if error:
                print_centered(f"Error: {error}", Colors.WARNING)
            print("\n")
            print_centered("Press any key to try again...", Colors.DIM)
            get_key()
            return False

def manual_wifi_connection(interface, wifi_tools):
    """Manual WiFi connection with SSID and password input."""
    clear_screen()
    draw_header()
    print("\n" * 2)
    print_centered("Manual WiFi Connection", Colors.BRIGHT_WHITE + Colors.BOLD)
    print_centered("Enter network details manually", Colors.DIM)
    print("\n" * 2)

    print_centered("Network Name (SSID):", Colors.BRIGHT_CYAN)
    try:
        ssid = input("SSID: ").strip()
        if not ssid:
            return False
    except (KeyboardInterrupt, EOFError):
        return False

    print("\n")
    print_centered("Password (leave empty for open network):", Colors.BRIGHT_CYAN)
    print_centered("(Password will be hidden)", Colors.DIM)
    try:
        password = input("Password: ").strip()
    except (KeyboardInterrupt, EOFError):
        return False

    # Attempt connection
    success, error = attempt_wifi_connection(ssid, password if password else None, interface, wifi_tools)

    if success:
        print_centered("WiFi connection successful!", Colors.BRIGHT_GREEN)
        print("\n")
        print_centered("Press any key to continue...", Colors.DIM)
        get_key()
        return True
    else:
        print_centered("Connection failed", Colors.FAIL)
        if error:
            print_centered(f"Error: {error}", Colors.WARNING)
        print("\n")
        print_centered("Press any key to try again...", Colors.DIM)
        get_key()
        return False

def attempt_wifi_connection(ssid, password, interface, wifi_tools):
    """Attempt WiFi connection using available tools."""
    for tool in wifi_tools:
        try:
            if tool == "iwctl":
                success, error = connect_wifi_iwctl(interface, ssid, password)
            elif tool == "nmcli":
                success, error = connect_wifi_nmcli(ssid, password)
            elif tool == "wpa_supplicant":
                success, error = connect_wifi_wpa(ssid, password)
            else:
                continue

            if success:
                return True, None
        except Exception as e:
            continue

    return False, "All connection methods failed"

def clear_screen():
    os.system('clear')

def advanced_settings_menu():
    partition_sizes = DEFAULT_PARTITION_SIZES.copy()
    file_system_type = "ext4"
    
    while True:
        clear_screen()
        width, height = get_terminal_size()
        draw_header()
        print("\n" * 2)
        print_centered("Advanced Settings", Colors.BRIGHT_WHITE + Colors.BOLD)
        print_centered("Configure partition sizes and other options", Colors.DIM)
        print("\n" * 2)
        
        size_options = [
            f"ESP Size: {Colors.BRIGHT_CYAN}{partition_sizes['esp_size']}{Colors.ENDC}",
            f"Root FS Size: {Colors.BRIGHT_CYAN}{partition_sizes['rootfs_size']}{Colors.ENDC}",
            f"ETC Size: {Colors.BRIGHT_CYAN}{partition_sizes['etc_size']}{Colors.ENDC}",
            f"VAR Size: {Colors.BRIGHT_CYAN}{partition_sizes['var_size']}{Colors.ENDC}",
            f"File System Type: {Colors.BRIGHT_CYAN}{file_system_type.upper()}{Colors.ENDC}",
            "Reset to Defaults",
            "Save and Continue"
        ]
        
        choice = selection_menu("Advanced Settings", size_options, "Configure partition sizes")
        
        if choice is None:
            return None
        
        if choice.startswith("ESP Size:"):
            new_size = input(f"Enter new ESP size (default: {DEFAULT_PARTITION_SIZES['esp_size']}): ").strip()
            if new_size:
                partition_sizes['esp_size'] = new_size
        elif choice.startswith("Root FS Size:"):
            new_size = input(f"Enter new Root FS size (default: {DEFAULT_PARTITION_SIZES['rootfs_size']}): ").strip()
            if new_size:
                partition_sizes['rootfs_size'] = new_size
        elif choice.startswith("ETC Size:"):
            new_size = input(f"Enter new ETC size (default: {DEFAULT_PARTITION_SIZES['etc_size']}): ").strip()
            if new_size:
                partition_sizes['etc_size'] = new_size
        elif choice.startswith("VAR Size:"):
            new_size = input(f"Enter new VAR size (default: {DEFAULT_PARTITION_SIZES['var_size']}): ").strip()
            if new_size:
                partition_sizes['var_size'] = new_size
        elif choice.startswith("File System Type:"):
            fs_options = ["ext4", "f2fs"]
            selected_fs = selection_menu("Select File System Type", fs_options, "Choose the file system for your partitions")
            if selected_fs:
                file_system_type = selected_fs
        elif choice == "Reset to Defaults":
            partition_sizes = DEFAULT_PARTITION_SIZES.copy()
            file_system_type = "ext4"
        elif choice == "Save and Continue":
            if confirm(
                "Save these advanced settings and continue?",
                summary="Advanced configuration will be applied",
                details=[
                    f"ESP Size: {partition_sizes['esp_size']}",
                    f"Root FS Size: {partition_sizes['rootfs_size']}",
                    f"ETC Size: {partition_sizes['etc_size']}",
                    f"VAR Size: {partition_sizes['var_size']}",
                    f"File System Type: {file_system_type.upper()}",
                    "These settings will be used for the installation"
                ]
            ):
                return {"partition_sizes": partition_sizes, "file_system_type": file_system_type}
    
    return None

def installation_flow(action):
    dual_boot_choice = selection_menu(
        "Dual Boot Configuration", 
        ["Enable Dual Boot", "Single Boot Only"],
        "Keep existing OS alongside ObsidianOS?"
    )
    if dual_boot_choice is None:
        return
    dual_boot = dual_boot_choice.startswith("Enable")

    # NEW: WiFi connection step for laptops
    if not wifi_connection_menu():
        return  # WiFi setup failed/blocked

    advanced_settings_result = advanced_settings_menu()
    if advanced_settings_result is None:
        return
    partition_sizes = advanced_settings_result["partition_sizes"]
    file_system_type = advanced_settings_result["file_system_type"]
    
    disks = get_disks()
    if not disks:
        clear_screen()
        print_centered("NO DISKS DETECTED", Colors.FAIL + Colors.BOLD)
        print_centered("Please check your system configuration", Colors.WARNING)
        print("\n")
        print_centered("Press any key to continue...", Colors.DIM)
        get_key()
        return

    disk_options = [f"{disk}" for disk in disks]
    disk_choice = selection_menu("Select Target Disk", disk_options, "WARNING: Selected disk will be modified!")
    if disk_choice is None:
        return
    
    disk = disk_choice.split(' ')[0]
    image_path = select_system_image(action.lower())
    if image_path is None:
        return

    if show_status_screen(action, disk, image_path, dual_boot=dual_boot, partition_sizes=partition_sizes, file_system_type=file_system_type):
        command = f"{OBSIDIANCTL_PATH} {action.lower()}"
        if dual_boot:
            command += " --dual-boot"
        command += f" --esp-size {partition_sizes['esp_size']}"
        command += f" --rootfs-size {partition_sizes['rootfs_size']}"
        command += f" --etc-size {partition_sizes['etc_size']}"
        command += f" --var-size {partition_sizes['var_size']}"
        if file_system_type == "f2fs":
            command += " --use-f2fs"
        command += f" {disk} {image_path}"
        run_command(command, f"{action}ing ObsidianOS")

def update_flow(title):
    disk_selection_options = ["Current Disk", "Select a Disk"]
    disk_selection_choice = selection_menu(
        f"Disk Selection for {title}",
        disk_selection_options,
        "Choose whether to use the current disk or select a new one"
    )
    if disk_selection_choice is None:
        return

    selected_disk = None
    if disk_selection_choice == "Select a Disk":
        disks = get_disks()
        if not disks:
            clear_screen()
            print_centered("NO DISKS DETECTED", Colors.FAIL + Colors.BOLD)
            print_centered("Please check your system configuration", Colors.WARNING)
            print("\n")
            print_centered("Press any key to continue...", Colors.DIM)
            get_key()
            return
        disk_options = [f"{disk}" for disk in disks]
        disk_choice = selection_menu("Select Target Disk", disk_options, "WARNING: Selected disk will be modified!")
        if disk_choice is None:
            return
        selected_disk = disk_choice.split(' ')[0]

    slots = get_current_slots()
    slot_options = [f"Slot {slot.upper()}" for slot in slots]
    slot_choice = selection_menu(
        f"Select Slot to {title}", 
        slot_options,
        f"Choose which system slot to {title}"
    )
    if slot_choice is None:
        return
    slot = slot_choice.split("Slot ")[1].lower()
    image_path = select_system_image("update")
    if image_path is None:
        return
    
    target_display = selected_disk if selected_disk else f"System Slot {slot.upper()}"
    if show_status_screen(title, target_display, image_path, slot=slot):
        command = f"{OBSIDIANCTL_PATH} update {slot} {image_path}"
        if selected_disk:
            command += f" --device {selected_disk}"
        run_command(command, f"Updating slot {slot.upper()}")

def reboot_system():
    if confirm(
        "Reboot the system now?",
        warning=True,
        summary="System will be restarted immediately",
        details=[
            "All running processes will be terminated",
            "Make sure to save any unsaved work",
            "The system will boot into the newly installed/updated system"
        ]
    ):
        run_command("sudo reboot", "Rebooting system")

def main():
    while True:
        main_options = [
            "Install ObsidianOS",
            "Repair ObsidianOS", 
            "Drop to Terminal",
            "Reboot System"
        ]
        if not IS_ARCHISO:
            main_options.extend([
                "Update System",
                "Switch Slot and Reboot (temporary)",
                "Switch Slot and Reboot (permanent)",
                "Sync slots"
            ])
        choice = selection_menu("ARbs - the ARch image Based inStaller", main_options, "What would you like to do?")
        if choice == "Install ObsidianOS":
            installation_flow("Install")
        elif choice == "Repair ObsidianOS":
            update_flow("Repair")
        elif choice == "Update System":
            update_flow("Update")
        elif choice == "Switch Slot and Reboot (temporary)":
            run_command(f"{OBSIDIANCTL_PATH} switch-once {NEXT_SLOT}", "Switching slot...")
            reboot_system()
            print_centered("Please reboot to switch slots.")
        elif choice == "Switch Slot and Reboot (permanent)":
            run_command(f"{OBSIDIANCTL_PATH} switch {NEXT_SLOT}", "Switching slot...")
            reboot_system()
            print_centered("Please reboot to switch slots.")
        elif choice == "Sync slots":
            run_command(f"{OBSIDIANCTL_PATH} sync {NEXT_SLOT}", "Syncing slots...")
            print_centered("Slots synced.")
        elif choice == "Drop to Terminal":
            clear_screen()
            print_centered("Dropping to terminal...", Colors.BRIGHT_GREEN)
            time.sleep(0.5)
            sys.exit(0)
        elif choice == "Reboot System":
            reboot_system()
        elif choice is None:
            clear_screen()
            print_centered("Thanks for using ObsidianOS!", Colors.BRIGHT_CYAN)
            time.sleep(0.5)
            sys.exit(0)

if __name__ == "__main__":
    if IS_ARCHISO and not os.path.isfile("/etc/obsidian-wizard-resized"):
        try:
            clear_screen()
            run_command("mount -o remount,size=75% /run/archiso/cowspace", "Resizing tmpfs...")
            open("/etc/obsidian-wizard-resized", "w").close()
        except (KeyboardInterrupt, SystemExit):
            clear_screen()
            print_centered("Resizing aborted. It is probably a good idea to restart your computer.", Colors.WARNING)
            time.sleep(0.5)
        except Exception as e:
            clear_screen()
            print_centered("CRITICAL ERROR", Colors.FAIL + Colors.BOLD)
            print_centered(str(e), Colors.FAIL)
            print_centered("Please report this bug", Colors.DIM)
            print_centered("REBOOTING...", Colors.FAIL + Colors.BOLD)
            time.sleep(5)
            run_command("sudo reboot", f"Rebooting system due to error {str(e)}...")
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        clear_screen()
        print_centered("Installation cancelled by user", Colors.WARNING)
        time.sleep(0.5)
    except Exception as e:
        clear_screen()
        print_centered("CRITICAL ERROR", Colors.FAIL + Colors.BOLD)
        print_centered(str(e), Colors.FAIL)
        print_centered("Please report this bug", Colors.DIM)
        time.sleep(2)
