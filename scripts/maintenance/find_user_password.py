import hashlib

# Test common passwords
test_passwords = [
    "123456",
    "password",
    "12345678",
    "qwerty",
    "123456789",
    "12345",
    "1234",
    "111111",
    "1234567",
    "dragon",
    "123123",
    "baseball",
    "iloveyou",
    "trustno1",
    "1234567890",
    "superman",
    "Yahia123",
    "Yahia1234",
    "yahia123",
    "salma123",
    "Salma123",
    "mohsen123",
    "Mohsen123",
    "Mohsen@123",
    "tihambz123"
]

# MD5 hashes from database
user_hashes = {
    'Y.Yasser2202@nu.edu.eg': '04e51d7554584eb3b70e0b5e34f924f51c695902e6c34a9ca9ac2db0a838b22e',
    's@nu.edu.eg': '77693dee90e4af686b73a26fdeb55b5bfc827765a023112ac96df4d31eb5a42d',
    'tihambz@gmail.com': 'pbkdf2_sha256$1000000$aJfPQP9ndrj30uzCIywRvI$aARQw'  # This one is Django hash
}

print("Testing passwords for users with hash issues:")
print()

for email, stored_hash in user_hashes.items():
    if len(stored_hash) == 64:  # SHA256
        print(f"{email} (SHA256 hash):")
        for pwd in test_passwords:
            sha256 = hashlib.sha256(pwd.encode()).hexdigest()
            if sha256 == stored_hash:
                print(f"  ✓ FOUND: '{pwd}'")
                break
        else:
            print(f"  ✗ Password not found in common list")
    elif len(stored_hash) == 32:  # MD5
        print(f"{email} (MD5 hash):")
        for pwd in test_passwords:
            md5 = hashlib.md5(pwd.encode()).hexdigest()
            if md5 == stored_hash:
                print(f"  ✓ FOUND: '{pwd}'")
                break
        else:
            print(f"  ✗ Password not found in common list")
    print()
