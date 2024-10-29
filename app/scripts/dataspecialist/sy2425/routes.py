from flask import render_template, send_file

from app.scripts import scripts

@scripts.route("/dataspecialistprojects/2024_2025")
def return_data_specialist_project_2024_2025_reports():
    reports = [
        {
            "report_title": "2024-2025 Data Specialist Project Reports",
            "report_function": "scripts.return_data_specialist_project_2024_2025_artifacts",
            "report_description": "Return analysis for the 2024-2025 data specialist project",
        },

        
    ]
    return render_template(
        "dataspecialist/templates/dataspecialist/2024_2025/index.html", reports=reports
    )

import app.scripts.dataspecialist.sy2425.return_artifacts as sy2425_return_artifacts
@scripts.route("/dataspecialistprojects/2024_2025/artifacts")
def return_data_specialist_project_2024_2025_artifacts():
    f, download_name = sy2425_return_artifacts.main()

    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )    