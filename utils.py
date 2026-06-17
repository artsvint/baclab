from functools import wraps
from flask import flash, redirect, request, session, url_for


def current_user():
    return session.get("user")


def _login_redirect():
    next_url = request.full_path if request.query_string else request.path
    return redirect(url_for("auth.auth_page", next=next_url))


def login_required(view):
    @wraps(view)
    async def wrapped_view(*args, **kwargs):
        if not current_user():
            flash("Для доступа к системе необходимо войти.", "warning")
            return _login_redirect()
        return await view(*args, **kwargs)
    return wrapped_view


def roles_required(*role_codes):
    def decorator(view):
        @wraps(view)
        async def wrapped_view(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Для выполнения действия необходимо войти.", "warning")
                return _login_redirect()
            if user.get("ROLE_CODE") not in role_codes:
                flash("Недостаточно прав для выполнения действия.", "danger")
                return redirect(url_for("main.index"))
            return await view(*args, **kwargs)
        return wrapped_view
    return decorator


def sync_login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not current_user():
            flash("Для доступа к системе необходимо войти.", "warning")
            return _login_redirect()
        return view(*args, **kwargs)
    return wrapped_view


def sync_roles_required(*role_codes):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Для выполнения действия необходимо войти.", "warning")
                return _login_redirect()
            if user.get("ROLE_CODE") not in role_codes:
                flash("Недостаточно прав для выполнения действия.", "danger")
                return redirect(url_for("main.index"))
            return view(*args, **kwargs)
        return wrapped_view
    return decorator


def can_edit():
    user = current_user()
    return bool(user and user.get("ROLE_CODE") in ("admin", "operator"))


def can_admin():
    user = current_user()
    return bool(user and user.get("ROLE_CODE") == "admin")
