from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

import db
from utils import sync_login_required


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _safe_next(default_endpoint="main.index"):
    next_url = request.form.get("next") or request.args.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return url_for(default_endpoint)


@auth_bp.get("/")
def auth_page():
    return render_template("pages/auth.html", next_url=request.args.get("next") or url_for("main.index"))


@auth_bp.post("/login")
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    user = db.get_user_by_username(username)
    if not user or not check_password_hash(user["PASSWORD_HASH"], password):
        flash("Неверный логин или пароль.", "danger")
        return redirect(url_for("auth.auth_page", next=_safe_next()))

    if not user["IS_ACTIVE"]:
        flash("Учетная запись отключена администратором.", "danger")
        return redirect(url_for("auth.auth_page"))

    session["user"] = {
        "USER_ID": user["USER_ID"],
        "USERNAME": user["USERNAME"],
        "FULL_NAME": user["FULL_NAME"],
        "ROLE_CODE": user["ROLE_CODE"],
        "ROLE_NAME": user["ROLE_NAME"],
    }
    db.write_audit_log(user["USER_ID"], "LOGIN", "APP_USER", user["USER_ID"], "Вход в систему")
    flash("Вход выполнен.", "success")
    return redirect(_safe_next())


@auth_bp.post("/register")
def register():
    full_name = request.form.get("full_name", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    password_repeat = request.form.get("password_repeat", "")

    if not full_name or not username or not password:
        flash("Заполните ФИО, логин и пароль.", "warning")
        return redirect(url_for("auth.auth_page"))

    if password != password_repeat:
        flash("Пароли не совпадают.", "warning")
        return redirect(url_for("auth.auth_page"))

    if db.get_user_by_username(username):
        flash("Пользователь с таким логином уже существует.", "warning")
        return redirect(url_for("auth.auth_page"))

    role_code = "admin" if db.count_users() == 0 else "viewer"
    user_id = db.create_user(username, password, full_name, role_code=role_code)
    db.write_audit_log(user_id, "REGISTER", "APP_USER", user_id, f"Регистрация пользователя с ролью {role_code}")

    flash("Учетная запись создана. Теперь войдите в систему.", "success")
    return redirect(url_for("auth.auth_page"))


@auth_bp.get("/logout")
@sync_login_required
def logout():
    user = session.get("user")
    if user:
        db.write_audit_log(user["USER_ID"], "LOGOUT", "APP_USER", user["USER_ID"], "Выход из системы")
    session.clear()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("auth.auth_page"))
