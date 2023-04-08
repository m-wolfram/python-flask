from hashlib import pbkdf2_hmac
from os import urandom


def generate_pwd_hash(password, salt_size=16, iterations=100000):
    salt = urandom(salt_size)
    hash_ = pbkdf2_hmac("sha512",
                        password.encode("utf-8"),
                        salt,
                        iterations)
    return hash_ + salt


def check_pwd_hash(hash_, password):
    salt = hash_[64:]
    pwd_hash = hash_[:64]
    new_hash = pbkdf2_hmac("sha512",
                        password.encode("utf-8"),
                        salt,
                        100000)
    return new_hash == pwd_hash


if __name__ == "__main__":
    password = "dkpkg123"

    hash_ = generate_pwd_hash(password)
    print(hash_, "len:", len(hash_))
    check = check_pwd_hash(hash_, password)
    print(check)


