import subprocess
import sys

def main():
    try:
        if len(sys.argv) < 6:
            print("Usage: cocore-start-vm <vm_number> --cpus <num_cpus> --memory <memory_mb>")
            sys.exit(1)

        vm_number = sys.argv[1]
        cpus = sys.argv[3]
        memory = sys.argv[5]

        result = subprocess.run([f'./cocore_installer/start_vm.sh', vm_number, cpus, memory], check=True)

        if result.returncode != 0:
            print(f"Error: start_vm.sh exited with status {result.returncode}")
            sys.exit(result.returncode)

    except subprocess.CalledProcessError as e:
        print(f"Command '{e.cmd}' returned non-zero exit status {e.returncode}.")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
