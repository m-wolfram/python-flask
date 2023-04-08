import os


class ConfigDefault:
    DEBUG = False
    SECRET_KEY = b"\xd2l\x1c\xa3\x0c\xc4\x91\x19\xbb\xf3\x15\xfe\xfc\xee\xe6\xed*\xf1\x1c\xb1v\xb5r\xac"
    # posts
    POST_MAXLENGHT = 280
    POSTS_PER_PAGE = 8
    # registration
    REGISTRATION_GENDERS = [
        "Male",
        "Female"
    ]
    REGISTRATION_MONTHS = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December"
    }
    REGISTRATION_YEARS = list(range(2009, 1902-1, -1))
    # username
    USERNAME_MINLENGHT = 4
    USERNAME_MAXLENGHT = 20
    # firstname
    FIRST_NAME_MINLENGHT = 2
    FIRST_NAME_MAXLENGHT = 20
    # lastname
    LAST_NAME_MINLENGHT = 2
    LAST_NAME_MAXLENGHT = 20
    # password
    PASSWORD_MINLENGHT = 8
    PASSWORD_MAXLENGHT = 20
    #bio
    BIO_MAXLENGHT = 280


if __name__ == "__main__":
    # secret_key = os.urandom(24)
    # print(secret_key)
    pass

