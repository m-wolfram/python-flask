import os
import re
import sys
from uuid import uuid4
from unicodedata import normalize
from urllib.parse import urlparse, urljoin


def is_safe_url(target, host_url):
    ref_url = urlparse(host_url)
    test_url = urlparse(urljoin(host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def secure_filename_unicode(filename: str) -> str:
    PY2 = sys.version_info[0] == 2
    if PY2:
        text_type = unicode
    else:
        text_type = str

    _windows_device_files = (
        "CON",
        "AUX",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "LPT1",
        "LPT2",
        "LPT3",
        "PRN",
        "NUL",
    )
    _filename_strip_re = re.compile(r"[^A-Za-zа-яА-ЯёЁ0-9_.-]")

    if isinstance(filename, text_type):
        filename = normalize("NFKD", filename)

    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, " ")

    filename = str(_filename_strip_re.sub("", "_".join(filename.split()))).strip("._")

    if os.name == "nt" and filename and filename.split(".")[0].upper() in _windows_device_files:
        filename = f"_{filename}"

    return filename


def remove_file_if_exists(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    else:
        return False
