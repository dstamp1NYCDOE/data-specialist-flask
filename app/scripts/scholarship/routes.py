import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file


from app.scripts import scripts, files_df
import app.scripts.utils as utils

import app.scripts.scholarship.grade_point_trajectory as grade_point_trajectory

@scripts.route("/scholarship")
def return_scholarship_reports():
    reports = [
        {
            "report_title": "Transcript Analysis",
            "report_function": "scripts.return_transcript_analysis_reports",
            "report_description": "Reports related student transcripts",
        },
    ]
    return render_template(
        "scholarship/templates/scholarship/index.html", reports=reports
    )

@scripts.route("/scholarship/transcript_analysis")
def return_transcript_analysis_reports():
    reports = [
        {
            "report_title": "Grade Point Trajectory",
            "report_function": "scripts.return_grade_point_trajectory",
            "report_description": "Reports related to the SAT and PSAT",
            "files_needed":'1-14',
        },
    ]
    return render_template(
        "scholarship/templates/scholarship/index_transcript_analysis.html", reports=reports
    )

@scripts.route("/scholarship/transcript_analysis/grade_point_trajectory")
def return_grade_point_trajectory():
    grade_point_trajectory_pvt = grade_point_trajectory.main()

    if request.args.get('download') == 'true':
        f = BytesIO()
        grade_point_trajectory_pvt.to_excel(f, index=False)
        f.seek(0)
        download_name = f"GradePointTrajectory.xlsx"
        return send_file(f, as_attachment=True, download_name=download_name)
    else:
        grade_point_trajectory_pvt = grade_point_trajectory_pvt.style.set_table_attributes(
            'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
        )
        grade_point_trajectory_pvt_html = grade_point_trajectory_pvt.to_html(classes=["table","table-sm"])

        data = {
            'reports':[
                {'html':grade_point_trajectory_pvt_html,
                'title':'Grade Point Trajectory'
                },
            ]
        }
        return render_template("viewReport.html", data=data)