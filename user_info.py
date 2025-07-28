import os
import platform
import getpass
import socket
import subprocess

def get_user_info():
    info = {}

    # Common Info
    info['Username'] = getpass.getuser()
    info['Hostname'] = socket.gethostname()
    info['IP Address'] = socket.gethostbyname(socket.gethostname())
    info['Home Directory'] = os.path.expanduser("~")

    # Platform-specific info
    system = platform.system()

    if system == "Windows":
        info['Domain'] = os.environ.get("USERDOMAIN", "N/A")
        info['Full Name'] = get_windows_full_name()
        info['Shell'] = os.environ.get("ComSpec", "N/A")  # typically cmd.exe or powershell
    else:
        try:
            import pwd
            pw = pwd.getpwnam(info['Username'])
            info['Full Name'] = pw.pw_gecos.split(',')[0]
            info['User ID'] = pw.pw_uid
            info['Group ID'] = pw.pw_gid
            info['Shell'] = pw.pw_shell
        except Exception as e:
            info['Full Name'] = f"Error: {e}"
            info['Shell'] = "N/A"

    # Print results
    print("\n--- User Information ---")
    for k, v in info.items():
        print(f"{k}: {v}")

    print("\n--- Environment Variables ---")
    for k in ['USER', 'USERNAME', 'USERDOMAIN', 'LOGNAME', 'SHELL', 'HOME']:
        print(f"{k}: {os.environ.get(k, 'N/A')}")

def get_windows_full_name():
    try:
        username = os.getlogin()
        domain = os.environ.get("USERDOMAIN", "")
        command = f'wmic useraccount where "name=\'{username}\' and domain=\'{domain}\'" get fullname'
        output = subprocess.check_output(command, shell=True).decode('cp862').splitlines()
        lines = [line.strip() for line in output if line.strip()]
        return lines[1] if len(lines) > 1 else "N/A"
    except Exception as e:
        return f"Error: {e}"

# Run it
if __name__ == "__main__":
    get_user_info() 