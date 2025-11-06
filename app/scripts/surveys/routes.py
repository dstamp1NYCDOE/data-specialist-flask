from flask import render_template, request, send_file, session



from app.scripts import utils
from app.scripts import scripts, files_df

from flask import Flask, request, send_file, jsonify
import pandas as pd
from io import BytesIO

from .forms import SurveyUploadForm

# Import the analysis function and config
from .main import analyze_survey
from .config.belongingness_config import BelongingnessConfig




@scripts.route('surveys/analyze_belongingness', methods=['GET','POST'])
def analyze_belongingness_survey():
    """
    Flask endpoint to analyze belongingness survey data.
    
    Expected request format:
    - File upload with CSV/Excel containing survey data
    - OR JSON with survey data
    
    Returns:
    - Excel file with analysis results
    """
    if request.method == 'GET':
        form = SurveyUploadForm()
        return render_template('surveys/templates/form.html', form=form)    
    try:
        # Option 1: Receive uploaded file
        if 'file' in request.files:
            file = request.files['file']
            
            # Read file into dataframe
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return jsonify({'error': 'Unsupported file format'}), 400
        
        # Option 2: Receive JSON data
        elif request.is_json:
            data = request.get_json()
            df = pd.DataFrame(data['survey_data'])
        
        else:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get optional parameters from request
        handle_missing = request.form.get('handle_missing', 'flag')
        additional_bio_columns = request.form.getlist('bio_columns')

        ## attach student info

        school_year = session["school_year"]
        term = session["term"]
        year_and_semester = f"{school_year}-{term}"

        filename = utils.return_most_recent_report_by_semester(
            files_df, "3_07", year_and_semester=year_and_semester
        )
        register_df = utils.return_file_as_df(filename)
        register_df["year_in_hs"] = register_df["GEC"].apply(utils.return_year_in_hs, args=(school_year,))
        register_df = register_df[['StudentID','LastName','FirstName','year_in_hs']]
        df = register_df.merge(df, on=['StudentID'], how='left')
        
        filename = utils.return_most_recent_report_by_semester(
            files_df, "1_49", year_and_semester=year_and_semester
        )
        counselors_df = utils.return_file_as_df(filename)
        counselors_df = counselors_df[['StudentID','Counselor']]
        df = counselors_df.merge(df, on=['StudentID'], how='left')

        
        # Run analysis
        output_file = analyze_survey(
            df=df,
            config=BelongingnessConfig(),
            biographical_columns=additional_bio_columns,
            handle_missing=handle_missing,
            question_text_map=BelongingnessConfig().get_question_text_map()
        )
        
        # Send file back to client
        return send_file(
            output_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='belongingness_analysis.xlsx'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500