import asyncio
from flask import Blueprint, render_template, request

import db
from utils import login_required
from config import Config


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
@login_required
async def index():
    search = request.args.get("q", "").strip()
    selected_patient_id = request.args.get("patient_id", type=int)

    patients = await asyncio.to_thread(
        db.get_patients,
        search,
        Config.PATIENTS_PAGE_LIMIT,
        0
    )
    patient = None
    analyses = []

    if selected_patient_id:
        patient = await asyncio.to_thread(db.get_patient, selected_patient_id)
        analyses = await asyncio.to_thread(db.get_tests_by_patient, selected_patient_id)

    patient_count = await asyncio.to_thread(db.get_patient_count)
    analysis_count = await asyncio.to_thread(db.get_analysis_count)

    return render_template(
        "pages/index.html",
        search=search,
        patients=patients,
        selected_patient_id=selected_patient_id,
        selected_patient=patient,
        analyses=analyses,
        patient_count=patient_count,
        analysis_count=analysis_count,
    )
