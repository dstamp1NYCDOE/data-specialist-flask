import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import files_df
import app.scripts.utils.utils as utils


from app.scripts.graduation import graduation

from app.scripts.graduation.diplomas.forms import DiplomaMockupForm
import app.scripts.graduation.diplomas.diploma_mockups as diploma_mockups


@graduation.route("certification/diploma_mockup", methods=["GET", "POST"])
def return_diploma_mockup():
    if request.method == "GET":
        form = DiplomaMockupForm()
        return render_template(
            "/graduation/templates/graduation/diplomas/mockup_form.html",
            form=form,
        )
    else:
        form = DiplomaMockupForm(request.form)
        f = diploma_mockups.main(form, request)
        school_year = session["school_year"]
        download_name = f"June{school_year+1}_Diploma_Mockups.pptx"
        # return ""
        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )
