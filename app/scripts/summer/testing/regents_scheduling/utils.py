def return_full_exam_title(ExamTitle):
    
    exam_title_dict = {
        "ELA": "ELA",
        "Global": "Global History",
        "USH": "US History",
        "Alg1": "Algebra I",
        "Geo": "Geometry",
        "Alg2": "Algebra II/Trigonometry",
        "LE": "Living Environment",
        "ES": "Earth Science",
        "Chem": "Chemistry",
        "Phys": "Physics",
    }
    return exam_title_dict.get(ExamTitle)