from datetime import datetime, date
from flask import Flask, request, current_app, g, \
    url_for, render_template, make_response, redirect, abort, \
    flash, session, jsonify
from flask_paginate import Pagination
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from util.check_password import generate_pwd_hash, check_pwd_hash
from util.registration_checks import RegistrationForm
from util.util import is_safe_url
from util.users import UserSQLite
import os
import sqlite3
from pprint import pprint


app = Flask(__name__)
app.logger.setLevel("INFO")
app.config.from_object("config.ConfigDefault")
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploaded_files")
app.config["DB_PATH"] = os.path.join(app.root_path, "database", "database.db")
login_manager = LoginManager(app)
login_manager.login_view = "log_in"
login_manager.login_message = "You are not logged in."
login_manager.login_message_category = "danger"
login_manager.session_protection = "strong"


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
@login_required
def upload_file():
    if request.method == "GET":
        return render_template("pages/upload_file.html")
    elif request.method == "POST":
        f = request.files["outcoming_file"]
        if f.content_type != "application/octet-stream":
            f.save(os.path.join(current_app.config["UPLOAD_FOLDER"], f.filename))
            flash("File uploaded successfully!", category="success")
            app.logger.info("File '{}' saved.".format(f.filename))
        else:
            flash("You have not chosen any file.", category="danger")
        return redirect(url_for("upload_file"))


@app.route("/leave_message", methods=["GET", "POST"])
def leave_message():
    db = get_db()
    cur = db.cursor()

    if request.method == "GET":
        prev_text = request.args.get("msg", None)
        return render_template("pages/leave_message.html", msg_text=prev_text)
    elif request.method == "POST":
        msg_text = request.form["msg_text"]

        if len(msg_text) > 0:
            data = {
                "author": getattr(current_user, "username", ""),
                "text": msg_text,
                "date": datetime.now().strftime("%m.%d.%Y %H:%M:%S")
            }
            cur.execute("""
                INSERT INTO Posts (author_id, text, date)
                VALUES(
                    (SELECT id FROM users WHERE username = :author), :text, :date
                )
            """, data)
            db.commit()

            app.logger.info("MSG FROM '{}': {}".format(getattr(current_user, "username", ""), msg_text))
            flash("Successfully sent!", category="success")
            return redirect(url_for("leave_message"))
        if len(msg_text) == 0:
            flash("You did not enter message text.", category="danger")
        return redirect(url_for("leave_message"))


@app.route("/leave_message/posts", methods=["GET"])
def leave_message_posts():
    db = get_db()
    cur = db.cursor()

    page = request.args.get("page", "1")

    page_posts_query_data = {
        "limit": app.config["POSTS_PER_PAGE"],
        "offset": (int(page)-1) * current_app.config["POSTS_PER_PAGE"],
        "user_id": getattr(current_user, "id", "")
    }
    page_posts = cur.execute("""
        SELECT p.id id, username, text, date, COUNT(pl.id) likes,
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
        ORDER BY date DESC LIMIT :offset, :limit
    """, page_posts_query_data).fetchall()
    return render_template("elements/leave_message_posts.html", posts=page_posts)


@app.route("/leave_message/posts_parameters", methods=["GET"])
def leave_message_posts_parameters():
    db = get_db()
    cur = db.cursor()

    posts_count = cur.execute("SELECT COUNT(*) count from Posts").fetchone()["count"]

    rsp = jsonify({
        "posts_count": posts_count,
        "posts_per_page": current_app.config["POSTS_PER_PAGE"]
    })

    return rsp


@app.route("/leave_message/like", methods=["GET"])
def leave_message_like():
    db = get_db()
    cur = db.cursor()

    post_id = request.args.get("post_id", None)

    # NOT FOR LOGIN_REQUIRED!
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
            return redirect(url_for("log_in"))
        elif user is None:
            flash("User not found.", category="danger")
            return redirect(url_for("log_in"))

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
                                  int(reg_form.birthdate_day)).strftime("%d.%m.%Y"),
                "bio": reg_form.bio,
                "registration_date": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
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


@app.route("/log_out", methods=["GET"])
def log_out():
    if current_user.is_authenticated:
        logout_user()
        flash("Successfully logged out!", category="dark")
    else:
        flash("You are not logged in.", category="danger")
        return redirect(url_for("log_in"))
    return redirect(url_for("log_in"))


@app.route("/rsp_tuple_list", methods=["GET"])
def rsp_tuple_test_list():
    return "Rsp text list", 200, [("header1", "val1"), ("header2", "val2")]


@app.route("/rsp_tuple_dict", methods=["GET"])
def rsp_tuple_test_dict():
    return "Rsp text dict", 200, {"header1": "val1", "header2": "val2"}


@app.route("/user/<int:user_id>/", methods=["GET", "POST"])
def user_profile(user_id):
    """
    GET POST PUT DELETE HEAD OPTIONS;
    """
    app.logger.info("[*] Received request for user_profile with method {}..".format(request.method))
    return "Profile page of user #{}".format(user_id)


@app.route("/cookies_test", methods=["GET"])
def cookies_test():
    app.logger.info("old cookies: {}".format(request.cookies.get("last_time_visited", None)))
    rsp = make_response(render_template("pages/index.html"), 200)
    rsp.set_cookie("last_time_visited",
                   datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                   max_age=300,
                   httponly=True,
                   samesite="Strict")
    # rsp.headers["cookies_set"] = True
    return rsp


@app.route("/anonymous_user_test", methods=["GET"])
def anonymous_user_test():
    if "anonymous" in current_user.__class__.__name__.lower():
        return "True"
    else:
        return "False"


@app.route("/books/<string:genre>/")
@login_required
def books(genre):
    app.logger.info("method:", request.method)
    app.logger.info("app.name", current_app.name)
    return "All Books in {} category".format(genre)


@app.route("/p/<path:path>/")
@login_required
def path_converter_test(path):
    return "path converter is: {}".format(path)


@app.route("/s/<string:string>/")
@login_required
def string_converter_test(string):
    return "string converter is: {}".format(string)


@app.route("/i/<int:integer>/")
@login_required
def int_converter_test(integer):
    return "int converter is: {}".format(integer)


@app.route("/f/<float:f>/")
@login_required
def float_converter_test(f):
    return "float converter is: {}".format(f)


@app.route("/slashed/")
@login_required
def slashed():
    return "Redirects to slashed if there's no slash at the end of link"


@app.route("/unslashed")
@login_required
def unslashed():
    return "404 if slash at the end of link"


@app.errorhandler(404)
def not_found(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(403)
def not_found(error):
    return render_template("errors/403.html"), 403


@app.errorhandler(401)
def unauthorized(error):
    return render_template("errors/401.html"), 401


@app.teardown_request
def teardown_db(error):
    if hasattr(g, "db"):
        g.db.close()


with app.test_request_context():
    print("hello from test request")
    print(url_for("unslashed"))
    print(url_for("slashed"))
    print(url_for("float_converter_test", f=0.9))
    print(url_for("int_converter_test", integer=10))
    print(url_for("path_converter_test", path="a/b/c/d/usr"))
    print("\nstatic file path:", url_for("static", filename="biden.png"))
    print("url_for args", url_for("leave_message", txt="HelloMyName", nonearg=None, author="authorIsMe"))

with app.app_context():
    print('hello from app context')


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
    # app.run(host="0.0.0.0", port=5000, debug=False)
