#!/usr/bin/env python3
import os
import sys
import tty
import termios
import tempfile
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
DEFAULT_MKOBSFS_CONTENT = """BUILD_DIR=\"obsidian_rootfs\" # SquashFS generation directory # Below is default packages for an install of arch and this script to work.
PACKAGES=\"base linux linux-firmware networkmanager sudo vim nano efibootmgr python squashfs-tools arch-install-scripts base-devel git gptfdisk wget os-prober\"
OUTPUT_SFS=\"system.sfs\" # Output SquashFS
TIMEZONE=\"\"             # Olson Timezone
HOSTNAME=\"obsidianbtw\"  # Hostname
YAY_GET=\"obsidianctl-git\" # AUR Packages to install
ROOT_HAVEPASSWORD=\"nopassword\"    # Set this to anything other than blank to remove the password from the root user.
CUSTOM_SCRIPTS_DIR=\"\"   # Place where scripts that must run in the SquashFS will run.
ADMIN_USER=\"user\"           # Creates an user with the 'wheel' group
ADMIN_DOTFILES=\"\"       # If an admin is created, a git repo that will be cloned to the new user.
ADMIN_DOTFILES_TYPE=\"\"  # Type of dotfile repo. Requires git in PACKAGES if HOME or CONFIG.
# HOME - the inside of the repo has data for your home directory (ex: .zshrc, .config, .bashrc)
# CONFIG - the inside of the repo has data for your .config directory (ex: gtk, fish, kitty, hypr)
# * - ignore dotfiles repo (can be empty string) and copy dotfiles from that user's home.
#     recommended: set this to $SUDO_USER if this is being run with sudo.
"""

def get_terminal_size():
    try:
        return os.get_terminal_size()
    except OSError:
        return 80, 24

def print_centered(text, color=""):
    width, _ = get_terminal_size()
    padding = (width - len(text)) // 2
    print(" " * padding + color + text + Colors.ENDC)

def print_menu(title, options, selected_index):
    clear_screen()
    _, height = get_terminal_size()
    menu_height = len(options) + 5
    top_padding = max(0, (height - menu_height) // 2)
    print("\n" * top_padding)
    print_centered(title, Colors.HEADER + Colors.BOLD)
    print("\n" * 2)
    for i, option in enumerate(options):
        if i == selected_index:
            print_centered(f"> {option}", Colors.OKCYAN)
        else:
            print_centered(option)
    print("\n" * 2)

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch += sys.stdin.read(2)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def selection_menu(title, options):
    selected_index = 0
    while True:
        print_menu(title, options, selected_index)
        key = get_key()
        if key == '\x1b[A':
            selected_index = (selected_index - 1) % len(options)
        elif key == '\x1b[B':
            selected_index = (selected_index + 1) % len(options)
        elif key == '\r':
            return options[selected_index]
        elif key == '\x03' or key == 'q':
            return None

def get_disks():
    try:
        output = os.popen("lsblk -d -n -o NAME,SIZE").read().strip().split('\n')
        disks = [f"/dev/{line.split()[0]} ({line.split()[1]})" for line in output if line]
        return disks
    except Exception:
        return []

def confirm_action(message):
    clear_screen()
    _, height = get_terminal_size()
    top_padding = max(0, (height - 7) // 2)
    print("\n" * top_padding)
    print_centered(message, Colors.WARNING)
    print("\n" * 2)
    confirm_options = ["Yes", "No"]
    choice = selection_menu("Confirm", confirm_options)
    return choice == "Yes"

def select_system_image():
    preconf_path = "/usr/preconf"
    mkobsfs_files = []
    if os.path.exists(preconf_path):
        for f in os.listdir(preconf_path):
            if f.endswith(".mkobsfs"):
                mkobsfs_files.append(f.replace(".mkobsfs", ""))
    
    options = ["Default System Image", "Make a new config"] + sorted(mkobsfs_files)
    while True:
        choice = selection_menu("Select System Image", options)

        if choice is None:
            return None

        if choice == "Default System Image":
            if confirm_action("Use default system image (/etc/system.sfs)?"):
                return "/etc/system.sfs"
        elif choice == "Make a new config":
            config_file_path = os.path.expanduser("~/config.mkobsfs")
            with open(config_file_path, "w") as f:
                f.write(DEFAULT_MKOBSFS_CONTENT)
            os.system(f"nano {config_file_path}")
            return config_file_path
        else:
            full_path = os.path.join(preconf_path, f"{choice}.mkobsfs")
            if confirm_action(f"Use {full_path}?"):
                return full_path

def get_image_path():
    return select_system_image()

def confirmation_menu(action, disk, image, dual_boot):
    options = [
        f"Action: {action} ObsidianOS",
        f"Disk: {disk}",
        f"Image: {image}",
        f"Dual Boot: {'Yes' if dual_boot else 'No'}",
        "",
        "Are you sure?",
        "",
        "Yes",
        "No"
    ]
    selected_index = 0
    while True:
        clear_screen()
        _, height = get_terminal_size()
        menu_height = len(options) + 5
        top_padding = max(0, (height - menu_height) // 2)
        print("\n" * top_padding)
        print_centered(f"Confirm {action}", Colors.HEADER + Colors.BOLD)
        print("\n" * 2)
        for i, option in enumerate(options):
            if i == len(options) - 2 and selected_index == 0:
                print_centered(f"> {option}", Colors.OKCYAN)
            elif i == len(options) - 1 and selected_index == 1:
                print_centered(f"> {option}", Colors.OKCYAN)
            else:
                print_centered(option)
        print("\n" * 2)
        key = get_key()
        if key == '\x1b[A' or key == '\x1b[B':
            selected_index = 1 - selected_index
        elif key == '\r':
            return selected_index == 0
        elif key == '\x03' or key == 'q':
            return False

def run_command(command):
    clear_screen()
    _, height = get_terminal_size()
    top_padding = max(0, (height - 7) // 2)
    print("\n" * top_padding)
    print_centered("Running command...", Colors.OKGREEN)
    print_centered(command, Colors.BOLD)
    print("\n")
    os.system(command)
    print("\n" * 2)
    print_centered("Press any key to continue.", Colors.WARNING)
    get_key()

def clear_screen():
    os.system('clear')

def installation_flow(action):
    dual_boot_choice = selection_menu("Dual Boot", ["Yes", "No"])
    if dual_boot_choice is None:
        return
    dual_boot = dual_boot_choice == "Yes"
    disks = get_disks()
    if not disks:
        clear_screen()
        _, height = get_terminal_size()
        top_padding = max(0, (height - 7) // 2)
        print("\n" * top_padding)
        print_centered("No disks found!", Colors.FAIL)
        print_centered("Please check your system.", Colors.WARNING)
        print("\n" * 2)
        get_key()
        return

    disk = selection_menu("Select a Disk", disks)
    if disk is None:
        return

    image_path = get_image_path()
    if image_path is None:
        return

    if confirmation_menu(action, disk, image_path, dual_boot):
        command = f"obsidianctl {action.lower()}"
        if dual_boot:
            command += " --dual-boot"
        command += f" {disk.split(' ')[0]}"
        command += f" {image_path}"
        run_command(command)

def reboot_system():
    clear_screen()
    _, height = get_terminal_size()
    top_padding = max(0, (height - 7) // 2)
    print("\n" * top_padding)
    print_centered("Are you sure you want to reboot the system?", Colors.WARNING)
    print("\n" * 2)
    confirm_options = ["Yes, Reboot Now", "No, Go Back"]
    choice = selection_menu("Confirm Reboot", confirm_options)
    if choice == "Yes, Reboot Now":
        run_command("sudo reboot")
    else:
        pass

def main():
    while True:
        main_menu_options = ["Install ObsidianOS", "Repair ObsidianOS", "Terminal", "Reboot"]
        choice = selection_menu("ObsidianOS Wizard", main_menu_options)
        if choice == "Install ObsidianOS":
            installation_flow("Install")
        elif choice == "Repair ObsidianOS":
            installation_flow("Repair")
        elif choice == "Terminal":
            clear_screen()
            sys.exit(0)
        elif choice == "Reboot":
            reboot_system()
        elif choice is None:
            clear_screen()
            sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        clear_screen()
    except Exception as e:
        clear_screen()
        print_centered("An unexpected error occurred:", Colors.FAIL)
        print_centered(str(e), Colors.FAIL)
