import subprocess
import sys


def check_package_installed(package_name):
    python_bin_path = sys.executable
    command = [python_bin_path, "-m", "pip", "list"]

    output = subprocess.run(command, universal_newlines=True, check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pkg_list = output.stdout.split("\n")
    pkg_names = (pkg.split() for pkg in pkg_list)

    return package_name in pkg_names


def install_package(package_name):
    if check_package_installed(package_name):
        return 0

    python_bin_path = sys.executable
    command = [python_bin_path, "-m", "pip", "install", package_name]

    output = subprocess.run(command, universal_newlines=True, check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if output.stdout:
        print(f"{output.stdout}")
    if output.stderr:
        print(f"{output.stderr}")

    return output.returncode
