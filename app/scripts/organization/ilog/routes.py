import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename


import app.scripts.utils.utils as utils


from app.scripts import scripts, files_df

from app.scripts.organization.ilog.forms import iLogForm
from app.scripts.organization.ilog import main as ilog_main
@scripts.route("/organization/ilog/automation", methods=["GET", "POST"])
def return_ilog_automation():

    if request.method == "GET":
        form = iLogForm()
        return render_template(
            "organization/ilog/templates/ilog_form.html",
            form=form,
        )
    else:
        form = iLogForm(request.form)
        ilog_main.main(form, request)
        flash("iLog automation completed successfully.", "success")
        return redirect(url_for("scripts.return_ilog_automation"))