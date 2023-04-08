from flask_login import UserMixin


class UserSQLite(UserMixin):
    def __init__(self, sqlite_user_row):
        self.id = sqlite_user_row["id"]
        self.username = sqlite_user_row["username"]