import subprocess
import sys

def main():
    vm_number = sys.argv[1]
    cpus = sys.argv[3]
    memory = sys.argv[5]
    # Use bash -c correctly, with _ as $0 and the script arguments
    subprocess.run(['bash', '-c', f'./cocore_installer/start_vm.sh "$0" "$1" "$2"', '_', vm_number, cpus, memory], check=True)

if __name__ == "__main__":
    main()
