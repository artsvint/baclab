import asyncio

import pymysql
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

import db
from utils import login_required, roles_required


references_bp = Blueprint("references", __name__, url_prefix="/references")


@references_bp.get("/")
@login_required
@roles_required("admin")
async def references_page():
    tables = await asyncio.to_thread(db.get_reference_table_list)
    selected_key = request.args.get("table") or (tables[0]["key"] if tables else None)

    if selected_key and not db.get_reference_config(selected_key):
        flash("Выбранный справочник не найден.", "warning")
        selected_key = tables[0]["key"] if tables else None

    selected_config = db.get_reference_config(selected_key) if selected_key else None
    rows = []
    options = {}

    if selected_config:
        rows = await asyncio.to_thread(db.get_reference_rows, selected_key)
        options = await asyncio.to_thread(db.get_reference_form_options, selected_key)

    return render_template(
        "pages/references.html",
        tables=tables,
        selected_key=selected_key,
        selected_config=selected_config,
        rows=rows,
        options=options,
    )


@references_bp.post("/<table_key>/add")
@login_required
@roles_required("admin")
async def add_reference(table_key):
    try:
        record_id = await asyncio.to_thread(db.create_reference_row, table_key, request.form)
        user = session.get("user")
        await asyncio.to_thread(db.write_audit_log, user["USER_ID"], "CREATE_REFERENCE", table_key, record_id, "Создана запись справочника")
        flash("Запись справочника создана.", "success")
    except ValueError as error:
        flash(str(error), "warning")
    except pymysql.err.IntegrityError as error:
        flash(f"Не удалось создать запись: нарушено ограничение БД. {error}", "danger")
    return redirect(url_for("references.references_page", table=table_key))


@references_bp.post("/<table_key>/<int:record_id>/edit")
@login_required
@roles_required("admin")
async def edit_reference(table_key, record_id):
    try:
        await asyncio.to_thread(db.update_reference_row, table_key, record_id, request.form)
        user = session.get("user")
        await asyncio.to_thread(db.write_audit_log, user["USER_ID"], "UPDATE_REFERENCE", table_key, record_id, "Изменена запись справочника")
        flash("Запись справочника обновлена.", "success")
    except ValueError as error:
        flash(str(error), "warning")
    except pymysql.err.IntegrityError as error:
        flash(f"Не удалось обновить запись: нарушено ограничение БД. {error}", "danger")
    return redirect(url_for("references.references_page", table=table_key))


@references_bp.post("/<table_key>/<int:record_id>/delete")
@login_required
@roles_required("admin")
async def delete_reference(table_key, record_id):
    try:
        await asyncio.to_thread(db.delete_reference_row, table_key, record_id)
        user = session.get("user")
        await asyncio.to_thread(db.write_audit_log, user["USER_ID"], "DELETE_REFERENCE", table_key, record_id, "Удалена запись справочника")
        flash("Запись справочника удалена.", "info")
    except pymysql.err.IntegrityError:
        flash("Запись нельзя удалить: она уже используется в пациентах, анализах или связанных справочниках.", "danger")
    except ValueError as error:
        flash(str(error), "warning")
    return redirect(url_for("references.references_page", table=table_key))
