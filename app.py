import os
from datetime import datetime
from flask import Flask
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from blueprints.auth.views import auth
from blueprints.public_messages.views import public_messages
from blueprints.file_uploader.views import file_uploader
from blueprints.home_page.views import home_page
from util.users import UserSQLite
from database import sqlite3db


login_manager = LoginManager()
scheduler = APScheduler()


def create_app():
    app = Flask(__name__)

    app.register_blueprint(auth)
    app.register_blueprint(public_messages)
    app.register_blueprint(file_uploader)
    app.register_blueprint(home_page)

    app.config.from_object("config.ConfigDefault")
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploaded_files")
    app.config["DB_PATH"] = os.path.join(app.root_path, "database", "database.db")

    sqlite3db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "log_in"
    login_manager.login_message = "You are not logged in."
    login_manager.login_message_category = "danger"
    login_manager.session_protection = "strong"

    app.logger.setLevel("DEBUG")

    scheduler.init_app(app)
    scheduler.start()

    return app


@login_manager.user_loader
def load_user(user_id):
    db = sqlite3db.get_db()
    cur = db.cursor()

    user = cur.execute("SELECT * FROM users WHERE id = ?", [user_id]).fetchone()
    if user is not None:
        return UserSQLite(user)
    return None


@scheduler.task('interval', id="remove_expired_files", hours=1)
def remove_expired_files():
    with scheduler.app.app_context():
        db = sqlite3db.get_db()
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
            os.remove(os.path.join(scheduler.app.config['UPLOAD_FOLDER'], expired_file["unique_file_name"]))

        scheduler.app.logger.debug(f"{len(expiring_files)} expired files successfully removed.")


@scheduler.task('interval', id="sync_files_with_db", hours=6)
def sync_files_with_db():
    with scheduler.app.app_context():
        db = sqlite3db.get_db()
        cur = db.cursor()

        files = os.listdir(os.path.join(scheduler.app.root_path, "uploaded_files"))
        sql = "DELETE FROM files where unique_file_name NOT IN ({})".format(','.join(['?'] * len(files)))
        cur.execute(sql, files)

        db.commit()
        db.close()

        scheduler.app.logger.debug("Uploaded files successfully synced with db.")


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000)
    #create_app().run(host="0.0.0.0", port=5000, debug=False)
