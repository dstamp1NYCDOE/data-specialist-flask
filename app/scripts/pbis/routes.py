import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, session


from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.scripts.pbis.forms import ABC_AnalysisForm

import app.scripts.pbis.academic_intervention_plan as academic_intervention_plan
import app.scripts.pbis.abc_analysis as abc_analysis


@scripts.route("/pbis")
def return_pbis_reports():
    reports = [
        {
            "report_title": "Academic Intervention Plan Candidates",
            "report_function": "scripts.return_academic_intervention_plan_candidates",
            "report_description": "Return Academic Intervention Plan Candidates",
        },
        {
            "report_title": "ABC Analysis",
            "report_function": "scripts.return_abc_analysis",
            "report_description": "Return ABC Analysis",
        },
        {
            "report_title": "SmartPass Analysis",
            "report_function": "scripts.return_smartpass_reports",
            "report_description": "Return SmartPass Analysis reports",
        },
        {
            "report_title": "Univeral Screener Analysis",
            "report_function": "scripts.return_screener_reports",
            "report_description": "Return Univeral Screener Analysis reports",
        },
        {
            "report_title": "Phone Call Tracker Analysis",
            "report_function": "scripts.return_phone_call_tracker_reports",
            "report_description": "Return Phone Call Tracker Analysis",
        },
        {
            "report_title": "Student Network Analysis",
            "report_function": "scripts.return_student_network_routes",
            "report_description": "Return student network analysis reports",
        },
    ]
    title = "PBIS"
    return render_template(
        "section.html",
        reports=reports,
        title=title,
    )


@scripts.route("pbis/AIP")
def return_academic_intervention_plan_candidates():
    df = academic_intervention_plan.return_candidates()
    semester = session["semester"]
    report_name = f"Academic Intervention Plan Candidates {semester}"
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


@scripts.route("/pbis/abc", methods=["GET", "POST"])
def return_abc_analysis():
    if request.method == "GET":
        form = ABC_AnalysisForm()
        return render_template("pbis/templates/pbis/abc_form.html", form=form)
    else:
        form = ABC_AnalysisForm(request.form)
        df = abc_analysis.main(form, request)
        data = {"df_to_html": df.to_html()}
        return render_template("pbis/templates/pbis/abc_results.html", data=data)
