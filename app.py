from flask import Flask, request, redirect, url_for, render_template, flash
from forms import FileForm, ReportForm
from werkzeug.utils import secure_filename

from scripts.programming.class_lists import generate_class_list

import os 
import utils

app = Flask(__name__)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

files_df = utils.return_dataframe_of_files()

@app.route('/')
def return_index():
    form = ReportForm()
    return render_template('index.html',form=form)


@app.route("/view/")
def view_all_reports():
    reports_html = files_df.to_html(classes=["table", "table-sm"])
    return render_template("viewReport.html", report_html=reports_html)


@app.route('/view/<report>')
def view_most_recent_report(report):
    report_path = utils.return_most_recent_report(files_df, report)
    report_df = utils.return_file_as_df(report_path)
    report_html = report_df.to_html(classes=["table", "table-sm"])
    return render_template("viewReport.html", report_html=report_html)

@app.route('/run', methods=['POST'])
def run_script():
    data = request.form
    report = request.form['report']
    reports_map = {"scripts.programming.class_lists": generate_class_list}

    reports_map.get(report)(data)

    return redirect(url_for("return_index"))

@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    form = FileForm()

    if form.validate_on_submit():
        f = form.file.data
        filename = secure_filename(f.filename)
        filename = filename.replace('_',"-")
        report_name = filename.split('.')[0]
        extension = filename.split(".")[1]
        if 'CustomReport' in report_name:
            report_name = report_name[13:-5]
            filename = f"{report_name}.{extension}"

        download_date = form.download_date.data
        year_and_semester = form.year_and_semester.data
        filename = f"{year_and_semester}_{download_date}_{filename}"

        path = os.path.join(app.root_path, f"data/{year_and_semester}/{report_name}")
        isExist = os.path.exists(path)
        if not isExist:
            os.makedirs(path)
        f.save(os.path.join(path, filename))
        flash(f"{filename} successfully uploaded",category="success")
        return redirect(url_for("upload_files"))

    return render_template("upload.html", form=form)
