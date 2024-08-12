import subprocess
import sys

def main():
    vm_number = sys.argv[1]
    cpus = sys.argv[3]
    memory = sys.argv[5]
    # Directly pass the script and its arguments without using bash -c
    subprocess.run([f'./cocore_installer/start_vm.sh', vm_number, cpus, memory], check=True)

if __name__ == "__main__":
    main()
