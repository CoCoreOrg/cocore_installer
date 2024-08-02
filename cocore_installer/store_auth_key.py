import os
import argparse
from cryptography.fernet import Fernet

AUTH_KEY_FILE = "/etc/cocore/auth_key"

def generate_key():
    return Fernet.generate_key()

def store_auth_key(auth_key, key):
    cipher_suite = Fernet(key)
    encrypted_key = cipher_suite.encrypt(auth_key.encode())

    os.makedirs(os.path.dirname(AUTH_KEY_FILE), exist_ok=True)
    with open(AUTH_KEY_FILE, "wb") as file:
        file.write(encrypted_key)

def main():
    parser = argparse.ArgumentParser(description="Store the authentication key securely.")
    parser.add_argument('--key', type=str, required=True, help='The authentication key to be stored.')
    args = parser.parse_args()

    key = generate_key()
    with open("/etc/cocore/secret.key", "wb") as key_file:
        key_file.write(key)
    
    store_auth_key(args.key, key)
    print("Authentication key stored securely.")

if __name__ == "__main__":
    main()
