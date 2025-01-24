import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file


from app.scripts import scripts, files_df
import app.scripts.utils as utils


@scripts.route("/jupiter_assignments_reports")
def return_jupiter_assignments_analysis_reports():
    reports = [
        {
            "report_title": "Student Marks Errors",
            "report_function": "scripts.return_jupiter_assignments_mark_errors",
            "report_description": "Reports related student transcripts",
        },
        {
            "report_title": "TeacherAnalysis",
            "report_function": "scripts.return_jupiter_assignments_teacher_analysis",
            "report_description": "s",
        },
        {
            "report_title": "Teacher Gradebook Analysis",
            "report_function": "scripts.return_jupiter_assignments_teacher_gradebook_setup",
            "report_description": "s",
        },        
    ]
    return render_template(
        "assignments/templates/assignments/index.html", reports=reports
    )

from app.scripts.assignments.special_mark_check import special_mark_check
@scripts.route("/jupiter_assignments_reports/marks_errors")
def return_jupiter_assignments_mark_errors():
    f, download_name = special_mark_check.main()
    return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )


from app.scripts.assignments.teacher_analysis import teacher_analysis
@scripts.route("/jupiter_assignments_reports/teacher_analysis")
def return_jupiter_assignments_teacher_analysis():
    f, download_name = teacher_analysis.main()
    return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )


from app.scripts.assignments.teacher_analysis import teacher_gradebook_setup
@scripts.route("/jupiter_assignments_reports/teacher_analysis/teacher_gradebook_setup")
def return_jupiter_assignments_teacher_gradebook_setup():
    f, download_name = teacher_gradebook_setup.main()
    return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )