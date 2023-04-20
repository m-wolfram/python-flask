from datetime import datetime
from flask import Blueprint, render_template, request, flash, abort, current_app, redirect, jsonify, url_for, g
from flask_login import current_user, login_required
from database import sqlite3db


public_messages = Blueprint("public_messages", __name__, static_folder="static", template_folder="templates")


@public_messages.route("/leave_message", methods=["GET", "POST"])
def leave_message():
    db = sqlite3db.get_db()
    cur = db.cursor()

    if request.method == "GET":
        prev_text = request.args.get("msg", None)
        return render_template("public_messages/leave_message.html", msg_text=prev_text)
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
                return redirect(url_for("public_messages.leave_message"))
            if len(msg_text) == 0:
                flash("You did not enter message text.", category="danger")
            return redirect(request.url)
        else:
            abort(401)


@public_messages.route("/leave_message/posts/parameters", methods=["GET"])
def leave_message_posts_parameters():
    db = sqlite3db.get_db()
    cur = db.cursor()

    posts_count = cur.execute("SELECT COUNT(*) count from Posts").fetchone()["count"]

    return jsonify({
        "posts_count": posts_count,
        "posts_per_page": current_app.config["POSTS_PER_PAGE"]
    })


@public_messages.route("/leave_message/posts/load_posts", methods=["GET"])
def leave_message_load_posts():
    db = sqlite3db.get_db()
    cur = db.cursor()

    page = request.args.get("page", "1", int)
    post_index = request.args.get("index", None, int)

    posts_per_page = current_app.config["POSTS_PER_PAGE"]
    page_offset = (page - 1) * posts_per_page

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
        limit = posts_per_page

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
    """, page_posts_query_data).fetchall()  # TODO: split
    return render_template("elements/posts.html", posts=page_posts)


@public_messages.route("/leave_message/posts/delete/<int:post_id>", methods=["DELETE"])
@login_required
def leave_message_delete_post(post_id):
    db = sqlite3db.get_db()
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


@public_messages.route("/leave_message/posts/like", methods=["GET"])
def leave_message_like():
    """
    TODO?:
    split into 3 requests:
        insert like (PUT),
        delete like (DELETE),
        get likes (GET).
    """

    db = sqlite3db.get_db()
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


@public_messages.teardown_request
def teardown_db(error):
    if hasattr(g, "db"):
        g.db.close()


@public_messages.errorhandler(401)
def unauthorized(error):
    return render_template("errors/401.html"), 401


@public_messages.errorhandler(403)
def forbidden(error):
    return render_template("errors/403.html"), 403


@public_messages.errorhandler(404)
def not_found(error):
    return render_template("errors/404.html"), 404


@public_messages.errorhandler(413)
def request_entity_too_large(error):
    return render_template("errors/413.html"), 413
