import asyncio
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

import db
from utils import login_required, roles_required


users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.get("/")
@login_required
@roles_required("admin")
async def users_list():
    users = await asyncio.to_thread(db.get_users)
    roles = await asyncio.to_thread(db.get_roles)
    return render_template("pages/users.html", users=users, roles=roles)


@users_bp.post("/<int:user_id>/role")
@login_required
@roles_required("admin")
async def change_role(user_id):
    role_id = request.form.get("ROLE_ID")
    if not role_id:
        flash("Выберите роль.", "warning")
        return redirect(url_for("users.users_list"))

    await asyncio.to_thread(db.update_user_role, user_id, role_id)
    current = session.get("user")
    await asyncio.to_thread(db.write_audit_log, current["USER_ID"], "UPDATE_ROLE", "APP_USER", user_id, "Изменена роль пользователя")
    flash("Роль пользователя обновлена.", "success")
    return redirect(url_for("users.users_list"))


@users_bp.post("/<int:user_id>/toggle")
@login_required
@roles_required("admin")
async def toggle_user(user_id):
    is_active = request.form.get("IS_ACTIVE") == "1"
    await asyncio.to_thread(db.set_user_active, user_id, is_active)
    current = session.get("user")
    await asyncio.to_thread(db.write_audit_log, current["USER_ID"], "TOGGLE_ACTIVE", "APP_USER", user_id, "Изменена активность пользователя")
    flash("Статус пользователя обновлен.", "success")
    return redirect(url_for("users.users_list"))
