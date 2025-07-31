import pyautogui
import pytesseract 
from PIL import Image
import time
import re 
import pandas as pd 

screen_width, screen_height = pyautogui.size()
right_half = (screen_width // 2, 0, screen_width // 2, screen_height)

class ScreenshotOCR:
    def extract_text_from_image(self, image, config=''):
        """Extract text from PIL Image using OCR"""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using pytesseract
            text = pytesseract.image_to_string(image, config=config)
            return text.strip()
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""
        
    def preprocess_image(self, image):
        """Basic image preprocessing to improve OCR accuracy"""
        from PIL import ImageEnhance
        
        # Convert to grayscale
        image = image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        return image

    def capture_region(self, x, y, width, height, save_path=None):
        """Capture a specific region of the screen"""
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        if save_path:
            screenshot.save(save_path)
        return screenshot


def capture_right_half_and_extract_text():
    """Capture the right half of the screen and extract text using OCR"""
    ocr = ScreenshotOCR()
    
    # Capture the right half of the screen
    screenshot = ocr.capture_region(*right_half)
    
    # Preprocess the image
    processed_image = ocr.preprocess_image(screenshot)
    
    # Extract text from the processed image
    extracted_text = ocr.extract_text_from_image(processed_image)
    
    return extracted_text            


def return_student_VEXM_main(form, request):
    student_lst_str = form.students_str.data
    student_lst = []
    if student_lst_str != '':
        student_lst = student_lst_str.split("\r\n")
        student_lst = [int(x) for x in student_lst]

    return return_student_VEXM_list(student_lst)

def return_student_VEXM(StudentID):
    # enter the student info and press enter
    pyautogui.write(str(StudentID))
    pyautogui.press("enter")

    # take a screenshot and read the text
    extracted_text = capture_right_half_and_extract_text()
    processed_exams_lst = process_extracted_vexm_test(extracted_text,StudentID)
    # refresh the page
    pyautogui.press("f9")

    return processed_exams_lst

def return_student_VEXM_list(StudentID_list):
    results = []
    time.sleep(5)
    for StudentID in StudentID_list:
        result = return_student_VEXM(StudentID)
        results.extend(result)

    results_df = pd.DataFrame(results)
    return results_df.to_html()


VEXM_regex_pattern = r"^(?:\w+\s+)?(\w{5})\s+.*?(\d+|MIS|ABS|INV)(?:\s+[A-Z])?$"
def process_extracted_vexm_test(extracted_text,StudentID):
    """Process the extracted text from VEXM"""
    # Split the text into lines
    lines = extracted_text.split('\n')
    
    processed_exams_lst = []
    for line in lines:
        # Use regex to find the VEXM test results
        match = re.search(VEXM_regex_pattern, line)
        print(line)
        if match:
            # Extract the relevant parts
            test_name = match.group(1)
            result = match.group(2)
            # Create a dictionary for the result
            processed_exams_lst.append({
                "StudentID": StudentID,
                "TestName": test_name,
                "Result": result,
                "RAW":line,
            })

    return processed_exams_lst