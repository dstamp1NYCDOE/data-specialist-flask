import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import scripts, files_df
import app.scripts.utils as utils

import app.scripts.college_and_career.scripts.IPR_monitoring.main as IPR_monitoring
from app.scripts.college_and_career.scripts.IPR_monitoring.forms import IPRMonitoringForm

@scripts.route("/college_and_career/IPR_monitoring", methods=["GET", "POST"])
def return_IPR_monitoring():
    if request.method == "GET":
        form = IPRMonitoringForm()
        return render_template(
            "college_and_career/templates/college_and_career/IPR_monitoring/form.html", form=form
        )
    else:
        form = IPRMonitoringForm(request.form)
        f = IPR_monitoring.main(form, request)

        download_name = f"IPR_Monitoring_{dt.datetime.today().strftime('%Y-%m-%d')}.xlsx"

        # return ""
        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/pdf",
        )