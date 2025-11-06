import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, flash, redirect, url_for


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
            "report_function": "scripts.teacher_gradebook_analysis",
            "report_description": "New script to analyze teacher gradebooks with visualizations and tables",
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


from app.scripts.assignments.teacher_analysis.main import generate_gradebook_report


@scripts.route("/assignments/teacher-analysis", methods=["GET", "POST"])
def teacher_gradebook_analysis():
    """Route for teacher gradebook analysis report"""
    if request.method == "POST":
        try:
            output_format = request.form.get("output_format", "excel")
            report_scope = request.form.get("report_scope", "school")
            
            file_obj, filename = generate_gradebook_report(
                output_format=output_format,
                report_scope=report_scope
            )
            
            mimetype = (
                "application/pdf" if output_format == "pdf" 
                else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            return send_file(
                file_obj,
                as_attachment=True,
                download_name=filename,
                mimetype=mimetype
            )
        except Exception as e:
            flash(f"Error generating report: {str(e)}", "danger")
            return redirect(url_for("scripts.teacher_gradebook_analysis"))
    
    return render_template(
        "assignments/templates/assignments/teacher_analysis_form.html"
    )