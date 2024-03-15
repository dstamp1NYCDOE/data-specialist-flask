import pandas as pd 


def process_spreadsheet(form, request):
    survey_responses = request.files[form.survey_responses.name]
    surveys_dict = pd.read_excel(survey_responses, sheet_name=None)
    
    surveys_df = pd.concat(surveys_dict.values())
    print(surveys_df)
    return surveys_df