import subprocess

def main():
    subprocess.run(['bash', '-c', 'cocore_installer/start_vm.sh'], check=True)