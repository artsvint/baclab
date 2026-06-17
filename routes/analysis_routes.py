import asyncio
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

import db
from utils import login_required, roles_required


analysis_bp = Blueprint("analysis", __name__, url_prefix="/analysis")


DRUG_SHORT_NAMES = [
    "S", "H", "R", "E", "Km", "Eto", "Ofx", "Cm", "Am", "PAS", "Cs", "Z",
    "Lfx", "Mfx", "Lzd", "K", "TCH", "Na", "NR", "Mfx1", "Bdq", "Dlm", "CFZ"
]


def _test_form_data(patient_id=None):
    user = session.get("user") or {}
    return {
        "PATIENT_ID": patient_id or request.form.get("PATIENT_ID"),
        "LAB_ID": request.form.get("LAB_ID") or None,
        "MU_ID": request.form.get("MU_ID") or None,
        "MU_OFFICE_ID": request.form.get("MU_OFFICE_ID") or None,
        "MATTER_ORIGIN": request.form.get("MATTER_ORIGIN") or None,
        "TEST_NUMBER": request.form.get("TEST_NUMBER", "").strip(),
        "TEST_DATE": request.form.get("TEST_DATE") or None,
        "TEST_CODE": request.form.get("TEST_CODE") or None,
        "MATTER_ID": request.form.get("MATTER_ID") or None,
        "BACT_EXCRETION": request.form.get("BACT_EXCRETION") or None,
        "TEST_RESULT": request.form.get("TEST_RESULT") or None,
        "GROWTH_DAY": request.form.get("GROWTH_DAY") or None,
        "GROWTH_RATE": request.form.get("GROWTH_RATE", "").strip() or None,
        "ABG_DATE": request.form.get("ABG_DATE") or None,
        "TEST_NOTES": request.form.get("TEST_NOTES", "").strip() or None,
        "USER_ID": user.get("USER_ID"),
    }


def _abg_form_data():
    result = {}
    for short_name in DRUG_SHORT_NAMES:
        result[short_name] = request.form.get(f"ABG_{short_name}") or None
    return result


def _validate_test(data):
    errors = []
    if not data["PATIENT_ID"]:
        errors.append("Не выбран пациент.")
    if not data["TEST_NUMBER"]:
        errors.append("Укажите номер анализа.")
    if not data["TEST_DATE"]:
        errors.append("Укажите дату анализа.")
    if not data["TEST_CODE"]:
        errors.append("Выберите исследование.")
    if str(data.get("MU_ID") or "") == "13812" and not data.get("MU_OFFICE_ID"):
        errors.append("Для ККПТД № 1 выберите подразделение.")
    if str(data.get("MU_ID") or "") != "13812":
        data["MU_OFFICE_ID"] = None
    return errors


@analysis_bp.get("/add/<int:patient_id>")
@login_required
@roles_required("admin", "operator")
async def add_test_form(patient_id):
    patient = await asyncio.to_thread(db.get_patient, patient_id)
    if not patient:
        flash("Пациент не найден.", "warning")
        return redirect(url_for("main.index"))

    dictionaries = await asyncio.to_thread(db.get_dictionaries)
    return render_template(
        "pages/test_form.html",
        mode="add",
        patient=patient,
        test=None,
        abg_results={},
        dictionaries=dictionaries,
        drug_short_names=DRUG_SHORT_NAMES,
        test_values=[],
    )


@analysis_bp.post("/add/<int:patient_id>")
@login_required
@roles_required("admin", "operator")
async def add_test(patient_id):
    data = _test_form_data(patient_id)
    abg_data = _abg_form_data()
    errors = _validate_test(data)
    patient = await asyncio.to_thread(db.get_patient, patient_id)
    dictionaries = await asyncio.to_thread(db.get_dictionaries)
    test_values = await asyncio.to_thread(db.get_test_values_by_test_code, data["TEST_CODE"]) if data.get("TEST_CODE") else []

    if errors:
        for error in errors:
            flash(error, "warning")
        return render_template(
            "pages/test_form.html",
            mode="add",
            patient=patient,
            test=data,
            abg_results={k: {"RESISTANCE_ID": v} for k, v in abg_data.items()},
            dictionaries=dictionaries,
            drug_short_names=DRUG_SHORT_NAMES,
            test_values=test_values,
        )

    test_id = await asyncio.to_thread(db.create_test, data, abg_data)
    user = session.get("user")
    await asyncio.to_thread(db.write_audit_log, user["USER_ID"], "CREATE", "TEST", test_id, "Создан анализ")
    flash("Анализ добавлен.", "success")
    return redirect(url_for("main.index", patient_id=patient_id))


@analysis_bp.get("/<int:test_id>/edit")
@login_required
@roles_required("admin", "operator")
async def edit_test_form(test_id):
    test = await asyncio.to_thread(db.get_test, test_id)
    if not test:
        flash("Анализ не найден.", "warning")
        return redirect(url_for("main.index"))

    patient = await asyncio.to_thread(db.get_patient, test["PATIENT_ID"])
    dictionaries = await asyncio.to_thread(db.get_dictionaries)
    abg_results = await asyncio.to_thread(db.get_abg_results, test_id)
    test_values = await asyncio.to_thread(db.get_test_values_by_test_code, test["TEST_CODE"])

    return render_template(
        "pages/test_form.html",
        mode="edit",
        patient=patient,
        test=test,
        abg_results=abg_results,
        dictionaries=dictionaries,
        drug_short_names=DRUG_SHORT_NAMES,
        test_values=test_values,
    )


@analysis_bp.post("/<int:test_id>/edit")
@login_required
@roles_required("admin", "operator")
async def edit_test(test_id):
    old_test = await asyncio.to_thread(db.get_test, test_id)
    if not old_test:
        flash("Анализ не найден.", "warning")
        return redirect(url_for("main.index"))

    data = _test_form_data(old_test["PATIENT_ID"])
    abg_data = _abg_form_data()
    errors = _validate_test(data)
    patient = await asyncio.to_thread(db.get_patient, old_test["PATIENT_ID"])
    dictionaries = await asyncio.to_thread(db.get_dictionaries)
    test_values = await asyncio.to_thread(db.get_test_values_by_test_code, data["TEST_CODE"]) if data.get("TEST_CODE") else []

    if errors:
        for error in errors:
            flash(error, "warning")
        data["TEST_ID"] = test_id
        return render_template(
            "pages/test_form.html",
            mode="edit",
            patient=patient,
            test=data,
            abg_results={k: {"RESISTANCE_ID": v} for k, v in abg_data.items()},
            dictionaries=dictionaries,
            drug_short_names=DRUG_SHORT_NAMES,
            test_values=test_values,
        )

    await asyncio.to_thread(db.update_test, test_id, data, abg_data)
    user = session.get("user")
    await asyncio.to_thread(db.write_audit_log, user["USER_ID"], "UPDATE", "TEST", test_id, "Изменен анализ")
    flash("Анализ обновлен.", "success")
    return redirect(url_for("main.index", patient_id=old_test["PATIENT_ID"]))


@analysis_bp.post("/<int:test_id>/delete")
@login_required
@roles_required("admin", "operator")
async def delete_test(test_id):
    test = await asyncio.to_thread(db.get_test, test_id)
    if not test:
        flash("Анализ не найден.", "warning")
        return redirect(url_for("main.index"))

    await asyncio.to_thread(db.delete_test, test_id)
    user = session.get("user")
    await asyncio.to_thread(db.write_audit_log, user["USER_ID"], "DELETE", "TEST", test_id, "Анализ помечен как удаленный")
    flash("Анализ удален.", "info")
    return redirect(url_for("main.index", patient_id=test["PATIENT_ID"]))


@analysis_bp.get("/test-values/<int:test_code_id>")
@login_required
async def test_values(test_code_id):
    values = await asyncio.to_thread(db.get_test_values_by_test_code, test_code_id)
    return jsonify(values)


@analysis_bp.get("/mu-offices/<int:mu_id>")
@login_required
async def mu_offices(mu_id):
    if mu_id != 13812:
        return jsonify([])
    offices = await asyncio.to_thread(db.get_mu_offices, mu_id)
    return jsonify(offices)
