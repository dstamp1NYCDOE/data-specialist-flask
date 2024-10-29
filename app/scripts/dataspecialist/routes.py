from flask import render_template

from app.scripts import scripts

@scripts.route("/dataspecialistprojects")
def return_data_specialist_project_reports():
    reports = [
        {
            "report_title": "2024-2025 Data Specialist Project Reports",
            "report_function": "scripts.return_data_specialist_project_2024_2025_reports",
            "report_description": "Return analysis for the 2024-2025 data specialist project",
        },

        
    ]
    return render_template(
        "dataspecialist/templates/dataspecialist/index.html", reports=reports
    )