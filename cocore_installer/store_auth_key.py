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

def load_secret_key(secretfile):
    with open(secretfile, "rb") as key_file:
        key = key_file.read()
    return key

def validate_host(auth_key, secretfile):
    key = load_secret_key(secretfile)
    cipher_suite = Fernet(key)
    encrypted_auth_key = cipher_suite.encrypt(auth_key.encode()).decode()

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
    args = parser.parse_args()

    token = validate_host(args.key, args.secretfile)
    if not token:
        print("Authentication failed.")
        sys.exit(1)

    os.makedirs(os.path.dirname(args.secretfile), exist_ok=True)
    key = generate_key()
    with open(args.secretfile, "wb") as key_file:
        key_file.write(key)
    print(f'Wrote auth key to {args.secretfile}')
    
    store_auth_key(args.key, key, args.keyfile)
    print("Authentication key stored securely.")

    # Save the token for later use
    with open("/path/to/tokenfile", "w") as token_file:
        token_file.write(token)

if __name__ == "__main__":
    main()
