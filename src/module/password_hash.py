import bcrypt

def hash_password(password, rounds=12):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds)).decode()


def check_password(user_password, hashed_password):
    return bcrypt.checkpw(user_password.encode(), hashed_password.encode())

def main():
    from getpass import getpass
    raw_password = getpass()
    if len(raw_password) < 8:
        print("Too short pasword. We required more than 8 charactors.")
        return
    hashed_password = hash_password(raw_password)
    print(hashed_password)

if __name__ == "__main__":
    main()