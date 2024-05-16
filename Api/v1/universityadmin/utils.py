from models import StudentClassGrade, ClassGrade, Class, Course, CourseEnrolled, CourseGrade, StudentClassSubjectGrade, Subject, ClassSubject, Class, Faculty, Student, db, UniversityAdmin, ClassSubjectGrade, Metadata, Curriculum, LatestBatchSemester
from sqlalchemy import desc, distinct, func, and_
import re
from werkzeug.security import check_password_hash, generate_password_hash
from collections import defaultdict

from datetime import date, datetime
from sklearn.linear_model import LinearRegression

from flask import session, jsonify
from static.js.utils import convertGradeToPercentage, checkStatus
from flask_mail import Message
from mail import mail
import pandas as pd
import random
import string
from sqlalchemy.orm import Session


from collections import defaultdict

def getCurrentUser():
    current_user_id = session.get('user_id')
    return UniversityAdmin.query.get(current_user_id)


def is_valid_email(email):
    # Regular expression for a basic email validation
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(email_pattern, email)


def is_valid_phone_number(phone_number):
    # Regular expression for a phone number validation
    phone_pattern = r'^09\d{9}$'
    return re.match(phone_pattern, phone_number)


def generate_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password
    

def getUniversityAdminData(str_univ_admin_id):
    try:
        data_university_admin = (
            db.session.query(UniversityAdmin).filter(
                UniversityAdmin.UnivAdminId == str_univ_admin_id).first()
        )

        if data_university_admin:
          

            dict_student_data = {
                "UnivAdminNumber": data_university_admin.UnivAdminNumber,
                "Name": data_university_admin.Name,
                "PlaceOfBirth": data_university_admin.PlaceOfBirth,
                "ResidentialAddress": data_university_admin.ResidentialAddress,
                "Email": data_university_admin.Email,
                "MobileNumber": data_university_admin.MobileNumber,
                "Gender": "Male" if data_university_admin.Gender == 1 else "Female",
            }

            return (dict_student_data)
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def updateUniversityAdminData(str_univ_admin_id, number, residentialAddress):
    try:
        number = re.sub(r'\D', '', number)  # Remove non-digit characters
        number_pattern = re.compile(r'^09\d{9}$')

        if not number_pattern.match(number):
            return {"type": "mobile", "status": 400}

        if residentialAddress is None or residentialAddress.strip() == "":
            return {"type": "residential", "status": 400}

        # Update the student data in the database
        data_univ_admin = db.session.query(UniversityAdmin).filter(UniversityAdmin.UnivAdminId == str_univ_admin_id).first()
        
        if data_univ_admin:
            data_univ_admin.MobileNumber = number
            data_univ_admin.ResidentialAddress = residentialAddress
            db.session.commit()
                        
            return {"message": "Data updated successfully", "number": number, "residentialAddress": residentialAddress, "status": 200}
        else:
            return {"message": "Something went wrong", "status": 404}

    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}


def updatePassword(str_university_admin_id, password, new_password, confirm_password):
    try:
        data_university_admin = db.session.query(UniversityAdmin).filter(UniversityAdmin.UnivAdminId == str_university_admin_id).first()

  
        password_validator = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$'

        error = False
        errorList = []
        if not password:
            error = True
            errorList.append({'type': 'current_password', 'message': "Password must not be invalid"})
        elif len(password) < 8:
            error = True
            errorList.append({'type': 'current_password', 'message': "Password must be 8 characters long"})
        elif not re.match(password_validator, password):
            error = True
            errorList.append({'type': 'current_password', 'message': "Password must contain a number and characters uppercase and lowercase"})

        if not new_password:
            error = True
            errorList.append({'type': 'new_password', 'message': "New Password must not be invalid"})
        elif len(new_password) < 8:
            error = True
            errorList.append({'type': 'new_password', 'message': "New Password must be 8 characters long"})
        elif not re.match(password_validator, new_password):
            error = True
            errorList.append({'type': 'new_password', 'message': "New Password must contain a number and characters uppercase and lowercase"})

        if not confirm_password:
            error = True
            errorList.append({'type': 'confirm_password', 'message': "Confirm Password must not be invalid"})
        elif len(confirm_password) < 8:
            error = True
            errorList.append({'type': 'confirm_password', 'message': "Confirm Password must be 8 characters long"})
        elif not re.match(password_validator, confirm_password):
            error = True
            errorList.append({'type': 'confirm_password', 'message': "Confirm Password must contain a number and characters uppercase and lowercase"})

        if new_password != confirm_password:
            error = True
            errorList.append({'type': 'confirm_password', 'message': "Password does not match"})

        if error:
            return {"error": True, 'errorList': errorList, "status": 400}
            
        
        if data_university_admin:
            # Assuming 'password' is the hashed password stored in the database
            hashed_password = data_university_admin.Password

            if check_password_hash(hashed_password, password):
                # If the current password matches
                new_hashed_password = generate_password_hash(new_password)
                data_university_admin.Password = new_hashed_password
                db.session.commit()
                return {"message": "Password changed successfully", "status": 200}

            else:
                return {"message": "Changing Password was unsuccessful. Please try again.", "status": 401}
        else:
            return {"message": "Something went wrong", "status": 404}

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}



def getEnrollmentTrends():
    try:
        # Query data with required fields
        data_course_enrolled = db.session.query(
            Course.CourseCode, CourseEnrolled.DateEnrolled
        ).join(Course, Course.CourseId == CourseEnrolled.CourseId).order_by(CourseEnrolled.DateEnrolled).all()

        if data_course_enrolled:
            # Create a dictionary to store year-wise course counts
            course_year_counts = defaultdict(lambda: defaultdict(int))
            list_course = []
            
            # Iterate through the data to calculate counts
            for course_code, date_enrolled in data_course_enrolled:
                # Check if course code existing in list course if not add to the list
                if course_code not in list_course:
                    list_course.append(course_code)
                
                year_enrolled = date_enrolled.year
                course_year_counts[year_enrolled][course_code] += 1

            # Convert the counts to a list of dictionaries with the desired format
            trend_data = []

            # Find lowest, highest, and total enrollment counts
            for year, course_counts in course_year_counts.items():
                trend_item = {"x": year, **course_counts}
                trend_data.append(trend_item)
            
            return jsonify({'success': True, 'enrollment_trends': trend_data, 'course_list': list_course})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def get_lister_counts(item):
    president_lister_count = db.session.query(func.count(StudentClassGrade.Lister)).\
        join(Class, Class.ClassId == StudentClassGrade.ClassId).\
        join(Metadata, Metadata.MetadataId == Class.MetadataId).\
        filter(Metadata.Batch == item.Batch, StudentClassGrade.Lister == 1).\
        scalar()

    dean_lister_count = db.session.query(func.count(StudentClassGrade.Lister)).\
        join(Class, Class.ClassId == StudentClassGrade.ClassId).\
        join(Metadata, Metadata.MetadataId == Class.MetadataId).\
        filter(Metadata.Batch == item.Batch, StudentClassGrade.Lister == 2).\
        scalar()

    return president_lister_count, dean_lister_count

def get_list_lister_data(data_latest_batch_semester):
    list_lister_data = []
    max_count = 0
    min_count = None

    if data_latest_batch_semester:
        for item in data_latest_batch_semester:
            president_lister_count, dean_lister_count = get_lister_counts(item)

            max_count = max(max_count, president_lister_count, dean_lister_count)
            if not min_count:
                min_count = min(president_lister_count, dean_lister_count)
            else:
                min_count = min(min_count, president_lister_count, dean_lister_count)

            grade_dict = {"year": str(item.Batch), "president": president_lister_count, "dean": dean_lister_count}
            list_lister_data.append(grade_dict)

        return list_lister_data, max_count, min_count

    return None, None, None


def getListerTrends():
    try:
        data_latest_batch_semester_desc = db.session.query(LatestBatchSemester).distinct(LatestBatchSemester.Batch).order_by(desc(LatestBatchSemester.Batch)).limit(5).all()
        data_latest_batch_semester = list(reversed(data_latest_batch_semester_desc))

        list_lister_data, max_count, min_count = get_list_lister_data(data_latest_batch_semester)
        interval = 0
        # Make a 5 interval in max count and min count Ex. 100/5 = 20 then interval is 20
        if max_count and min_count:
            max_count = max_count + 1
            min_count = min_count - 1
            interval = int((max_count - min_count) / 5)
    
        if list_lister_data:
            return jsonify({'success': True, 'lister': list_lister_data, "max": max_count, "min": min_count, "interval": interval})
        else:
            return None

    except Exception as e:
        print("ERROR: ", e)
        return None


def getCurrentGpaGiven():
    try:
        data_course_gpa = db.session.query(
            CourseGrade).order_by(CourseGrade.Year).all()

        if data_course_gpa:
            course_year_grades = defaultdict(list)

            for course_gpa in data_course_gpa:
                year = course_gpa.Year
                grade = course_gpa.Grade

                course_year_grades[year].append(grade)

            # Find the latest year
            latest_year = max(course_year_grades.keys())

            # Calculate the average Grade for the latest year
            if latest_year in course_year_grades:
                latest_year_grades = course_year_grades[latest_year]
                average_grade = sum(latest_year_grades) / \
                    len(latest_year_grades)
                # Format the average Grade to two decimal places
                average_grade = round(average_grade, 2)
            else:
                average_grade = None

            return {"AverageGrade": average_grade}
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
def predict_performance(data):
    # Extracting features and labels from the data
    years = [entry['x'] for entry in data]
    courses_data = [{key: entry[key] for key in entry if key != 'x'} for entry in data]

    # Initializing the linear regression model
    model = LinearRegression()

    # Predicting performance level for each course
    predictions = []
    for course_data in courses_data:
        # Training the model for each course
        model.fit([[year] for year in years], list(course_data.values()))
        # Predicting the performance for the latest year
        latest_year = max(years)
        prediction = model.predict([[latest_year]])[0]

        # Classifying performance levels
        if prediction < 85:
            performance_level = "Need Improvement"
        elif prediction >= 85 and prediction <= 90:
            performance_level = "Maintain"
        else:
            performance_level = "Great Performance"

        predictions.append({
            "Course": list(course_data.keys())[list(course_data.values()).index(prediction)],
            "Prediction": prediction,
            "Performance Level": performance_level
        })

    return predictions

def getOverallCoursePerformance():
    try:
        # Get course performance for the last 5 years
        data_course_grade = db.session.query(
            Course.CourseId,
            Course.CourseCode,
            CourseGrade.Batch,
            func.avg(CourseGrade.Grade).label('average_grade')
        ).join(
            Course, Course.CourseId == CourseGrade.CourseId
        ).group_by(
            Course.CourseId, CourseGrade.Batch
        ).order_by(
            CourseGrade.Batch, Course.CourseId
        ).all()

        list_course = []

        if data_course_grade:
            course_year_grades = defaultdict(dict)

            for course_grade in data_course_grade:
                course_code = course_grade.CourseCode
                year = course_grade.Batch
                course_id = course_grade.CourseId
                
                # Check if course_code is not in list_course
                if course_code not in list_course:
                    list_course.append(course_code)

                grade = round(convertGradeToPercentage(course_grade.average_grade), 2)

                if year not in course_year_grades:
                    course_year_grades[year] = {"x": year}

                course_year_grades[year][course_code] = grade
            
            # Convert the data into a list of dictionaries
            formatted_data = list(course_year_grades.values())
            return jsonify({'success': True, 'list_course': list_course, 'course_performance': formatted_data})
        else:
            return None
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return e
    
    
def getAllClassData(skip, top, order_by, filter):
    try:
        class_grade_query = db.session.query(Class, Metadata,  Course, ClassGrade).join(Metadata, Metadata.MetadataId == Class.MetadataId).join(Course, Course.CourseId == Metadata.CourseId).join(ClassGrade, ClassGrade.ClassId == Class.ClassId)
        
        
        filter_conditions = []
        
        if filter:
            filter_parts = filter.split(' and ')
            for part in filter_parts:
                # Check if part has to lower in value
                if '(tolower(' in part:
                    # Extracting column name and value
                    column_name = part.split("(")[3].split("),'")[0]
                    value = part.split("'")[1]
                    column_str = None
                    
                    if column_name.strip() == 'ClassName':
                        split_values = value.split(' ')
                        
                        if len(split_values) >= 2:
                            # Check split values if have a number
                            if any(char.isdigit() for char in split_values[-1]):
                                batch_section = split_values[-1]
                                course_code = ' '.join(split_values[:-1])
                                column_arr_1 = getattr(Course, 'CourseCode')
                                year, section = None, None
                                
                                if '-' in batch_section:
                                    year, section = batch_section.split('-')
                                    if section:
                                        column_arr_3 = getattr(Class, 'Section')
                                    column_arr_2 = getattr(Metadata, 'Year')
                                else:
                                    year = batch_section
                                    column_arr_2 = getattr(Metadata, 'Year')
                            else:
                                course_code = ' '.join(split_values)
                                year, section = None, None
                                column_arr_1 = getattr(Course, 'CourseCode')

                            # Append column_arr_1
                            filter_conditions.append(
                                func.lower(column_arr_1).like(f'%{split_values[0]}%')
                            )
                            # Check if year then append
                            if year:
                                filter_conditions.append(Metadata.Year == int(year))
                                
                            if section:
                                filter_conditions.append(
                                    Class.Section == int(section)
                                )
                            continue
                        elif len(split_values) == 1:
                            course_code, year, section = None, None, None
                            # check if value contains "-" and digit in it
                            if '-' in value and any(x.isdigit() for x in value):
                                year, section = value.split('-')
                                column_arr_2 = Metadata.Year
                                column_arr_3 = Class.Section
                            else:
                                course_code = value
                                column_arr_1 = getattr(Course, 'CourseCode')
                            
                            if course_code:
                                filter_conditions.append(column_arr_1.like(f'%{course_code.upper()}%'))

                            if year:
                                filter_conditions.append(
                                    column_arr_2 == int(year)
                                )
                            
                            if section:
                                filter_conditions.append(
                                    column_arr_3 == int(section)
                                )
                            continue
                    elif column_name.strip() == 'Course':
                        column_str = getattr(Course, 'Name')
                    elif column_name.strip() == 'Grade':
                        filter_conditions.append(
                            ClassGrade.Grade == value
                        )
                        continue
                 
                    if column_str:
                        # Append column_str
                        filter_conditions.append(
                            func.lower(column_str).like(f'%{value}%')
                        )
                else:
                    # column_name = part[0][1:]  # Remove the opening '('
                    column_name, value = [x.strip() for x in part[:-1].split("eq")]
                    column_name = column_name[1:]
                    column_num = None
                    int_value = value.strip(')')
                    
                    # Check for column name 
                    if column_name.strip() == 'Batch':
                        column_num = Metadata.Batch
                    elif column_name.strip() == 'Semester':
                        column_num = Metadata.Semester
               
                    
                    if column_num:
                        # Append column_num
                        filter_conditions.append(
                            column_num == int_value
                        )
                # END OF ELSE PART
            # END OF FOR LOOP
                
        
        # Apply all filter conditions with 'and'
  
        filter_query = class_grade_query.filter(and_(*filter_conditions))
        # print('FILTER: ', filter_query.statement.compile().params)
        
         # Apply sorting logic
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'Course':
                order_attr = getattr(Course, 'Name')
            elif order_by.split(' ')[0] == "Batch":
                order_attr = getattr(Metadata, "Batch")
            elif order_by.split(' ')[0] == 'Semester':
                order_attr = getattr(Metadata, 'Semester')
            elif order_by.split(' ')[0] == 'Grade':
                order_attr = getattr(ClassGrade, 'Grade')
            else:
                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(Metadata.Batch), desc(Metadata.Semester), desc(Course.CourseCode), desc(Class.Section))
                else:
                    order_query = filter_query.order_by(Metadata.Batch, Metadata.Semester, Course.CourseCode, Class.Section)

            # Check if order_by contains space
            if not order_by.split(' ')[0] == "ClassName":
                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(order_attr))
                else:
                    order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(desc(Metadata.Batch), desc(Metadata.CourseId), desc(Metadata.Year), Class.Section, desc(Metadata.Semester))
        
        total_count = order_query.count()
        class_grade_main_query = order_query.offset(skip).limit(top).all()
        

        if class_grade_main_query:
            list_classes = []
            seen_class_ids = set()  # Initialize a set to track seen ClassIds

            for class_subject_grade in class_grade_main_query:
                class_id = class_subject_grade.Class.ClassId

                # Check if the ClassId is not in the seen_class_ids set
                if class_id not in seen_class_ids:
                    # Get the class name
                    # Check if Grade exists
                    if class_subject_grade.ClassGrade.Grade is not None:
                        # If Grade exists, format it with two decimal places
                        grade_value = f"{class_subject_grade.ClassGrade.Grade:.2f}"
                    else:
                        # If Grade does not exist, set it to 'N/A'
                        grade_value = 0.00
                        
                    class_obj = {
                        'ClassId': class_id,
                        'ClassName': f"{class_subject_grade.Course.CourseCode} {class_subject_grade.Metadata.Year}-{class_subject_grade.Class.Section}",
                        'Semester': class_subject_grade.Metadata.Semester,
                        "Course": class_subject_grade.Course.Name,
                        "Batch": class_subject_grade.Metadata.Batch,
                        "Grade": grade_value
                    }

                    # Add class_id to the seen_class_ids set
                    seen_class_ids.add(class_id)

                    # Add class_obj to the list_classes
                    list_classes.append(class_obj)

            # Return the list of class objects
            return {'result': list_classes, 'count': total_count}
        else:
            return None

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def predict_class_performance(data):
    if(len(data) == 1 and data[0]['y'] == 0 ):
        return "No class data available"
    
    # Extract x and y values from the data
    X = [[entry['x']] for entry in data]
    y = [entry['y'] for entry in data]

    # Train a linear regression model
    model = LinearRegression()
    model.fit(X, y)

    # Predict future performance for the next year
    future_year = max([entry['x'] for entry in data]) + 1
    X_pred = [[future_year]]
    future_performance = model.predict(X_pred)[0]

    # Classify the predicted performance
    if future_performance < 85:
        class_status = "Needs Improvement"
    elif 85 <= future_performance < 90:
        class_status = "Good Performance"
    else:
        class_status = "Great Performance"

    return class_status

def getClassPerformance(class_id):
    try:
        class_grade = (
            db.session.query(
                ClassGrade, Course, Class, Metadata
            )
            .join(Class, Class.ClassId == ClassGrade.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .join(Course, Course.CourseId == Metadata.CourseId)
            .filter(ClassGrade.ClassId == class_id)
            .first()
        )

        
        if class_grade:

            # Calculate class name
            class_name = f"{class_grade.Course.CourseCode} {class_grade.Metadata.Year}-{class_grade.Class.Section} ({class_grade.Metadata.Batch})"
            num_class_batch = class_grade.Metadata.Batch
            num_class_section = class_grade.Class.Section

            dict_class_grade = {
                'Class': class_name,
                'Batch': num_class_batch,
                'ListGrade': [],
                'PresidentLister': class_grade.ClassGrade.PresidentsLister,
                'DeanLister': class_grade.ClassGrade.DeansLister
            }
            
            list_grade = []
            for i in range(1, class_grade.Metadata.Year+1):
                batch = class_grade.Metadata.Batch - class_grade.Metadata.Year + i
                class_grade_result = (
                    db.session.query(
                        Class,
                        Metadata,
                        ClassGrade,
                    )
                    .join(ClassGrade, ClassGrade.ClassId == Class.ClassId)
                    .filter(Metadata.Year == i, Metadata.Batch == batch, Class.Section == num_class_section, Class.ClassId == class_id)
                    .first()

                )

                list_grade.append(
                    {'x': class_grade_result.Metadata.Batch, 'y': convertGradeToPercentage(class_grade_result.ClassGrade.Grade)})
                
            dict_class_grade['ListGrade'].extend(list_grade)
            prediction = predict_class_performance(dict_class_grade['ListGrade'])
            dict_class_grade['Status'] = prediction

            return (dict_class_grade)
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def processAddingStudents(data, excelType=False):
    try:
        def errorObject(data):
            return ({
                        'StudentNumber': data[0],
                        'LastName': data[1],
                        'FirstName': data[2],
                        'MiddleName': data[3],
                        'Email': data[4],
                        'Phone': data[5],
                        'Address': data[6],
                        'Gender': data[7],
                        'CourseCode': data[8],
                        'DateEnrolled': data[9],  # Adding the original string for reference
                        'Batch': data[10],
                        'Error': data[11]
                    })
        
        if excelType == True:
            # Check if the file is empty
            if data.filename == '':
                return jsonify({'error': 'No selected file'}), 400

            # Check file extension
            if not data.filename.endswith(('.xlsx', '.xls')):
                return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400


            # Read the Excel file into a DataFrame
            df = pd.read_excel(data)
            
            # dict data list
            list_student_data = []
            errors = []
            
            for index, row in df.iterrows():
                student_number = row['Student Number'] # OK
                student_lastname = row['LastName']
                student_firstname = row['FirstName']
                student_middlename = row['MiddleName']
                student_email = row['Email']
                student_mobile =  str(row['Phone Number'])
                student_address = row['Address'] # OK
                student_gender = row['Gender'] # OK
                student_program = row['Program'] # Change to program
                student_date_enrolled = row['Date Enrolled']
                student_batch = row['Batch'] # OK

                if student_mobile:
                    # Check for length of phone number if 10 add 0 in first
                    if len(student_mobile) == 10:
                        student_mobile = '0' + student_mobile
                    elif len(student_mobile) != 11:
                        errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Invalid Mobile Format']))
                        continue
                    
            
                # Check if Date Enrolled is a valid date format
                if student_date_enrolled is not None:
                    # Check if it is in date format then convert it into YYYY-MM-DD
                    if isinstance(student_date_enrolled, datetime):
                        student_date_enrolled = student_date_enrolled.strftime("%Y-%m-%d")
                    else:
                        errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Invalid Date Enrolled format']))
                        continue
                else:
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Invalid Date Enrolled']))
                    continue
                
                # Check if Batch is a valid format (e.g., numeric)
                if not str(student_batch).isdigit():
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Invalid Batch format']))
                    continue
                elif not student_batch:
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Invalid Batch']))
                    continue
                
                # Check if Email is a valid format
                if not is_valid_email(student_email):
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Invalid Email format']))
                    continue
                elif not student_email:
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender  , student_program, student_date_enrolled, student_batch, 'Invalid Email format']))
                    continue
                
                # Check if Phone Number is a valid format
                if student_mobile and not is_valid_phone_number(student_mobile):
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Invalid Phone Number format']))
                    continue
            
                if not student_program:
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Invalid Course']))
                    continue
                
                # Check if the student is already exist in the database based on StudentNumber or Email
                student_number_data = db.session.query(Student).filter(
                    (Student.StudentNumber == student_number) 
                ).first()
                student_email_data = db.session.query(Student).filter(
                    (Student.Email == student_email) 
                ).first()

                if not student_number_data and not student_email_data:
                    password = generate_password()
                    gender = 1 if student_gender == 'Male' else (2 if student_gender == 'Female' else None)

                    course = db.session.query(Course).filter_by(CourseCode=student_program).first()

                    # Add the new student in the database

                    # Ensure the mobile number has a leading zero
                    if not student_mobile.startswith('0'):
                        student_mobile = '0' + student_mobile

                    new_student = Student(
                        StudentNumber=student_number,
                        LastName=student_lastname,
                        FirstName=student_firstname,
                        MiddleName=student_middlename,
                        Email=student_email,
                        MobileNumber=str(student_mobile),
                        ResidentialAddress=student_address,
                        Gender=gender,
                        Password=generate_password_hash(password)
                    )


                    db.session.add(new_student)
                    db.session.flush()
                    
                    new_course_enrolled = CourseEnrolled(
                        CourseId=course.CourseId,
                        StudentId=new_student.StudentId,
                        DateEnrolled=student_date_enrolled,
                        Status=1,
                        CurriculumYear=student_batch
                    )
                    
                    # # Add the new course enrolled to the session
                    db.session.add(new_course_enrolled)
                    db.session.commit()
                    
                    msg = Message('Your current PUP Account has been granted.', sender='your_email@example.com',
                                recipients=[str(new_student.Email)])
                    # The message body should be the credentials details
                    msg.body = f"Your current PUP Account has been granted. \n\n Email: {str(new_student.Email)} \n Password: {str(password)} \n\n Please change your password after you log in. \n\n Thank you."
                    
                    mail.send(msg)
                    
                    if not gender:
                        list_student_data.append({
                            "Email": str(student_email),
                            "Gender": "N/A",
                            "Mobile Number": str(student_mobile),
                            'LastName': student_lastname,
                            'FirstName': student_firstname,
                            'MiddleName': student_middlename,
                            "Student Number": str(student_number)
                        })
                    else:
                        list_student_data.append({
                            "Email": str(student_email),
                            "Gender": student_gender,
                            "Mobile Number": str(student_mobile),
                            'LastName': student_lastname,
                            'FirstName': student_firstname,
                            'MiddleName': student_middlename,
                            "Student Number": str(student_number)
                        })
                else:
                    if student_number_data:
                        errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Student Number already exist']))
                    else:
                        errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Email already exist']))
                    
            if errors and list_student_data:
                db.session.rollback()
                return jsonify({'warning': 'Some data cannot be added.', 'errors': errors, 'data': list_student_data}), 500
            if errors and not list_student_data:
                db.session.rollback()
                return jsonify({'error': 'Adding data failed.', 'errors': errors}), 500
            else:        
                return  jsonify({'result': 'Data added successfully', 'data': list_student_data}), 200
        else:
            if data:
                student_number = data['StudentNumber'].strip()
                student_lastname = data['LastName']
                student_firstname = data['FirstName']
                student_middlename = data.get('MiddleName', '')
                student_email = data['Email'].strip()
                student_gender = data.get('Gender', 1) # OK
                student_mobile =  str(data['MobileNumber']).strip()
                student_program = data['Program'].strip()
                student_date_enrolled = data['DateEnrolled']
                student_batch = data['Batch'] # OK
                
                
                if student_mobile:
                    # Check for length of phone number if 10 add 0 in first
                    if len(student_mobile) == 10:
                        student_mobile = '0' + student_mobile
                    
            
                # Convert student_date_enrolled to date format
                if student_date_enrolled is not None:
                    try:
                        # Adjust the format string to include the time component
                        student_date_enrolled = datetime.strptime(student_date_enrolled, "%Y-%m-%dT%H:%M:%S.%fZ")
                        
                        # Extract only the date part
                        student_date_enrolled = student_date_enrolled.date()
                        
                    except Exception as e:
                        return jsonify({'error': 'Invalid Date Enrolled format'}), 400
              
                # Check if Batch is a valid format (e.g., numeric)
                if not type(student_batch) == int:
                    # Return error
                    # print
                    return jsonify({'error': 'Invalid Batch format'}), 400
                
                # Check if Email is a valid format
                if not is_valid_email(student_email):
                    # Return error
                    # print
                    return jsonify({'error': 'Invalid Email format'}), 400
                # Check if Phone Number is a valid format
                if student_mobile and not is_valid_phone_number(student_mobile):
                    # Return error
                    # print
                    return jsonify({'error': 'Invalid Phone Number format'}), 400

                
                # Check if the student is already exist in the database based on StudentNumber or Email
                student_number_data = db.session.query(Student).filter(
                    (Student.StudentNumber == student_number) 
                ).first()
                student_email_data = db.session.query(Student).filter(
                    (Student.Email == student_email) 
                ).first()

                if not student_number_data and not student_email_data:
                    
                    password = generate_password()
                    gender = 1 if student_gender == 'Male' else (2 if student_gender == 'Female' else None)

                    course = db.session.query(Course).filter_by(CourseCode=student_program).first()
                    
                    
                # Add the new student in the database

                    # Ensure the mobile number has a leading zero
                    if not student_mobile.startswith('0'):
                        student_mobile = '0' + student_mobile
                    
                    new_student = Student(
                        StudentNumber=student_number,
                        LastName=student_lastname,
                        FirstName=student_firstname,
                        MiddleName=str(student_middlename),
                        Email=student_email,
                        MobileNumber=str(student_mobile),
                        Gender=gender,
                        Password=generate_password_hash(password)
                    )
                    
                    db.session.add(new_student)
                    db.session.flush()
                    new_course_enrolled = CourseEnrolled(
                        CourseId=course.CourseId,
                        StudentId=new_student.StudentId,
                        DateEnrolled=student_date_enrolled,
                        Status=1,
                        CurriculumYear=student_batch
                    )
                    # # Add the new course enrolled to the session
                    db.session.add(new_course_enrolled)
                    db.session.commit()
                    
                    msg = Message('Your current PUP Account has been granted.', sender='your_email@example.com',
                                recipients=[str(new_student.Email)])
                    # The message body should be the credentials details
                    msg.body = f"Your current PUP Account has been granted. \n\n Email: {str(new_student.Email)} \n Password: {str(password)} \n\n Please change your password after you log in. \n\n Thank you."
                    
                    mail.send(msg)
                    # Return data added success
                    
                    return jsonify({'result': 'Data added successfully'}), 200
                    
                else:
                    if student_number_data:
                        return jsonify({'error': 'Student Number already exist'}), 400
                    else:
                        # Return email already exist
                        return jsonify({'error': 'Email already exist'}), 400
                    

    except Exception as e:
        db.session.rollback()
        print("ERROR: ", e)
        return jsonify({'errorException': 'An error occurred while processing the file'}), 500
    
    
def processAddingClass(file):
    try:
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

        df = pd.read_excel(file)
        
        list_new_class_data = []
        errors = []
        
        for index, row in df.iterrows():
            course_code = row['Course Code']
            section = int(row['Section'])
            year = int(row['Year Level'])
            semester = int(row['Semester'])
            batch = int(row['Batch'])

            course = db.session.query(Course).filter_by(CourseCode=course_code).first()
            
            if not course:
                errors.append({"CourseCode": course_code, "Section": section, "Year": year, "Semester": semester, "Batch": batch, "Error": "Course Not Exist"})
                continue
            
            # Check if LatestBatchSemester
            latest_batch_semester = db.session.query(LatestBatchSemester).filter_by(Batch=batch, Semester=semester).first()
            
            # Check if IsEnrollmentStarted and IsGradeFinalized
            if latest_batch_semester:
                if latest_batch_semester.IsEnrollmentStarted and latest_batch_semester.IsGradeFinalized:
                    errors.append({"CourseCode": course_code, "Section": section, "Year": year, "Semester": semester, "Batch": batch, "Error": "Batch and semester are already done"})
                    continue
                
            
            metadata = db.session.query(Metadata).filter_by(CourseId=course.CourseId, Year=year, Semester=semester, Batch=batch).first()

            if metadata:
                # Find the Latest Batch Semester that match in metadata
                latest_batch_semester = db.session.query(LatestBatchSemester).filter_by(Batch=metadata.Batch, Semester=metadata.Semester).first()
                
                if not latest_batch_semester:
                    # Create one
                    new_latest_batch_semester = LatestBatchSemester(
                        Batch=metadata.Batch,
                        Semester=metadata.Semester
                    )
                    
                    db.session.add(new_latest_batch_semester)
                # If not 
            else:
                errors.append({"CourseCode": course_code, "Section": section, "Year": year, "Semester": semester, "Batch": batch, "Error": "Curriculum not exist"})
                continue

            if course and metadata:
                curriculum = db.session.query(Curriculum).filter_by(MetadataId=metadata.MetadataId).all()
                if curriculum:
                    class_data = db.session.query(Class, Metadata).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(
                        Metadata.CourseId==course.CourseId, Metadata.Year==year, Class.Section==section, Metadata.Semester==semester, Metadata.Batch==batch).first()

                    if not class_data:
                        class_name = f"{course_code} {year}-{section}"
                        course_name = course.Name
                        new_class = Class(
                            Section=section,
                            IsGradeFinalized=False,
                            # Transition to metadata
                            MetadataId = metadata.MetadataId
                            # Semester=semester,
                            # Batch=batch,
                            # CourseId=course.CourseId,
                            # Year=year
                        )

                        db.session.add(new_class)
                        db.session.flush()
                        new_class_grade = ClassGrade(
                            ClassId=new_class.ClassId,
                            DeansLister=0,
                            PresidentsLister=0,
                            Grade=0
                        )

                        db.session.add(new_class_grade)
                        
                        # list_new_class_data add the new class data
                        list_new_class_data.append({
                            "ClassId": new_class.ClassId,
                            "ClassName": class_name,
                            "Course": course_name,
                            "Grade": 'N/A',
                            "Semester": metadata.Semester,
                            "Batch": metadata.Batch
                        })
                        
                        for cur in curriculum:
                            new_class_subject = ClassSubject(
                                ClassId=new_class.ClassId,
                                SubjectId=cur.SubjectId
                            )
                            db.session.add(new_class_subject)
                            db.session.flush()
                            new_class_subject_grade = ClassSubjectGrade(
                                ClassSubjectId=new_class_subject.ClassSubjectId,
                                Grade=0,
                                Passed=0,
                                Failed=0,
                                Incomplete=0,
                                Dropout=0
                            )

                            db.session.add(new_class_subject_grade)
                            db.session.commit()
                    else:
                        errors.append({"CourseCode": course_code, "Section": section, "Year": year, "Semester": semester, "Batch": batch, "Error": "Class already exist"})
                else:
                    errors.append({"CourseCode": course_code, "Section": section, "Year": year, "Semester": semester, "Batch": batch, "Error": "Curriculum not exist"})
            
                
        if errors and list_new_class_data:  
            db.session.rollback()
            return jsonify({'warning': "Some data cannot be added.", 'errors': errors, 'data': list_new_class_data}), 400
        if errors and not list_new_class_data:
            db.session.rollback()
            return jsonify({'error': 'Adding data failed.', 'errors': errors}), 400
        else:
            
            return jsonify({'result': 'Data added successfully', 'data': list_new_class_data}), 200
 
    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()
        return jsonify({'errorException': 'An error occurred while processing the file'}), 500


def processClassStudents(file, class_id):
    try:
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

        df = pd.read_excel(file)
        
        list_student_added = []
        errors = []
        
        # Find the class
        class_data = db.session.query(Class, Metadata).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(Class.ClassId==class_id).first()
        
        # Check latest batch semester
        latest_batch_semester = db.session.query(LatestBatchSemester).filter_by(Batch=class_data.Metadata.Batch, Semester=class_data.Metadata.Semester).first()
        
        # Check if latest_batch_semester.IsStartEnrollment is False
        if not latest_batch_semester.IsEnrollmentStarted:
            return jsonify({'error': 'Cannot add students. Enrollment is not yet started.'}), 400
        
        if class_data.Class.IsGradeFinalized:
                return jsonify({'error': 'Cannot add student. Grade is already finalized'}), 400
            
        if class_data:
            # Check for student first if exist in df
            for index, row in df.iterrows():
                student_number = str(row['Student Number'])
                student_date_enrolled = row['Date Enrolled']
                student_class_grade_exist = False;
                
                if not student_number:
                    errors.append({
                        'StudentNumber': 'N/A',
                        'DateEnrolled': student_date_enrolled,
                        'Error': 'Student Number must have a value'
                    })
                    continue
                
                if student_date_enrolled:
                    if isinstance(student_date_enrolled, datetime):
                        student_date_enrolled = student_date_enrolled.strftime("%Y-%m-%d")
                    else:
                        errors.append({
                            'StudentNumber': student_number,
                            'DateEnrolled': "N/A",
                            'Error': 'Invalid Date Enrolled format'
                        })
                        continue
                
                if not student_date_enrolled:
                    errors.append({
                        'StudentNumber': student_number,
                        'DateEnrolled': 'N/A',
                        'Error': 'Date Enrolled must have a value'
                    })
                    continue
           
                student_data = db.session.query(Student).filter_by(StudentNumber=student_number).first()

                if not student_data:
                    errors.append({
                        'StudentNumber': student_number,
                        'DateEnrolled': student_date_enrolled,
                        'Error': 'Student Number does not exist'
                    })
                    continue
                
                else:
                    class_subject_data = db.session.query(ClassSubject).filter_by(ClassId=class_id).all()
                    if class_subject_data:
                        # for loop of it
                        for class_subject in class_subject_data:
                            # Find class subject that has the same SubjectId and StudentId
                            student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(StudentId=student_data.StudentId, ClassSubjectId=class_subject.ClassSubjectId).first()
                            
                            if student_class_subject_grade:
                                # Check if student Class Subject Grade Academic Status is 1
                                if student_class_subject_grade.AcademicStatus == 1:
                                    # Append errors
                                    errors.append({
                                        'StudentNumber': student_number,
                                        'DateEnrolled': student_date_enrolled,
                                        'Error': 'Student already taken and passed the subject'
                                    })
                                    # Go to next loop
                                    continue
                                
                                # Check if Academic Status is none then tell that already enrolled
                                if student_class_subject_grade.AcademicStatus is None:
                                    errors.append({
                                        'StudentNumber': student_number,
                                        'DateEnrolled': student_date_enrolled,
                                        'Error': 'Student already enrolled'
                                    })
                                    # Go to next loop
                                    continue
                        
                            # Check if not class_grade_exist then create and set it to True
                            if not student_class_grade_exist:
                                student_class_grade = db.session.query(StudentClassGrade).filter_by(StudentId=student_data.StudentId, ClassId=class_id
                                ).all()
                                if not student_class_grade:
                                    new_student_class_grade = StudentClassGrade(
                                        StudentId=student_data.StudentId,
                                        ClassId=class_id
                                    )
                                    db.session.add(new_student_class_grade)
                                    db.session.flush()
                                    student_class_grade_exist = True;
                                
                                    
                            subject_data = db.session.query(Subject).filter_by(SubjectId=class_subject.SubjectId).first()
                            
                            # check if student_class_subject_grade_exist
                            student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(StudentId=student_data.StudentId, ClassSubjectId=class_subject.ClassSubjectId).first()
                            if not student_class_subject_grade:
                                new_student_class_subject_grade = StudentClassSubjectGrade(
                                    StudentId=student_data.StudentId,
                                    ClassSubjectId=class_subject.ClassSubjectId,
                                    DateEnrolled=student_date_enrolled,
                                    Grade= 0.00
                                )
                                db.session.add(new_student_class_subject_grade)
                                db.session.commit()
                            
                                # Append list_student_added
                                list_student_added.append({
                                    "StudentNumber": student_number,
                                    "SubjectCode": subject_data.SubjectCode
                                })
                            else:
                                # Check if student_class_subject_grade.AcademicStatus is 2
                                if student_class_subject_grade.AcademicStatus == 2:
                                    # Check if student_class_subject_grade get the ClassSubject and its Class itself
                                    class_subject_data = db.session.query(ClassSubject, Class).join(Class, Class.ClassId == ClassSubject.ClassId).filter(
                                        ClassSubject.ClassSubjectId == student_class_subject_grade.ClassSubjectId
                                    ).first()
                                    
                                    # Check if class subject already grade finalized
                                    if class_subject_data.Class.IsGradeFinalized:
                                        # Update the details of student_class_subject_grade Academic Status to 5
                                        student_class_subject_grade.AcademicStatus = 5
                                        # Make a new student class subject grade
                                        new_student_class_subject_grade = StudentClassSubjectGrade(
                                            StudentId=student_data.StudentId,
                                            ClassSubjectId=class_subject.ClassSubjectId,
                                            DateEnrolled=student_date_enrolled,
                                            Grade= 0.00
                                        )
                                        
                                        # commit
                                        db.session.add(new_student_class_subject_grade)
                                        db.session.commit()
                                elif student_class_subject_grade.AcademicStatus == 1:
                                    # Append error telling that the student already taken subject and passed it
                                    errors.append({
                                        'StudentNumber': student_number,
                                        'DateEnrolled': student_date_enrolled,
                                        'Error': 'Student already taken and passed the subject'
                                    })
                    else:
                        # return no class subject yet
                        return jsonify({'error': 'No class subject yet'}), 400
  
            if errors and not list_student_added:
                db.session.rollback()
                return jsonify({'error': 'Adding students failed', 'errors': errors}), 400
            else:
                return jsonify({'result': 'Data added successfully'}), 200
        else:
            # return error with message cannot find the class
            return jsonify({'error': 'Cannot find the class'}), 400    
            
    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()
        return jsonify({'errorException': 'An error occurred while processing the file'}), 500
            
            
            
    #         class_subject_data = db.session.query(ClassSubject).filter_by(ClassId=class_id).all()
    #         if class_subject_data:
    #             # for loop the class_subject_data
                
    #             for class_subject in class_subject_data:                    
    #                 # Create StudentClassSubjectGrade for all ClassSubjectId 
    #                 for index, row in df.iterrows():
    #                     class_grade_exist = False;
    #                     student_number = row['Student Number']
    #                     date_enrolled = row['Date Enrolled'].date()
                        
    #                     # Get the student data
    #                     student_data = db.session.query(Student).filter_by(StudentNumber=student_number).first()
    #                     if student_data:
    #                         # Check if student_class_subject_grade exist
    #                         student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(StudentId=student_data.StudentId, ClassSubjectId=class_subject.ClassSubjectId).first()
    #                         if student_class_subject_grade:
    #                             # Find the subject 
    #                             subject_data = db.session.query(Subject).filter_by(SubjectId=class_subject.SubjectId).first()
                        
    #                             list_student_class_subject_exist.append({
    #                                 "StudentNumber": student_number,
    #                                 "SubjectCode": subject_data.SubjectCode
    #                             }) 
    #                         else:
                                
    #                             if not class_grade_exist:
    #                                 # Check if studentClassGrade already exist if not create one
    #                                 student_class_grade = db.session.query(StudentClassGrade).filter_by(StudentId=student_data.StudentId, ClassId=class_id).first()
                                    
    #                                 if not student_class_grade:
    #                                     new_student_class_grade = StudentClassGrade(
    #                                         StudentId=student_data.StudentId,
    #                                         ClassId=class_id
    #                                     )
    #                                     db.session.add(new_student_class_grade)
    #                                     db.session.flush()
    #                                     class_grade_exist = True;
                                
    #                             subject_data = db.session.query(Subject).filter_by(SubjectId=class_subject.SubjectId).first()
                                
    #                             new_student_class_subject_grade = StudentClassSubjectGrade(
    #                                 StudentId=student_data.StudentId,
    #                                 ClassSubjectId=class_subject.ClassSubjectId,
    #                                 DateEnrolled=date_enrolled
    #                             )
    #                             db.session.add(new_student_class_subject_grade)
    #                             db.session.commit()
                                
    #                             # Append list_student_added
    #                             list_student_added.append({
    #                                 "StudentNumber": student_number,
    #                                 "SubjectCode": subject_data.SubjectCode
    #                             })
    #                     else:
    #                         if student_number not in list_student_number_not_exist:
    #                             list_student_number_not_exist.append(student_number)   
    #         else:
    #             # return no class subject yet
    #             return jsonify({'error': 'No class subject yet'}), 400
    #     else:
    #         # return error with message cannot find the class
    #         return jsonify({'error': 'Cannot find the class'}), 400
        
    #     if list_student_number_not_exist:
            
    #     if list_student_class_subject_exist:
            
    #     if not list_student_added:
        
    #     # Check if length of list_student_number_not_exist or list_student_class_subject_exist
    #     if (list_student_number_not_exist or list_student_class_subject_exist) and list_student_added:
    #         db.session.rollback()
    #         return jsonify({'error': 'Some data cannot be added', 'errors': {'student_number_not_exist': list_student_number_not_exist, 'student_class_subject_exist': list_student_class_subject_exist}}), 400
    #     elif (list_student_number_not_exist or list_student_class_subject_exist) and not list_student_added:
    #         db.session.rollback()
    #         return jsonify({'error': 'Adding students failed', 'errors': {'student_number_not_exist': list_student_number_not_exist, 'student_class_subject_exist': list_student_class_subject_exist}}), 400
    #     else:
    #         return jsonify({'result': 'Data added successfully'}), 200

    # except Exception as e:
    #     db.session.rollback()
    #     return jsonify({'error': 'An error occurred while processing the file'}), 500


def getStudentData(skip, top, order_by, filter):
    try:
        student_query = (
            db.session.query(CourseEnrolled, Student, Course).join(Student, Student.StudentId == CourseEnrolled.StudentId).join(Course, Course.CourseId == CourseEnrolled.CourseId)
        )
        
        filter_conditions = []
        if filter:
            filter_parts = filter.split(' and ')
            for part in filter_parts:
                
                # Check if part has to lower in value
                if '(tolower(' in part:
                    # Extracting column name and value
                    column_name = part.split("(")[3].split("),'")[0]
                    value = part.split("'")[1]
                    column_str = None
                    if column_name.strip() == 'StudentNumber':
                        column_str = getattr(Student, 'StudentNumber')
                    elif column_name.strip() == 'LastName':
                        column_str = getattr(Student, 'LastName')
                    elif column_name.strip() == 'FirstName':
                        column_str = getattr(Student, 'FirstName')
                    elif column_name.strip() == 'MiddleName':
                        column_str = getattr(Student, 'MiddleName')
                    elif column_name.strip() == 'Email':
                        column_str =  getattr(Student, 'Email')     
                    elif column_name.strip() == 'MobileNumber':
                        column_str = getattr(Student, 'MobileNumber')
                    elif column_name.strip() == 'Program':
                        column_str = getattr(Course, 'CourseCode')
                    elif column_name.strip() == 'DateEnrolled':
                        column_str = getattr(CourseEnrolled, 'DateEnrolled')
                        filter_conditions.append(
                            CourseEnrolled.DateEnrolled == (1 if value == 'male' else 2)
                        )
                    elif column_name.strip() == 'Gender':
                        filter_conditions.append(
                            Student.Gender == (1 if value == 'male' else 2)
                        )
                        continue
                    
                    if column_str:
                        # Append column_str
                        filter_conditions.append(
                            func.lower(column_str).like(f'%{value}%')
                        )
                else:
                    # column_name = part[0][1:]  # Remove the opening '('
                    column_name, value = [x.strip() for x in part[:-1].split("eq")]
                    column_name = column_name[1:]
                    
                    column_num = None
                    int_value = value.strip(')')
             
                    if column_name.strip() == 'Batch':
                        column_num = CourseEnrolled.CurriculumYear
                    
                    if column_num:
                        # Append column_num
                        filter_conditions.append(
                            column_num == int_value
                        )
                        
        filter_query = student_query.filter(and_(*filter_conditions))
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'StudentNumber':
                order_attr = getattr(Student, 'StudentNumber')
            elif order_by.split(' ')[0] == "LastName":
                order_attr = getattr(Student, 'LastName')
            elif order_by.split(' ')[0] == "FirstName":
                order_attr = getattr(Student, 'FirstName')
            elif order_by.split(' ')[0] == "MiddleName":
                order_attr = getattr(Student, 'MiddleName')
            elif order_by.split(' ')[0] == 'Email':
                order_attr = getattr(Student, 'Email')
            elif order_by.split(' ')[0] == 'Gender':
                order_attr = getattr(Student, 'Gender')
            elif order_by.split(' ')[0] == 'MobileNumber':
                order_attr = getattr(Student, 'MobileNumber')
            elif order_by.split(' ')[0] == 'Program':
                order_attr = getattr(Course, 'CourseCode')
            elif order_by.split(' ')[0] == 'DateEnrolled':
                order_attr = getattr(CourseEnrolled, 'DateEnrolled')
            elif order_by.split(' ')[0] == 'Batch':
                order_attr = getattr(CourseEnrolled, 'CurriculumYear')
           
           
            if ' ' in order_by:
                order_query = filter_query.order_by(desc(order_attr))
            else:
                order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(desc(CourseEnrolled.CurriculumYear), desc(Course.CourseCode), desc(Student.StudentNumber))
        
        
        # Query for counting all records
        total_count = order_query.count()
        # Limitized query = 
        student_limit_offset_query = order_query.offset(skip).limit(top).all()
        if student_limit_offset_query:
             # For loop the student_query and put it in dictionary
            list_student_data = []
            for data in student_limit_offset_query:
                dict_student = {
                    "StudentId": data.Student.StudentId,
                    "StudentNumber": data.Student.StudentNumber,
                    "LastName": data.Student.LastName,
                    "FirstName": data.Student.FirstName,
                    "MiddleName": data.Student.MiddleName,
                    "Email": data.Student.Email,
                    "MobileNumber": data.Student.MobileNumber,
                    "Gender": "Male" if data.Student.Gender == 1 else "Female",
                    "Program": data.Course.CourseCode,
                    "DateEnrolled": data.CourseEnrolled.DateEnrolled.strftime('%Y-%m-%d'),
                    "Batch": data.CourseEnrolled.CurriculumYear
                }
                # Append the data
                list_student_data.append(dict_student)
            return jsonify({"result": list_student_data, "count":total_count})
        else:
            return None
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None


def getStudentAddOptions():
    try:
      # Make gender options
        genderOptionList = [{"Gender":"Male"},{"Gender":"Female"}]
        # Make course options
        courseOptionList = []
        course_data = db.session.query(Course).all()
        if course_data:
            for course in course_data:
                courseOptionList.append({"CourseCode": course.CourseCode})
        
        # Make batch options for prev year, current year and future year. For example 2024 is current year then it should be 2023, 2024, 2025
        
        
        current_year = datetime.now().year
        batchOptionList = [{"Batch": current_year+1}, {"Batch": current_year},{"Batch": current_year-1}]
        
        return jsonify({'result':{"genderOptions": genderOptionList, "courseOptions": courseOptionList, "batchOptions": batchOptionList}})
        
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': e})

    
def getAllClassSubjectData():
    try:
        data_class_subject = (
            db.session.query(ClassSubject, Subject, Class, Metadata, Course, Faculty).join(Subject, Subject.SubjectId == ClassSubject.SubjectId).join(Class, Class.ClassId == ClassSubject.ClassId).join(Metadata, Metadata.MetadataId == Class.MetadataId).join(Course, Course.CourseId == Metadata.CourseId).join(Faculty, Faculty.FacultyId == ClassSubject.FacultyId).order_by(desc(Metadata.Batch),desc(Metadata.Semester), (Subject.Name)).all()
        )
        

        
        if data_class_subject:
                # For loop the data_student and put it in dictionary
            list_class_subject = []
            for class_subject in data_class_subject:
                # Combine the course_code, year, section to class_name variable
                class_name = f"{class_subject.Course.CourseCode} {class_subject.Metadata.Year}-{class_subject.Class.Section}"
                middle_name = class_subject.Faculty.middle_name if class_subject.Faculty.middle_name else ""
                full_name = f"{class_subject.Faculty.last_name}, {class_subject.Faculty.first_name} {middle_name}"
                
                dict_class_subject = {
                    "Section Code": class_name,
                    "Subject": class_subject.Subject.Name,
                    "Teacher":full_name,
                    "Schedule": class_subject.ClassSubject.Schedule,
                    'Batch': class_subject.Metadata.Batch,
                    'Semester': class_subject.Metadata.Semester
                }
                # # Append the data
                list_class_subject.append(dict_class_subject)
            return jsonify({'result': list_class_subject})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    

def getStudentClassSubjectGrade(skip, top, order_by, filter):
    try:
        # Initial query
        query = (
            db.session.query(
                ClassSubject,
                StudentClassSubjectGrade,
                Subject,
                Class,
                Metadata,
                Course,
                Student
            )
            .join(StudentClassSubjectGrade, StudentClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
            .join(Subject, Subject.SubjectId == ClassSubject.SubjectId)
            .join(Class, Class.ClassId == ClassSubject.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .join(Course, Course.CourseId == Metadata.CourseId)
            .join(Student, Student.StudentId == StudentClassSubjectGrade.StudentId)
            # .filter(ClassSubject.FacultyId == str_teacher_id, Class.Batch >= current_year-4)
        )

        # Parse and apply filters
        
        filter_conditions = []
        # Split filter string by 'and'
        # append the str_teacher_id
        # filter_conditions.append(
        #     ClassSubject.FacultyId == str_teacher_id
        # )

        if filter:
            filter_parts = filter.split(' and ')
            for part in filter_parts:
                # Check if part has to lower in value
                if '(tolower(' in part:
                    # Extracting column name and value
                    column_name = part.split("(")[3].split("),'")[0]
                    value = part.split("'")[1]
                    column_str = None
                    
                    if column_name.strip() == 'Class':
                        split_values = value.split(' ')
                        
                        if len(split_values) >= 2:
                            # Check split values if have a number
                            if any(char.isdigit() for char in split_values[-1]):
                                batch_section = split_values[-1]
                                course_code = ' '.join(split_values[:-1])
                                column_arr_1 = getattr(Course, 'CourseCode')
                                year, section = None, None
                                
                                if '-' in batch_section:
                                    year, section = batch_section.split('-')
                                    if section:
                                        column_arr_3 = getattr(Class, 'Section')
                                    column_arr_2 = getattr(Metadata, 'Year')
                                else:
                                    year = batch_section
                                    column_arr_2 = getattr(Metadata, 'Year')
                            else:
                                course_code = ' '.join(split_values)
                                year, section = None, None
                                column_arr_1 = getattr(Course, 'CourseCode')

                            # Append column_arr_1
                            filter_conditions.append(
                                func.lower(column_arr_1).like(f'%{split_values[0]}%')
                            )
                            # Check if year then append
                            if year:
                                filter_conditions.append(Metadata.Year == int(year))
                                
                            if section:
                                filter_conditions.append(
                                    Class.Section == int(section)
                                )
                            continue
                        elif len(split_values) == 1:
                            course_code, year, section = None, None, None
                            # check if value contains "-" and digit in it
                            if '-' in value and any(x.isdigit() for x in value):
                                year, section = value.split('-')
                                column_arr_2 = Metadata.Year
                                column_arr_3 = Class.Section
                            else:
                                course_code = value
                                column_arr_1 = getattr(Course, 'CourseCode')
                            
                            if course_code:
                                filter_conditions.append(column_arr_1.like(f'%{course_code.upper()}%'))

                            if year:
                                filter_conditions.append(
                                    column_arr_2 == int(year)
                                )
                            
                            if section:
                                filter_conditions.append(
                                    column_arr_3 == int(section)
                                )
                            continue
                    elif column_name.strip() == 'LastName':
                        column_str = getattr(Student, 'LastName')
                    elif column_name.strip() == 'FirstName':
                        column_str = getattr(Student, 'FirstName')
                    elif column_name.strip() == 'MiddleName':
                        column_str = getattr(Student, 'MiddleName')
                    elif column_name.strip() == 'StudentNumber':
                        column_str =  getattr(Student, 'StudentNumber')     
                    elif column_name.strip() == 'SubjectCode':
                        column_str = getattr(Subject, 'SubjectCode')
                 
                    if column_str:
                        # Append column_str
                        filter_conditions.append(
                            func.lower(column_str).like(f'%{value}%')
                        )
                else:
                    # column_name = part[0][1:]  # Remove the opening '('
                    column_name, value = [x.strip() for x in part[:-1].split("eq")]
                    column_name = column_name[1:]
                    
                    column_num = None
                    int_value = value.strip(')')
                    
                    # Check for column name 

                    if column_name.strip() == 'Grade':
                        column_num = StudentClassSubjectGrade.Grade
                    elif column_name.strip() == 'Batch':
                        column_num = Metadata.Batch
                    elif column_name.strip() == 'Semester':
                        column_num = Metadata.Semester
                    
                    if column_num:
                        # Append column_num
                        filter_conditions.append(
                            column_num == int_value
                        )
                # END OF ELSE PART
            # END OF FOR LOOP
                
        
        # Apply all filter conditions with 'and'
  
        filter_query = query.filter(and_(*filter_conditions))

 
        # Apply sorting logic
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'StudentNumber':
                order_attr = getattr(Student, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == "LastName":
                order_attr = getattr(Student, 'LastName')
            elif order_by.split(' ')[0] == "FirstName":
                order_attr = getattr(Student, 'FirstName')
            elif order_by.split(' ')[0] == "MiddleName":
                order_attr = getattr(Student, 'MiddleName')
            elif order_by.split(' ')[0] == 'Grade':
                order_attr = getattr(StudentClassSubjectGrade, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == 'SubjectCode':
                order_attr = getattr(Subject, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == 'Batch':
                order_attr = getattr(Metadata, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == 'Semester':
                order_attr = getattr(Metadata, order_by.split(' ')[0])
            else:

                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(Course.CourseCode), desc(Metadata.Year), desc(Class.Section))
                
                else:
                    order_query = filter_query.order_by(Course.CourseCode, Metadata.Year, Class.Section)
                # close the if_order by and go to next line of it

            # Check if order_by contains space
            if not order_by.split(' ')[0] == "Class":
                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(order_attr))
                else:
                    order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(
                desc(Course.CourseCode), desc(Metadata.Batch), desc(Metadata.Year), desc(Metadata.Semester), Student.LastName
            )

        # Check if order_query and filter query exists:
        total_count = order_query.count()
        result_all = order_query.offset(skip).limit(top).all()
       
        if result_all:
            list_data_class_subject_grade = []
            unique_classes = set()
     
            for class_subject_grade in result_all:
               
                class_name = f"{class_subject_grade.Course.CourseCode} {class_subject_grade.Metadata.Year}-{class_subject_grade.Class.Section}"

                dict_class_subject_grade = {
                    'ClassSubjectId': class_subject_grade.ClassSubject.ClassSubjectId ,
                    'StudentId': class_subject_grade.Student.StudentId,
                    'StudentNumber': class_subject_grade.Student.StudentNumber,
                    'LastName': class_subject_grade.Student.LastName,
                    'FirstName': class_subject_grade.Student.FirstName,
                    'MiddleName': class_subject_grade.Student.MiddleName,
                    'Class': class_name,
                    'Batch': class_subject_grade.Metadata.Batch,
                    'Semester': class_subject_grade.Metadata.Semester,
                    'Grade': class_subject_grade.StudentClassSubjectGrade.Grade,
                    'SubjectCode': class_subject_grade.Subject.SubjectCode
                }

                list_data_class_subject_grade.append(dict_class_subject_grade)
                unique_classes.add(class_name)

            sorted_unique_classes = sorted(unique_classes)
      
            # Return the list of class grades, the classes, and pagination information
            return jsonify({'result':list_data_class_subject_grade, 'count': total_count, 'classes': list(sorted_unique_classes)})
        else:
            return {'ClassSubjectGrade': [], 'Classes': [], 'currentPage': 1, 'totalPages': 0, 'totalItems': 0}

    except Exception as e:
        print("ERROR: ", e)
        # Log the exception or handle it appropriately
        return None
    

def predict_future_grade(data):
    # Filter out entries with grade 0
    filtered_data = [entry for entry in data if entry['Grade'] != 0]

    if not filtered_data:
        return "No valid data for prediction", None

    X = []
    y = []
    for entry in filtered_data:
        grade = entry['Grade']
        semester = entry['Semester']
        year = entry['Year']
        X.append([semester, year])
        y.append(grade)

    model = LinearRegression()
    model.fit(X, y)

    # Predict future grade for the next semester
    future_semester = max([entry['Semester'] for entry in filtered_data]) + 1
    future_year = max([entry['Year'] for entry in filtered_data])
    X_pred = [[future_semester, future_year]]
    future_grade = model.predict(X_pred)[0]
    struggling = future_grade < 85

    return future_grade, struggling  # Threshold for struggling student

    
def getStudentPerformance(str_student_id):
    try:
        list_student_performance = (
            db.session.query(StudentClassGrade, Class, Metadata)
            .join(Class, StudentClassGrade.ClassId == Class.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .filter(StudentClassGrade.StudentId == str_student_id)
            .order_by(desc(Metadata.Batch), desc(Metadata.Semester))
            .all()
        )

        
        if list_student_performance:
            list_performance_data = []  # Initialize a list to store dictionary data
          
            latest_year = list_student_performance[0].Metadata.Year
            latest_semester = list_student_performance[0].Metadata.Semester
        
            for gpa in list_student_performance:
                # Check if Grade is not 0 or NoneTypew
                if gpa.StudentClassGrade.Grade == 0 or gpa.StudentClassGrade.Grade is None:
                    continue
                else:
                    gpa_dict = {
                        'Grade': convertGradeToPercentage(gpa.StudentClassGrade.Grade),
                        'Semester': gpa.Metadata.Semester,
                        'Year': gpa.Metadata.Batch,
                    }
                    # Append the dictionary to the list
                    list_performance_data.append(gpa_dict)

            # Check for missing entries
            batch_semester_map = {(gpa_dict["Year"], semester): False for semester in range(
                1, 4) for gpa_dict in list_performance_data}

            for gpa_dict in list_performance_data:
                batch_semester_map[(gpa_dict["Year"],
                                    gpa_dict["Semester"])] = True

            missing_entries = []
            for (batch, semester), is_present in batch_semester_map.items():
                if not is_present:
                    missing_entries.append({
                        "Year": batch,
                        "Grade": 0,
                        "Semester": semester
                    })

            # Append missing entries to list_performance_data
            list_performance_data.extend(missing_entries)

            # Sort the combined list based on year descending and semester descending
            sorted_list_performance_data = sorted(list_performance_data, key=lambda x: (
                x['Year'], x['Semester']), reverse=True)
            
            predicted_grade, struggling = predict_future_grade(sorted_list_performance_data)
            
            
            print(latest_year , latest_semester)
            # # Check whether the 
            if(latest_year == 4 and latest_semester < 2):
                predicted_grade = round(predicted_grade, 2)
            elif (latest_year <= 3 and latest_semester <= 3):
                predicted_grade = round(predicted_grade, 2)
            else:
                predicted_grade = "Not Applicable"
            
            if struggling == True:
                struggling = "Academic Struggling"
            else:
                struggling = "Meet Academic Expectations"

            return ({'grade': sorted_list_performance_data, 'future_grade': predicted_grade, 'status': struggling})
        else:
            return None

    except Exception as e:
        print("ERROR: ", e )
        # Handle the exception here, e.g., log it or return an error response
        return None


def processGradeSubmission(file):
    try:
        # Check if the file is empty
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Check file extension
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

        # Read the Excel file into a DataFrame
        df = pd.read_excel(file)
        
        list_finalized_grade = []
        is_some_submitted = False
        # Now you can access and manipulate the data in the DataFrame
        # For example, you can iterate through rows and access columns like this:
        for index, row in df.iterrows():
            # Extract the values from the DataFrame
            student_number = row['Student Number'] # OK
            student_lastname = row['LastName']
            student_firstname = row['FirstName']
            student_middlename = row['MiddleName']
            section_code = row['Section Code']
            subject_code = row['SubjectCode'] # OK
            semester = row['Semester'] # OK
            grade = row['Grade']
            batch = row['Batch'] # OK
            
            # print full name
            print(f"{student_lastname}, {student_firstname} {student_middlename}")
            # Split the section_code by the last space and keep the first part
            course_code = section_code.rsplit(' ', 1)[0] 
            
            # Split the section_code by space, get the last part, and split it by hyphen '-' to extract year and section
            year, section = section_code.split(' ')[-1].split('-')
            # Now you can use the modified_section_code as needed in your code
            student_data = (
                db.session.query(Student,  StudentClassSubjectGrade, ClassSubject, Class, Subject, Course, Metadata)
                .join(StudentClassSubjectGrade, StudentClassSubjectGrade.StudentId == Student.StudentId)
                .join(ClassSubject, ClassSubject.ClassSubjectId == StudentClassSubjectGrade.ClassSubjectId)
                .join(Class, Class.ClassId == ClassSubject.ClassId)
                .join(Metadata, Metadata.MetadataId == Class.MetadataId)
                .join(Subject, Subject.SubjectId == ClassSubject.SubjectId)
                .join(Course, Course.CourseId == Metadata.CourseId)
                .filter(Student.StudentNumber == student_number, Metadata.Year == year, Class.Section == section, Metadata.Batch == batch, Metadata.Semester == semester,  Subject.SubjectCode == subject_code)
                .order_by(desc(Student.LastName), desc(Metadata.Year), desc(Class.Section), desc(Metadata.Batch))
                .first()
            )
            print('student_data.Class.IsGradeFinalized: ', student_data.Class.IsGradeFinalized)
            if(student_data.Class.IsGradeFinalized==False):
                print('student_data.Class.IsGradeFinalized: ', student_data.Class.IsGradeFinalized)
                if isinstance(grade, int) or isinstance(grade, float):
                    if grade <= 3: # PASSED
                        student_data.StudentClassSubjectGrade.Grade = grade
                        student_data.StudentClassSubjectGrade.AcademicStatus = 1
                        db.session.add(student_data.StudentClassSubjectGrade)
                        is_some_submitted = True
                    elif grade > 3 and grade <= 5: # FAILED
                        student_data.StudentClassSubjectGrade.Grade = grade
                        student_data.StudentClassSubjectGrade.AcademicStatus = 2
                        db.session.add(student_data.StudentClassSubjectGrade)
                        is_some_submitted = True
                else:
                    if grade == "Inc" or grade == 'Incomplete' or grade == "I": # WITHDRAWN
                        student_data.StudentClassSubjectGrade.AcademicStatus = 3
                        # Update grade to 0
                        student_data.StudentClassSubjectGrade.Grade = 0
                        db.session.add(student_data.StudentClassSubjectGrade)
                        is_some_submitted = True
                    else: # DROPOUT
                        student_data.StudentClassSubjectGrade.AcademicStatus = 4
                        # Update grade
                        student_data.StudentClassSubjectGrade.Grade = 0
                        db.session.add(student_data.StudentClassSubjectGrade)
                        is_some_submitted = True
            else:
                # Append the object to list_finalized_grade
                list_finalized_grade.append({
                    "StudentNumber": student_number,
                    "LastName": student_lastname,
                    "FirstName": student_firstname,
                    "MiddleName": student_middlename,
                    "SectionCode": section_code,
                    "SubjectCode": subject_code,
                    "Semester": semester,
                    "Grade": grade,
                    "Batch": batch,
                    "Error": "Grade has been finalized already in class"
                })
        # If all data is updated successfully then commit the data
        db.session.commit()
        
        if list_finalized_grade and is_some_submitted:
            return jsonify({'warning': 'Some data cannot be updated', 'errors': list_finalized_grade}), 400
        elif list_finalized_grade and not is_some_submitted:
            return jsonify({'error': 'All data are already finalized or not existing', 'errors': list_finalized_grade}), 400
        else:
            return jsonify({'result': 'File uploaded and data processed successfully'}), 200

    except Exception as e:
        print("ERROR: ", e)
        return jsonify({'error': 'An error occurred while processing the file'}), 500
    
def getClassSubject(class_id):
    try:
        data_class_subject = (
            db.session.query(Class, Metadata, ClassSubject, Subject, ClassSubjectGrade, Course)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .join(ClassSubject, ClassSubject.ClassId == Class.ClassId)
            .join(Subject, Subject.SubjectId == ClassSubject.SubjectId)
            .join(Course, Course.CourseId == Metadata.CourseId)
            .join(ClassSubjectGrade, ClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
            .filter(ClassSubject.ClassId == class_id)
            .all()
        )

        if data_class_subject:
            # For loop the data_student and put it in dictionary
            list_class_subject = []
            for class_subject in data_class_subject:
                # Combine the course_code, year, section to class_name variable
                class_name = f"{class_subject.Course.CourseCode} {class_subject.Metadata.Year}-{class_subject.Class.Section}"

                # Check if the class_subject.FacultyId exists, if yes, make a query for it
                if class_subject.ClassSubject.FacultyId or class_subject.ClassSubject.Schedule:
                    teacher_id = 0
                    if class_subject.ClassSubject.FacultyId:
                        teacher = db.session.query(Faculty).filter(Faculty.FacultyId == class_subject.ClassSubject.FacultyId).first()
                        if teacher:
                            teacher_id = teacher.FacultyId

                    schedule = class_subject.ClassSubject.Schedule if class_subject.ClassSubject.Schedule else None
                else:
                    teacher_id = None
                    schedule = None

                dict_class_subject = {
                    "ClassSubjectId": class_subject.ClassSubject.ClassSubjectId,
                    "SubjectCode": class_subject.Subject.SubjectCode,
                    "Section Code": class_name,
                    "Grade": round(class_subject.ClassSubjectGrade.Grade, 2) if class_subject.ClassSubjectGrade else None,
                    "Subject": class_subject.Subject.Name,
                    "TeacherId": teacher_id,
                    "Schedule": schedule,
                    'Batch': class_subject.Metadata.Batch if class_subject.Metadata else None,
                }

                # Append the data
                list_class_subject.append(dict_class_subject)

            return jsonify({'data': list_class_subject})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    
def getClassDetails(class_id):
    try:
        data_class_details = db.session.query(Class, Metadata, Course).join(Metadata, Metadata.MetadataId == Class.MetadataId).join(Course, Course.CourseId == Metadata.CourseId).filter(Class.ClassId == class_id).all()
        
        if data_class_details:
                # For loop the data_student and put it in dictionary
            for class_details in data_class_details:
                # Combine the course_code, year, section to class_name variable
                class_name = f"{class_details.Course.CourseCode} {class_details.Metadata.Year}-{class_details.Class.Section}"

                dict_class_details = {
                    "Course": class_details.Course.Name,
                    "Section Code": class_name,
                    'Batch': class_details.Metadata.Batch,
                    "Semester": class_details.Metadata.Semester
                }
                return jsonify({'data': dict_class_details})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    

# DOING HERE
def getStudentClassSubjectData(classSubjectId, skip, top, order_by, filter):
    try:
        data_class_details = db.session.query(ClassSubject).filter_by(ClassSubjectId = classSubjectId).first()
        
        # Get the StudentClassSubjectGrade
        if data_class_details:
            data_student_subject_grade_query = db.session.query(StudentClassSubjectGrade, Student).join(Student, Student.StudentId == StudentClassSubjectGrade.StudentId)
            
            # Default filter
            # .filter(StudentClassSubjectGrade.ClassSubjectId == data_class_details.ClassSubjectId).all()
            
            filter_conditions = []
            
            filter_conditions.append(
                StudentClassSubjectGrade.ClassSubjectId == classSubjectId
            )
            
            if filter:
                filter_parts = filter.split(' and ')
                for part in filter_parts:
                    
                    # Check if part has to lower in value
                    if '(tolower(' in part:
                        # Extracting column name and value
                        column_name = part.split("(")[3].split("),'")[0]
                        value = part.split("'")[1]
                        column_str = None
                        if column_name.strip() == 'StudentNumber':
                            column_str = getattr(Student, 'StudentNumber')
                        elif column_name.strip() == 'LastName':
                            column_str = getattr(Student, 'LastName')
                        elif column_name.strip() == 'FirstName':
                            column_str = getattr(Student, 'FirstName')
                        elif column_name.strip() == 'MiddleName':
                            column_str = getattr(Student, 'MiddleName')
                        elif column_name.strip() == 'Email':
                            column_str =  getattr(Student, 'Email')     
                            
                        if column_str:
                            # Append column_str
                            filter_conditions.append(
                                func.lower(column_str).like(f'%{value}%')
                            )
                    else:
                        # column_name = part[0][1:]  # Remove the opening '('
                        column_name, value = [x.strip() for x in part[:-1].split("eq")]
                        column_name = column_name[1:]
                        
                        column_num = None
                        int_value = value.strip(')')
                
                        if column_name.strip() == 'Grade':
                            column_num = StudentClassSubjectGrade.Grade
                        
                            filter_conditions.append(
                                column_num == int_value
                            )
                            
            filter_query = data_student_subject_grade_query.filter(and_(*filter_conditions))
            
            if order_by:
                # Determine the order attribute
                if order_by.split(' ')[0] == 'StudentNumber':
                    order_attr = getattr(Student, 'StudentNumber')
                elif order_by.split(' ')[0] == "LastName":
                    order_attr = getattr(Student, 'LastName')
                elif order_by.split(' ')[0] == "FirstName":
                    order_attr = getattr(Student, 'FirstName')
                elif order_by.split(' ')[0] == "MiddleName":
                    order_attr = getattr(Student, 'MiddleName')
                elif order_by.split(' ')[0] == 'Email':
                    order_attr = getattr(Student, 'Email')
                elif order_by.split(' ')[0] == 'Grade':
                    order_attr = getattr(StudentClassSubjectGrade, 'Grade')
                else:
                    order_attr = getattr(StudentClassSubjectGrade, 'DateEnrolled')
    
                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(order_attr))
                else:
                    order_query = filter_query.order_by(order_attr)
            else:
                # Apply default sorting
                order_query = filter_query.order_by(desc(Student.StudentNumber))
        
        
            # Query for counting all records
            total_count = order_query.count()
            # Limitized query = 
            student_limit_offset_query = order_query.offset(skip).limit(top).all()
            
            if student_limit_offset_query:
                list_student_data = []
                    # For loop the data_student and put it in dictionary
                for student_subject_grade in student_limit_offset_query:
                    dict_student_subject_grade = {
                        'DateEnrolled': student_subject_grade.StudentClassSubjectGrade.DateEnrolled,
                        "ClassSubjectId": student_subject_grade.StudentClassSubjectGrade.ClassSubjectId,
                        "StudentId": student_subject_grade.Student.StudentId,
                        "StudentNumber": student_subject_grade.Student.StudentNumber,
                        "LastName": student_subject_grade.Student.LastName,
                        "FirstName": student_subject_grade.Student.FirstName,
                        "MiddleName": student_subject_grade.Student.MiddleName,
                        "Email": student_subject_grade.Student.Email,
                        "Grade": student_subject_grade.StudentClassSubjectGrade.Grade
                    }
                    list_student_data.append(dict_student_subject_grade)
                return  jsonify({'result': list_student_data, 'count': total_count}), 200
            else:
                return jsonify({'result': [], 'count': 0})
        else:
            return None
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    
def deleteClassSubjectStudent(class_subject_id, student_id):
    try:
        student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(ClassSubjectId = class_subject_id, StudentId = student_id).first()
        # Find class_subject
        class_subject = db.session.query(ClassSubject).filter_by(ClassSubjectId = class_subject_id).first()
        # Find the class_subject with same ClassId
        class_subjects = db.session.query(ClassSubject).filter_by(ClassId = class_subject.ClassId).all()
        # for loop the class_subjects and count the amount of subject of student
        total_subjects = 0
        
        # Get Class
        class_data = db.session.query(Class).filter_by(ClassId = class_subject.ClassId).first()
        
        # Check if grade is already finalized
        if class_data.IsGradeFinalized:
            return jsonify({'success': False, 'error': 'Cannot delete student because the grade is already finalized'}), 400
        
        for class_subject in class_subjects:
            student_class_subject_grade_data = db.session.query(StudentClassSubjectGrade).filter_by(ClassSubjectId = class_subject.ClassSubjectId, StudentId = student_id).first()
            if student_class_subject_grade_data:
                total_subjects += 1
                if total_subjects == 2:
                    break
                
        if student_class_subject_grade:
            if total_subjects == 1:
                # Delete the student_class_grade:
                student_class_grade = db.session.query(StudentClassGrade).filter_by(ClassId = class_subject.ClassId, StudentId = student_id).first()
                db.session.delete(student_class_grade)
            
            db.session.delete(student_class_subject_grade)
            db.session.commit()
            return jsonify({'success': True, 'result': 'Data deleted successfully'}), 200
        else:
            return jsonify({'error': 'Data cannot be deleted'})
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    # getCurriculumSubject


def deleteStudentData(studentId):
    try:
      # Find student
        student_data = db.session.query(Student).filter_by(StudentId = studentId).first()
        if student_data:
            # Check if student existing in one of the class subject grade
            student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(StudentId = studentId).first()
            if student_class_subject_grade:
                return jsonify({'error': 'Student cannot be deleted because it is existing in the class already'}), 400
            else:
                db.session.delete(student_data)
                db.session.commit()
                return jsonify({'result': 'Data deleted successfully'}), 200
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': e}), 500

def getCurriculumData(skip, top, order_by, filter):
    try:
        
        metadata_query = (
            db.session.query(Curriculum, Metadata, Course, Subject)
            .join(Metadata, Metadata.MetadataId == Curriculum.MetadataId)
            .join(Course, Course.CourseId == Metadata.CourseId)
            .join(Subject, Subject.SubjectId == Curriculum.SubjectId)
        )
        
        # metadata_query = db.session.query(Curriculum, Metadata, Course, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Course, Course.CourseId == Metadata.CourseId).join(Subject, Subject.SubjectId == Curriculum.SubjectId)
        # DEFAULT ORDER BY
        # .order_by(desc(Metadata.Batch), desc(Metadata.Year)).all()
        
        filter_conditions = []
        # Split filter string by 'and'
        # append the str_teacher_id
        if filter:
            filter_parts = filter.split(' and ')
            for part in filter_parts:
                # Check if part has to lower in value
                if '(tolower(' in part:
                    # Extracting column name and value
                    column_name = part.split("(")[3].split(")")[0]
                    value = part.split("'")[1]
                    column_str = None
                    
                    if column_name.strip() == 'CourseCode':
                        column_str = getattr(Course, 'CourseCode')
                    elif column_name.strip() == 'SubjectCode':
                        column_str = getattr(Subject, 'SubjectCode')
                    elif column_name.strip() == 'Subject':
                        column_str =  getattr(Subject, 'Name')     
                 
                    if column_str:
                        # Append column_str
                        filter_conditions.append(
                            func.lower(column_str).like(f'%{value}%')
                        )
                else:
                    # column_name = part[0][1:]  # Remove the opening '('
                    column_name, value = [x.strip() for x in part[:-1].split("eq")]
                    column_name = column_name[1:]
                    
                    column_num = None
                    int_value = value.strip(')')

                    if not int_value.isdigit():
                        int_value = 0
                    
                    if column_name.strip() == 'Year':
                        column_num = Metadata.Year
                    elif column_name.strip() == 'Batch':
                        column_num = Metadata.Batch
                    elif column_name.strip() == 'Semester':
                        column_num = Metadata.Semester
                    
                    if column_num:
                        # Append column_num
                        filter_conditions.append(
                            column_num == int_value
                        )
                    
        filter_query = metadata_query.filter(and_(*filter_conditions))
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'CourseCode':
                order_attr = getattr(Course, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == "SubjectCode":
                order_attr = getattr(Subject, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == 'Subject':
                order_attr = getattr(Subject, 'Name')
            elif order_by.split(' ')[0] == 'Year':
                order_attr = getattr(Metadata, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == 'Semester':
                order_attr = getattr(Metadata, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == 'Batch':
                order_attr = getattr(Metadata, order_by.split(' ')[0])
           
           
            if ' ' in order_by:
                order_query = filter_query.order_by(desc(order_attr))
            else:
                order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(desc(Metadata.Batch), desc(Metadata.Year))
        
        
        # Query for counting all records
        total_count = order_query.count()
        # Limitized query = 
        metadata_limit_offset = order_query.offset(skip).limit(top).all()

       
        
        # Get the StudentClassSubjectGrade
        if metadata_limit_offset:
            list_metadata = []
                # For loop the data_student and put it in dictionary
            for data in metadata_limit_offset:
                # Convert the Year to 1st, 2nd, 3rd, 4th
                dict_metadata = {
                    "CurriculumId": data.Curriculum.CurriculumId,
                    "MetadataId": data.Metadata.MetadataId,
                    "Year": data.Metadata.Year,
                    "Semester": data.Metadata.Semester,
                    "Batch": data.Metadata.Batch,
                    "CourseCode": data.Course.CourseCode,
                    "Subject": data.Subject.Name,
                    "SubjectCode": data.Subject.SubjectCode
                }
                list_metadata.append(dict_metadata)
            
            return jsonify({'result': list_metadata, 'count': total_count})

        else:
            return jsonify({'result': [], 'count': 0})
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        print("ERROR: ", e)
        return None
    
    
def getCurriculumOptions():
    try:
      # Get all unique SubjectCode and CourseCode
        unique_subject_code = db.session.query(Subject).all()
        unique_course_code = db.session.query(Course).all()
        
        if not unique_subject_code:
            return jsonify({'error': 'No subject found'}), 400
        elif not unique_course_code:
            return jsonify({'error': 'No course found'}), 400
        else:
            year_options = []
            batch_options = []
            semester_options = []
            course_options = []
            subject_options = []
            
            current_year = datetime.now().year
            previous_year = current_year - 1
            future_year = current_year + 1
            
            # Options for frontend
            year = [1, 2, 3, 4]
            batch = [previous_year , current_year, future_year]
            semesters = [1, 2, 3]
            
            
            for y in year:
                year_dict = {
                    "Year": y
                }
                year_options.append(year_dict)
                
            for b in batch:
                batch_dict = {
                    "Batch": b
                }
                batch_options.append(batch_dict)
            
            for s in semesters:
                semester_dict = {
                    "Semester": s
                }
                semester_options.append(semester_dict)
            
            for c in unique_course_code:
                course_dict = {
                    "CourseCode": c.CourseCode
                }
                course_options.append(course_dict)
                
            for s in unique_subject_code:
                subject_dict = {
                    "SubjectCode": s.SubjectCode + ' - ' + s.Name
                }
                subject_options.append(subject_dict)
            
            # Return all options
            return jsonify({'result': {'yearOptions': year_options, 'subjectCodeOptions': subject_options, 'batchOptions': batch_options, 'courseOptions': course_options, 'semesterOptions': semester_options}})
        
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': e})
    

def getCurriculumSubject(metadata_id):
    try:
        curriculum_subjects = db.session.query(Curriculum, Subject).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Curriculum.MetadataId == metadata_id).all()
        # Get the StudentClassSubjectGrade
        if curriculum_subjects:
            list_curriculum_subjects = []
                # For loop the data_student and put it in dictionary
            for data in curriculum_subjects:
                dict_curriculum_subjects = {
                    "Subject Code": data.Subject.SubjectCode,
                    "Name": data.Subject.Name,
                    "Units": "{:.2f}".format(round(data.Subject.Units, 2))
                }
                list_curriculum_subjects.append(dict_curriculum_subjects)
            return  jsonify({'data': list_curriculum_subjects})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    

def getActiveTeacher():
    try:
        active_teacher = db.session.query(Faculty).filter_by(Status = "Active").all()
        # Get the StudentClassSubjectGrade
        if active_teacher:
            list_active_teacher = []
                # For loop the active_teacher and put it in dictionary
            for data in active_teacher:
                middle_name = data.MiddleName if data.MiddleName else ""
                full_name = f"{data.LastName}, {data.FirstName} {middle_name}"
                
                dict_active_teacher = {
                    "TeacherId": data.FacultyId,
                    "TeacherName": full_name,
                }
                list_active_teacher.append(dict_active_teacher)
            return  jsonify({'data': list_active_teacher})
        # Else no teacher message
        else:
            return jsonify({'error': 'No active teacher found'}), 400
        
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    
def processAddingCurriculumSubjects(data, excelType=False):
    # MANUAL ADDING DATA
    if excelType == False:
        course_code = data['CourseCode']
        subject_code = data['SubjectCode']
        year_level = data['Year']
        semester = data['Semester']
        batch = data['Batch']
        
        if ' - ' in subject_code:
            # Split and get the 1st element
            subject_code = subject_code.split(' - ')[0]
        
        course = db.session.query(Course).filter_by(CourseCode = course_code).first()
                
        # Check if course existing
        if not course:
            
            # Return cannot added data. Course already exist
            return jsonify({'error': 'Invalid Course'}), 400
        else:
            # Check if already have classes and avoid adding curriculum.
            class_data = db.session.query(Class, Metadata).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(Metadata.Year == year_level, Metadata.Semester == semester, Metadata.Batch == batch, Metadata.CourseId == course.CourseId).first()
            if class_data:
                # Return cannot added data. Class already exist
                return jsonify({'error': 'Cannot add subject curriculum has already class existing.'}), 400
            
            metadata = db.session.query(Metadata).filter_by(Year = year_level, Semester = semester, Batch = batch, CourseId = course.CourseId).first()
            # Check if have a class already with yhe same year_level, semester, batch and course id
            if metadata:                
                # Check if subject is existing
                subject = db.session.query(Subject).filter_by(SubjectCode = subject_code).first()
                
                if subject:
                    # Check if Curriculum is existing
                    curriculum_subject_exist = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Metadata.CourseId == course.CourseId, Subject.SubjectCode == subject_code, Metadata.Year == year_level, Metadata.Semester == semester, Metadata.Batch == batch).first()
                    
                    # If no curriculum subject exist then create curriculum
                    if not curriculum_subject_exist:
                        # Create a curriculum
                        new_curriculum = Curriculum(
                            MetadataId=metadata.MetadataId,
                            SubjectId=subject.SubjectId
                        )
                    
                        db.session.add(new_curriculum)
                        db.session.commit()                        
                        
                        dict_subject = subject.to_dict()
                        
                        # Return data added successfully
                        return jsonify({'success': 'Data added successfully'}), 200
                    else:
                        # Return cannot added data. Curriculum already exist
                        return jsonify({'error': 'Curriculum already exist'}), 400
                else:
                    # Return cannot added data. Invalid Subject Code
                    return jsonify({'error': 'Invalid Subject Code'}), 400
            else:
                 # Check if LatestBatchSemester already have the same Batch, Semester
                # batch_semester = db.session.query(LatestBatchSemester).filter_by(Batch = batch, Semester = semester).first()
                # # Check if batch semester not exist then create one
                # if not batch_semester:
                #     # Create a batch semester
                #     new_batch_semester = LatestBatchSemester(
                #         Batch=batch,
                #         Semester=semester
                #     )
                    
                #     db.session.add(new_batch_semester)
                #     db.session.flush()
                #     print("NEW BATCH ADDED ", batch , ' ' , semester )
                
                # Check if subject is existing
                subject = db.session.query(Subject).filter_by(SubjectCode = subject_code).first()   
        
                new_metadata = Metadata(
                    CourseId=course.CourseId,
                    Year=year_level,
                    Semester=semester,
                    Batch=batch
                )
                    
                db.session.add(new_metadata)
                db.session.flush()
                                                    
                if subject:                       
                    curriculum_subject_exist = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Subject.SubjectCode == subject_code, Metadata.Year == year_level, Metadata.Semester == semester, Metadata.Batch == batch).first()
                        
                    if not curriculum_subject_exist:
                        # Create a curriculum
                        new_curriculum = Curriculum(
                            MetadataId=new_metadata.MetadataId,
                            SubjectId=subject.SubjectId
                        )
                
                        db.session.add(new_curriculum)
                        db.session.commit()
                        
                        dict_subject = subject.to_dict()
                        
                        # Return data added successfully
                        return jsonify({'success': 'Data added successfully', 'SubjectName': dict_subject['Name']}), 200
                    else:
                        # Return cannot added data. Curriculum already exist
                        return jsonify({'error': 'Already exist'}), 400
                    
                else:
                    # Return cannot added data. Invalid Subject Code
                    return jsonify({'error': 'Invalid Subject Code'}), 400
            
    # EXCEL TYPE
    if excelType == True:
        # Check if the file is empty
        if data.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Check file extension
        if not data.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

        # Read the Excel file into a DataFrame
        df = pd.read_excel(data)

        # dict data list
        list_curriculum_subjects = []
        errors = []
        
        # For example, you can iterate through rows and access columns like this:
        for index, row in df.iterrows():
            # Extract the values from the DataFrame
            course_code = row['Course']
            subject_code = row['Subject Code']
            year_level = row['Year']
            semester = row['Semester']
            batch = row['Batch']
            print("DONE GETTING")
            
            # Check if all field have value
            if not course_code and not subject_code and not year_level and not semester and not batch:
                # End the loop
                break
            
            if course_code:
                course = db.session.query(Course).filter_by(CourseCode = course_code).first()
                
            print("AFTER GETTING")
            # Check if course existing
            if not course:
                errors.append({
                    "Course": course_code,
                    "Subject Code": subject_code,
                    "Year": year_level,
                    "Semester": semester,
                    "Batch": batch,
                    "Error": "Invalid Course"
                })
            else:
                # Check if already have classes and avoid adding curriculum.
                class_data = db.session.query(Class, Metadata).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(Metadata.Year == year_level, Metadata.Semester == semester, Metadata.Batch == batch, Metadata.CourseId == course.CourseId).first()
                if class_data:
                    errors.append({
                                "Course": course_code,
                                "Subject Code": subject_code,
                                "Year": year_level,
                                "Semester": semester,
                                "Batch": batch,
                                "Error": "Curriculum has already class existing"
                    })
                    # Go to next for loop
                    continue
                
                metadata = db.session.query(Metadata).filter_by(Year = year_level, Semester = semester, Batch = batch, CourseId = course.CourseId).first()
                
                if metadata:
                    # Check if subject is existing
                    subject = db.session.query(Subject).filter_by(SubjectCode = subject_code).first()
                    
                    if subject:
                        # Check if Curriculum is existing
                        curriculum_subject_exist = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Metadata.CourseId == course.CourseId, Subject.SubjectCode == subject_code, Metadata.Year == year_level, Metadata.Semester == semester, Metadata.Batch == batch).first()
                        if not curriculum_subject_exist:
                            # Create a curriculum
                            new_curriculum = Curriculum(
                                MetadataId=metadata.MetadataId,
                                SubjectId=subject.SubjectId
                            )
                        
                            db.session.add(new_curriculum)
                            db.session.commit()
                            
                            # Append the list_curriculum_subjects
                            list_curriculum_subjects.append({
                                "MetadataId": metadata.MetadataId,
                                "Course": course_code,
                                "Subject Code": subject_code,
                                "Year": year_level,
                                "Semester": semester,
                                "Batch": batch
                            })
                        else:
                            db.session.rollback()
                            errors.append({
                                "Course": course_code,
                                "Subject Code": subject_code,
                                "Year": year_level,
                                "Semester": semester,
                                "Batch": batch,
                                "Error": "Curriculum subject already exist"
                            })
                            
                            
                    else:
                        db.session.rollback()
                        errors.append({
                                "Course": course_code,
                                "Subject Code": subject_code,
                                "Year": year_level,
                                "Semester": semester,
                                "Batch": batch,
                                "Error": "Invalid Subject Code"
                        })
                        
                else: # NO META DATA FIELD
                     # Check if LatestBatchSemester already have the same Batch, Semester
                    # batch_semester = db.session.query(LatestBatchSemester).filter_by(Batch = batch, Semester = semester).first()
                    # # Check if batch semester not exist then create one
                    # if not batch_semester:
                    #     # Create a batch semester
                    #     new_batch_semester = LatestBatchSemester(
                    #         Batch=batch,
                    #         Semester=semester
                    #     )
                        
                    #     db.session.add(new_batch_semester)
                    #     db.session.flush()
                    #     print("NEW BATCH ADDED ", batch , ' ' , semester )
                    # Check if subject is existing
                    subject = db.session.query(Subject).filter_by(SubjectCode = subject_code).first()   
            
                    new_metadata = Metadata(
                        CourseId=course.CourseId,
                        Year=year_level,
                        Semester=semester,
                        Batch=batch
                    )
                        
                    db.session.add(new_metadata)
                    db.session.flush()
                                                        
                    if subject:                       
                        curriculum_subject_exist = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Subject.SubjectCode == subject_code, Metadata.Year == year_level, Metadata.Semester == semester, Metadata.Batch == batch).first()
                            
                        if not curriculum_subject_exist:
                            # Create a curriculum
                            new_curriculum = Curriculum(
                                MetadataId=new_metadata.MetadataId,
                                SubjectId=subject.SubjectId
                            )
                    
                            db.session.add(new_curriculum)
                            db.session.commit()
                            
                            # Append the list_curriculum_subjects
                            list_curriculum_subjects.append({
                                "MetadataId": new_metadata.MetadataId,
                                "Course": course_code,
                                "Subject Code": subject_code,
                                "Year": year_level,
                                "Semester": semester,
                                "Batch": batch
                            })
                        else:
                            db.session.rollback()
                            errors.append({
                                "Course": course_code,
                                "Subject Code": subject_code,
                                "Year": year_level,
                                "Semester": semester,
                                "Batch": batch,
                                "Error": "Already exist"
                            })
                        
                    else:
                        db.session.rollback()
                        errors.append({
                                "Course": course_code,
                                "Subject Code": subject_code,
                                "Year": year_level,
                                "Semester": semester,
                                "Batch": batch,
                                "Error": "Invalid Subject Code"
                        })
                    
            
        if errors and not list_curriculum_subjects:
            return jsonify({'error': 'Something went wrong. The data could not be processed successfully.', 'errors': errors}), 500
        if errors and list_curriculum_subjects:
            return jsonify({'warning': 'Some data added successfully', 'errors': errors, 'data': list_curriculum_subjects}), 500
        else:
            db.session.commit()
            return  jsonify({'result': 'Data added successfully', 'data': (list_curriculum_subjects)}), 200
        
        
def deleteCurriculumSubjectData(curriculumId):
    try:
      # Get curriculum
        curriculum = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Curriculum.CurriculumId == curriculumId).first()
      
        if curriculum:
            # Find a class that has the same metadata value which is CourseId, Year, Semester, Batch
            class_data = db.session.query(Class, Metadata).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(Metadata.CourseId == curriculum.Metadata.CourseId, Metadata.Year == curriculum.Metadata.Year, Metadata.Semester == curriculum.Metadata.Semester, Metadata.Batch == curriculum.Metadata.Batch).first()
            
            if class_data:
                return jsonify({'error': 'Cannot delete subject. Already have class existing'}), 400
            else:
                # Get curriculum, metadata, subject that matches the same year and semester of it
                curriculum_subjects = db.session.query(Curriculum, Metadata).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).filter(Metadata.Semester == curriculum.Metadata.Semester, Metadata.Batch == curriculum.Metadata.Batch).all()
                
                # Check if curriculum subjects if onle have 1
                if len(curriculum_subjects) == 1:
                    # Delete the LatestBatchSemester with the same batch and semester
                    db.session.delete(curriculum.Metadata)
                    # db.session.query(LatestBatchSemester).filter_by(Batch = curriculum.Metadata.Batch, Semester = curriculum.Metadata.Semester).delete()
                    # Delete the metadata also
                    
                
                # Look for curriculum that has the same MetadataId and limit it to 2 sstore in curricu
                
                db.session.delete(curriculum.Curriculum)
                db.session.commit()
                return jsonify({'result': 'Data deleted successfully'}), 200
        else:
            return jsonify({'error': 'Data cannot be deleted'}), 400
        
    except Exception as e:
        # Rollback the changes in case of an error
        db.session.rollback()
        # Return an error response
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
      

def processUpdatingClassSubjectDetails(data):
    try:
        if data:
            # Update all data in the database
            for class_subject in data:

                class_subject_id = class_subject['ClassSubjectId']
                
                # Get the teacher_name, set it to None if 'TeacherName' is not present
                teacher_id = class_subject['TeacherId']
                schedule = class_subject['Schedule']
                
                # If teacher_id update teacher_id only:
                if teacher_id:
                    db.session.query(ClassSubject).filter_by(ClassSubjectId=class_subject_id).update({
                        'TeacherId': teacher_id
                    })
                
                if schedule:
                    db.session.query(ClassSubject).filter_by(ClassSubjectId=class_subject_id).update({
                        'Schedule': schedule
                    })
                    
                if teacher_id and schedule:
                    db.session.query(ClassSubject).filter_by(ClassSubjectId=class_subject_id).update({
                        'TeacherId': teacher_id,
                        'Schedule': schedule
                    })

            # Commit the changes to the database
            db.session.commit()

            # Return success
            return jsonify({'result': 'Data updated successfully'}), 200
        else:
            # Return updating details failed
            return jsonify({'error': 'Updating details failed. No data provided'}), 500
    except Exception as e:
        # Rollback the changes in case of an error
        db.session.rollback()
        # Return an error response
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


def processAddingStudentInSubject(data, class_subject_id, excelType=False):
    try:
        if excelType:
            if data.filename == '':
                return jsonify({'error': 'No selected file'}), 400

            if not data.filename.endswith(('.xlsx', '.xls')):
                return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

            df = pd.read_excel(data)
            list_students_added = []
            
            # list_student_graduate = []
            errors = []

            class_subject = db.session.query(ClassSubject, Class).join(Class, Class.ClassId == ClassSubject.ClassId).filter(ClassSubject.ClassSubjectId == class_subject_id).first()

             # Get the class
            class_data = db.session.query(Class, Metadata).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(Class.ClassId==class_subject.Class.ClassId).first()
            
            # Check latest batch semester
            latest_batch_semester = db.session.query(LatestBatchSemester).filter_by(Batch=class_data.Metadata.Batch, Semester=class_data.Metadata.Semester).first()
            
            # Check if latest_batch_semester.IsStartEnrollment is False
            if not latest_batch_semester.IsEnrollmentStarted:
                print("SHOULD NOT ADD")
                return jsonify({'error': 'Cannot add students. Enrollment is not yet started.'}), 400
            
            # Check if grade is already finalized
            if class_data:
                if class_data.Class.IsGradeFinalized:
                    return jsonify({'error': True, 'errorLast': 'Cannot add student. Grade is already finalized'}), 400
            
            if class_subject:

                for index, row in df.iterrows():
                    # find class_subject_id
                    student_number = str(row['Student Number'])
                    student_date_enrolled = row['Date Enrolled']
                    
                    if not student_number:
                        errors.append({
                            'StudentNumber': 'N/A',
                            'DateEnrolled': student_date_enrolled,
                            'Error': 'Student Number must have a value'
                        })
                        continue
                    
                    if student_date_enrolled:
                        if isinstance(student_date_enrolled, datetime):
                            student_date_enrolled = student_date_enrolled.strftime("%Y-%m-%d")
                        else:
                            errors.append({
                                'StudentNumber': student_number,
                                'DateEnrolled': "N/A",
                                'Error': 'Invalid Date Enrolled format'
                            })
                            continue
                    
                    if not student_date_enrolled:
                        errors.append({
                            'StudentNumber': student_number,
                            'DateEnrolled': 'N/A',
                            'Error': 'Date Enrolled must have a value'
                        })
                        continue
                    
                    
                    student = db.session.query(Student).filter_by(StudentNumber = student_number).first()
                
                    if student:
                        student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(StudentId = student.StudentId, ClassSubjectId = class_subject_id).first()
                        
                        if student_class_subject_grade:
                            errors.append({
                                'StudentNumber': student_number,
                                'DateEnrolled': student_date_enrolled,
                                'Error': 'Student already exist in the subject'
                            })
                        else:
                            # Check if student has already studentClassGrade
                            student_class_grade = db.session.query(StudentClassGrade).filter_by(StudentId = student.StudentId, ClassId = class_subject.Class.ClassId).first()
                            if not student_class_grade:
                                # Create StudentClassGrade
                                new_student_class_grade = StudentClassGrade(
                                    StudentId=student.StudentId,
                                    ClassId=class_subject.Class.ClassId,
                                    Grade=0.00
                                )
                                
                                db.session.add(new_student_class_grade)
                                db.session.flush()
                            
                            # Create StudentClassSubjectGrade
                            new_student_class_subject_grade = StudentClassSubjectGrade(
                                StudentId=student.StudentId,
                                ClassSubjectId=class_subject_id,
                                DateEnrolled=student_date_enrolled,
                                Grade=0.00
                            )
                            
                            db.session.add(new_student_class_subject_grade)
                            db.session.commit()
                            
                            full_name = student.LastName + ', ' + student.FirstName + ' ' + student.MiddleName
                            dict_student_class_subject_grade = {
                                "ClassSubjectId": class_subject_id,
                                "StudentId": student.StudentId,
                                "StudentNumber": student.StudentNumber,
                                "Name": full_name,
                                "Email": student.Email,
                                "Grade": new_student_class_subject_grade.Grade
                            }

                            # append the list_students_added
                            list_students_added.append(dict_student_class_subject_grade)
                    else:
                        # Append in errors
                        errors.append({
                            'StudentNumber': student_number,
                            'DateEnrolled': student_date_enrolled,
                            'Error': 'Student Number does not exist'
                        })
                
                if errors and len(list_students_added) > 0:
                    db.session.rollback()
                    return jsonify({'warning': 'Some data added successfully', 'errors': errors, 'data': list_students_added}), 500
                elif errors and len(list_students_added) == 0:
                    db.session.rollback()
                    return jsonify({'error': 'Adding the data failed', 'errors': errors}), 500
                else:
                    return jsonify({'result': 'Data added successfully', 'data': list_students_added}), 200
            else:
                return jsonify({'error': 'Class Subject does not exist'}), 400
            
        else:
            # Get the data.StudentNumber and DateEnrolled
            student_number = data['StudentNumber']
            student_date_enrolled = data['DateEnrolled']
            
            # Check if student numberhave value and remove unecessary spaces
            if not student_number:
                return jsonify({'error': 'Student Number must have a value'}), 400
            else:
                student_number = student_number.strip()
            
            # Convert student_date_enrolled to date format
            if student_date_enrolled is not None:
                try:
                    # Adjust the format string to include the time component
                    student_date_enrolled = datetime.strptime(student_date_enrolled, "%Y-%m-%dT%H:%M:%S.%fZ")
                    
                    # Extract only the date part
                    student_date_enrolled = student_date_enrolled.date()
                    
                except Exception as e:
                    return jsonify({'error': 'Invalid Date Enrolled format'}), 400
            
            # Find class_subject_id
            class_subject = db.session.query(ClassSubject).filter_by(ClassSubjectId = class_subject_id).first()
            # Check if not class_subject then return
            if not class_subject:
                return jsonify({'error': 'Class Subject does not exist'}), 400
            
            # Get the class
            class_data = db.session.query(Class).filter_by(ClassId = class_subject.ClassId).first()
            # Check if grade is already finalized
            if class_data:
                if class_data.IsGradeFinalized:
                    return jsonify({'error': 'Cannot add student. Grade is already finalized'}), 400
            
            # Check if student_number is existing
            student = db.session.query(Student).filter_by(StudentNumber = student_number).first()
            if student:
                # Check if student has already studentClassSubjectGrade
                student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(StudentId = student.StudentId, ClassSubjectId = class_subject_id).first()
                if student_class_subject_grade:
                    return jsonify({'error': 'Student already exist in the subject'}), 400
                else:
                    # Check if student has already studentClassGrade
                    student_class_grade = db.session.query(StudentClassGrade).filter_by(StudentId = student.StudentId, ClassId = class_subject.ClassId).first()
                    if not student_class_grade:
                        # Create StudentClassGrade
                        new_student_class_grade = StudentClassGrade(
                            StudentId=student.StudentId,
                            ClassId=class_subject.ClassId,
                            Grade=0.00
                        )
                        
                        db.session.add(new_student_class_grade)
                        db.session.flush()
                    
                    # Create StudentClassSubjectGrade
                    new_student_class_subject_grade = StudentClassSubjectGrade(
                        StudentId=student.StudentId,
                        ClassSubjectId=class_subject_id,
                        DateEnrolled=student_date_enrolled,
                        Grade=0.00
                    )
                    
                    db.session.add(new_student_class_subject_grade)
                    db.session.commit()
                    
                    dict_student_class_subject_grade = {
                        "ClassSubjectId": class_subject_id,
                        "StudentId": student.StudentId,
                        "StudentNumber": student.StudentNumber,
                        "LastName": student.LastName,
                        "FirstName": student.FirstName,
                        "MiddleName": student.MiddleName,
                        "Email": student.Email,
                        "Grade": new_student_class_subject_grade.Grade
                    }
                    
                    return jsonify({'success': True, 'message': "Successfully"})
            else:
                return jsonify({'error': 'Student Number does not exist'}), 400
        
    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    
 
def getMetadata(skip, top, order_by, filter):
    try:
        
        metadata_query = db.session.query(Metadata, Course).join(Course, Course.CourseId == Metadata.CourseId).distinct(Course.CourseCode, Course.Name, Metadata.Batch, Metadata.Semester)
        
        # Order default
        # .order_by(desc(Metadata.Batch), desc(Metadata.Semester))


        filter_conditions = []
        if filter:
            filter_parts = filter.split(' and ')
            for part in filter_parts:
                # Check if part has to lower in value
                if '(tolower(' in part:
                    # Extracting column name and value
                    column_name = part.split("(")[3].split("),'")[0]
                    value = part.split("'")[1]
                    column_str = None
                    
                    if column_name.strip() == 'CourseCode':
                        column_str = getattr(Course, 'CourseCode')
                    elif column_name.strip() == 'Course':
                        column_str = getattr(Course, 'Name')
                 
                    if column_str:
                        # Append column_str
                        filter_conditions.append(
                            func.lower(column_str).like(f'%{value}%')
                        )
                else:
                    # column_name = part[0][1:]  # Remove the opening '('
                    column_name, value = [x.strip() for x in part[:-1].split("eq")]
                    column_name = column_name[1:]
                    column_num = None
                    int_value = value.strip(')')
                    
                    # Check for column name 
                    if column_name.strip() == 'Batch':
                        column_num = Metadata.Batch
                    elif column_name.strip() == 'Semester':
                        column_num = Metadata.Semester
    
                    
                    if column_num:
                        # Append column_num
                        filter_conditions.append(
                            column_num == int_value
                        )
                # END OF ELSE PART
            # END OF FOR LOOP
                
        
        # Apply all filter conditions with 'and'
  
        filter_query = metadata_query.filter(and_(*filter_conditions))
        
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'CourseCode':
                order_attr = getattr(Course, 'CourseCode')
            elif order_by.split(' ')[0] == "Course":
                order_attr = getattr(Course, 'Name')
            elif order_by.split(' ')[0] == 'Batch':
                order_attr = getattr(Metadata, 'Batch')
            elif order_by.split(' ')[0] == 'Semester':
                order_attr = getattr(Metadata, 'Semester')           
           
            if ' ' in order_by:
                order_query = filter_query.order_by(desc(order_attr))
            else:
                order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(desc(Metadata.Batch), desc(Metadata.Semester))
            # order params
            

        metadata_main_query = order_query.offset(skip).limit(top).all()
        total_count = order_query.count()

        list_metadata = []
        if metadata_main_query:
            for data in metadata_main_query:
                # Check data.Course.Name, data.Metadata.Batch and data.Metadata.Semester if exist in list_metadata
                # Find a class that has the same MetadataId
                class_data = db.session.query(Class).filter_by(MetadataId=data.Metadata.MetadataId).first()

                # Check if class_data exists
                if class_data:
                    # Set IsGradeFinalized to its value if it exists, else set it to None
                    is_grade_finalized = class_data.IsGradeFinalized if hasattr(class_data, 'IsGradeFinalized') else None
                else:
                    # Set to None if class_data doesn't exist
                    is_grade_finalized = None

                # Create a dict
                dict_metadata = {
                    'MetadataId': data.Metadata.MetadataId,
                    'Course': data.Course.Name,
                    'CourseCode': data.Course.CourseCode,
                    'Semester': data.Metadata.Semester,
                    'Batch': data.Metadata.Batch,
                    'IsGradeFinalized': is_grade_finalized
                }

                # Append the dict to the list_metadata
                list_metadata.append(dict_metadata)
            
            return jsonify({'result': list_metadata, 'count': total_count})
        else:
            return jsonify({'result': None})
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return jsonify(error=str(e))



 
def getBatchSemester(skip, top, order_by, filter):
    try:
        
        batch_semester_query = db.session.query(LatestBatchSemester)
        
        # Order default
        # .order_by(desc(Metadata.Batch), desc(Metadata.Semester))


        filter_conditions = []
        if filter:
            filter_parts = filter.split(' and ')
            for part in filter_parts:
                # Check if part has to lower in value
                if '(tolower(' in part:
                    print("STRINGS FUNCTIONS")
                    # # Extracting column name and value
                    # column_name = part.split("(")[3].split("),'")[0]
                    # value = part.split("'")[1]
                    # column_str = None
                    
                    # if column_name.strip() == 'CourseCode':
                    #     column_str = getattr(Course, 'CourseCode')
                    # elif column_name.strip() == 'Course':
                    #     column_str = getattr(Course, 'Name')
                 
                    # if column_str:
                    #     # Append column_str
                    #     filter_conditions.append(
                    #         func.lower(column_str).like(f'%{value}%')
                    #     )
                else:
                    # column_name = part[0][1:]  # Remove the opening '('
                    column_name, value = [x.strip() for x in part[:-1].split("eq")]
                    column_name = column_name[1:]
                    column_num = None
                    int_value = value.strip(')')
                    
                    # Check for column name 
                    if column_name.strip() == 'Batch':
                        column_num = LatestBatchSemester.Batch
                    elif column_name.strip() == 'Semester':
                        column_num = LatestBatchSemester.Semester
    
                    
                    if column_num:
                        # Append column_num
                        filter_conditions.append(
                            column_num == int_value
                        )
                # END OF ELSE PART
            # END OF FOR LOOP
                
        
        # Apply all filter conditions with 'and'
  
        filter_query = batch_semester_query.filter(and_(*filter_conditions))
        
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'Batch':
                order_attr = getattr(LatestBatchSemester, 'Batch')
            elif order_by.split(' ')[0] == 'Semester':
                order_attr = getattr(LatestBatchSemester, 'Semester')           
           
            if ' ' in order_by:
                order_query = filter_query.order_by(desc(order_attr))
            else:
                order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(desc(LatestBatchSemester.Batch), desc(LatestBatchSemester.Semester))
            # order params
            

        latest_batch_semester_main_query = order_query.offset(skip).limit(top).all()
        total_count = order_query.count()

        list_metadata = []
        if latest_batch_semester_main_query:
            for data in latest_batch_semester_main_query:
                # Create a dict
                # Get the data to dict
                dict_metadata = data.to_dict()

                # Append the dict to the list_metadata
                list_metadata.append(dict_metadata)
            
            return jsonify({'result': list_metadata, 'count': total_count})
        else:
            return jsonify({'result': None})
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return jsonify(error=str(e))



def getStatistics():
    try:
        # Get the teacher active in Faculty
        teacher_active_count = Faculty.query.filter_by(Status="Active").count()
        print('teacher_active_count:', teacher_active_count)
        
        # Get count of student enrolled in courses with the current year
        # Get the current year
        current_year = datetime.now().year
        # Get the count of student enrolled in courses based on DateEnrolled from last date
        student_enrolled_count = db.session.query(CourseEnrolled).filter(CourseEnrolled.DateEnrolled >= f'{current_year}-01-01').count()
        
        # Check if student enrolled if not then - 1 with current year
        if student_enrolled_count == 0:
            student_enrolled_count = db.session.query(CourseEnrolled).filter(CourseEnrolled.DateEnrolled >= f'{current_year - 1}-01-01').count()
        
        # Get the class
        class_data_count = db.session.query(Class, Metadata).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(Metadata.Batch == current_year).count()
        
        # Check if class data
        if class_data_count == 0:
            class_data_count = db.session.query(Class, Metadata).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(Metadata.Batch == current_year - 1).count()
        # Return all elements
        return jsonify({ 
            'success': True, 
            'result':{
                'teacher_active_count': teacher_active_count,
                'student_enrolled_count': student_enrolled_count,
                'class_data_count': class_data_count
            }
        })
        
    except Exception as e:
        print("ERROR: ", e)
        # Rollback the changes in case of an error
        db.session.rollback()
        # Return an error response
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500



def getClassListDropdown(batch=False):
    # Get all unique class with distinc of CourseId, Year, Section
    if batch:
        class_grade_query = db.session.query(Class, Metadata,  Course, ClassGrade).join(Metadata, Metadata.MetadataId == Class.MetadataId).join(Course, Course.CourseId == Metadata.CourseId).join(ClassGrade, ClassGrade.ClassId == Class.ClassId).all()
        
        if class_grade_query:
            # loop the data of it
            list_class = []
            for data in class_grade_query:
                section = str(data.Metadata.Year) + "-" + str(data.Class.Section)

                dict_class = {
                    "course": data.Course.CourseCode,
                    "section": section,
                    "batch": data.Metadata.Batch
                }
                # Append
                list_class.append(dict_class)
        
            return list_class
    else:
        class_grade_query = db.session.query(Class, Metadata,  Course, ClassGrade).join(Metadata, Metadata.MetadataId == Class.MetadataId).join(Course, Course.CourseId == Metadata.CourseId).join(ClassGrade, ClassGrade.ClassId == Class.ClassId).distinct(Course.CourseId, Metadata.Year, Class.Section).all()
        
        if class_grade_query:
            # loop the data of it
            list_class = []
            for data in class_grade_query:
                section = str(data.Metadata.Year) + "-" + str(data.Class.Section)

                dict_class = {
                    "course": data.Course.CourseCode,
                    "section": section
                }
                # Append
                list_class.append(dict_class)
        
            return list_class


def startEnrollmentProcess(batch_semester_id):
    try:
        # Get tlatest batch semester 
        latest_batch_semester = db.session.query(LatestBatchSemester).filter_by(LatestBatchSemesterId = batch_semester_id).first()
        
        # Check if IsEnrollmentStarted is true
        if latest_batch_semester.IsEnrollmentStarted:
            return jsonify({'error': True, 'message': 'Enrollment is already started'}), 400
        elif latest_batch_semester.IsGradeFinalized:
            return jsonify({'error': True, 'message': 'Cannot start enrollment. Grade is already finalized'}), 400
        else:
            latest_batch_semester.IsEnrollmentStarted = True
         
            db.session.commit()
            return jsonify({'success': True, 'message': 'Enrollment started successfully'}), 200
    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()
        # Return an error response
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


def getListersCount():
    try:
        
        def get_classes_query(current_year):
            return (
                db.session.query(
                    Metadata.CourseId,
                    Course.CourseCode,
                    func.sum(ClassGrade.DeansLister).label('deans_lister_count'),
                    func.sum(ClassGrade.PresidentsLister).label('presidents_lister_count')
                )
                .join(Class, Metadata.MetadataId == Class.MetadataId)
                .join(Course, Course.CourseId == Metadata.CourseId)
                .join(ClassGrade, ClassGrade.ClassId == Class.ClassId)
                .filter(Metadata.Batch == current_year)
                .group_by(Metadata.CourseId, Course.CourseCode)
                .all()
            )
            
        current_year = datetime.now().year

        # Get classes query for the current year
        classes_query = get_classes_query(current_year)

        # If there are no results, try the previous year
        if not classes_query:
            current_year -= 1
            classes_query = get_classes_query(current_year)

        list_lister_data = []

        for result in classes_query:
            course_id, course_code, deans_lister_count, presidents_lister_count = result

            # Make a dictionary for it
            dict_lister_data = {
                'CourseId': course_id,
                'CourseCode': course_code,
                'DeansListerCount': deans_lister_count,
                'PresidentsListerCount': presidents_lister_count
            }
            # Append
            list_lister_data.append(dict_lister_data)

        # Return all elements
        return jsonify({'success': True, 'result': list_lister_data})
    except Exception as e:
        # Rollback the changes in case of an error
        db.session.rollback()
        # Return an error response
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


def deleteClassData(classId):
    try:
        # Find the class using classId
        class_data = db.session.query(Class, Metadata).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(Class.ClassId == classId).first()
        
        # Check if class data exist
        if class_data:
            # Check if class data isGradeFinalized already
            if class_data.Class.IsGradeFinalized:
                return jsonify({'error': 'Cannot delete class. Grade is already finalized'}), 400
                
            
            # Get all class subject
            class_subject = db.session.query(ClassSubject).filter_by(ClassId = classId).all()
            
            # Check all class subject if have student
            for data in class_subject:
                # Get all student class subject grade
                student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(ClassSubjectId = data.ClassSubjectId).first()
                
                # Check if student_class_subject_grade has value
                if student_class_subject_grade:
                    # Return cannot be deleted it already have students listed
                    return jsonify({'error': 'Cannot delete class. Class has students'}), 400
    
            # For deleting latest batch semester (If equal to 1 delete)
            class_count = db.session.query(Class, Metadata).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(Metadata.Batch == class_data.Metadata.Batch, Metadata.Semester == class_data.Metadata.Semester).count()
            
            # For deleting metadata (If equal to 1 delete)
            class_metadata_count = db.session.query(Class).filter_by(MetadataId = class_data.Metadata.MetadataId).count()
            
            # Return class count
            if class_count > 1 :
                # Delete the class from database
                db.session.query(Class).filter_by(ClassId = classId).delete()
            elif class_count == 1:
                db.session.query(Class).filter_by(ClassId = classId).delete()
                db.session.query(LatestBatchSemester).filter_by(Batch = class_data.Metadata.Batch, Semester = class_data.Metadata.Semester).delete()

            db.session.commit()
            # return success
            return jsonify({'result': 'Data deleted successfully'}), 200
        else:
            return jsonify({'error': 'Class does not exist'}), 400
        
    except Exception as e:
        print("ERROR: ", e)
        # Rollback the changes in case of an error
        db.session.rollback()
        # Return an error response
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


def finalizedGradesReport(metadata_id):
    try:
        data_metadata = db.session.query(Metadata, Course).join(Course, Course.CourseId == Metadata.CourseId).filter(Metadata.MetadataId == metadata_id).first()
        # print('data_metadata: ', data_metadata)
        if data_metadata:
            # Select class that has the same Batch, Semester and Course
            data_course_class = db.session.query(Class, Metadata, Course).join(Metadata, Metadata.MetadataId == Class.MetadataId).join(Course, Course.CourseId == Metadata.CourseId).filter(Metadata.Batch == data_metadata.Metadata.Batch, Metadata.Semester == data_metadata.Metadata.Semester, Metadata.CourseId == data_metadata.Course.CourseId).order_by(Metadata.Year, Class.Section).all()
            # if data class 
            if data_course_class:
                student_class_grade_list = [] # For list of grade in class subject (Object - Lister, StudentId, ClassId etc...)

                course_grade_list = [] # Class grade lisst to calculate course grade
                
                student_list = [] # For checking of student if graduated
                list_class = [] # For class list that will be reiterated
                list_grade_analytics_details = [] # For details of analytics (Lister, Passed, Failed, Incomplete etc.)
                
                # Get count of subject with the same metadata
                count_subject = db.session.query(Curriculum).filter_by(MetadataId = metadata_id).count()
        
                # for loop the data_class and make a dictionary and append to the list_class
                for course_class_data in data_course_class:
                    dict_class = {
                        'ClassId': course_class_data.Class.ClassId,
                        'CourseId': course_class_data.Metadata.CourseId,
                        'Section': course_class_data.Class.Section,
                        'Course': course_class_data.Course.CourseCode,
                        'Year': course_class_data.Metadata.Year,
                        'Semester': course_class_data.Metadata.Semester,
                        'Batch': course_class_data.Metadata.Batch,
                        'SubjectCount': count_subject
                    }
                    # Append th list_class
                    list_class.append(dict_class)

                    # Make a course grade data for CourseId, Batch, Semester, Grade and Grades Array for storing all grades
                    course_grade_data = {
                        'CourseId': course_class_data.Metadata.CourseId,
                        'Batch': course_class_data.Metadata.Batch,
                        'Semester': course_class_data.Metadata.Semester,
                        'Grade': 0.00,
                        'Grades': []
                    }
                
                if list_class:
                    # for loop it
                    for class_data in list_class:
                        # Get the class_subject
                        print('class_data: ', class_data)
                        # Get Class data and update IsGradeFinalized
                        class_data_update = db.session.query(Class).filter_by(ClassId = class_data['ClassId']).first()
                        class_data_update.IsGradeFinalized = True
                        
                        data_class_subject = db.session.query(ClassSubject, Subject).join(Subject, Subject.SubjectId == ClassSubject.SubjectId).filter(ClassSubject.ClassId == class_data['ClassId']).all()
                        # data_class_subject = db.session.query(ClassSubject, Subject, Faculty).join(Subject, Subject.SubjectId == ClassSubject.SubjectId).join(Faculty, Faculty.TeacherId == ClassSubject.TeacherId).filter(ClassSubject.ClassId == class_data['ClassId']).all()

                        
                        list_class_subject = []
                        
                        if data_class_subject:
                            # for loop the data_class_subject and make a dictionary and append to the list_class_subject
                            for class_subject in data_class_subject:
                                # print('===============================================================================================================================================: ')
                                dict_class_subject = {
                                    'ClassSubjectId': class_subject.ClassSubject.ClassSubjectId,
                                    'SubjectCode': class_subject.Subject.SubjectCode,
                                    'Subject': class_subject.Subject.Name,
                                    'Schedule': class_subject.ClassSubject.Schedule
                                }
                                
                                # Make a dict_class_subject_grade
                                dict_grade_data_list = {
                                    'ClassSubjectId': class_subject.ClassSubject.ClassSubjectId,
                                    'ClassId': class_subject.ClassSubject.ClassId,
                                    'StudentId': [],
                                    'StudentClassSubjectGrade': [],
                                    'Grade': 0,
                                    'Passed': 0,
                                    'Failed': 0,
                                    'Incomplete': 0,
                                    'Dropout': 0,
                                    'PresidentsLister': 0,
                                    'DeansLister': 0
                                }
                                
                                
                                # Append the list_class_subject
                                list_class_subject.append(dict_class_subject)
                                # Get all student in the classSubject with the same classId
                                data_student_class_subject_grade = db.session.query(StudentClassSubjectGrade, Student).join(Student, Student.StudentId == StudentClassSubjectGrade.StudentId).filter(StudentClassSubjectGrade.ClassSubjectId == class_subject.ClassSubject.ClassSubjectId).all()
                                
                                # Additional details for generating report for analytics (Passed, Failed, PresidentLister, DeansLister)
                                if data_student_class_subject_grade:
                                    for student_class_subject_grade in data_student_class_subject_grade:
                                        
                                        
                                        current_student_id = student_class_subject_grade.Student.StudentId
                                        current_grade = student_class_subject_grade.StudentClassSubjectGrade.Grade
                                        # Get academic status
                                        academic_status = student_class_subject_grade.StudentClassSubjectGrade.AcademicStatus
                                        
                                        if academic_status == 1:
                                            dict_grade_data_list['Passed'] += 1
                                        elif academic_status == 2:
                                            dict_grade_data_list['Failed'] += 1
                                        elif academic_status == 3:
                                            dict_grade_data_list['Incomplete'] += 1
                                        elif academic_status == 4:
                                            dict_grade_data_list['Dropout'] += 1
                                            
                                        # Append StudentId
                                        dict_grade_data_list['StudentId'].append(current_student_id)
                                        

                                        if current_grade != 0: 
                                            dict_grade_data_list['StudentClassSubjectGrade'].append(current_grade)
                                            # Check if an entry with the same StudentId already exists in student_class_grade_list
                                            found_entry = next((entry for entry in student_class_grade_list if entry["StudentId"] == current_student_id), None)
                                            
                                            if found_entry:
                                                # If an entry with the same StudentId exists, append the grade to the existing entry
                                                found_entry["Grade"].append(current_grade)
                                            else:
                                                # If no entry with the same StudentId exists, add a new entry to student_class_grade_list
                                                student_class_grade_list.append({
                                                    "StudentId": current_student_id,
                                                    "ClassId": class_subject.ClassSubject.ClassId,
                                                    "Grade": [current_grade],
                                                    # "IsGradeCompleted": True,
                                                    "Lister": 0
                                                })
                                                
                                        # else:
                                        #     # Check if an entry with the same StudentId already exists in student_class_grade_list
                                        #     found_entry = next((entry for entry in student_class_grade_list if entry["StudentId"] == current_student_id), None)
                                            
                                        #     if found_entry:
                                        #         # If an entry with the same StudentId exists, append the grade to the existing entry
                                        #         found_entry["IsGradeCompleted"] = False
                                        #     else:
                                        #         # If no entry with the same StudentId exists, add a new entry to student_class_grade_list
                                        #         student_class_grade_list.append({
                                        #             "StudentId": current_student_id,
                                        #             "ClassId": course_class_data.Class.ClassId,
                                        #             "Grade": [],
                                        #             "IsGradeCompleted": False,
                                        #             "Lister": 0
                                        #         })
                                        
                                    list_grade_analytics_details.append(dict_grade_data_list)
                            # Append the list_class_subject to the class_data
                            class_data['ClassSubject'] = list_class_subject
                            
                        else:
                            class_data['ClassSubject'] = None
                    # print('ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ: ')
                    # For caclculating the student overall grade
                    
                    for data in student_class_grade_list:
                        print("=================================================================================")
                        print("CLS GRADE (BEFORE CONVERT): ", data)
                        # append stundet id
                        student_list.append(data['StudentId'])
                        # Check the length of grade if more than or equal to 1
                        print('CLASS DATA SUBJECT COUNT: ')
                        if len(data['Grade']) >= 1:
                            # Check if any grade is 4.0, if yes, set Lister to 0
                            is_lister = 1

                            
                            if len(data['Grade']) != class_data['SubjectCount']:
                                is_lister = 0
                            
                            if any(grade  >= 2.75 for grade in data['Grade']) and is_lister != 0:
                                is_lister = 0
                                
                            sum_grade = sum(data['Grade'])
                            # Get the average grade
                            average_grade = sum_grade / len(data['Grade'])
                            # Update the Grade
                            data['Grade'] = average_grade
                            
                            # Check if sum grade is below 1.75
                            if average_grade <= 1.5 and is_lister != 0:
                                print("PRESIDENT")
                                data['Lister'] = 1
                            elif average_grade <= 1.75 and average_grade > 1.5 and is_lister != 0:
                                data['Lister'] = 2
                                print("DEAN")
                            
                            
                            # STUDENT CLASS GRADE - StudentId, ClassId, Grade, Lister
                            # Data for Student Class Grade Average
                            student_class_grade = db.session.query(StudentClassGrade).filter_by(StudentId = data['StudentId'], ClassId = data['ClassId']).first()
                            if student_class_grade:
                                db.session.query(StudentClassGrade).filter_by(StudentId = data['StudentId'], ClassId = data['ClassId']).update({
                                    'Grade': data['Grade'], 'Lister': data['Lister']
                                })
                                print("UPDATING LISTER: ", data['Lister'])
                            else:
                                # Create a student_class_grade
                                new_student_class_grade = StudentClassGrade(
                                    StudentId = data['StudentId'],
                                    ClassId = data['ClassId'],
                                    Grade = data['Grade'],
                                    Lister = data['Lister']
                                )
                                print("UPDATING LISTER: ", data['Lister'])
                                db.session.add(new_student_class_grade)
                                db.session.flush()
                        print("CLS GRADE (UPDATED): ", data)
                    
                    # print('/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////: ')
                    # In analyticcs we have already StudentId this can be used to track class subject grade?
                    class_grade_list = []
                    
                    for data in list_grade_analytics_details:
                        # print("DATA ANALYtICS: ", data)
                        # CLASS SUBJET GRADE - ClassSubjectId, Grade, (Passed, Failed, Incomplete Dropout)
                        # CLASS GRADE - ClassId, (DeansLister, PresidentsLister), Grade
                        
                        # Find the average of StudentClassSubjectGrade
                        if len(data['StudentClassSubjectGrade']) >= 1:
                            sum_grade = sum(data['StudentClassSubjectGrade'])
                            # Get the average grade rounded to 2 decimal places
                            average_grade = round(sum_grade / len(data['StudentClassSubjectGrade']), 2)
                            # Update the Grade
                            data['StudentClassSubjectGrade'] = average_grade
                        else:
                            data['StudentClassSubjectGrade'] = 0.00
                            
                        
                        # For loop the StudentId
                        for student_id in data['StudentId']:
                            # Check if student_id is in student_class_grade_list
                            found_entry = next((entry for entry in student_class_grade_list if entry["StudentId"] == student_id), None)
                            
                            if found_entry:
                                # Check if Lister is 1
                                if found_entry['Lister'] == 1:
                                    data['PresidentsLister'] += 1
                                elif found_entry['Lister'] == 2:
                                    # Print president
                                    data['DeansLister'] += 1
                            
                            else:
                                print("NOT FOUND")
                                
                        # Add it in database:
                        # Check if class_subject_grade is existing
                        class_subject_grade = db.session.query(ClassSubjectGrade).filter_by(ClassSubjectId = data['ClassSubjectId']).first()
                        # If yes update it with new values
                        if class_subject_grade:
                            db.session.query(ClassSubjectGrade).filter_by(ClassSubjectId = data['ClassSubjectId']).update({
                                'Grade': data['StudentClassSubjectGrade'],
                                'Passed': data['Passed'],
                                'Failed': data['Failed'],
                                'Incomplete': data['Incomplete'],
                                'Dropout': data['Dropout']
                            })
                        else:
                            # Create a class_subject_grade
                            new_class_subject_grade = ClassSubjectGrade(
                                ClassSubjectId = data['ClassSubjectId'],
                                Grade = data['StudentClassSubjectGrade'],
                                Passed = data['Passed'],
                                Failed = data['Failed'],
                                Incomplete = data['Incomplete'],
                                Dropout = data['Dropout']
                            )
                            
                            db.session.add(new_class_subject_grade)
                            db.session.flush()
                            
                        # Check if ClassId already exisitng in class_grade_list
                        found_entry = next((entry for entry in class_grade_list if entry["ClassId"] == data['ClassId']), None)
                        if not any(d['ClassId'] == data['ClassId'] for d in class_grade_list):
                            # If not existing then append
                            class_grade_list.append({
                                'ClassId': data['ClassId'],
                                'DeansLister': data['DeansLister'],
                                'PresidentsLister': data['PresidentsLister'],
                                # Append Grade in array
                                'Grade': [data['StudentClassSubjectGrade']]
                            })
                            
                        else:
                            # If existing then append grade only
                            found_entry['Grade'].append(data['StudentClassSubjectGrade'])
                            
                    print('')
                    
                    for data in class_grade_list:
                        # print("ANALYTICS: ", data)
                        
                        # Check if grade is more than or equal to 1
                        if len(data['Grade']) >= 1:
                            # Get the sum of grade
                            sum_grade = sum(data['Grade'])
                            # Get the average grade rounded to 2 decimal places
                            average_grade = round(sum_grade / len(data['Grade']), 2)
                            # Update the Grade
                            data['Grade'] = average_grade
                            # Append average in course_grade_list
                            course_grade_list.append(average_grade)
                        else:
                            data['Grade'] = 0.00
                            
                        class_grade = db.session.query(ClassGrade).filter_by(ClassId = data['ClassId']).first()
                        
                        # print('DEANLISTER: ', data['DeansLister'])
                        # print('PRESIDENTSLISTER: ', data['PresidentsLister'])
                        # CLASS GRADE - Analytics for Class Grade Report
                        if class_grade:
                            # Update the class_grade
                            db.session.query(ClassGrade).filter_by(ClassId = data['ClassId']).update({
                                'DeansLister': data['DeansLister'],
                                'PresidentsLister': data['PresidentsLister'],
                                'Grade': data['Grade']
                            })             
                        else:
                            # Create a class_grade
                            new_class_grade = ClassGrade(
                                ClassId = data['ClassId'],
                                DeansLister = data['DeansLister'],
                                PresidentsLister = data['PresidentsLister'],
                                Grade = data['Grade']
                            )
                            
                            db.session.add(new_class_grade)
                            db.session.flush()

                        # Update the course grade by average of all class grade
                        # Check if course_grade is existing
                   
                    course_grade = db.session.query(CourseGrade).filter_by(CourseId = course_grade_data['CourseId'], Batch = course_grade_data['Batch'], Semester = course_grade_data['Semester']).first()
                    
                    average_course_grade = sum(course_grade_list) / len(course_grade_list)
                    
                    # COURSE GRADE - Calculating data of course grade
                    if course_grade:
                        # Update the course_grade
                        db.session.query(CourseGrade).filter_by(CourseId = course_grade_data['CourseId'], Batch = course_grade_data['Batch'], Semester = course_grade_data['Semester']).update({
                            'Grade': round(average_course_grade, 2)
                        })
                        
                        # # COURSE GRADE CHECKER
                        # print("\nUPDATED COURSE GRADE: " + str({
                        #     'CourseId': course_grade_data['CourseId'],
                        #     'Batch': course_grade_data['Batch'],
                        #     'Semester': course_grade_data['Semester'],
                        #     'Grade': round(average_course_grade, 2)
                        # }))
                    else:
                        # Create a course_grade
                        new_course_grade = CourseGrade(
                            CourseId = course_grade_data['CourseId'],
                            Batch = course_grade_data['Batch'],
                            Semester = course_grade_data['Semester'],
                            Grade = round(average_course_grade, 2)
                        )
                        
                        db.session.add(new_course_grade)
                        db.session.flush()
                        
                        # # COURSE GRADE CHECKER
                        # print("\nUPDATED COURSE GRADE: " + str({
                        #     'CourseId': course_grade_data['CourseId'],
                        #     'Batch': course_grade_data['Batch'],
                        #     'Semester': course_grade_data['Semester'],
                        #     'Grade': round(average_course_grade, 2)
                        # }))
                    
                    # COURSE ENROLLED - Checking if Student is already graduated (Status).
                    if student_list:
                        # for loop the student_list
                        for student_id in student_list:
                            # Get student id in "CourseEnrolled" column order by latest of "DateEnrolled"
                            course_enrolled = db.session.query(CourseEnrolled).filter_by(StudentId = student_id).order_by(desc(CourseEnrolled.DateEnrolled)).first()
                            # print('course_enrolled.DateEnrolled: ', course_enrolled.DateEnrolled)
                            
                            # Get the curriculum of course with the same batch
                            curriculum = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Metadata.Batch == course_enrolled.DateEnrolled.year, Metadata.CourseId == course_grade_data['CourseId']).all()
                            
                            # For loop and print the Subject Name
                            bool_graduate = True;
                            for data in curriculum:
                                # print('data: ', data)
                                # Find class with the same StudentId
                                class_subject_grade_data = db.session.query(ClassSubject, StudentClassSubjectGrade).join(StudentClassSubjectGrade, StudentClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId).filter(StudentClassSubjectGrade.StudentId == student_id, ClassSubject.SubjectId == data.Subject.SubjectId).order_by(desc(StudentClassSubjectGrade.DateEnrolled)).first()
                                
                                # print('class_data: ', class_data)
                                
                                # Check if existing
                                if class_subject_grade_data:
                                    if class_subject_grade_data.StudentClassSubjectGrade.AcademicStatus == 1:
                                        # Go to next for loop of curriculum
                                        continue
                                    else:
                                        bool_graduate = False;
                                        # # Set the CourseEnrolled Status to 0
                                        # course_enrolled = db.session.query(CourseEnrolled).filter_by(StudentId = student_id).first()
                                        # # Update the status of course_enrolled
                                        # if course_enrolled:
                                        #     course_enrolled.Status = 0  # Set status to 0
                                        #     db.session.commit()  # Commit the changes to the database
                                        
                                        # db.session.commit()
                                        break
                                else:
                                    bool_graduate = False;
                                    # Set the CourseEnrolled Status to 0
                                    # db.session.query(CourseEnrolled).filter_by(StudentId = student_id).update({
                                    #     'Status': 0
                                    # })
                                    # db.session.commit()
                                    break     
                            # Check for value of flag if still true
                            if bool_graduate:
                                # Set the CourseEnrolled Status to 1
                                db.session.query(CourseEnrolled).filter_by(StudentId = student_id).update({
                                    'Status': 1
                                })
                                db.session.commit()
            else:   
                db.session.rollback()
                return jsonify({"error": "There no class yet"})
            print("SUCCESS")
            return jsonify({"success": True, "message": "Data finalized successfully"})
        else:
            return jsonify(None)
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return jsonify(error=str(e))
    
    

def finalizedGradesBatchSemester(batch_semester_id):
    try:
        # Get latest batch semester
        latest_batch_semester = db.session.query(LatestBatchSemester).filter_by(LatestBatchSemesterId = batch_semester_id).first()
        
        # Check if IsEnrollmentStarted false
        if not latest_batch_semester.IsEnrollmentStarted:
            return jsonify({'error': 'Cannot finalize grade. Enrollment is not yet started.'}), 400
        
        # Check if latest_batch_semester is not yet IsGradeFinalized
        if latest_batch_semester.IsGradeFinalized:
            return jsonify({'error': 'Grade is already finalized'}), 400
        
        # Find all metadata with same batch and semester
        metadata_course = db.session.query(Metadata, Course).join(Course, Course.CourseId == Metadata.CourseId).filter(Metadata.Batch == latest_batch_semester.Batch, Metadata.Semester == latest_batch_semester.Semester).all()
        
        if metadata_course:
            # for loop metadata
            
            course_grade_info_list = []
            
            for data_of_metadata in metadata_course:
                # Select class that has the same Batch, Semester and Course
                data_course_class = db.session.query(Class, Metadata, Course).join(Metadata, Metadata.MetadataId == Class.MetadataId).join(Course, Course.CourseId == Metadata.CourseId).filter(Metadata.Batch == data_of_metadata.Metadata.Batch, Metadata.Year == data_of_metadata.Metadata.Year, Metadata.Semester == data_of_metadata.Metadata.Semester, Metadata.CourseId == data_of_metadata.Course.CourseId).order_by(Metadata.Year, Class.Section).all()
                # if data class 
                if data_course_class:
                    student_class_grade_list = [] # For list of grade in class subject (Object - Lister, StudentId, ClassId etc...)

                    course_grade_list = [] # Class grade lisst to calculate course grade
                    
                    student_list = [] # For checking of student if graduated
                    list_class = [] # For class list that will be reiterated
                    list_grade_analytics_details = [] # For details of analytics (Lister, Passed, Failed, Incomplete etc.)
                    
                    all_class_list = []
                            
                    # print('data_of_metadata.Metadata.MetadataId: ', data_of_metadata.Metadata.MetadataId)
                    # print('count_nstp: ', count_nstp)
                    # print('count_subject: ', count_subject)
                    # for loop the data_class and make a dictionary and append to the list_class
                    for course_class_data in data_course_class:
                         # Get count of subject with the same metadata
                        count_subject = db.session.query(Curriculum).filter_by(MetadataId = course_class_data.Metadata.MetadataId).count()
                        # Get count of curriculum where Subject.IsNSTP is True
                        count_nstp = db.session.query(Curriculum, Subject).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Curriculum.MetadataId == course_class_data.Metadata.MetadataId, Subject.IsNSTP == True).count()
                        
                        
                        dict_class = {
                            'ClassId': course_class_data.Class.ClassId,
                            'CourseId': course_class_data.Metadata.CourseId,
                            'Course': course_class_data.Course.CourseCode,
                            'Year': course_class_data.Metadata.Year,
                            'Section': course_class_data.Class.Section,
                            'Semester': course_class_data.Metadata.Semester,
                            'Batch': course_class_data.Metadata.Batch,
                            'SubjectCount': count_subject,
                            'NSTPCount': count_nstp
                        }
                        # Append th list_class
                        list_class.append(dict_class)

                        # Make a course grade data for CourseId, Batch, Semester, Grade and Grades Array for storing all grades
                        course_grade_data = {
                            'CourseId': course_class_data.Metadata.CourseId,
                            'Batch': course_class_data.Metadata.Batch,
                            'Semester': course_class_data.Metadata.Semester,
                            'Grade': 0.00,
                            'Grades': []
                        }
                    
                    if list_class:
                        # for loop it
                        for class_data in list_class:
                            # Get the class_subject
                            # Make a dict containing CourseId, Year, Semester, Batch and Grades Array
                            # dict_class_data = {
                            #     'ClassId': class_data['ClassId'],
                            #     'CourseId': class_data['CourseId'],
                            #     'Year': class_data['Year'],
                            #     'Semester': class_data['Semester'],
                            #     'Batch': class_data['Batch'],
                            #     'Grades': []
                            # }
                            
                            # Get Class data and update IsGradeFinalized
                            class_data_update = db.session.query(Class).filter_by(ClassId = class_data['ClassId']).first()
                            class_data_update.IsGradeFinalized = True
                            
                            data_class_subject = db.session.query(ClassSubject, Subject).join(Subject, Subject.SubjectId == ClassSubject.SubjectId).filter(ClassSubject.ClassId == class_data['ClassId']).all()
                            # data_class_subject = db.session.query(ClassSubject, Subject, Faculty).join(Subject, Subject.SubjectId == ClassSubject.SubjectId).join(Faculty, Faculty.TeacherId == ClassSubject.TeacherId).filter(ClassSubject.ClassId == class_data['ClassId']).all()
                            
                            list_class_subject = []
                            
                            if data_class_subject:
                                # for loop the data_class_subject and make a dictionary and append to the list_class_subject
                                for class_subject in data_class_subject:
                                    # print('===============================================================================================================================================: ')
                                    dict_class_subject = {
                                        'ClassSubjectId': class_subject.ClassSubject.ClassSubjectId,
                                        'SubjectCode': class_subject.Subject.SubjectCode,
                                        'Subject': class_subject.Subject.Name,
                                        'Schedule': class_subject.ClassSubject.Schedule,
                                        'IsNSTP': class_subject.Subject.IsNSTP,
                                    }
                                    
                                    # Make a dict_class_subject_grade
                                    dict_grade_data_list = {
                                        'ClassSubjectId': class_subject.ClassSubject.ClassSubjectId,
                                        'ClassId': class_subject.ClassSubject.ClassId,
                                        'IsNSTP': class_subject.Subject.IsNSTP,
                                        'StudentId': [],
                                        'StudentClassSubjectGrade': [],
                                        'Grade': 0,
                                        'Passed': 0,
                                        'Failed': 0,
                                        'Incomplete': 0,
                                        'Dropout': 0,
                                        'PresidentsLister': 0,
                                        'DeansLister': 0
                                    }
                                    
                                    
                                    # Append the list_class_subject
                                    list_class_subject.append(dict_class_subject)
                                    # Get all student in the classSubject with the same classId
                                    data_student_class_subject_grade = db.session.query(StudentClassSubjectGrade, Student).join(Student, Student.StudentId == StudentClassSubjectGrade.StudentId).filter(StudentClassSubjectGrade.ClassSubjectId == class_subject.ClassSubject.ClassSubjectId).all()
                                    
                                    # Additional details for generating report for analytics (Passed, Failed, PresidentLister, DeansLister)
                                    if data_student_class_subject_grade:
                                        for student_class_subject_grade in data_student_class_subject_grade:
                                            
                                            current_student_id = student_class_subject_grade.Student.StudentId
                                            current_grade = student_class_subject_grade.StudentClassSubjectGrade.Grade
                                            # Get academic status
                                            academic_status = student_class_subject_grade.StudentClassSubjectGrade.AcademicStatus
                                            
                                            if academic_status == 1:
                                                dict_grade_data_list['Passed'] += 1
                                            elif academic_status == 2:
                                                dict_grade_data_list['Failed'] += 1
                                            elif academic_status == 3:
                                                dict_grade_data_list['Incomplete'] += 1
                                            elif academic_status == 4:
                                                dict_grade_data_list['Dropout'] += 1
                                                
                                            # Append StudentId
                                            dict_grade_data_list['StudentId'].append(current_student_id)
                                            
                                            if class_subject.Subject.IsNSTP:
                                                # print("NSTP FOUND: ", current_student_id, student_class_subject_grade.Student.LastName, student_class_subject_grade.Student.FirstName)
                                                # print("NSTP GRADE: ", class_subject.Subject.SubjectCode, current_grade)
                                                dict_grade_data_list['StudentClassSubjectGrade'].append(current_grade)
                                                found_entry = next((entry for entry in student_class_grade_list if entry["StudentId"] == current_student_id), None)
                                                
                                                # Check if current grade < 2.75 then set the  variable lister 0
                                                lister = None if current_grade < 2.75 else 0
                                                
                                                if found_entry:
                                                    # If an entry with the same StudentId exists, append the grade to the existing entry
                                                    found_entry["NSTPGrade"].append(current_grade)
                                                    # Check if found entry Lister is None then set lister
                                                    if found_entry['Lister'] is None:
                                                        found_entry['Lister'] = lister
                                                else:
                                                    
                                                    # Check if current grade is < 2.75 
                                                    # If no entry with the same StudentId exists, add a new entry to student_class_grade_list
                                                    student_class_grade_list.append({
                                                        "StudentId": current_student_id,
                                                        "ClassId": class_subject.ClassSubject.ClassId,
                                                        "Grade": [],
                                                        "TotalUnits": 0,
                                                        "NSTPGrade": [current_grade],
                                                        "Lister": lister
                                                    })
                                                    
                                            if current_grade != 0 and not class_subject.Subject.IsNSTP: 
                                               
                                                dict_grade_data_list['StudentClassSubjectGrade'].append(current_grade)
                                                # Check if an entry with the same StudentId already exists in student_class_grade_list
                                                found_entry = next((entry for entry in student_class_grade_list if entry["StudentId"] == current_student_id), None)
                                                
                                                 # Check if current grade < 2.75 then set the  variable lister 0
                                                lister = None if current_grade < 2.75 else 0
                                                
                                                if found_entry:
                                                    # If an entry with the same StudentId exists, append the grade to the existing entry
                                                    found_entry["Grade"].append(current_grade * class_subject.Subject.Units)
                                                    # Update total units
                                                    found_entry["TotalUnits"] += class_subject.Subject.Units
                                                    # Update lister
                                                    if found_entry['Lister'] is None:
                                                        found_entry['Lister'] = lister
                                                else:
                                                    # If no entry with the same StudentId exists, add a new entry to student_class_grade_list
                                                    student_class_grade_list.append({
                                                        "StudentId": current_student_id,
                                                        "ClassId": class_subject.ClassSubject.ClassId,
                                                        "Grade": [current_grade * class_subject.Subject.Units],
                                                        "TotalUnits": class_subject.Subject.Units,
                                                        "NSTPGrade": [],
                                                        "Lister": lister
                                                    })
                                        list_grade_analytics_details.append(dict_grade_data_list)
                                # Append the list_class_subject to the class_data
                                class_data['ClassSubject'] = list_class_subject
                                all_class_list.append(class_data)
                            else:
                                class_data['ClassSubject'] = None
                                all_class_list.append(class_data)
                                
                        # # try to for loop all class list:
                        # for data_all_class in all_class_list:
                        #     print('\ndata_all_class: ', data_all_class)
                        # print('ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ: ')
                        # For caclculating the student overall grade
                        
                        # STUDENT CLASS GRADE
                        for data in student_class_grade_list:
                            # print("=================================================================================")
                            # print("CLS GRADE (BEFORE CONVERT): ", data)
                            # append stundet id
                            student_list.append(data['StudentId'])
                            # Check the length of grade if more than or equal to 1
                            if len(data['Grade']) >= 1:
                                # Check if any grade is 4.0, if yes, set Lister to 0
                                is_lister = data['Lister']
                                no_nstp_count = class_data['SubjectCount'] - class_data['NSTPCount']
                                # print('no_nstp_count: ', no_nstp_count)
                                if len(data['Grade']) != no_nstp_count:
                                    is_lister = 0
                                
                                # if any(grade  >= 2.75 for grade in data['Grade']) and is_lister != 0:
                                #     is_lister = 0
                                    
                                sum_grade = sum(data['Grade'])
                                # Get the average grade
                                average_grade = sum_grade / data['TotalUnits']
                                # Update the Grade
                                data['Grade'] = round(average_grade, 2)
                                
                                # Check if sum grade is below 1.75
                                if average_grade <= 1.5 and is_lister != 0:
                                    data['Lister'] = 1
                                elif average_grade <= 1.75 and average_grade > 1.5 and is_lister != 0:
                                    data['Lister'] = 2
                                else:
                                    data['Lister'] = 0
                                
                                # STUDENT CLASS GRADE - StudentId, ClassId, Grade, Lister
                                # Data for Student Class Grade Average
                                student_class_grade = db.session.query(StudentClassGrade).filter_by(StudentId = data['StudentId'], ClassId = data['ClassId']).first()
                                if student_class_grade:
                                    db.session.query(StudentClassGrade).filter_by(StudentId = data['StudentId'], ClassId = data['ClassId']).update({
                                        'Grade': data['Grade'], 'Lister': data['Lister']
                                    })
                                    # print("UPDATING LISTER: ", data['Lister'])
                                else:
                                    print("NEW STUDENT CLASS GRADE OCCUR")
                                    # Create a student_class_grade
                                    new_student_class_grade = StudentClassGrade(
                                        StudentId = data['StudentId'],
                                        ClassId = data['ClassId'],
                                        Grade = data['Grade'],
                                        Lister = data['Lister']
                                    )
                                    # print("UPDATING LISTER: ", data['Lister'])
                                    db.session.add(new_student_class_grade)
                                    db.session.flush()
                            # print("CLS GRADE (UPDATED): ", data)
                        
                        class_grade_list = []
                        
                        # ANALYTICS FOR CLASS SUBJECTS
                        for data in list_grade_analytics_details:
                            # print("\nCLASS SUBJECT ANALYtICS: ", data)
                            
                            # CLASS SUBJET GRADE - ClassSubjectId, Grade, (Passed, Failed, Incomplete Dropout)
                            # CLASS GRADE - ClassId, (DeansLister, PresidentsLister), Grade
                            
                            # Find the average of StudentClassSubjectGrade
                            if len(data['StudentClassSubjectGrade']) >= 1:
                                sum_grade = sum(data['StudentClassSubjectGrade'])
                                # Get the average grade rounded to 2 decimal places
                                average_grade = round(sum_grade / len(data['StudentClassSubjectGrade']), 2)
                                # Update the Grade
                                data['StudentClassSubjectGrade'] = average_grade
                            else:
                                data['StudentClassSubjectGrade'] = 0.00
                                
                            
                            # For loop the StudentId
                            for student_id in data['StudentId']:
                                # Check if student_id is in student_class_grade_list
                                found_entry = next((entry for entry in student_class_grade_list if entry["StudentId"] == student_id), None)
                                # print('found_entry: ', found_entry)
                                if found_entry:
                                    # Check if Lister is 1
                                    if found_entry['Lister'] == 1:
                                        data['PresidentsLister'] += 1
                                    elif found_entry['Lister'] == 2:
                                        # Print president
                                        data['DeansLister'] += 1
                                else:
                                    print("NOT FOUND")
                                    
                            # Add it in database:
                            # Check if class_subject_grade is existing
                            class_subject_grade = db.session.query(ClassSubjectGrade).filter_by(ClassSubjectId = data['ClassSubjectId']).first()
                            # If yes update it with new values
                            print("\n", data)
                            if class_subject_grade:
                                
                                db.session.query(ClassSubjectGrade).filter_by(ClassSubjectId = data['ClassSubjectId']).update({
                                    'Grade': data['StudentClassSubjectGrade'],
                                    'Passed': data['Passed'],
                                    'Failed': data['Failed'],
                                    'Incomplete': data['Incomplete'],
                                    'Dropout': data['Dropout']
                                })
                            else:
                                # Create a class_subject_grade
                                new_class_subject_grade = ClassSubjectGrade(
                                    ClassSubjectId = data['ClassSubjectId'],
                                    Grade = data['StudentClassSubjectGrade'],
                                    Passed = data['Passed'],
                                    Failed = data['Failed'],
                                    Incomplete = data['Incomplete'],
                                    Dropout = data['Dropout']
                                )
                                
                                db.session.add(new_class_subject_grade)
                                db.session.flush()
                                
                            # Check if ClassId already exisitng in class_grade_list
                            found_entry = next((entry for entry in class_grade_list if entry["ClassId"] == data['ClassId']), None)
                            if not any(d['ClassId'] == data['ClassId'] for d in class_grade_list):
                                # If not existing then append
                                class_grade_list.append({
                                    'ClassId': data['ClassId'],
                                    'DeansLister': data['DeansLister'],
                                    'PresidentsLister': data['PresidentsLister'],
                                    # Append Grade in array
                                    'Grade': [data['StudentClassSubjectGrade']]
                                })
                                
                            else:
                                # If existing then append grade only
                                found_entry['Grade'].append(data['StudentClassSubjectGrade'])
                            # print("\nUPDATED CLASSS SUBJECT ANALYtICS: ", data)
                            
                        print('')
                        
                        # ANALYTICS FOR CLASS (Updating data in the database)
                        for data in class_grade_list:
                            # Check if grade is more than or equal to 1
                            if len(data['Grade']) >= 1:
                                # Get the sum of grade
                                sum_grade = sum(data['Grade'])
                                # Get the average grade rounded to 2 decimal places
                                average_grade = round(sum_grade / len(data['Grade']), 2)
                                # Update the Grade
                                data['Grade'] = average_grade
                                # Append average in course_grade_list
                                course_grade_list.append(average_grade)
                            else:
                                data['Grade'] = 0.00
                                
                            class_grade = db.session.query(ClassGrade).filter_by(ClassId = data['ClassId']).first()
                            
                            if class_grade:
                                # Update the class_grade
                                db.session.query(ClassGrade).filter_by(ClassId = data['ClassId']).update({
                                    'DeansLister': data['DeansLister'],
                                    'PresidentsLister': data['PresidentsLister'],
                                    'Grade': data['Grade']
                                })             
                            else:
                                # Create a class_grade
                                new_class_grade = ClassGrade(
                                    ClassId = data['ClassId'],
                                    DeansLister = data['DeansLister'],
                                    PresidentsLister = data['PresidentsLister'],
                                    Grade = data['Grade']
                                )
                                
                                db.session.add(new_class_grade)
                                db.session.flush()

                            # Check if courseid, batch, semester already exist in the course_grade_info_list
                            found_entry = next((entry for entry in course_grade_info_list if entry["CourseId"] == data_of_metadata.Course.CourseId and entry["Batch"] == data_of_metadata.Metadata.Batch and entry["Semester"] == data_of_metadata.Metadata.Semester), None)
                            
                            if found_entry:
                                # If existing then append grade only
                                found_entry['Grade'].append(data['Grade'])
                            else:
                                # If not existing then append
                                course_grade_info_list.append({
                                    'CourseId': data_of_metadata.Course.CourseId,
                                    'Batch': data_of_metadata.Metadata.Batch,
                                    'Semester': data_of_metadata.Metadata.Semester,
                                    'Grade': [data['Grade']]
                                })
                            
                        # course_grade_list = [{
                        #     'CourseId': course_grade_data['CourseId'],
                        #     'Batch': course_grade_data['Batch'],
                        #     'Semester': course_grade_data['Semester'],
                        #     'Grades': []
                        # }]
                        
                        course_grade = db.session.query(CourseGrade).filter_by(CourseId = course_grade_data['CourseId'], Batch = course_grade_data['Batch'], Semester = course_grade_data['Semester']).first()
                        
                        average_course_grade = sum(course_grade_list) / len(course_grade_list)
                        
                        # COURSE GRADE - Calculating data of course grade
                        # if course_grade:
                        #     # Update the course_grade
                        #     db.session.query(CourseGrade).filter_by(CourseId = course_grade_data['CourseId'], Batch = course_grade_data['Batch'], Semester = course_grade_data['Semester']).update({
                        #         'Grade': round(average_course_grade, 2)
                        #     })
                            
                        #     # # COURSE GRADE CHECKER
                        #     print("\nUPDATED COURSE GRADE: " + str({
                        #         'CourseId': course_grade_data['CourseId'],
                        #         'Batch': course_grade_data['Batch'],
                        #         'Semester': course_grade_data['Semester'],
                        #         'Grade': round(average_course_grade, 2)
                        #     }))
                        # else:
                        #     # Create a course_grade
                        #     new_course_grade = CourseGrade(
                        #         CourseId = course_grade_data['CourseId'],
                        #         Batch = course_grade_data['Batch'],
                        #         Semester = course_grade_data['Semester'],
                        #         Grade = round(average_course_grade, 2)
                        #     )
                            
                        #     db.session.add(new_course_grade)
                        #     db.session.flush()
                            
                        #     # # COURSE GRADE CHECKER
                        #     print("\nUPDATED COURSE GRADE: " + str({
                        #         'CourseId': course_grade_data['CourseId'],
                        #         'Batch': course_grade_data['Batch'],
                        #         'Semester': course_grade_data['Semester'],
                        #         'Grade': round(average_course_grade, 2)
                        #     }))
                        
                        # COURSE ENROLLED - Checking if Student is already graduated (Status).
                        if student_list:
                            # for loop the student_list
                            for student_id in student_list:
                                # Get student id in "CourseEnrolled" column order by latest of "DateEnrolled"
                                course_enrolled = db.session.query(CourseEnrolled).filter_by(StudentId = student_id).order_by(desc(CourseEnrolled.DateEnrolled)).first()
                                # print('course_enrolled.DateEnrolled: ', course_enrolled.DateEnrolled)
                                
                                # Get the curriculum of course with the same batch
                                curriculum = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Metadata.Batch == course_enrolled.DateEnrolled.year, Metadata.CourseId == course_grade_data['CourseId']).all()
                                
                                # For loop and print the Subject Name
                                bool_graduate = True;
                                for data in curriculum:
                                    # print('data: ', data)
                                    # Find class with the same StudentId
                                    class_subject_grade_data = db.session.query(ClassSubject, StudentClassSubjectGrade).join(StudentClassSubjectGrade, StudentClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId).filter(StudentClassSubjectGrade.StudentId == student_id, ClassSubject.SubjectId == data.Subject.SubjectId).order_by(desc(StudentClassSubjectGrade.DateEnrolled)).first()
                                    
                                    # print('class_data: ', class_data)
                                    
                                    # Check if existing
                                    if class_subject_grade_data:
                                        if class_subject_grade_data.StudentClassSubjectGrade.AcademicStatus == 1:
                                            # Go to next for loop of curriculum
                                            continue
                                        else:
                                            bool_graduate = False;
                                            
                                            # Set the CourseEnrolled Status to 0
                                            db.session.query(CourseEnrolled).filter_by(StudentId = student_id).update({
                                                'Status': 0
                                            })
                                            db.session.commit()
                                            break
                                    else:
                                        bool_graduate = False;
                                        # Set the CourseEnrolled Status to 0
                                        db.session.query(CourseEnrolled).filter_by(StudentId = student_id).update({
                                            'Status': 0
                                        })
                                        db.session.commit()
                                        break     
                                # Check for value of flag if still true
                                if bool_graduate:
                                    # Set the CourseEnrolled Status to 1
                                    db.session.query(CourseEnrolled).filter_by(StudentId = student_id).update({
                                        'Status': 1
                                    })
                                    db.session.commit()
            
            # Check if course_grade_info_list have data
            if course_grade_info_list:
                # loop it
                for data in course_grade_info_list:
                    # Get the course grade
                    course_grade = db.session.query(CourseGrade).filter_by(CourseId = data['CourseId'], Batch = data['Batch'], Semester = data['Semester']).first()
                    # Check if course grade is existing
                    # sum of data['Grade'] divided by its length
                    average_course_grade = sum(data['Grade']) / len(data['Grade'])
                    
                    if course_grade:
                        # Update the course_grade
                        # Update course grade value
                        course_grade.Grade == round(average_course_grade, 2)
                        

                    else:
                        # Create a course_grade
                        new_course_grade = CourseGrade(
                            CourseId = data['CourseId'],
                            Batch = data['Batch'],
                            Semester = data['Semester'],
                            Grade = round(average_course_grade, 2)
                        )
                        
                        db.session.add(new_course_grade)
                        db.session.flush()
                        
                db.session.query(LatestBatchSemester).filter_by(LatestBatchSemesterId = batch_semester_id).update({
                    'IsGradeFinalized': True
                })
                db.session.commit()
                # Set the IsGradeFinalized to True
            # Return succcess
            return jsonify({'success': True, 'message':'Successfully updated grades.'}), 201
            # else:
            #     return jsonify(None)
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return jsonify(error=str(e))




def getListerStudent(skip, top, order_by, filter):
    try:
        student_lister_query = db.session.query(StudentClassGrade, Class, Student, Metadata, Course).join(Class, Class.ClassId == StudentClassGrade.ClassId).join(Student, Student.StudentId == StudentClassGrade.StudentId).join(Metadata, Metadata.MetadataId == Class.MetadataId).join(Course, Metadata.CourseId == Course.CourseId)
        
        filter_conditions = []
        
        filter_conditions.append(
            StudentClassGrade.Lister != 0
        )
        
        if filter:
            filter_parts = filter.split(' and ')
            for part in filter_parts:
                # Check if part has to lower in value
                if '(tolower(' in part:
                    # Extracting column name and value
                    column_name = part.split("(")[3].split("),'")[0]
                    value = part.split("'")[1]
                    column_str = None
                    
                    if column_name.strip() == 'ClassName':
                        split_values = value.split(' ')
                        
                        if len(split_values) >= 2:
                            # Check split values if have a number
                            if any(char.isdigit() for char in split_values[-1]):
                                batch_section = split_values[-1]
                                course_code = ' '.join(split_values[:-1])
                                column_arr_1 = getattr(Course, 'CourseCode')
                                year, section = None, None
                                
                                if '-' in batch_section:
                                    year, section = batch_section.split('-')
                                    if section:
                                        column_arr_3 = getattr(Class, 'Section')
                                    column_arr_2 = getattr(Metadata, 'Year')
                                else:
                                    year = batch_section
                                    column_arr_2 = getattr(Metadata, 'Year')
                            else:
                                course_code = ' '.join(split_values)
                                year, section = None, None
                                column_arr_1 = getattr(Course, 'CourseCode')

                            # Append column_arr_1
                            filter_conditions.append(
                                func.lower(column_arr_1).like(f'%{split_values[0]}%')
                            )
                            # Check if year then append
                            if year:
                                filter_conditions.append(Metadata.Year == int(year))
                                
                            if section:
                                filter_conditions.append(
                                    Class.Section == int(section)
                                )
                            continue
                        elif len(split_values) == 1:
                            course_code, year, section = None, None, None
                            # check if value contains "-" and digit in it
                            if '-' in value and any(x.isdigit() for x in value):
                                year, section = value.split('-')
                                column_arr_2 = Metadata.Year
                                column_arr_3 = Class.Section
                            else:
                                course_code = value
                                column_arr_1 = getattr(Course, 'CourseCode')
                            
                            if course_code:
                                filter_conditions.append(column_arr_1.like(f'%{course_code.upper()}%'))

                            if year:
                                filter_conditions.append(
                                    column_arr_2 == int(year)
                                )
                            
                            if section:
                                filter_conditions.append(
                                    column_arr_3 == int(section)
                                )
                            continue
                    elif column_name.strip() == 'Course':
                        column_str = getattr(Course, 'Name')
                    elif column_name.strip() == 'StudentNumber':
                        column_str = getattr(Student, 'StudentNumber')
                    elif column_name.strip() == 'LastName':
                        column_str = getattr(Student, 'LastName')
                    elif column_name.strip() == 'FirstName':
                        column_str = getattr(Student, 'FirstName')
                    elif column_name.strip() == 'MiddleName':
                        column_str = getattr(Student, 'MiddleName')
                    elif column_name.strip() == 'Grade':
                        filter_conditions.append(
                            ClassGrade.Grade == value
                        )
                        continue
                 
                    if column_str:
                        # Append column_str
                        filter_conditions.append(
                            func.lower(column_str).like(f'%{value}%')
                        )
                else:
                    # column_name = part[0][1:]  # Remove the opening '('
                    column_name, value = [x.strip() for x in part[:-1].split("eq")]
                    column_name = column_name[1:]
                    column_num = None
                    int_value = value.strip(')')
                    
                    # Check for column name 
                    if column_name.strip() == 'Batch':
                        column_num = Metadata.Batch
                    elif column_name.strip() == 'Semester':
                        column_num = Metadata.Semester
               
                    
                    if column_num:
                        # Append column_num
                        filter_conditions.append(
                            column_num == int_value
                        )
                # END OF ELSE PART
            # END OF FOR LOOP
                
        
        # Apply all filter conditions with 'and'
  
        filter_query = student_lister_query.filter(and_(*filter_conditions))
        # print('FILTER: ', filter_query.statement.compile().params)
        
         # Apply sorting logic
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'StudentNumber':
                order_attr = getattr(Student, 'StudentNumber')
            elif order_by.split(' ')[0] == 'FirstName':
                order_attr = getattr(Student, 'LastName')
            elif order_by.split(' ')[0] == 'LastName':
                order_attr = getattr(Student, 'LastName')
            elif order_by.split(' ')[0] == 'MiddleName':
                order_attr = getattr(Student, 'MiddleName')
            elif order_by.split(' ')[0] == "Batch":
                order_attr = getattr(Metadata, "Batch")
            elif order_by.split(' ')[0] == "Lister":
                order_attr = getattr(StudentClassGrade, "Lister")
            elif order_by.split(' ')[0] == 'Semester':
                order_attr = getattr(Metadata, 'Semester')
            else:
                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(Metadata.Batch), desc(Metadata.Semester), desc(Course.CourseCode), desc(Class.Section))
                else:
                    order_query = filter_query.order_by(Metadata.Batch, Metadata.Semester, Course.CourseCode, Class.Section)

            # Check if order_by contains space
            if not order_by.split(' ')[0] == "ClassName":
                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(order_attr))
                else:
                    order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(desc(Metadata.Batch), desc(Metadata.CourseId), desc(Metadata.Year), Class.Section, desc(Metadata.Semester))
        
        total_count = order_query.count()
        student_lister_main_query = order_query.offset(skip).limit(top).all()
        
        
        
        # student_lister_count = student_lister_query.count()
        # student_lister = student_lister_query.all()
        
        # Get the StudentClassSubjectGrade
        if student_lister_main_query:
            list_metadata = []
                # For loop the data_student and put it in dictionary
            for data in student_lister_main_query:
                class_name = f"{data.Course.CourseCode} {data.Metadata.Year}-{data.Class.Section}"
                lister = "President Lister" if data.StudentClassGrade.Lister == 2 else "Dean Lister"
                dict_metadata = {
                    
                    "StudentNumber": data.Student.StudentNumber,
                    "LastName": data.Student.LastName,
                    "FirstName": data.Student.FirstName,
                    "MiddleName": data.Student.MiddleName,
                    "Batch": data.Metadata.Batch,
                    "Semester": data.Metadata.Semester,
                    "ClassName": class_name,
                    "Lister": lister,
                }
                list_metadata.append(dict_metadata)
            
            return jsonify({'result': list_metadata, 'count': total_count})

        else:
            return jsonify({'result': [], 'count': 0})
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None





def getStudentList(skip, top, order_by, filter):
    try:
        student_query = (
            db.session.query(CourseEnrolled, Student, Course).join(Student, Student.StudentId == CourseEnrolled.StudentId).join(Course, Course.CourseId == CourseEnrolled.CourseId)
        )
        
        filter_conditions = []
        if filter:
            filter_parts = filter.split(' and ')
            for part in filter_parts:
                
                # Check if part has to lower in value
                if '(tolower(' in part:
                    # Extracting column name and value
                    column_name = part.split("(")[3].split("),'")[0]
                    value = part.split("'")[1]
                    column_str = None
                    if column_name.strip() == 'StudentNumber':
                        column_str = getattr(Student, 'StudentNumber')
                    elif column_name.strip() == 'LastName':
                        column_str = getattr(Student, 'LastName')
                    elif column_name.strip() == 'FirstName':
                        column_str = getattr(Student, 'FirstName')
                    elif column_name.strip() == 'MiddleName':
                        column_str = getattr(Student, 'MiddleName')
                    elif column_name.strip() == 'Email':
                        column_str =  getattr(Student, 'Email')     
                    elif column_name.strip() == 'MobileNumber':
                        column_str = getattr(Student, 'MobileNumber')
                    elif column_name.strip() == 'CourseCode':
                        column_str = getattr(Course, 'CourseCode')
                    elif column_name.strip() == 'ResidentialAddress':
                        column_str = getattr(Course, 'ResidentialAddress')
                    elif column_name.strip() == 'DateEnrolled':
                        column_str = getattr(CourseEnrolled, 'DateEnrolled')
                        filter_conditions.append(
                            CourseEnrolled.DateEnrolled == (1 if value == 'male' else 2)
                        )
                    elif column_name.strip() == 'Gender':
                        filter_conditions.append(
                            Student.Gender == (1 if value == 'male' else 2)
                        )
                        continue
                    
                    if column_str:
                        # Append column_str
                        filter_conditions.append(
                            func.lower(column_str).like(f'%{value}%')
                        )
                else:
                    # column_name = part[0][1:]  # Remove the opening '('
                    column_name, value = [x.strip() for x in part[:-1].split("eq")]
                    column_name = column_name[1:]
                    
                    column_num = None
                    int_value = value.strip(')')
             
                    if column_name.strip() == 'Batch':
                        column_num = CourseEnrolled.CurriculumYear
                    if column_name.strip() == 'Status':
                        column_num = CourseEnrolled.Status
                    
                    if column_num:
                        # Append column_num
                        filter_conditions.append(
                            column_num == int_value
                        )
                        
        filter_query = student_query.filter(and_(*filter_conditions))
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'StudentNumber':
                order_attr = getattr(Student, 'StudentNumber')
            elif order_by.split(' ')[0] == "LastName":
                order_attr = getattr(Student, 'LastName')
            elif order_by.split(' ')[0] == "FirstName":
                order_attr = getattr(Student, 'FirstName')
            elif order_by.split(' ')[0] == "MiddleName":
                order_attr = getattr(Student, 'MiddleName')
            elif order_by.split(' ')[0] == 'Email':
                order_attr = getattr(Student, 'Email')
            elif order_by.split(' ')[0] == 'DateOfBirth':
                order_attr = getattr(Student, 'DateOfBirth')
            elif order_by.split(' ')[0] == 'Gender':
                order_attr = getattr(Student, 'Gender')
            elif order_by.split(' ')[0] == 'MobileNumber':
                order_attr = getattr(Student, 'MobileNumber')
            elif order_by.split(' ')[0] == 'ResidentialAddress':
                order_attr = getattr(Student, 'ResidentialAddress')
            elif order_by.split(' ')[0] == 'CourseCode':
                order_attr = getattr(Course, 'CourseCode')
            elif order_by.split(' ')[0] == 'DateEnrolled':
                order_attr = getattr(CourseEnrolled, 'DateEnrolled')
            elif order_by.split(' ')[0] == 'Batch':
                order_attr = getattr(CourseEnrolled, 'CurriculumYear')
            elif order_by.split(' ')[0] == 'Status':
                order_attr = getattr(CourseEnrolled, 'Status')
           
            if ' ' in order_by:
                order_query = filter_query.order_by(desc(order_attr))
            else:
                order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(desc(CourseEnrolled.CurriculumYear), desc(Course.CourseCode), desc(Student.StudentNumber))
        
        
        # Query for counting all records
        total_count = order_query.count()
        # Limitized query = 
        student_limit_offset_query = order_query.offset(skip).limit(top).all()
        if student_limit_offset_query:
             # For loop the student_query and put it in dictionary
            list_student_data = []
            for data in student_limit_offset_query:
                status = "Regular" if data.CourseEnrolled.Status == 0 else "Graduated" if data.CourseEnrolled.Status == 1 else "Irregular" if data.CourseEnrolled.Status == 2 else "Drop"
                date_of_birth = data.Student.DateOfBirth.strftime('%Y-%m-%d') if data.Student.DateOfBirth else None
                dict_student = {
                    "StudentId": data.Student.StudentId,
                    "StudentNumber": data.Student.StudentNumber,
                    "LastName": data.Student.LastName,
                    "FirstName": data.Student.FirstName,
                    "MiddleName": data.Student.MiddleName,
                    "Email": data.Student.Email,
                    "DateOfBirth": date_of_birth,
                    "ResidentialAddress": data.Student.ResidentialAddress,
                    "MobileNumber": data.Student.MobileNumber,
                    "Gender": "Male" if data.Student.Gender == 1 else "Female",
                    "CourseCode": data.Course.CourseCode,
                    "DateEnrolled": data.CourseEnrolled.DateEnrolled.strftime('%Y-%m-%d'),
                    "Batch": data.CourseEnrolled.CurriculumYear,
                    "Status": status
                }
                # Append the data
                list_student_data.append(dict_student)
            return jsonify({"result": list_student_data, "count":total_count})
        else:
            return None
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None