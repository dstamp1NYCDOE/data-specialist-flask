import json
import pandas as pd
import datetime as dt
from io import BytesIO


from flask import render_template, request, send_file

from app.scripts import scripts, files_df
import app.scripts.utils as utils


@scripts.route("/pbis/student_network/", methods=["GET", "POST"])
def return_student_network_routes():
    reports = [
        {
            "report_title": "Return Schoolwide Network",
            "report_function": "scripts.return_student_network_overall_analysis",
            "report_description": "Return Student Network Overall Analysis",
        },
    ]
    return render_template("PBIS/templates/smartpass/index.html", reports=reports)


from app.scripts.pbis.student_network import main as student_network_overall


@scripts.route("/pbis/student_network/overall")
def return_student_network_overall_analysis():
    f, download_name = student_network_overall.main()
    return send_file(f, as_attachment=True, download_name=download_name)
