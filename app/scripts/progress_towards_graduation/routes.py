import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, redirect, url_for, flash, session
from werkzeug.utils import secure_filename


import app.scripts.utils as utils


from app.scripts import scripts, files_df

from app.scripts.progress_towards_graduation.forms import PlaceholderForm

from app.scripts.progress_towards_graduation import analyze_progress_towards_graduation


@scripts.route("/progress_towards_graduation")
def return_progress_towards_graduation_reports():
    reports = [
        {
            "report_title": "Analyze Progress Towards Graduation",
            "report_function": "analyze_progress_towards_graduation",
            "report_description": "Analyzes the most up to date CR1.68 file uploaded to the database",
            "report_form":PlaceholderForm(meta={'title':'MissingAssignmentsForFailingOneCourseForm','type':'placeholder'}),
        },
        {
            "report_title": "Analyze Regents Max Report (CR 1_42)",
            "report_function": "analyze_regents_max",
            "report_description": "Analyzes the most up to date CR1.42 file uploaded to the database",
            "report_form":PlaceholderForm(meta={'title':'MissingAssignmentsForFailingOneCourseForm','type':'placeholder'}),
        },        
    ]
    return render_template(
        "progress_towards_graduation/templates/progress_towards_graduation/index.html", reports=reports
    )

@scripts.route("/progress_towards_graduation/<report_function>", methods=['GET','POST'])
def return_progress_towards_graduation_report(report_function):
    if request.method == 'GET':
        flash(f"Resubmit form to run {report_function}", category="warning")
        return redirect(url_for('scripts.return_progress_towards_graduation_reports'))
    
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"    

    if report_function == 'analyze_progress_towards_graduation':
        data = {
            'form':request.form
        }
        f = analyze_progress_towards_graduation.main(data)
        
        download_name = f"ProgressTowardsGraduationAnalysis.xlsx"
        return send_file(f, as_attachment=True, download_name=download_name)
    if report_function == 'analyze_regents_max':
        from app.scripts.utils_v2.stars import analyze_regents_max
        cr_1_42_filename = utils.return_most_recent_report_by_semester(files_df, "1_42", year_and_semester=year_and_semester)
        cr_1_42_df = utils.return_file_as_df(cr_1_42_filename)
        f = analyze_regents_max.main(cr_1_42_df)
        download_name = f"RegentsMaxAnalysis_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return f.to_html()
        return send_file(f, as_attachment=True, download_name=download_name)