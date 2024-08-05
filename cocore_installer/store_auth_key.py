import os
import json
import argparse
import sys
import subprocess
from cryptography.fernet import Fernet

def generate_key():
    return Fernet.generate_key()

def store_auth_key(auth_key, key, keyfile):
    cipher_suite = Fernet(key)
    encrypted_key = cipher_suite.encrypt(auth_key.encode())

    os.makedirs(os.path.dirname(keyfile), exist_ok=True)
    with open(keyfile, "wb") as file:
        file.write(encrypted_key)

def validate_host(auth_key, encrypted_auth_key):
    payload = {
        "uuid": auth_key,
        "auth_key": encrypted_auth_key
    }

    cmd = [
        'curl',
        '-X', 'POST',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(payload),
        'https://cocore.io/hosts/validate'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    response = json.loads(result.stdout)

    if result.returncode == 0 and response.get("valid"):
        return response.get("token")
    else:
        print(response.get("message"))
        return None

def main():
    parser = argparse.ArgumentParser(description="Store the authentication key securely.")
    parser.add_argument('--key', type=str, required=True, help='The authentication key to be stored.')
    parser.add_argument('--keyfile', type=str, required=True, help='Where to store the authentication key')
    parser.add_argument('--secretfile', type=str, required=True, help='Where to store the secret key')
    parser.add_argument('--workdir', type=str, required=True, help='Current working directory')
    args = parser.parse_args()

    # Ensure the workdir exists
    os.makedirs(args.workdir, exist_ok=True)
    os.makedirs(os.path.dirname(args.secretfile), exist_ok=True)
    os.makedirs(os.path.dirname(args.keyfile), exist_ok=True)

    # Generate and store the secret key
    key = generate_key()
    with open(os.path.join(args.workdir, args.secretfile), "wb") as key_file:
        key_file.write(key)
    print(f'Wrote auth key to {os.path.join(args.workdir, args.secretfile)}')

    # Encrypt the authentication key with the secret key
    cipher_suite = Fernet(key)
    encrypted_auth_key = cipher_suite.encrypt(args.key.encode()).decode()

    # Validate the host
    token = validate_host(args.key, encrypted_auth_key)
    if not token:
        print("Authentication failed.")
        sys.exit(1)

    # Store the authentication key securely
    store_auth_key(args.key, key, os.path.join(args.workdir, args.keyfile))
    print("Authentication key stored securely.")

    # Ensure the /etc/cocore directory exists
    os.makedirs("/etc/cocore", exist_ok=True)

    # Save the token for later use
    with open("/etc/cocore/tokenfile", "w") as token_file:
        token_file.write(token)

if __name__ == "__main__":
    main()