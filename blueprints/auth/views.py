from datetime import date, datetime, timedelta
from flask import Blueprint, request, render_template, flash, redirect, url_for, abort, current_app, g
from flask_login import current_user, login_user, logout_user
from util.check_password import generate_pwd_hash, check_pwd_hash
from util.registration_form import RegistrationForm
from util.users import UserSQLite
from util.util import is_safe_url
from database import sqlite3db


auth = Blueprint("auth", __name__, static_folder="static", template_folder="templates")


@auth.route("/log_in", methods=["GET", "POST"])
def log_in():
    if request.method == "GET":
        if current_user.is_authenticated:
            flash("You are already logged in.", category="dark")
            return redirect(url_for("home_page.index"))
        else:
            return render_template("auth/login.html")
    elif request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        remember = eval(request.form.get("remember", "False"))
        next_ = request.args.get("next", "")

        db = sqlite3db.get_db()
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
                login_user(UserSQLite(user), remember=remember, duration=timedelta(weeks=4))
            else:
                login_user(UserSQLite(user))

            if not is_safe_url(next_, request.host_url):
                return abort(400)
            flash("Successfully logged in!", category="success")
            return redirect(next_ or url_for("home_page.index"))
        else:
            flash("Incorrect password.", category="danger")
            return redirect(request.url)


@auth.route("/log_out", methods=["GET"])
def log_out():
    if current_user.is_authenticated:
        logout_user()
        flash("Successfully logged out!", category="dark")
    else:
        flash("You are not logged in.", category="danger")
        return redirect(url_for("auth.log_in"))
    return redirect(url_for("auth.log_in"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if current_user.is_authenticated:
            flash("You are logged in.", category="dark")
            return redirect(url_for("home_page.index"))
        else:
            return render_template("auth/registration.html")
    elif request.method == "POST":
        reg_form = RegistrationForm(request.form, genders_list=current_app.config["REGISTRATION_GENDERS"],
                                    birthdate_months=current_app.config["REGISTRATION_MONTHS"],
                                    birthdate_years=current_app.config["REGISTRATION_YEARS"])

        validations = reg_form.check_all()
        is_valid = validations["check"]

        if not is_valid:
            flash("One or more fields are incorrect.", category="danger")
            return render_template("auth/registration.html", validations=validations["validations"], form=reg_form)
        else:
            db = sqlite3db.get_db()
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
                return render_template("auth/registration.html", validations=validations["validations"], form=reg_form)

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
            return redirect(url_for("auth.log_in"))


@auth.teardown_request
def teardown_db(error):
    if hasattr(g, "db"):
        g.db.close()


@auth.errorhandler(401)
def unauthorized(error):
    return render_template("errors/401.html"), 401


@auth.errorhandler(403)
def forbidden(error):
    return render_template("errors/403.html"), 403


@auth.errorhandler(404)
def not_found(error):
    return render_template("errors/404.html"), 404


@auth.errorhandler(413)
def request_entity_too_large(error):
    return render_template("errors/413.html"), 413
