import os
import datetime


class ConfigDefault:
    DEBUG = False
    SECRET_KEY = b"\xd2l\x1c\xa3\x0c\xc4\x91\x19\xbb\xf3\x15\xfe\xfc\xee\xe6\xed*\xf1\x1c\xb1v\xb5r\xac"
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024

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
    USERNAME_MINLENGHT = 4
    USERNAME_MAXLENGHT = 20
    FIRST_NAME_MINLENGHT = 2
    FIRST_NAME_MAXLENGHT = 20
    LAST_NAME_MINLENGHT = 2
    LAST_NAME_MAXLENGHT = 20
    PASSWORD_MINLENGHT = 8
    PASSWORD_MAXLENGHT = 20
    BIO_MAXLENGHT = 280

    # public messages
    POSTS_PER_PAGE = 10
    POST_MAXLENGHT = 280

    # file upload
    FILE_UPLOAD_MAX_SIZE = 32 * 1024 * 1024
    PUBLIC_FILES_PER_PAGE = 5
    FILES_PER_USER = 16
    FILE_DESCRIPTION_LENGTH = 72
    FILE_UPLOAD_ACCESSIBILITY_OPTIONS = [
        "Public",
        "Private",
        "By link"
    ]
    FILE_UPLOAD_EXPIRATION_OPTIONS = {
        "1 hour": datetime.timedelta(hours=1),
        "12 hours": datetime.timedelta(hours=12),
        "1 day": datetime.timedelta(days=1),
        "1 week": datetime.timedelta(weeks=1),
        "1 month": datetime.timedelta(weeks=4),
        "1 year": datetime.timedelta(days=365)
    }
    FILE_UPLOAD_ALLOWED_EXTENSIONS = [
        "doc", "docx", "xls",
        "xlsx", "ppt", "pptx",
        "pdf", "png", "jpg",
        "jpeg", "bmp", "gif",
        "webm", "zip", "rar",
        "txt", "mp3", "mp4"
    ]
    FILE_UPLOAD_VERBOSE_UNIQUE_FILE_NAMES = True


if __name__ == "__main__":
    # secret_key = os.urandom(24)
    # print(secret_key)
    pass

