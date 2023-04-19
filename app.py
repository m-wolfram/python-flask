import os
import sqlite3
from pprint import pprint
from uuid import uuid4
from datetime import datetime, date
from flask import Flask, request, current_app, g, \
    url_for, render_template, make_response, redirect, abort, \
    flash, session, jsonify, send_from_directory
from flask_paginate import Pagination
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_apscheduler import APScheduler
from util.check_password import generate_pwd_hash, check_pwd_hash
from util.forms_checks import RegistrationForm, FileUploadForm
from util.util import is_safe_url, secure_filename_unicode, remove_file_if_exists
from util.users import UserSQLite


app = Flask(__name__)

app.config.from_object("config.ConfigDefault")
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploaded_files")
app.config["DB_PATH"] = os.path.join(app.root_path, "database", "database.db")

login_manager = LoginManager(app)
login_manager.login_view = "log_in"
login_manager.login_message = "You are not logged in."
login_manager.login_message_category = "danger"
login_manager.session_protection = "strong"

app.logger.setLevel("INFO")

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


def connect_db():
    con = sqlite3.connect(app.config["DB_PATH"])
    con.row_factory = sqlite3.Row
    return con


def get_db():
    if not hasattr(g, "db"):
        g.db = connect_db()
    return g.db


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource("database/schema.sql", "r") as sql_schema:
            db.executescript(sql_schema.read())
        db.commit()


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cur = db.cursor()

    user = cur.execute("SELECT * FROM users WHERE id = ?", [user_id]).fetchone()
    if user is not None:
        return UserSQLite(user)
    return None


@app.route("/", methods=["GET"])
def index():
    return render_template("pages/index.html")


@app.route("/upload_file", methods=["GET", "POST"])
def upload_file():
    if request.method == "GET":
        db = get_db()
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
            public_files = cur.execute("""
                SELECT f.id, original_file_name, unique_file_name, size_in_bytes,
                       owner_id, privacy, strftime("%d.%m.%Y %H:%M", upload_date) upload_date,
                       strftime("%d.%m.%Y %H:%M", expires) expires, description, username
                FROM files f
                LEFT JOIN users u ON f.owner_id = u.id
                WHERE privacy = 'Public' AND f.owner_id <> ?
                ORDER BY datetime(upload_date) DESC
            """, [current_user.id]).fetchall()
        else:
            user_files = None
            public_files = cur.execute("""
                SELECT f.id, original_file_name, unique_file_name, size_in_bytes,
                       owner_id, privacy, strftime("%d.%m.%Y %H:%M", upload_date) upload_date,
                       strftime("%d.%m.%Y %H:%M", expires) expires, description, username
                FROM files f
                LEFT JOIN users u ON f.owner_id = u.id
                WHERE privacy = 'Public'
                ORDER BY datetime(upload_date) DESC
            """).fetchall()

        return render_template("pages/upload_file.html", user_files=user_files, public_files=public_files)
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
                return render_template("pages/upload_file.html", validations=validations["validations"],
                                       form=upload_form)

            db = get_db()
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


@app.route("/files/delete/<path:unique_file_name>", methods=["POST"])
@login_required
def delete_file(unique_file_name):
    db = get_db()
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
        return redirect(url_for("upload_file"))
    else:
        abort(403)


@app.route("/files/<path:unique_file_name>", methods=["GET"])
def download_file(unique_file_name):
    db = get_db()
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


@app.route("/leave_message", methods=["GET", "POST"])
def leave_message():
    db = get_db()
    cur = db.cursor()

    if request.method == "GET":
        prev_text = request.args.get("msg", None)
        return render_template("pages/leave_message.html", msg_text=prev_text)
    elif request.method == "POST":
        if current_user.is_authenticated:
            msg_text = request.form["msg_text"]

            if len(msg_text) > 0:
                data = {
                    "author": getattr(current_user, "username", ""),
                    "text": msg_text,
                    "date": datetime.now().isoformat()
                }
                cur.execute("""
                    INSERT INTO Posts (author_id, text, date)
                    VALUES(
                        (SELECT id FROM users WHERE username = :author), :text, :date
                    )
                """, data)
                db.commit()

                current_app.logger.info("MSG FROM '{}': {}".format(getattr(current_user, "username", ""), msg_text))
                flash("Successfully sent!", category="success")
                return redirect(url_for("leave_message"))
            if len(msg_text) == 0:
                flash("You did not enter message text.", category="danger")
            return redirect(request.url)
        else:
            abort(401)


@app.route("/leave_message/posts/parameters", methods=["GET"])
def leave_message_posts_parameters():
    db = get_db()
    cur = db.cursor()

    posts_count = cur.execute("SELECT COUNT(*) count from Posts").fetchone()["count"]

    rsp = jsonify({
        "posts_count": posts_count,
        "posts_per_page": current_app.config["POSTS_PER_PAGE"]
    })
    return rsp


@app.route("/leave_message/posts/load_posts", methods=["GET"])
def leave_message_load_posts():
    db = get_db()
    cur = db.cursor()

    page = request.args.get("page", "1", int)
    post_index = request.args.get("index", None, int)

    posts_per_page = current_app.config["POSTS_PER_PAGE"]
    page_offset = (page-1) * posts_per_page

    if post_index is not None:
        if abs(post_index) in range(posts_per_page):
            if post_index >= 0:
                offset = page_offset + post_index
            else:
                offset = page_offset + (posts_per_page - abs(post_index))
        else:
            abort(400, "Incorrect index.")
        limit = 1
    else:
        offset = page_offset
        limit = app.config["POSTS_PER_PAGE"]

    page_posts_query_data = {
        "offset": offset,
        "limit": limit,
        "user_id": getattr(current_user, "id", "")
    }
    page_posts = cur.execute("""
        SELECT p.id id, username, text, strftime("%d.%m.%Y %H:%M", date) date, COUNT(pl.id) likes,
        CASE
            WHEN ul.like_author_id=:user_id THEN 1
            ELSE 0
        END is_liked_by_current_user
        FROM Posts p
        LEFT JOIN users u ON p.author_id = u.id
        LEFT JOIN posts_likes pl ON p.id = pl.post_id
        LEFT JOIN
            (SELECT * FROM posts_likes pl
             WHERE like_author_id=:user_id) ul
        ON p.id = ul.post_id
        GROUP BY p.id
        ORDER BY datetime(date) DESC LIMIT :offset, :limit
    """, page_posts_query_data).fetchall() # TODO: split
    return render_template("elements/leave_message_posts.html", posts=page_posts)


@app.route("/leave_message/posts/delete/<int:post_id>", methods=["DELETE"])
@login_required
def leave_message_delete_post(post_id):
    db = get_db()
    cur = db.cursor()

    post_author_id = cur.execute("""
        SELECT author_id FROM posts WHERE id=?
    """, [post_id]).fetchone()

    if post_author_id is not None and current_user.id == post_author_id["author_id"]:
        cur.execute("""
            DELETE FROM posts WHERE id=?
        """, [post_id])
        db.commit()

        return jsonify({
            "deleted_post_id": post_id
        })
    else:
        abort(400)


@app.route("/leave_message/posts/like", methods=["GET"])
def leave_message_like():
    """
    TODO:
    split into 3 requests:
        insert like (PUT),
        delete like (DELETE),
        get likes (GET).
    """

    db = get_db()
    cur = db.cursor()

    post_id = request.args.get("post_id", None)

    # NOT FOR LOGIN_REQUIRED!
    # because if user are not authenticated likes are loaded anyway
    if not current_user.is_authenticated:
        abort(401)

    username = getattr(current_user, "username", "")

    is_liked_by_current_user = bool(cur.execute("""
        SELECT EXISTS
        (SELECT * FROM posts_likes
        WHERE post_id=? AND like_author_id=(SELECT id FROM users WHERE username=?)) ex
    """, [post_id, username]).fetchone()["ex"])
    if not is_liked_by_current_user:
        cur.execute("""
            INSERT INTO posts_likes VALUES(NULL, ?, (SELECT id FROM users WHERE username=?))
        """, [post_id, username])
        db.commit()
    else:
        cur.execute("""
            DELETE
            FROM posts_likes WHERE post_id=? AND like_author_id=(SELECT id FROM users WHERE username=?)
        """, [post_id, username])
        db.commit()

    post_likes_query_data = {
        "username": username,
        "post_id": post_id
    }
    post_likes = cur.execute("""
        WITH uid AS (SELECT id from users WHERE username=:username)
    
        SELECT p.id id, COUNT(pl.id) likes,
        CASE
            WHEN ul.like_author_id=(SELECT * FROM uid) THEN 1
            ELSE 0
        END is_liked_by_current_user
        FROM posts p
        LEFT JOIN posts_likes pl ON p.id = pl.post_id
        LEFT JOIN
            (SELECT * FROM posts_likes pl
             WHERE like_author_id=(SELECT * FROM uid)) ul
        ON p.id = ul.post_id
        GROUP BY p.id
        HAVING p.id = :post_id
    """, post_likes_query_data).fetchone()
    return render_template("elements/likes_button.html", post=post_likes)


@app.route("/log_in", methods=["GET", "POST"])
def log_in():
    if request.method == "GET":
        if current_user.is_authenticated:
            flash("You are already logged in.", category="dark")
            return redirect(url_for("index"))
        else:
            return render_template("pages/login.html")
    elif request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        remember = eval(request.form.get("remember", "False"))
        next_ = request.args.get("next", "")

        db = get_db()
        cur = db.cursor()

        user = cur.execute("SELECT * FROM users WHERE username = ?", [username]).fetchone()

        if len(username) == 0 or len(password) == 0:
            flash("Incorrect data.", category="danger")
            return redirect(request.url)
        elif user is None:
            flash("User not found.", category="danger")
            return redirect(request.url)

        if check_pwd_hash(user["password_hash"], password):
            if remember:
                login_user(UserSQLite(user), remember=remember, duration=None)
            else:
                login_user(UserSQLite(user))

            if not is_safe_url(next_, request.host_url):
                return abort(400)
            flash("Successfully logged in!", category="success")
            return redirect(next_ or url_for("index"))
        else:
            flash("Incorrect password.", category="danger")
            return redirect(request.url)


@app.route("/log_out", methods=["GET"])
def log_out():
    if current_user.is_authenticated:
        logout_user()
        flash("Successfully logged out!", category="dark")
    else:
        flash("You are not logged in.", category="danger")
        return redirect(url_for("log_in"))
    return redirect(url_for("log_in"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if current_user.is_authenticated:
            flash("You are logged in.", category="dark")
            return redirect(url_for("index"))
        else:
            return render_template("pages/registration.html")
    elif request.method == "POST":
        reg_form = RegistrationForm(request.form, genders_list=current_app.config["REGISTRATION_GENDERS"],
                                    birthdate_months=current_app.config["REGISTRATION_MONTHS"],
                                    birthdate_years=current_app.config["REGISTRATION_YEARS"])

        validations = reg_form.check_all()
        is_valid = validations["check"]

        if not is_valid:
            flash("One or more fields are incorrect.", category="danger")
            return render_template("pages/registration.html", validations=validations["validations"], form=reg_form)
        else:
            db = get_db()
            cur = db.cursor()

            username_taken = bool(
                cur.execute("SELECT EXISTS (SELECT * FROM users WHERE username = ?) ex",
                            [reg_form.username]).fetchone()["ex"])

            if username_taken:
                validations["check"] = False
                validations["validations"].update({
                    "username": RegistrationForm.make_check_result(False, "Username has already been taken.")
                })
                flash("Username is unavailable.", category="danger")
                return render_template("pages/registration.html", validations=validations["validations"], form=reg_form)

            create_user_query_data = [reg_form.username, generate_pwd_hash(reg_form.password)]
            create_profile_query_data = {
                "username": reg_form.username,
                "first_name": reg_form.first_name,
                "last_name": reg_form.last_name,
                "gender": reg_form.gender,
                "birthdate": date(int(reg_form.birthdate_year),
                                  int(reg_form.birthdate_month_num),
                                  int(reg_form.birthdate_day)).isoformat(),
                "bio": reg_form.bio,
                "registration_date": datetime.now().isoformat()
            }
            cur.execute("""
                INSERT INTO users VALUES(NULL, ?, ?)
            """, create_user_query_data)
            db.commit()
            cur.execute("""
                INSERT INTO profiles VALUES(
                    NULL,
                    (SELECT id FROM users WHERE username=:username),
                    :first_name,
                    :last_name,
                    :gender,
                    :birthdate,
                    :bio,
                    :registration_date
                )
            """, create_profile_query_data)
            db.commit()

            flash("Successfully registered!", category="success")
            return redirect(url_for("log_in"))


@app.teardown_request
def teardown_db(error):
    if hasattr(g, "db"):
        g.db.close()


@app.errorhandler(401)
def unauthorized(error):
    return render_template("errors/401.html"), 401


@app.errorhandler(403)
def forbidden(error):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def not_found(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(413)
def request_entity_too_large(error):
    return render_template("errors/413.html"), 413


@scheduler.task('interval', id="remove_expired_files", hours=1)
def remove_expired_files():
    with scheduler.app.app_context():
        db = get_db()
        cur = db.cursor()

        current_time = datetime.now().isoformat()

        expiring_files = cur.execute("""
            SELECT * FROM files
            WHERE datetime(expires) <= datetime(?)
        """, [current_time]).fetchall()

        cur.execute("""
            DELETE FROM files
            WHERE datetime(expires) <= datetime(?)
        """, [current_time])

        db.commit()
        db.close()

        for expired_file in expiring_files:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], expired_file["unique_file_name"]))

        current_app.logger.debug(f"{len(expiring_files)} expired files successfully removed.")




if __name__ == "__main__":
    #app.run(host="127.0.0.1", port=5000)
    app.run(host="0.0.0.0", port=5000, debug=False)
