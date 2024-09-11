import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file


import app.scripts.utils as utils


from app.scripts import scripts, files_df
import app.scripts.attendance.attendance_tiers as attendance_tiers
import app.scripts.attendance.process_RATR as process_RATR
import app.scripts.attendance.jupiter_attd_by_teacher as jupiter_attd_by_teacher
import app.scripts.attendance.jupiter_attd_by_student as jupiter_attd_by_student
import app.scripts.attendance.jupiter_attd_benchmark_analysis as jupiter_attd_benchmark_analysis
import app.scripts.attendance.jupiter_attd_summary_by_class as jupiter_attd_summary_by_class
import app.scripts.attendance.jupiter_attd_teacher_completion as jupiter_attd_teacher_completion
import app.scripts.attendance.jupiter_attd_patterns as jupiter_attd_patterns

import app.scripts.attendance.daily_attd_predictor as daily_attd_predictor

from app.scripts.attendance.forms import JupiterCourseSelectForm


@scripts.route("/attendance")
def return_attendance_reports():
    reports = [
        {
            "report_title": "Student Attendance Analysis",
            "report_function": "scripts.return_RATR_analysis",
            "report_description": "Analyze student daily attendance using ATS report RATR",
        },
        {
            "report_title": "RDAL Analysis",
            "report_function": "scripts.return_rdal_analysis_spreadsheet",
            "report_description": "Analysis daily RDAL file and return file to upload",
        },
        {
            "report_title": "Student Attendance Tiers",
            "report_function": "scripts.return_attd_tiers_from_RATR",
            "report_description": "Return Student Attendance Tiers using ATS report RATR",
        },
        {
            "report_title": "Jupiter Attd Analysis By Teacher",
            "report_function": "scripts.return_jupiter_attd_analysis_by_teacher",
            "report_description": "Analyze student Jupiter attendance by teacher",
        },
        {
            "report_title": "Jupiter Attd Analysis By Student",
            "report_function": "scripts.return_jupiter_attd_analysis_by_student",
            "report_description": "Analyze student Jupiter attendance by student",
        },
        {
            "report_title": "Jupiter Attd Benchmark Analysis By Student",
            "report_function": "scripts.return_jupiter_attd_benchmark_analysis",
            "report_description": "Analyze student Jupiter attendance by student and return benchmark",
        },
        {
            "report_title": "Jupiter Period Attendance Completion By Teacher",
            "report_function": "scripts.return_teacher_jupiter_attd",
            "report_description": "Return Jupiter Attendance Completion by teacher for current term",
        },
        {
            "report_title": "Jupiter Attendance Patterns",
            "report_function": "scripts.return_jupiter_attd_patterns",
            "report_description": "Return Jupiter Attendance Patterns",
        },
        {
            "report_title": "Daily Attd Predictor",
            "report_function": "scripts.return_daily_attd_predictor",
            "report_description": "Return Daily Attd Predictor",
        },
        {
            "report_title": "Cut Analysis",
            "report_function": "scripts.return_cut_analysis",
            "report_description": "Return Cut Analysis",
        },
    ]
    return render_template(
        "attendance/templates/attendance/index.html", reports=reports
    )


@scripts.route("/attendance/tiers", methods=["GET", "POST"])
def return_attd_tiers_from_RATR():
    RATR_filename = utils.return_most_recent_report(files_df, "RATR")
    RATR_df = utils.return_file_as_df(RATR_filename)
    df_dict = attendance_tiers.main(RATR_df)

    report_name = "Student Attd Tiers"
    if request.args.get("download") == "true":
        f = BytesIO()
        writer = pd.ExcelWriter(f)
        for sheet_name, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        writer.close()
        f.seek(0)
        download_name = f"{report_name.replace(' ','')}.xlsx"
        return send_file(f, as_attachment=True, download_name=download_name)
    else:
        df = df_dict["ytd"]
        df = df.style.set_table_attributes(
            'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
        )
        df_html = df.to_html(classes=["table", "table-sm"])

        data = {
            "reports": [
                {
                    "html": df_html,
                    "title": report_name,
                },
            ]
        }
        return render_template("viewReport.html", data=data)


@scripts.route("/attendance/teacher_jupiter_attd", methods=["GET", "POST"])
def return_teacher_jupiter_attd():
    df = jupiter_attd_teacher_completion.main()
    report_name = "Jupiter Period Attendance Completition By Teacher"
    if request.args.get("download") == "true":
        f = BytesIO()
        df.to_excel(f, index=False)
        f.seek(0)
        download_name = f"{report_name.replace(' ','')}.xlsx"
        return send_file(f, as_attachment=True, download_name=download_name)
    else:
        df = df.style.set_table_attributes(
            'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
        )
        df_html = df.to_html(classes=["table", "table-sm"])

        data = {
            "reports": [
                {
                    "html": df_html,
                    "title": report_name,
                },
            ]
        }
        return render_template("viewReport.html", data=data)


@scripts.route("/attendance/daily_attd_predictor")
def return_daily_attd_predictor():
    RATR_filename = utils.return_most_recent_report(files_df, "RATR")
    RATR_df = utils.return_file_as_df(RATR_filename)

    output_df = daily_attd_predictor.main(RATR_df)

    output_df = output_df.style.set_table_attributes(
        'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
    )
    data = {
        "report_title": "Daily Attd Predictor",
        "dfs": [
            output_df.to_html(),
        ],
    }
    template_str = "templates/scripts/dataframes_generic.html"
    return render_template(template_str, data=data)


@scripts.route("/attendance/RATR_analysis")
def return_RATR_analysis():
    RATR_filename = utils.return_most_recent_report(files_df, "RATR")
    RATR_df = utils.return_file_as_df(RATR_filename)
    RATR_df = process_RATR.clean(RATR_df)

    student_pvt = process_RATR.student_attd_by_weekday(RATR_df)
    student_pvt = student_pvt.style.set_table_attributes(
        'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
    )

    student_by_month_pvt = process_RATR.student_attd_by_month(RATR_df)
    student_by_month_pvt = student_by_month_pvt.style.set_table_attributes(
        'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
    )

    overall_by_month_pvt = process_RATR.overall_attd_by_month(RATR_df)
    overall_by_month_pvt = overall_by_month_pvt.style.set_table_attributes(
        'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
    )

    overall_pvt = process_RATR.overall_attd_by_weekday(RATR_df)
    overall_pvt = overall_pvt.style.set_table_attributes(
        'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
    )

    data = {
        "report_title": "RATR Analysis",
        "dfs": [
            student_pvt.to_html(),
            overall_pvt.to_html(),
            overall_by_month_pvt.to_html(),
            student_by_month_pvt.to_html(),
        ],
    }
    template_str = "templates/scripts/dataframes_generic.html"
    return render_template(template_str, data=data)


@scripts.route("/attendance/jupiter/by_teacher")
def return_jupiter_attd_analysis_by_teacher():
    df = jupiter_attd_by_teacher.main()
    report_name = "Jupiter Period Attendance Analysis By Teacher"
    if request.args.get("download") == "true":
        f = BytesIO()
        df.to_excel(f, index=False)
        f.seek(0)
        download_name = f"{report_name.replace(' ','')}.xlsx"
        return send_file(f, as_attachment=True, download_name=download_name)
    else:
        df = df.style.set_table_attributes(
            'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
        )
        df_html = df.to_html(classes=["table", "table-sm"])

        data = {
            "reports": [
                {
                    "html": df_html,
                    "title": report_name,
                },
            ]
        }
        return render_template("viewReport.html", data=data)


@scripts.route("/attendance/jupiter/patterns")
def return_jupiter_attd_patterns():
    df = jupiter_attd_patterns.main()
    report_name = "Jupiter Attendance Patterns"
    if request.args.get("download") == "true":
        f = BytesIO()
        df.to_excel(f, index=False)
        f.seek(0)
        download_name = f"{report_name.replace(' ','')}.xlsx"
        return send_file(f, as_attachment=True, download_name=download_name)
    else:
        df = df.style.set_table_attributes(
            'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
        )
        df_html = df.to_html(classes=["table", "table-sm"])

        data = {
            "reports": [
                {
                    "html": df_html,
                    "title": report_name,
                },
            ]
        }
        return render_template("viewReport.html", data=data)


@scripts.route("/attendance/jupiter/by_student")
def return_jupiter_attd_analysis_by_student():
    df = jupiter_attd_by_student.main()
    report_name = "Jupiter Period Attendance Analysis By Student"
    if request.args.get("download") == "true":
        f = BytesIO()
        df.to_excel(f, index=False)
        f.seek(0)
        download_name = f"{report_name.replace(' ','')}.xlsx"
        return send_file(f, as_attachment=True, download_name=download_name)
    else:
        df = df.style.set_table_attributes(
            'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
        )
        df_html = df.to_html(classes=["table", "table-sm"])

        data = {
            "reports": [
                {
                    "html": df_html,
                    "title": report_name,
                },
            ]
        }
        return render_template("viewReport.html", data=data)


@scripts.route("/attendance/jupiter/student_benchmark_analysis")
def return_jupiter_attd_benchmark_analysis():
    data = {
        "present": 0.9,
        "on_time": 0.8,
    }
    df = jupiter_attd_benchmark_analysis.main(data)
    report_name = "Jupiter Period Attendance Benchmark Analysis By Student"
    if request.args.get("download") == "true":
        f = BytesIO()
        df.to_excel(f, index=False)
        f.seek(0)
        download_name = f"{report_name.replace(' ','')}.xlsx"
        return send_file(f, as_attachment=True, download_name=download_name)
    else:
        df = df.style.set_table_attributes(
            'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
        )
        df_html = df.to_html(classes=["table", "table-sm"])

        data = {
            "reports": [
                {
                    "html": df_html,
                    "title": report_name,
                },
            ]
        }
        return render_template("viewReport.html", data=data)


import app.scripts.attendance.cut_analysis.main as cut_analysis


@scripts.route("/attendance/class_report/", methods=["GET", "POST"])
def generate_jupiter_attendance_class_report():
    if request.method == "GET":
        data = {"form": JupiterCourseSelectForm()}
        return render_template(
            "attendance/templates/attendance/attendance_by_class.html", data=data
        )
    else:
        course_and_section = request.form.get("course_and_section")
        course, section = course_and_section.split("/")

        data = {
            "Course": course,
            "Section": section,
        }
        df = jupiter_attd_summary_by_class.main(data)

        df = df.style.set_table_attributes(
            'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
        )
        df_html = df.to_html(classes=["table", "table-sm"])

        report_name = f"{course}/{section} Attendance Analysis"
        data = {
            "reports": [
                {
                    "html": df_html,
                    "title": report_name,
                },
            ]
        }
        return render_template("viewReport.html", data=data)


import app.scripts.attendance.cut_analysis.main as cut_analysis


@scripts.route("/attendance/return_cut_analysis")
def return_cut_analysis():
    f = cut_analysis.main()
    return ""
    download_name = f"CutAnalysis.xlsx"
    return send_file(f, as_attachment=True, download_name=download_name)
