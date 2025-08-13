#!/usr/bin/env python3
import os
import sys
import tty
import termios
import tempfile
import time
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

DEFAULT_MKOBSFS_CONTENT = """BUILD_DIR=\"obsidian_rootfs\"
PACKAGES=\"base linux linux-firmware networkmanager sudo vim nano efibootmgr python squashfs-tools arch-install-scripts base-devel git gptfdisk wget os-prober\"
OUTPUT_SFS=\"system.sfs\"
TIMEZONE=\"\"
HOSTNAME=\"obsidianbtw\"
YAY_GET=\"obsidianctl-git\"
ROOT_HAVEPASSWORD=\"nopassword\"
CUSTOM_SCRIPTS_DIR=\"\"
ADMIN_USER=\"user\"
ADMIN_DOTFILES=\"\"
ADMIN_DOTFILES_TYPE=\"\"
"""

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
    import re
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
        output = os.popen("lsblk -d -n -o NAME,SIZE,MODEL").read().strip().split('\n')
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

def get_current_slots():
    return ["a", "b"]

def confirm(message, warning=False):
    clear_screen()
    width, height = get_terminal_size()
    if warning:
        color = Colors.BRIGHT_YELLOW
        icon = "!"
    else:
        color = Colors.BRIGHT_CYAN
        icon = "?"
    
    top_padding = max(0, (height - 10) // 2)
    print("\n" * top_padding)
    print(f"{color}{icon} CONFIRMATION {icon}{Colors.ENDC}", Colors.BOLD)
    print("\n")
    print(message, color)
    print("\n" * 2)
    options = ["Yes, Continue", "No, Go Back"]
    choice = selection_menu("", options)
    return choice and choice.startswith("Yes")

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
    
    options = ["Default System Image", "Create New Config"]
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
            if confirm("Use default system image (/etc/system.sfs)?"):
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
            if confirm(f"Use {filepath}?"):
                return filepath

def show_status_screen(action, disk, image, slot=None, dual_boot=None):
    clear_screen()
    width, height = get_terminal_size()
    draw_header()
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
    
    for info in status_info:
        print_centered(info)
        print()
    
    print("\n")
    options = ["Execute Now", "Cancel"]
    choice = selection_menu("Final Confirmation", options)
    return choice == "Execute Now"

def run_command(command, description):
    clear_screen()
    width, height = get_terminal_size()
    print_centered(f"{Colors.BRIGHT_GREEN}EXECUTING {Colors.ENDC}", Colors.BOLD)
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

def clear_screen():
    os.system('clear')

def installation_flow(action):
    dual_boot_choice = selection_menu(
        "Dual Boot Configuration", 
        ["Enable Dual Boot", "Single Boot Only"],
        "Keep existing OS alongside ObsidianOS?"
    )
    if dual_boot_choice is None:
        return
    dual_boot = dual_boot_choice.startswith("Enable")
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

    if show_status_screen(action, disk, image_path, dual_boot=dual_boot):
        command = f"obsidianctl {action.lower()}"
        if dual_boot:
            command += " --dual-boot"
        command += f" {disk} {image_path}"
        run_command(command, f"{action}ing ObsidianOS")

def update_flow(title):
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
    
    if show_status_screen(title, f"System Slot {slot.upper()}", image_path, slot=slot):
        command = f"obsidianctl update {slot} {image_path}"
        run_command(command, f"Updating slot {slot.upper()}")

def reboot_system():
    if confirm("Reboot the system now?", warning=True):
        run_command("sudo reboot", "Rebooting system")

def main():
    while True:
        main_options = [
            "Install ObsidianOS",
            "Repair ObsidianOS", 
            "Update System",
            "Drop to Terminal",
            "Reboot System"
        ]
        
        choice = selection_menu("ObsidianOS Installation Wizard", main_options, "What would you like to do?")
        if choice == "Install ObsidianOS":
            installation_flow("Install")
        elif choice == "Repair ObsidianOS":
            update_flow("Repair")
        elif choice == "Update System":
            update_flow("Update")
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
