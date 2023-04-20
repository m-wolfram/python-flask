import os
from datetime import datetime
from uuid import uuid4
from flask import Blueprint, render_template, request, redirect, current_app, url_for, abort, flash,\
    send_from_directory, g, jsonify
from flask_login import current_user, login_required
from util.upload_file_form import FileUploadForm
from util.util import secure_filename_unicode, remove_file_if_exists
from database import sqlite3db


file_uploader = Blueprint("file_uploader", __name__, static_folder="static", template_folder="templates")


@file_uploader.route("/upload_file", methods=["GET", "POST"])
def upload_file():
    if request.method == "GET":
        db = sqlite3db.get_db()
        cur = db.cursor()

        if current_user.is_authenticated:
            user_files = cur.execute("""
                SELECT f.id, original_file_name, unique_file_name, size_in_bytes,
                   owner_id, privacy, strftime("%d.%m.%Y %H:%M", upload_date) upload_date,
                   strftime("%d.%m.%Y %H:%M", expires) expires, description, username
                FROM files f
                LEFT JOIN users u ON f.owner_id = u.id
                WHERE owner_id = ?
                ORDER BY datetime(upload_date) DESC
            """, [current_user.id]).fetchall()
        else:
            user_files = None

        return render_template("file_uploader/upload_file.html", user_files=user_files)
    elif request.method == "POST":
        if current_user.is_authenticated:
            upload_form = FileUploadForm(request.form, request.files,
                                         fields_names_mapping={
                                             "file": "outcoming_file",
                                             "accessibility": "privacy",
                                             "expiration": "expiration",
                                             "description": "file_description"
                                         },
                                         accessibility_options=current_app.config["FILE_UPLOAD_ACCESSIBILITY_OPTIONS"],
                                         expiration_options=current_app.config["FILE_UPLOAD_EXPIRATION_OPTIONS"],
                                         allowed_extensions=current_app.config["FILE_UPLOAD_ALLOWED_EXTENSIONS"],
                                         allowed_file_size=current_app.config["FILE_UPLOAD_MAX_SIZE"])
            validations = upload_form.check_all()
            is_valid = validations["check"]

            if not is_valid:
                flash("One or more fields are incorrect.", category="danger")
                return render_template("file_uploader/upload_file.html", validations=validations["validations"],
                                       form=upload_form)

            db = sqlite3db.get_db()
            cur = db.cursor()

            users_files_count = cur.execute("""
                SELECT COUNT(*) count FROM files
                WHERE owner_id = ?
            """, [current_user.id]).fetchone()['count']

            if int(users_files_count) >= current_app.config['FILES_PER_USER']:
                flash("You have reached files limit!", category="danger")
                return redirect(request.url)

            file = request.files["outcoming_file"]

            # "Don't optimize unless you know you need to, and measure rather than guessing."
            original_file_name_secured = secure_filename_unicode(file.filename)
            if current_app.config["FILE_UPLOAD_VERBOSE_UNIQUE_FILE_NAMES"]:
                unique_file_name = f"{str(uuid4())}_{original_file_name_secured}"
            else:
                unique_file_name = f"{str(uuid4())}.{original_file_name_secured.rsplit('.', 1)[1]}"
            upload_date = datetime.now()
            expiration_date = upload_date + upload_form.expiration_timedelta

            file_save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_file_name)
            file.save(file_save_path)
            file_size = os.stat(file_save_path).st_size

            file_upload_query_data = {
                "original_file_name": original_file_name_secured,
                "unique_file_name": unique_file_name,
                "size_in_bytes": file_size,
                "owner_id": current_user.id,
                "privacy": upload_form.accessibility,
                "upload_date": upload_date.isoformat(),
                "expiration_date": expiration_date.isoformat(),
                "description": upload_form.description
            }
            cur.execute("""
                INSERT INTO files VALUES(
                    NULL,
                    :original_file_name,
                    :unique_file_name,
                    :size_in_bytes,
                    :owner_id,
                    :privacy,
                    :upload_date,
                    :expiration_date,
                    :description
                )
            """, file_upload_query_data)
            db.commit()

            flash("File uploaded successfully!", category="success")
            current_app.logger.info("File '{}' saved.".format(original_file_name_secured))

            return redirect(request.url)
        else:
            abort(401)


@file_uploader.route("/files/delete/<path:unique_file_name>", methods=["POST"])
@login_required
def delete_file(unique_file_name):
    db = sqlite3db.get_db()
    cur = db.cursor()

    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_file_name)
    file_record = cur.execute("""
        SELECT * FROM files
        WHERE unique_file_name = ?
    """, [unique_file_name]).fetchone()

    if file_record is None:
        abort(404)

    if int(file_record["owner_id"]) == current_user.id:
        cur.execute("""
            DELETE FROM files
            WHERE unique_file_name = ?
        """, [unique_file_name])
        remove_file_if_exists(file_path)
        db.commit()

        flash("File deleted successfully!", category="success")
        return redirect(url_for("file_uploader.upload_file"))
    else:
        abort(403)


@file_uploader.route("/files/<path:unique_file_name>", methods=["GET"])
def download_file(unique_file_name):
    db = sqlite3db.get_db()
    cur = db.cursor()

    file_record = cur.execute("""
        SELECT * FROM files
        WHERE unique_file_name = ?
    """, [unique_file_name]).fetchone()

    if file_record is None:
        abort(404)

    file_privacy = file_record["privacy"]

    if file_privacy == "Public" or file_privacy == "By link":
        return send_from_directory(current_app.config["UPLOAD_FOLDER"], file_record["unique_file_name"],
                                   download_name=file_record["original_file_name"])
    elif file_privacy == "Private":
        if current_user.is_authenticated:
            if int(file_record["owner_id"]) == current_user.id:
                return send_from_directory(current_app.config["UPLOAD_FOLDER"], file_record["unique_file_name"],
                                           download_name=file_record["original_file_name"])
            else:
                abort(403)
        else:
            abort(403)


@file_uploader.route("/public_files/parameters", methods=["GET"])
def file_uploader_public_files_parameters():
    db = sqlite3db.get_db()
    cur = db.cursor()

    is_for_user = request.args.get("for_user", 0, int)

    if is_for_user:
        if current_user.is_authenticated:
            public_files_count = cur.execute("""
                SELECT COUNT(*) count from files
                WHERE privacy = "Public" AND owner_id <> ?
            """, [current_user.id]).fetchone()["count"]
        else:
            abort(400)
    else:
        public_files_count = cur.execute("""
            SELECT COUNT(*) count from files
            WHERE privacy = "Public"
        """).fetchone()["count"]

    return jsonify({
        "public_files_count": public_files_count,
        "public_files_per_page": current_app.config["PUBLIC_FILES_PER_PAGE"]
    })


@file_uploader.route("/public_files/load_files", methods=["GET"])
def load_public_files():
    db = sqlite3db.get_db()
    cur = db.cursor()

    is_for_user = request.args.get("for_user", 0, int)
    page = request.args.get("page", 1, int)

    public_files_per_page = current_app.config["PUBLIC_FILES_PER_PAGE"]
    offset = (page - 1) * public_files_per_page
    limit = public_files_per_page

    if is_for_user:
        if current_user.is_authenticated:
            public_files = cur.execute("""
                SELECT f.id, original_file_name, unique_file_name, size_in_bytes,
                       owner_id, privacy, strftime("%d.%m.%Y %H:%M", upload_date) upload_date,
                       strftime("%d.%m.%Y %H:%M", expires) expires, description, username
                FROM files f
                LEFT JOIN users u ON f.owner_id = u.id
                WHERE privacy = 'Public' AND f.owner_id <> ?
                ORDER BY datetime(upload_date) DESC
                LIMIT ?, ?
            """, [current_user.id, offset, limit]).fetchall()
        else:
            abort(400)
    else:
        public_files = cur.execute("""
            SELECT f.id, original_file_name, unique_file_name, size_in_bytes,
                   owner_id, privacy, strftime("%d.%m.%Y %H:%M", upload_date) upload_date,
                   strftime("%d.%m.%Y %H:%M", expires) expires, description, username
            FROM files f
            LEFT JOIN users u ON f.owner_id = u.id
            WHERE privacy = 'Public'
            ORDER BY datetime(upload_date) DESC
            LIMIT ?, ?
        """, [offset, limit]).fetchall()

    return render_template("file_uploader/public_files.html", public_files=public_files)


@file_uploader.teardown_request
def teardown_db(error):
    if hasattr(g, "db"):
        g.db.close()


@file_uploader.errorhandler(401)
def unauthorized(error):
    return render_template("errors/401.html"), 401


@file_uploader.errorhandler(403)
def forbidden(error):
    return render_template("errors/403.html"), 403


@file_uploader.errorhandler(404)
def not_found(error):
    return render_template("errors/404.html"), 404


@file_uploader.errorhandler(413)
def request_entity_too_large(error):
    return render_template("errors/413.html"), 413
