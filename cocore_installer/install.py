import subprocess

def main():
    subprocess.run(["bash", "cocore_installer/install.sh"], check=True)
