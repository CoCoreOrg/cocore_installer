import subprocess
import sys

def main():
    if len(sys.argv) < 4:
        print("Usage: cocore-start-vm <vm_number> --cpus <num_cpus> --memory <memory_mb>")
        sys.exit(1)
    
    vm_number = sys.argv[1]
    cpus = sys.argv[3]
    memory = sys.argv[5]

    subprocess.run(['bash', '-c', f'cocore_installer/start_vm.sh {vm_number} {cpus} {memory}'], check=True)

if __name__ == "__main__":
    main()
