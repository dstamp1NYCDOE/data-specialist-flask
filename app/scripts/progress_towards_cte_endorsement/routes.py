import datetime as dt
import os

from flask import (
    render_template,
    request,
    send_file,
    redirect,
    url_for,
    flash,
    session,
    current_app,
)

from app.scripts import scripts

from app.scripts.progress_towards_cte_endorsement.forms import PlaceholderForm
from app.scripts.progress_towards_cte_endorsement import analyze_cte_progress

# form field name -> on-disk report name (dashes, matching the site-wide upload convention
# in app/main/routes.py:upload_files -- return_dataframe_of_files() converts dashes back to
# underscores, so this lands on the same "1_14"/"1_30"/"3_07"/"1_49" lookup keys utils.py uses)
UPLOAD_FIELDS_TO_REPORT_NAME = {
    "cr_1_14": "1-14",
    "cr_1_30": "1-30",
    "cr_3_07": "3-07",
    "cr_1_49": "1-49",
}


def save_uploaded_report(file_obj, report_dash_name):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    download_date = dt.datetime.today().strftime("%Y-%m-%d")
    extension = file_obj.filename.rsplit(".", 1)[-1]
    filename = f"{year_and_semester}_{download_date}_{report_dash_name}.{extension}"

    path = os.path.join(
        current_app.root_path, f"data/{year_and_semester}/{report_dash_name}"
    )
    os.makedirs(path, exist_ok=True)
    file_obj.save(os.path.join(path, filename))


@scripts.route("/progress_towards_cte_endorsement")
def return_progress_towards_cte_endorsement_reports():
    reports = [
        {
            "report_title": "Analyze Progress Towards CTE Endorsement",
            "report_function": "analyze_cte_progress",
            "report_description": "Tracks each student's CTE course sequence, WBL hours, and CTE final exam status across 10th-12th grade. Uses the most recently uploaded CR1.14/CR1.30/CR3.07/CR1.49 by default -- attach fresher copies below to use those instead.",
            "report_form": PlaceholderForm(
                meta={"title": "CTEProgressForm", "type": "placeholder"}
            ),
        },
    ]
    return render_template(
        "progress_towards_cte_endorsement/templates/progress_towards_cte_endorsement/index.html",
        reports=reports,
    )


@scripts.route(
    "/progress_towards_cte_endorsement/<report_function>", methods=["GET", "POST"]
)
def return_progress_towards_cte_endorsement_report(report_function):
    if request.method == "GET":
        flash(f"Resubmit form to run {report_function}", category="warning")
        return redirect(url_for("scripts.return_progress_towards_cte_endorsement_reports"))

    for field_name, report_dash_name in UPLOAD_FIELDS_TO_REPORT_NAME.items():
        uploaded_file = request.files.get(field_name)
        if uploaded_file and uploaded_file.filename:
            save_uploaded_report(uploaded_file, report_dash_name)

    if report_function == "analyze_cte_progress":
        data = {"form": request.form}
        f = analyze_cte_progress.main(data)
        download_name = (
            f"CTEEndorsementProgress_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        return send_file(f, as_attachment=True, download_name=download_name)
