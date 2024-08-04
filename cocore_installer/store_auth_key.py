import os
import argparse
import sys
from cryptography.fernet import Fernet

AUTH_KEY_FILE = "/etc/cocore/auth_key"
SECRET_KEY_FILE = "/etc/cocore/secret.key"

def generate_key():
    return Fernet.generate_key()

def store_auth_key(auth_key, key, keyfile):
    cipher_suite = Fernet(key)
    encrypted_key = cipher_suite.encrypt(auth_key.encode())

    os.makedirs(os.path.dirname(keyfile), exist_ok=True)
    with open(keyfile, "wb") as file:
        file.write(encrypted_key)

def main():
    parser = argparse.ArgumentParser(description="Store the authentication key securely.")
    parser.add_argument('--key', type=str, required=True, help='The authentication key to be stored.')
    parser.add_argument('--keyfile', type=str, required=True, help='Where to store the authentication key')
    parser.add_argument('--secretfile', type=str, required=True, help='Where to store the secret key')
    args = parser.parse_args()

    if args.key != "abcd":
        print("Authentication failed.")
        sys.exit(1)

    os.makedirs(os.path.dirname(args.secretfile), exist_ok=True)
    key = generate_key()
    with open(args.secretfile, "wb") as key_file:
        key_file.write(key)
    
    store_auth_key(args.key, key, args.keyfile)
    print("Authentication key stored securely.")

if __name__ == "__main__":
    main()
