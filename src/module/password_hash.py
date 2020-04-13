import sys

import bcrypt

def hash_password(password, rounds=12):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds)).decode()


def check_password(user_password, hashed_password):
    return bcrypt.checkpw(user_password.encode(), hashed_password.encode())

if __name__ == "__main__":
    pass