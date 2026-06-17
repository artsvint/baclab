import asyncio
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

import db
from utils import login_required, roles_required


patients_bp = Blueprint("patients", __name__, url_prefix="/patients")


def _patient_form_data():
    return {
        "PATIENT_LN": request.form.get("PATIENT_LN", "").strip(),
        "PATIENT_FN": request.form.get("PATIENT_FN", "").strip(),
        "PATIENT_SN": request.form.get("PATIENT_SN", "").strip(),
        "BIRTHDATE": request.form.get("BIRTHDATE") or None,
        "SNILS": request.form.get("SNILS", "").strip() or None,
        "PATIENT_VV": request.form.get("PATIENT_VV") == "on",
        "ACCOUNTING_DAY": request.form.get("ACCOUNTING_DAY") or None,
        "MDR": request.form.get("MDR") or None,
        "GDU": request.form.get("GDU") or None,
        "PATIENT_NOTES": request.form.get("PATIENT_NOTES", "").strip() or None,
    }


def _validate_patient(data):
    errors = []
    if not data["PATIENT_LN"]:
        errors.append("Укажите фамилию пациента.")
    if not data["PATIENT_FN"]:
        errors.append("Укажите имя пациента.")
    return errors


@patients_bp.get("/add")
@login_required
@roles_required("admin", "operator")
async def add_patient_form():
    dictionaries = await asyncio.to_thread(db.get_dictionaries)
    return render_template("pages/patient_form.html", patient=None, dictionaries=dictionaries, mode="add")


@patients_bp.post("/add")
@login_required
@roles_required("admin", "operator")
async def add_patient():
    data = _patient_form_data()
    errors = _validate_patient(data)
    if errors:
        for error in errors:
            flash(error, "warning")
        dictionaries = await asyncio.to_thread(db.get_dictionaries)
        return render_template("pages/patient_form.html", patient=data, dictionaries=dictionaries, mode="add")

    patient_id = await asyncio.to_thread(db.create_patient, data)
    user = session.get("user")
    await asyncio.to_thread(db.write_audit_log, user["USER_ID"], "CREATE", "PATIENT", patient_id, "Создана карточка пациента")
    flash("Пациент добавлен.", "success")
    return redirect(url_for("main.index", patient_id=patient_id))


@patients_bp.get("/<int:patient_id>/edit")
@login_required
@roles_required("admin", "operator")
async def edit_patient_form(patient_id):
    patient = await asyncio.to_thread(db.get_patient, patient_id)
    if not patient:
        flash("Пациент не найден.", "warning")
        return redirect(url_for("main.index"))
    dictionaries = await asyncio.to_thread(db.get_dictionaries)
    return render_template("pages/patient_form.html", patient=patient, dictionaries=dictionaries, mode="edit")


@patients_bp.post("/<int:patient_id>/edit")
@login_required
@roles_required("admin", "operator")
async def edit_patient(patient_id):
    data = _patient_form_data()
    errors = _validate_patient(data)
    if errors:
        for error in errors:
            flash(error, "warning")
        dictionaries = await asyncio.to_thread(db.get_dictionaries)
        data["PATIENT_ID"] = patient_id
        return render_template("pages/patient_form.html", patient=data, dictionaries=dictionaries, mode="edit")

    await asyncio.to_thread(db.update_patient, patient_id, data)
    user = session.get("user")
    await asyncio.to_thread(db.write_audit_log, user["USER_ID"], "UPDATE", "PATIENT", patient_id, "Изменена карточка пациента")
    flash("Данные пациента обновлены.", "success")
    return redirect(url_for("main.index", patient_id=patient_id))


@patients_bp.post("/<int:patient_id>/delete")
@login_required
@roles_required("admin", "operator")
async def delete_patient(patient_id):
    await asyncio.to_thread(db.delete_patient, patient_id)
    user = session.get("user")
    await asyncio.to_thread(db.write_audit_log, user["USER_ID"], "DELETE", "PATIENT", patient_id, "Пациент помечен как удаленный")
    flash("Пациент удален.", "info")
    return redirect(url_for("main.index"))
