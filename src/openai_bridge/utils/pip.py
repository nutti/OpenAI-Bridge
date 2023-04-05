import subprocess
import sys

def install_package(package_name):
    python_bin_path = sys.executable
    command = [python_bin_path, "-m", "pip", "install", package_name]

    output = subprocess.run(command, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if output.stdout:
        print(f"{output.stdout}")
    if output.stderr:
        print(f"{output.stderr}")

    return output.returncode
