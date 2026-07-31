from flask import (
    Blueprint,
    session,
    flash,
    redirect,
    url_for,
    request,
    render_template,
)

import app.scripts.utils as utils
from app.scripts.utils import MissingReportError, MissingResourceError
from app.scripts.forms import RequiredFilesForm

scripts = Blueprint("scripts", __name__, template_folder="")
files_df = utils.return_dataframe_of_files()
photos_df = utils.return_dataframe_of_photos()
gsheets_df = utils.return_dataframe_of_gsheets()


@scripts.before_request
def require_semester_selection():
    if "school_year" not in session or "term" not in session:
        flash("Please select a semester before using this report.", category="warning")
        return redirect(url_for("main.return_index"))


@scripts.errorhandler(MissingReportError)
def handle_missing_report(error):
    year_and_semester = error.year_and_semester or f"{session['school_year']}-{session['term']}"
    return redirect(
        url_for(
            "scripts.upload_missing_report",
            report=error.report,
            year_and_semester=year_and_semester,
            next=request.path,
        )
    )


@scripts.errorhandler(FileNotFoundError)
def handle_missing_file(error):
    flash(
        f"A required file for this report is missing: {error.filename}",
        category="danger",
    )
    return redirect(url_for("main.return_index"))


@scripts.errorhandler(MissingResourceError)
def handle_missing_resource(error):
    flash(str(error), category="danger")
    return redirect(url_for("main.return_index"))


@scripts.route("/upload_missing_report", methods=["GET", "POST"])
def upload_missing_report():
    report = request.args.get("report")
    year_and_semester = request.args.get("year_and_semester")
    next_url = request.args.get("next") or url_for("main.return_index")

    required_files_form = RequiredFilesForm([report], year_and_semester)

    if required_files_form.is_satisfied:
        return redirect(next_url)

    if request.method == "POST" and required_files_form.validate_on_submit():
        saved_filenames = required_files_form.save()
        global files_df
        files_df = utils.return_dataframe_of_files()
        flash(f"Uploaded {', '.join(saved_filenames)}", category="success")
        return redirect(next_url)

    return render_template(
        "missing_report_upload.html",
        form=required_files_form.form,
        report=report,
        year_and_semester=year_and_semester,
    )


from app.scripts.assignments import routes

from app.scripts.attendance import attendance
from app.scripts.attendance.rdal_analysis import routes
from app.scripts.attendance.confirmation_sheets import routes
from app.scripts.attendance.jupiter import routes
from app.scripts.attendance.late_analysis import routes
from app.scripts.attendance.cut_analysis import routes
from app.scripts.attendance.historical_period_attd import routes
from app.scripts.attendance.CAASS import routes

from app.scripts.college_and_career import routes

from app.scripts.family_engagement import routes
from app.scripts.family_engagement.weekly_assignment import routes
from app.scripts.family_engagement.jupiter_logins_analysis import routes

from app.scripts.dataspecialist import routes
from app.scripts.dataspecialist.sy2425 import routes

from app.scripts.officialclass import routes
from app.scripts.commutes import commutes
from app.scripts.classwork import routes

from app.scripts.organization import routes
from app.scripts.organization.gsheet_classlist import routes
from app.scripts.organization.locker_assignment_letters import routes
from app.scripts.organization.metrocards import routes
from app.scripts.organization.mailinglabels import routes
from app.scripts.organization.ms_teams import routes
from app.scripts.organization.gather_teacher_input_per_student_spreadsheet import routes
from app.scripts.organization.geocoding import routes
from app.scripts.organization.ilog import routes
from app.scripts.organization.ats_ocr import routes

from app.scripts.pbis import routes
from app.scripts.pbis.smartpass import routes
from app.scripts.pbis.screener import routes
from app.scripts.pbis.phone_call_tracker import routes
from app.scripts.pbis.student_network import routes


from app.scripts.privileges import routes
from app.scripts.programming import routes
from app.scripts.programming.spring_scheduling import routes
from app.scripts.programming.ICT_sections import routes
from app.scripts.programming.jupiter import routes
from app.scripts.programming.post_summer import routes
from app.scripts.progress_towards_cte_endorsement import routes
from app.scripts.progress_towards_graduation import routes
from app.scripts.scholarship import routes
from app.scripts.scholarship.reportcards import routes
from app.scripts.scholarship.egg import routes
from app.scripts.scholarship.stars import routes


from app.scripts.summer import routes
from app.scripts.summer.attendance import routes
from app.scripts.summer.organization import routes
from app.scripts.summer.programming import routes
from app.scripts.summer.testing import routes
from app.scripts.summer.testing.regents_organization import routes
from app.scripts.summer.testing.exam_only_admits import routes

from app.scripts.surveys import routes


from app.scripts.testing import routes
