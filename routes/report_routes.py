import asyncio
from flask import Blueprint, flash, redirect, render_template, url_for

import db
from utils import login_required


reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.get("/patient/<int:patient_id>")
@login_required
async def patient_report(patient_id):
    patient, tests = await asyncio.to_thread(db.get_patient_report, patient_id)
    if not patient:
        flash("Пациент не найден.", "warning")
        return redirect(url_for("main.index"))

    return render_template("pages/patient_report.html", patient=patient, tests=tests)
