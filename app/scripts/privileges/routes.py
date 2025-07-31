import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, session, url_for, redirect


from app.scripts import scripts, files_df
import app.scripts.utils.utils as utils

from app.main.forms import SelectStudentForm
from app.scripts.privileges.forms import StudentPrivilegeSummaryForm
from app.scripts.privileges.forms import AttendanceBenchmarkForm


@scripts.route("/privileges")
def return_privileges_reports():

    attendance_benchmark_form = AttendanceBenchmarkForm()
    student_privileges_summary_form = StudentPrivilegeSummaryForm()

    form_cards = [
        {
            "Title": "Attendance Benchmark",
            "Description": "Search individual student HSFI privileges",
            "form": attendance_benchmark_form,
            "route": "scripts.return_student_attendance_benchmark",
        },
        {
            "Title": "Student Privileges Lookup",
            "Description": "Search individual student HSFI privileges",
            "form": student_privileges_summary_form,
            "route": "scripts.return_student_privileges_report",
        },
        {
            "Title": "Attendance Benchmark Letters",
            "Description": "Return student letters with attendance benchmark leter",
            "form": attendance_benchmark_form,
            "route": "scripts.return_attendance_benchmark_letters",
        },        
    ]

    return render_template(
        "/privileges/templates/privileges/index.html", form_cards=form_cards
    )


from app.scripts.privileges.out_to_lunch import summary_page


@scripts.route("/privileges/student", methods=["GET", "POST"])
def return_student_privileges_report():
    if request.method == "GET":
        form = StudentPrivilegeSummaryForm()
        return redirect(url_for("scripts.return_privileges_reports"))
    else:
        form = StudentPrivilegeSummaryForm(request.form)
        f, student_name = summary_page.return_student_letter(form, request)
        download_name = f"{student_name}_Student_Privileges_report_{dt.datetime.today().strftime('%Y-%m-%d')}.pdf"
        mimetype = "application/pdf"

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype,
        )


from app.scripts.privileges.attendance_benchmark import attendance_benchmark


@scripts.route("/privileges/attendance_benchmark", methods=["GET", "POST"])
def return_student_attendance_benchmark():
    if request.method == "GET":

        return redirect(url_for("scripts.return_privileges_reports"))
    else:
        f = attendance_benchmark.return_overall_attd_file()

        download_name = (
            f"Attendance_Benchmark_{dt.datetime.today().strftime('%Y-%m-%d')}.xlsx"
        )
        mimetype = "application/pdf"

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype,
        )

from app.scripts.privileges.attendance_benchmark import attendance_benchmark_letters
@scripts.route("/privileges/attendance_benchmark_letters", methods=["GET", "POST"])
def return_attendance_benchmark_letters():
    if request.method == "GET":
        form = AttendanceBenchmarkForm()
        return redirect(url_for("scripts.return_privileges_reports"))
    else:
        form = AttendanceBenchmarkForm(request.form)
        f, student_name = attendance_benchmark_letters.return_attendance_benchmark_letters(form, request)
        download_name = f"{student_name}_Student_Privileges_report_{dt.datetime.today().strftime('%Y-%m-%d')}.pdf"
        mimetype = "application/pdf"

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype,
        )