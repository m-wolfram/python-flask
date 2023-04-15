import os


class FilesChecksMixin:
    @staticmethod
    def check_extension(filename, allowed_extensions):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

    @staticmethod
    def check_size(f, allowed_size_bytes):
        f_len = f.seek(0, os.SEEK_END)
        f.seek(0, os.SEEK_SET)
        return f_len <= allowed_size_bytes
