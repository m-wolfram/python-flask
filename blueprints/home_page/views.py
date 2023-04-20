from flask import Blueprint, render_template, g


home_page = Blueprint("home_page", __name__, static_folder="static", template_folder="templates")


@home_page.route("/", methods=["GET"])
def index():
    return render_template("home_page/index.html")


@home_page.teardown_request
def teardown_db(error):
    if hasattr(g, "db"):
        g.db.close()


@home_page.errorhandler(401)
def unauthorized(error):
    return render_template("errors/401.html"), 401


@home_page.errorhandler(403)
def forbidden(error):
    return render_template("errors/403.html"), 403


@home_page.errorhandler(404)
def not_found(error):
    return render_template("errors/404.html"), 404


@home_page.errorhandler(413)
def request_entity_too_large(error):
    return render_template("errors/413.html"), 413

