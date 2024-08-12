import subprocess
import sys

def main():
    vm_number = sys.argv[1] if len(sys.argv) > 1 else ""
    subprocess.run([f'./cocore_installer/start_vm.sh', vm_number], check=True)

if __name__ == "__main__":
    main()