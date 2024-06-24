import os

from flask import (
    render_template,
    request,
    Blueprint,
    redirect,
    url_for,
    flash,
    current_app,
    session,
)
from werkzeug.utils import secure_filename

import app.main.forms as report_forms

import app.scripts.utils as utils
import app.scripts.update_from_jupiter as update_from_jupiter

files_df = utils.return_dataframe_of_files()
gsheets_df = utils.return_dataframe_of_gsheets()

main = Blueprint("main", __name__, template_folder="templates", static_folder="static")


@main.route("/")
def return_index():
    sections = {
        "Programming": "scripts.return_programming_reports",
        "Commutes": "scripts.return_commute_reports",
        "Attendance": "scripts.return_attendance_reports",
        "Organization": "scripts.return_organization_reports",
        "Testing": "scripts.return_testing_reports",
        "Scholarship": "scripts.return_scholarship_reports",
        "PBIS": "scripts.return_pbis_reports",
        "Privileges": "scripts.return_privileges_reports",
        "Classwork": "scripts.return_classwork_reports",
        "Progress Towards Graduation": "scripts.return_progress_towards_graduation_reports",
        "Official Class": "scripts.return_officialclass_reports",
        "Summer School": "scripts.return_summer_school_routes",
        "Graduation Certification": "graduation.return_graduation_routes",
    }
    data = {"sections": dict(sorted(sections.items()))}
    return render_template("index.html", data=data)


@main.route("/view/")
def view_all_reports():

    data = {
        "reports": [
            {
                "html": files_df.to_html(classes=["table", "table-sm"]),
                "title": "View Files",
            },
            {
                "html": gsheets_df.to_html(classes=["table", "table-sm"]),
                "title": "View Gsheets",
            },
        ]
    }
    return render_template("viewReport.html", data=data)


@main.route("/view/<report>")
def view_most_recent_report(report):
    report_path = utils.return_most_recent_report(files_df, report)
    report_df = utils.return_file_as_df(report_path)
    report_html = report_df.to_html(classes=["table", "table-sm"])
    return render_template("viewReport.html", report_html=report_html)


@main.route("/update_from_jupiter", methods=["GET", "POST"])
def return_update_from_jupiter():
    form = report_forms.JupiterUpdateForm()
    if form.validate_on_submit():
        report = form.report.data
        year_and_semester = form.year_and_semester.data
        update_from_jupiter.main(report, year_and_semester)
        flash(f"{report} successfully uploaded", category="success")
        return redirect(url_for("main.return_index"))
    else:
        return render_template("updateJupiter.html", form=form)


@main.route("/upload_gsheet", methods=["GET", "POST"])
def upload_gsheet():
    form = report_forms.GsheetForm()

    if form.validate_on_submit():
        gsheet_category = form.gsheet_category.data
        gsheet_url = form.gsheet_url.data
        year_and_semester = form.year_and_semester.data
        school_year, semester = year_and_semester.split("-")

        file_dict = {
            "gsheet_url": gsheet_url,
            "gsheet_category": gsheet_category,
            "year_and_semester": year_and_semester,
            "school_year": school_year,
            "semester": semester,
        }

        from csv import DictWriter

        # list of column names
        field_names = [
            "gsheet_url",
            "gsheet_category",
            "year_and_semester",
            "school_year",
            "semester",
        ]

        # Open CSV file in append mode
        # Create a file object for this file
        gsheet_urls_csv_filepath = os.path.join(
            current_app.root_path, f"data/gsheet_urls.csv"
        )
        with open(gsheet_urls_csv_filepath, "a") as f_object:

            # Pass the file object and a list
            # of column names to DictWriter()
            # You will get a object of DictWriter
            dictwriter_object = DictWriter(f_object, fieldnames=field_names)

            # Pass the dictionary as an argument to the Writerow()
            dictwriter_object.writerow(file_dict)

            # Close the file object
            f_object.close()

        flash(f"{gsheet_category} successfully uploaded", category="success")
        return redirect(url_for("main.upload_gsheet"))

    return render_template("uploadGsheet.html", form=form)


@main.route("/upload", methods=["GET", "POST"])
def upload_files():
    form = report_forms.FileForm()

    if form.validate_on_submit():
        f = form.file.data
        filename = secure_filename(f.filename)
        filename = filename.replace("_", "-")
        if filename.count(".") > 2:
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
        if report_name == "attendance":
            filename = f"{year_and_semester}_9999-12-31_{filename}"
        else:
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


@main.route("/setsemester", methods=["POST"])
def set_semester():
    semester = request.form.get("semester")
    school_year, term = semester.split("-")

    session["semester"] = semester
    session["school_year"] = int(school_year)
    session["term"] = int(term)
    session.permanent = True

    flash(f"Semester set to {semester}")
    return redirect(request.referrer)
