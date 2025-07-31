import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file


from app.scripts import scripts, files_df
import app.scripts.utils as utils

import app.scripts.scholarship.grade_point_trajectory as grade_point_trajectory
import app.scripts.scholarship.jupiter_grades_benchmark_analysis as jupiter_grades_benchmark_analysis
import app.scripts.scholarship.jupiter_grades_teacher_analysis as jupiter_grades_teacher_analysis


@scripts.route("/scholarship")
def return_scholarship_reports():
    reports = [
        {
            "report_title": "Transcript Analysis",
            "report_function": "scripts.return_transcript_analysis_reports",
            "report_description": "Reports related student transcripts",
        },
        {
            "report_title": "STARS Reports",
            "report_function": "scripts.return_scholarship_stars_report",
            "report_description": "Return STARS reports",
        },
        {
            "report_title": "Jupiter Grades Analysis",
            "report_function": "scripts.return_jupiter_analysis_reports",
            "report_description": "Reports based on Jupiter Grades",
        },
        {
            "report_title": "Report Card Reports",
            "report_function": "scripts.return_reportcard_reports",
            "report_description": "Report card reports",
        },
        {
            "report_title": "EGG Reports",
            "report_function": "scripts.return_egg_reports",
            "report_description": "Report card reports",
        },
    ]
    return render_template(
        "scholarship/templates/scholarship/index.html", reports=reports
    )


@scripts.route("/scholarship/jupiter")
def return_jupiter_analysis_reports():
    reports = [
        {
            "report_title": "Jupiter Grades Benchmark Analysis",
            "report_function": "scripts.return_jupiter_grades_benchmark_analysis",
            "report_description": "Determine if students are meeting grades benchmark based on Jupiter",
        },
        {
            "report_title": "Jupiter Grades Trajectory",
            "report_function": "scripts.return_jupiter_grades_trajectory",
            "report_description": "Determine student grade trajectory for school year in Jupiter",
        },
        {
            "report_title": "Jupiter Grades Teacher Analysis",
            "report_function": "scripts.return_jupiter_grades_teacher_analysis",
            "report_description": "Analyze grades by teacher",
        },
        {
            "report_title": "Jupiter Grades Senior Checkup",
            "report_function": "scripts.return_jupiter_grads_senior_checkup",
            "report_description": "Analyze jupiter grades for seniors by teacher",
        },
        {
            "report_title": "Jupiter Grades Student Checkup By Cohort",
            "report_function": "scripts.return_jupiter_grades_students_checkup_by_counselor",
            "report_description": "Analyze jupiter grades by cohort",
        },
        {
            "report_title": "Jupiter Grades Student Checkup By Teacher",
            "report_function": "scripts.return_jupiter_grades_students_checkup_by_teacher",
            "report_description": "Analyze jupiter grades by teacher",
        },
        {
            "report_title": "Jupiter Grades Student Checkup By Department",
            "report_function": "scripts.return_jupiter_grades_students_checkup_by_dept",
            "report_description": "Analyze jupiter grades by Department",
        },
    ]
    return render_template(
        "scholarship/templates/scholarship/index_transcript_analysis.html",
        reports=reports,
    )


@scripts.route("/scholarship/transcript_analysis")
def return_transcript_analysis_reports():
    reports = [
        {
            "report_title": "Grade Point Trajectory",
            "report_function": "scripts.return_grade_point_trajectory",
            "report_description": "Reports related to the SAT and PSAT",
            "files_needed": "1-14",
        },
    ]
    return render_template(
        "scholarship/templates/scholarship/index_transcript_analysis.html",
        reports=reports,
    )


@scripts.route("/scholarship/transcript_analysis/grade_point_trajectory")
def return_grade_point_trajectory():
    grade_point_trajectory_pvt = grade_point_trajectory.main()

    if request.args.get("download") == "true":
        f = BytesIO()
        grade_point_trajectory_pvt.to_excel(f, index=False)
        f.seek(0)
        download_name = f"GradePointTrajectory.xlsx"
        return send_file(f, as_attachment=True, download_name=download_name)
    else:
        grade_point_trajectory_pvt = grade_point_trajectory_pvt.style.set_table_attributes(
            'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
        )
        grade_point_trajectory_pvt_html = grade_point_trajectory_pvt.to_html(
            classes=["table", "table-sm"]
        )

        data = {
            "reports": [
                {
                    "html": grade_point_trajectory_pvt_html,
                    "title": "Grade Point Trajectory",
                },
            ]
        }
        return render_template("viewReport.html", data=data)


from app.scripts.scholarship.jupiter import senior_checkup


@scripts.route("/scholarship/jupiter/senior_checkup")
def return_jupiter_grads_senior_checkup():
    pvt = senior_checkup.main()

    if request.args.get("download") == "true":
        f = BytesIO()
        pvt.to_excel(f, index=False)
        f.seek(0)
        download_name = f"JupiterGradesSeniorCheckup.xlsx"
        return send_file(f, as_attachment=True, download_name=download_name)
    else:
        pvt = pvt.style.set_table_attributes(
            'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
        )
        pvt_html = pvt.to_html(classes=["table", "table-sm"])

        data = {
            "reports": [
                {
                    "html": pvt_html,
                    "title": "Jupiter Grades Senior Checkup",
                },
            ]
        }
        return render_template("viewReport.html", data=data)


from app.scripts.scholarship.jupiter import semester_trajectory


@scripts.route("/scholarship/jupiter/grade_trajectory")
def return_jupiter_grades_trajectory():
    pvt = semester_trajectory.main()

    if request.args.get("download") == "true":
        f = BytesIO()
        pvt.to_excel(f, index=False)
        f.seek(0)
        download_name = f"JupiterGradesSemesterTrajectory.xlsx"
        return send_file(f, as_attachment=True, download_name=download_name)
    else:
        pvt = pvt.style.set_table_attributes(
            'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
        )
        pvt_html = pvt.to_html(classes=["table", "table-sm"])

        data = {
            "reports": [
                {
                    "html": pvt_html,
                    "title": "Jupiter Grades Benchmark Analysis",
                },
            ]
        }
        return render_template("viewReport.html", data=data)


@scripts.route("/scholarship/jupiter/grades_benchmark_analysis")
def return_jupiter_grades_benchmark_analysis():
    jupiter_grades_benchmark_analysis_pvt = jupiter_grades_benchmark_analysis.main()

    if request.args.get("download") == "true":
        f = BytesIO()
        jupiter_grades_benchmark_analysis_pvt.to_excel(f, index=False)
        f.seek(0)
        download_name = f"JupiterGradesBenchmarkAnalysis.xlsx"
        return send_file(f, as_attachment=True, download_name=download_name)
    else:
        jupiter_grades_benchmark_analysis_pvt = jupiter_grades_benchmark_analysis_pvt.style.set_table_attributes(
            'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
        )
        jupiter_grades_benchmark_analysis_pvt_html = (
            jupiter_grades_benchmark_analysis_pvt.to_html(classes=["table", "table-sm"])
        )

        data = {
            "reports": [
                {
                    "html": jupiter_grades_benchmark_analysis_pvt_html,
                    "title": "Jupiter Grades Benchmark Analysis",
                },
            ]
        }
        return render_template("viewReport.html", data=data)


@scripts.route("/scholarship/jupiter/grades_teacher_analysis")
def return_jupiter_grades_teacher_analysis():
    jupiter_grades_teacher_analysis_pvt = jupiter_grades_teacher_analysis.main()

    if request.args.get("download") == "true":
        f = BytesIO()
        jupiter_grades_teacher_analysis_pvt.to_excel(f, index=False)
        f.seek(0)
        download_name = f"JupiterGradesTeacherAnalysis.xlsx"
        return send_file(f, as_attachment=True, download_name=download_name)
    else:
        jupiter_grades_teacher_analysis_pvt = jupiter_grades_teacher_analysis_pvt.style.set_table_attributes(
            'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
        )
        jupiter_grades_teacher_analysis_pvt_html = (
            jupiter_grades_teacher_analysis_pvt.to_html(classes=["table", "table-sm"])
        )

        data = {
            "reports": [
                {
                    "html": jupiter_grades_teacher_analysis_pvt_html,
                    "title": "Jupiter Grades Benchmark Analysis",
                },
            ]
        }
        return render_template("viewReport.html", data=data)


from app.scripts.scholarship.jupiter.student_checkup_by_counselor import (
    main as jupiter_grades_student_checkup_by_counselor,
)


@scripts.route("/scholarship/jupiter/student_checkup_by_counselor")
def return_jupiter_grades_students_checkup_by_counselor():
    f, download_name = jupiter_grades_student_checkup_by_counselor()
    return send_file(f, as_attachment=True, download_name=download_name)


from app.scripts.scholarship.jupiter.student_checkup_by_teacher import (
    main as jupiter_grades_student_checkup_by_teacher,
)


@scripts.route("/scholarship/jupiter/student_checkup_by_teacher")
def return_jupiter_grades_students_checkup_by_teacher():
    f, download_name = jupiter_grades_student_checkup_by_teacher()
    return send_file(f, as_attachment=True, download_name=download_name)


from app.scripts.scholarship.jupiter.student_checkup_by_dept import (
    main as jupiter_grades_student_checkup_by_dept,
)


@scripts.route("/scholarship/jupiter/student_checkup_by_dept")
def return_jupiter_grades_students_checkup_by_dept():
    f, download_name = jupiter_grades_student_checkup_by_dept()
    return send_file(f, as_attachment=True, download_name=download_name)
