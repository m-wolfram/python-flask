import datetime
from util.mixins import FormsChecksMixin, FilesChecksMixin


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
