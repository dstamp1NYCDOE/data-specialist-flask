import os

from flask import render_template, request, Blueprint, redirect, url_for, flash, current_app, session
from werkzeug.utils import secure_filename

import app.main.forms as report_forms
from app.scripts.programming.class_lists import generate_class_list
from app.scripts.surveys.connect_google_survey_with_class_lists import connect_google_survey_with_class_lists

import app.scripts.utils as utils
files_df = utils.return_dataframe_of_files()

main = Blueprint("main", __name__, template_folder="templates", static_folder="static")


@main.route("/")
def return_index():
    sections = {
        "Programming": "scripts.return_programming_reports",
        "Commutes": "scripts.return_commute_reports",
        "Attendance": "scripts.return_attendance_reports",
        "Organization": "scripts.return_organization_reports",
        "Testing": "scripts.return_testing_reports",
    }
    data = {"sections": dict(sorted(sections.items()))}
    return render_template("index.html", data=data)


@main.route("/view/")
def view_all_reports():
    reports_html = files_df.to_html(classes=["table", "table-sm"])
    return render_template("viewReport.html", report_html=reports_html)


@main.route("/view/<report>")
def view_most_recent_report(report):
    report_path = utils.return_most_recent_report(files_df, report)
    report_df = utils.return_file_as_df(report_path)
    report_html = report_df.to_html(classes=["table", "table-sm"])
    return render_template("viewReport.html", report_html=report_html)


@main.route("/run", methods=["GET", "POST"])
def run_script():
    if request.method == "GET":
        return redirect(url_for("main.return_index"))
    data = request.form
    report = request.form["report"]
    reports_map = {
        "scripts.programming.class_lists": generate_class_list,
        "scripts.surveys.connect_google_survey_with_class_lists": connect_google_survey_with_class_lists,
    }

    response = reports_map.get(report)(data)
    if response:
        return response
    else:
        return redirect(url_for("main.return_index"))


@main.route("/upload", methods=["GET", "POST"])
def upload_files():
    form = report_forms.FileForm()

    if form.validate_on_submit():
        f = form.file.data
        filename = secure_filename(f.filename)
        filename = filename.replace("_", "-")
        if filename.count('.')>2:
            report_name = filename.split(".")[1]
            extension = filename.split(".")[-1]
            filename = f"{report_name}.{extension}"
        else:
            report_name = filename.split(".")[0]
            extension = filename.split(".")[1]
        if "CustomReport" in report_name:
            report_name = report_name[13:-5]
            filename = f"{report_name}.{extension}"

        download_date = form.download_date.data
        year_and_semester = form.year_and_semester.data
        filename = f"{year_and_semester}_{download_date}_{filename}"

        path = os.path.join(
            current_app.root_path, f"data/{year_and_semester}/{report_name}"
        )
        isExist = os.path.exists(path)
        if not isExist:
            os.makedirs(path)
        f.save(os.path.join(path, filename))
        flash(f"{filename} successfully uploaded", category="success")
        return redirect(url_for("main.upload_files"))

    return render_template("upload.html", form=form)

@main.route("/setsemester",methods=["POST"])
def set_semester():
    semester = request.form.get("semester")
    school_year, term = semester.split('-')
    
    session['semester'] = semester
    session["school_year"] = int(school_year)
    session["term"] = int(term)

    flash(f'Semester set to {semester}')
    return redirect(request.referrer)
