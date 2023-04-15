import datetime
from usernames import is_safe_username
from util.mixins import FilesChecksMixin


class FormsChecksMixin:
    @staticmethod
    def make_check_result(check, feedback):
        result = {
            "check": check,
            "feedback": feedback
        }
        return result


class RegistrationForm(FormsChecksMixin):
    """
    :request form: request registration form.
    :field_names_mapping: dict, keys are reg form field names, values are their html input names.
    :genders_list: list of strings, genders list.
    :birthdate_months: dict, keys are months numbers, values are their names.
    :birthdate_years: list if ints, available years that can be picked.
    """
    def __init__(self, request_form, fields_names_mapping=None, genders_list=None, birthdate_months=None,
                 birthdate_years=None):
        # defaults:
        if fields_names_mapping is None:
            self.fields_names_mapping = {
                "first_name": "first_name",
                "last_name": "last_name",
                "gender": "gender",
                "birthdate_day": "birthdate_day",
                "birthdate_month": "birthdate_month",
                "birthdate_year": "birthdate_year",
                "username": "username",
                "password": "password",
                "repeat_password": "repeat_password",
                "bio": "bio"
            }
        else:
            self.fields_names_mapping = fields_names_mapping

        if genders_list is None:
            self.genders_list = [
                "Male",
                "Female"
            ]
        else:
            self.genders_list = genders_list

        if birthdate_months is None:
            self.birthdate_months = {
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
        else:
            self.birthdate_months = birthdate_months

        if birthdate_years is None:
            self.birthdate_years = list(range(2009, 1902-1, -1))
        else:
            self.birthdate_years = birthdate_years

        # attrs:
        self.form = request_form
        self.first_name = self.form.get(self.fields_names_mapping["first_name"], "")
        self.last_name = self.form.get(self.fields_names_mapping["last_name"], "")
        self.gender = self.form.get(self.fields_names_mapping["gender"], "")
        self.birthdate_day = self.form.get(self.fields_names_mapping["birthdate_day"], "")
        self.birthdate_month = self.form.get(self.fields_names_mapping["birthdate_month"], "")
        self.birthdate_year = self.form.get(self.fields_names_mapping["birthdate_year"], "")
        self.username = self.form.get(self.fields_names_mapping["username"], "")
        self.password = self.form.get(self.fields_names_mapping["password"], "")
        self.repeat_password = self.form.get(self.fields_names_mapping["repeat_password"], "")
        self.bio = self.form.get(self.fields_names_mapping["bio"], "")

        # extra:
        self.birthdate_month_num = str([k for k, v in self.birthdate_months.items() if v == self.birthdate_month][0])

    def check_all(self):
        checks = {
            "first_name": self.check_first_name(),
            "last_name": self.check_last_name(),
            "gender": self.check_gender(),
            "birthdate_day": self.check_birthdate_day(),
            "birthdate_month": self.check_birthdate_month(),
            "birthdate_year": self.check_birthdate_year(),
            "username": self.check_username(),
            "password": self.check_password(),
            "repeat_password": self.check_repeat_password(),
            "bio": self.check_bio()
        }

        check = all([v["check"] for k, v in checks.items()])

        return {
            "check": check,
            "validations": checks
        }

    def check_first_name(self):
        checks = [
            2 <= len(self.first_name) <= 20,
            self.first_name.isalpha()
        ]

        check = all(checks)

        if check:
            feedback = "Ok!"
        else:
            feedback = "Not passed!"

        return self.make_check_result(check, feedback)

    def check_last_name(self):
        checks = [
            2 <= len(self.last_name) <= 20,
            self.last_name.isalpha()
        ]

        check = all(checks)

        if check:
            feedback = "Ok!"
        else:
            feedback = "Not passed!"

        return self.make_check_result(check, feedback)

    def check_gender(self):
        checks = [
            self.gender in self.genders_list
        ]

        check = all(checks)

        if check:
            feedback = "Ok!"
        else:
            feedback = "Choose gender from the list!"

        return self.make_check_result(check, feedback)

    def check_birthdate_day(self):
        checks = [
            1 <= int(self.birthdate_day) <= 31,
            self.validate_birthdate()
        ]

        check = all(checks)

        if check:
            feedback = "Ok!"
        else:
            feedback = "Not passed!"

        return self.make_check_result(check, feedback)

    def check_birthdate_month(self):
        checks = [
            self.birthdate_month in self.birthdate_months.values()
        ]

        check = all(checks)

        if check:
            feedback = "Ok!"
        else:
            feedback = "Choose month from the list!"

        return self.make_check_result(check, feedback)

    def check_birthdate_year(self):
        checks = [
            int(self.birthdate_year) in self.birthdate_years
        ]

        check = all(checks)

        if check:
            feedback = "Ok!"
        else:
            feedback = "Not passed!"

        return self.make_check_result(check, feedback)

    def check_username(self):
        checks = [
            4 <= len(self.username) <= 20,
            is_safe_username(self.username, max_length=20)
        ]

        check = all(checks)

        if check:
            feedback = "Ok!"
        else:
            feedback = "Not passed!"

        return self.make_check_result(check, feedback)

    def check_password(self):
        special_sym = ['$', '@', '#', '%', '_']

        checks = [
            8 <= len(self.password) <= 20,
            not (" " in self.password),
            any(char.isdigit() for char in self.password),
            any(char.isupper() for char in self.password),
            any(char.islower() for char in self.password),
            any(char in special_sym for char in self.password)
        ]

        check = all(checks)

        if check:
            feedback = "Ok!"
        else:
            feedback = "Not passed!"

        return self.make_check_result(check, feedback)

    def check_repeat_password(self):
        checks = [
            bool(self.repeat_password),
            self.password == self.repeat_password
        ]

        check = all(checks)

        if check:
            feedback = "Passwords match!"
        else:
            feedback = "Passwords do not match."

        return self.make_check_result(check, feedback)

    def check_bio(self):
        checks = [
            0 <= len(self.bio) <= 280
        ]

        check = all(checks)

        if check:
            feedback = "Ok!"
        else:
            feedback = "Not passed!"

        return self.make_check_result(check, feedback)

    def validate_birthdate(self):
        try:
            datetime.date(int(self.birthdate_year), int(self.birthdate_month_num), int(self.birthdate_day))
        except ValueError:
            return False

        return True


class FileUploadForm(FormsChecksMixin, FilesChecksMixin):
    """
    :request form: request file upload form.
    :field_names_mapping: dict, keys are file upload form field names, values are their html input names.
    :accessibility_options: list of strings, file accessibility options list.
    :expiration_options: list of strings, file expiration options list.
    """
    def __init__(self, request_form, request_files,
                 fields_names_mapping=None, accessibility_options=None, expiration_options=None,
                 allowed_extensions=None, allowed_file_size=None):
        # defaults:
        if fields_names_mapping is None:
            self.fields_names_mapping = {
                "file": "file",
                "accessibility": "accessibility",
                "expiration": "expiration",
                "description": "description"
            }
        else:
            self.fields_names_mapping = fields_names_mapping

        if accessibility_options is None:
            self.accessibility_options = [
                "Public",
                "Private",
                "By link"
            ]
        else:
            self.accessibility_options = accessibility_options

        if expiration_options is None:
            self.expiration_options = {
                "1 hour": datetime.timedelta(hours=1),
                "12 hours": datetime.timedelta(hours=12),
                "1 day": datetime.timedelta(days=1),
                "1 week": datetime.timedelta(weeks=1),
                "1 month": datetime.timedelta(weeks=4),
                "1 year": datetime.timedelta(days=365)
            }
        else:
            self.expiration_options = expiration_options

        if allowed_extensions is None:
            self.allowed_extensions = [
                "doc", "docx", "xls",
                "xlsx", "ppt", "pptx",
                "pdf", "png", "jpg",
                "jpeg", "bmp", "gif",
                "webm", "zip", "rar"
            ]
        else:
            self.allowed_extensions = allowed_extensions

        if allowed_file_size is None:
            self.allowed_file_size = 16 * 1000 * 1000
        else:
            self.allowed_file_size = allowed_file_size

        # attrs:
        self.form = request_form
        self.files = request_files
        self.accessibility = self.form.get(self.fields_names_mapping["accessibility"], "")
        self.expiration = self.form.get(self.fields_names_mapping["expiration"], "")
        self.description = self.form.get(self.fields_names_mapping["description"], "")

        # extra:
        self.expiration_timedelta = [v for k, v in self.expiration_options.items() if k == self.expiration][0]

    def check_all(self):
        checks = {
            "file": self.check_file(),
            "accessibility": self.check_accessibility(),
            "expiration": self.check_expiration(),
            "description": self.check_description()
        }

        check = all([v["check"] for k, v in checks.items()])

        return {
            "check": check,
            "validations": checks
        }

    def check_accessibility(self):
        checks = [
            self.accessibility in self.accessibility_options
        ]

        check = all(checks)

        if check:
            feedback = "Ok!"
        else:
            feedback = "Choose privacy option from the list!"

        return self.make_check_result(check, feedback)

    def check_expiration(self):
        checks = [
            self.expiration in self.expiration_options
        ]

        check = all(checks)

        if check:
            feedback = "Ok!"
        else:
            feedback = "Choose expiration time from the list!"

        return self.make_check_result(check, feedback)

    def check_description(self):
        checks = [
            0 <= len(self.description) <= 140
        ]

        check = all(checks)

        if check:
            feedback = "Ok!"
        else:
            feedback = "Not passed!"

        return self.make_check_result(check, feedback)

    def check_file(self):
        checks = [
            # file input exists in form
            self.fields_names_mapping["file"] in self.files,

            # file is not empty
            self.files[self.fields_names_mapping["file"]].filename != ''
            if self.fields_names_mapping["file"] in self.files
            else False,

            # file extension in allowed extensions
            self.check_extension(self.files[self.fields_names_mapping["file"]].filename, self.allowed_extensions)
            if self.fields_names_mapping["file"] in self.files
            else False,

            # size in allowed limit
            self.check_size(self.files[self.fields_names_mapping["file"]], self.allowed_file_size)
            if self.fields_names_mapping["file"] in self.files
            else False
        ]

        check = all(checks)

        if check:
            feedback = "Ok!"
        else:
            feedback = "Not passed!"

        return self.make_check_result(check, feedback)


if __name__ == "__main__":
    # date = "29.02.2023"
    # date_object = datetime.strptime(date, "%d.%m.%Y")
    # print(date_object)
    #
    # print(" Hi".isalpha())
    pass
