import datetime
from usernames import is_safe_username


class RegistrationForm:
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

    @staticmethod
    def make_check_result(check, feedback):
        result = {
            "check": check,
            "feedback": feedback
        }
        return result

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


if __name__ == "__main__":
    # date = "29.02.2023"
    # date_object = datetime.strptime(date, "%d.%m.%Y")
    # print(date_object)
    #
    # print(" Hi".isalpha())
    pass
