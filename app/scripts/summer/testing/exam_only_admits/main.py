import pyautogui
import time
import pandas as pd

screen_width, screen_height = pyautogui.size()

# Common regions:
top_half = (0, 0, screen_width, screen_height // 2)
bottom_half = (0, screen_height // 2, screen_width, screen_height // 2)
left_half = (0, 0, screen_width // 2, screen_height)
right_half = (screen_width // 2, 0, screen_width // 2, screen_height)

def main(form, request):    # Extract form data
    
    student_lst_str = form.students_str.data
    student_lst = []
    if student_lst_str != '':
        student_lst = student_lst_str.split("\r\n")
        student_lst = [int(x) for x in student_lst if len(x) == 9 and x.isdigit()]

    # waits 5 seconds to allow user to switch to the ATS screen
    time.sleep(5)
    results_lst = []
    for student_id in student_lst:
        try:
            result = traf_atsum(student_id)
            results_lst.append(result)
        except pyautogui.FailSafeException:
            results_df = pd.DataFrame(results_lst)
            return results_df

    results_df = pd.DataFrame(results_lst)
    return results_df


TRAF_SUCCESS_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/TRAF_success.png"
TRAF_WARNING_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/TRAF_warning.png"
TRAF_PROG_CODE_ERROR_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/TRAF_PROG_CODE_ERROR.png"
TRAF_ALREADY_TRANSFERRED_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/TRAF_already_transferred.png"
STUDENT_NOT_FOUND_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/STUDENT_NOT_FOUND.png"
DBN_REQUIRED_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/DBN_REQUIRED.png"
COURT_ORDER_WARNING_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/COURT_ORDER_WARNING.png"
GEOGRAPHY_CODE_NOT_VALID_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/GEOGRAPHY_CODE_NOT_VALID.png"
HOME_LANG_NOT_VALID_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/HOME_LANG_NOT_VALID.png"
PROOF_OF_AGE_NOT_VALID_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/PROOF_OF_AGE_NOT_VALID.png"
PLACE_OF_BIRTH_NOT_VALID_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/PLACE_OF_BIRTH_NOT_VALID.png"
INVALID_DBN_WARNING_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/INVALID_DBN_WARNING.png"
ETHNIC_STATUS_FIELD_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/ETHNIC_STATUS_FIELD.png"
RISING_9TH_GRADER_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/RISING_9TH_GRADER.png"
NON_DOE_CODE_REQUIRED_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/NON_DOE_CODE_REQUIRED.png"
ALREADY_SHARED_INSTRUCTION_WARNING_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/ALREADY_SHARED_INSTRUCTION_WARNING.png"

def traf_atsum(StudentID):
    status_dict = {'StudentID': StudentID,'Status':'Failure'}
    # type 3 on the BIOG screen and tab to Student ID area
    pyautogui.write("3")
    pyautogui.press("tab")
    # type StudentID number and type enter
    pyautogui.write(str(StudentID))
    pyautogui.press("enter")

    # Checks for errors
    # 1. check if court order warning is present and then press F5 to continue
    # 2. Check if student already admitted to summer program elsewhere
    # 3. Check if student already transferred into summer school
    # 4. Check if StudentID is invalid

    ## check if already admitted to a summer program and if admitted elsewhere, press F3 to quit and move on to the next student
    ## search for TRAF_warning.png on the screen
    try:
        pyautogui.locateOnScreen(COURT_ORDER_WARNING_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)
        pyautogui.press("f5")
    except pyautogui.ImageNotFoundException:
        pass
    
    try:
        pyautogui.locateOnScreen(TRAF_WARNING_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)

        # transition to the SIAD screen
        pyautogui.press("f3")
        pyautogui.write("15")
        pyautogui.press("enter")
        
        try:
            pyautogui.locateOnScreen(ALREADY_SHARED_INSTRUCTION_WARNING_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)
            print('hi')
            status_dict['Status'] = 'Already Admitted via SIAD'
            return status_dict
        except pyautogui.ImageNotFoundException:
            # type the current date as MMDDYY
            current_date = time.strftime("%m%d%y")
            pyautogui.write(current_date)
            ## type '000' for the official class
            pyautogui.write("000")
            ## type f2 to save
            pyautogui.press("f2")

            status_dict['Status'] = 'Admitted via SIAD'
        return status_dict
    except pyautogui.ImageNotFoundException:
        pass
    ## check if already transferred into summer school by looking for the TRAF_ALREADY_TRANSFERRED_IMG_PATH and moving on to the the next student by returning ''
    try:
        pyautogui.locateOnScreen(TRAF_ALREADY_TRANSFERRED_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)
        print(f"Student {StudentID} has already been transferred into summer school.")
        status_dict['Status'] = 'Already Transferred into this summer school'
        return status_dict
    except pyautogui.ImageNotFoundException:
        pass
    ## check if screen displays STUDENT NOT FOUND image               
    try:
        pyautogui.locateOnScreen(STUDENT_NOT_FOUND_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)
        
        status_dict['Status'] = 'Student Not Found with this StudentID number'
        return status_dict
    except pyautogui.ImageNotFoundException:
        pass
    ## check if pending discharge
    try:
        PENDING_DISCHARGE_IMG_PATH = "app/scripts/summer/testing/exam_only_admits/images/PENDING_DISCHARGE.png"
        pyautogui.locateOnScreen(PENDING_DISCHARGE_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)
        # pyautogui.type("5")
        # pyautogui.press("enter")
        status_dict['Status'] = 'Pending Discharge'
        return status_dict
    except pyautogui.ImageNotFoundException:
        pass

    # Once student is found, able to be admitted, and not already transferred, proceed to admit student
    ## determine number of fields to tab through
    num_of_tabs = 21
    try:
        pyautogui.locateOnScreen(ETHNIC_STATUS_FIELD_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)
        num_of_tabs = 22
    except pyautogui.ImageNotFoundException:
        pass    

    ## tab 21 times to get to the Exam Only field
    for _ in range(num_of_tabs):
        pyautogui.press("tab")
    # type Y to admit student
    pyautogui.write("Y")
    ## tab 5 times to get to the Off Class field
    for _ in range(5):
        pyautogui.press("tab")
    ### check if student is a rising 9th grader, and if so, type "190" then "09"
    try:
        pyautogui.locateOnScreen(RISING_9TH_GRADER_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)
        pyautogui.write("190")
        pyautogui.write("09")
    except pyautogui.ImageNotFoundException:
        pass        
    # type 000 to admit student off class
    pyautogui.write("000")
    # type keystroke f2 to save
    pyautogui.press("f2")

    ### check to see if proof of age is required, and if so, type "1" and press f2"
    try:
        pyautogui.locateOnScreen(PROOF_OF_AGE_NOT_VALID_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)
        # type the proof of age
        pyautogui.write("1")
        # press f2 to save
        pyautogui.press("f2")
    except pyautogui.ImageNotFoundException:
        pass 

    ### check to see if place of birth is required, and if so, type "88" and press f2"
    try:
        pyautogui.locateOnScreen(PLACE_OF_BIRTH_NOT_VALID_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)
        # type the place of birth
        pyautogui.write("88")
        # press f2 to save
        pyautogui.press("f2")
    except pyautogui.ImageNotFoundException:
        pass 

    ### check to see if GEO CODE is required, and if so, type "88" and press f2"
    try:
        pyautogui.locateOnScreen(GEOGRAPHY_CODE_NOT_VALID_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)
        # type the GEO CODE
        pyautogui.write("88")
        # press f2 to save
        pyautogui.press("f2")
    except pyautogui.ImageNotFoundException:
        pass  

    ### check to see if HOME LANG is required, and if so, type "NO" and press f2"
    try:
        pyautogui.locateOnScreen(HOME_LANG_NOT_VALID_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)
        # type the HOME LANG
        pyautogui.write("NO")
        # press f2 to save
        pyautogui.press("f2")
    except pyautogui.ImageNotFoundException:
        pass 

    ### check to see if DBN is required, and if so, type the DBN number and press f2
    try:
        pyautogui.locateOnScreen(DBN_REQUIRED_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)
        print(f"DBN is required for Student {StudentID}.")
        # type the DBN number
        pyautogui.write("02M600")  # Replace with actual DBN if needed
        # go back to the nondoe code
        for _ in range(2):
            pyautogui.hotkey('shift', 'tab')
        
        ## delete the nondoe code by typing delete key 5 times
        for _ in range(5):
            pyautogui.press("delete")
        # press f2 to save
        pyautogui.press("f2")
    except pyautogui.ImageNotFoundException:
        pass  

    ### check to see if NON_DOE CODE REQUIRED is required, and if so, type the 99999 and press f2
    try:
        pyautogui.locateOnScreen(NON_DOE_CODE_REQUIRED_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)
        print(f"NON_DOE_CODE is required for Student {StudentID}.")
        # type the NON_DOE_CODE
        pyautogui.write("99999")  # Replace with actual NON_DOE_CODE if needed
        # press f2 to save
        pyautogui.press("f2")
    except pyautogui.ImageNotFoundException:
        pass  

    ### check to see if a TRAF_PROG_CODE_ERROR, and if so, correct it by pressing the delete key twice and pressing f2
    try:
        pyautogui.locateOnScreen(TRAF_PROG_CODE_ERROR_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)
        pyautogui.press("delete")
        pyautogui.press("delete")
        pyautogui.press("f2")
    except pyautogui.ImageNotFoundException:
        pass
    
    ## check if there was an issue with a field that lead to typing over the DBN field and just abort
    try:
        pyautogui.locateOnScreen(INVALID_DBN_WARNING_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)
        pyautogui.press("f3")
        return status_dict
    except pyautogui.ImageNotFoundException:
        pass

    ## check if admit was successful based on pyautogui.locateonscreen to the TRAF_success.png file 
    try:
        pyautogui.locateOnScreen(TRAF_SUCCESS_IMG_PATH,grayscale=True,confidence=0.80,region=right_half)
        print(f"Student {StudentID} admitted successfully.")
        status_dict['Status'] = 'Student Admitted Successfully'
        return status_dict
    except pyautogui.ImageNotFoundException:
        print(f"Failed to admit Student {StudentID}.")
        # If admit was not successful, return an empty string
        # if the admit was not successful, press these keys to go back to the TRAF screen and move on to the next student.
        pyautogui.press("f3")
        pyautogui.write("TRAF")
        pyautogui.press("enter")

    return status_dict