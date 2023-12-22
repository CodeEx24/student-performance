from models import StudentClassGrade, ClassGrade, Class, Course, CourseEnrolled, CourseGrade, StudentClassSubjectGrade, Subject, ClassSubject, Class, Faculty, Student, db, UniversityAdmin, ClassSubjectGrade, Metadata, Curriculum
from sqlalchemy import desc, distinct, func, and_
import re
from werkzeug.security import check_password_hash, generate_password_hash
from collections import defaultdict
import datetime

from datetime import date

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


def updateUniversityAdminData(str_univ_admin_id, email, number, residentialAddress):
    try:
        if not re.match(r'^[\w\.-]+@[\w\.-]+$', email):
            return {"type": "email", "status": 400}

        if not re.match(r'^09\d{9}$', number):
            return {"type": "mobile", "status": 400}

        if residentialAddress is None or residentialAddress.strip() == "":
            return {"type": "residential", "status": 400}

        # Update the student data in the database
        data_student = db.session.query(UniversityAdmin).filter(
            UniversityAdmin.UnivAdminId == str_univ_admin_id).first()
        
        if data_student:
            data_student.Email = email
            data_student.MobileNumber = number
            data_student.ResidentialAddress = residentialAddress
            db.session.commit()
                        
            return {"message": "Data updated successfully", "email": email, "number": number, "residentialAddress": residentialAddress, "status": 200}
        else:
            return {"message": "Something went wrong", "status": 404}

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}

def updatePassword(str_university_admin_id, password, new_password, confirm_password):
    try:
        data_student = db.session.query(UniversityAdmin).filter(
            UniversityAdmin.UnivAdminId == str_university_admin_id).first()

        if data_student:
            # Assuming 'password' is the hashed password stored in the database
            hashed_password = data_student.Password

            if check_password_hash(hashed_password, password):
                # If the current password matches
                new_hashed_password = generate_password_hash(
                    new_password)
                data_student.Password = new_hashed_password
                db.session.commit()
                return {"message": "Password changed successfully", "status": 200}

            else:
                return {"message": "Changing Password was unsuccessful. Please try again.", "status": 400}
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

            # Iterate through the data to calculate counts
            for course_code, date_enrolled in data_course_enrolled:
                year_enrolled = date_enrolled.year
                course_year_counts[year_enrolled][course_code] += 1

            # Convert the counts to a list of dictionaries with the desired format
            trend_data = {
                "CourseDetails": [],
                "LowestEnrolledCount": None,
                "HighestEnrolledCount": None,
                "LowestEnrolledCourses": [],
                "HighestEnrolledCourses": [],
                "TotalEnrolled": None
            }

            # Find lowest, highest, and total enrollment counts
            for year, course_counts in course_year_counts.items():
                trend_item = {"x": year, **course_counts}
                trend_data["CourseDetails"].append(trend_item)

            if trend_data["CourseDetails"]:
                total_enrolled = sum(course for year_counts in course_year_counts.values() for course in year_counts.values())
                trend_data["TotalEnrolled"] = total_enrolled

                # Find the lowest and highest enrolled counts and their corresponding courses
                lowest_enrolled_count = min(course for year_counts in course_year_counts.values() for course in year_counts.values())
                highest_enrolled_count = max(course for year_counts in course_year_counts.values() for course in year_counts.values())

                for year_counts in course_year_counts.values():
                    for course_code, count in year_counts.items():
                        course_name = db.session.query(Course.Name).filter_by(
                            CourseCode=course_code).first()

                        if count == lowest_enrolled_count:
                            trend_data["LowestEnrolledCount"] = count
                            trend_data["LowestEnrolledCourses"].append(
                                course_name[0] if course_name else course_code)

                        if count == highest_enrolled_count:
                            trend_data["HighestEnrolledCount"] = count
                            trend_data["HighestEnrolledCourses"].append(
                                course_name[0] if course_name else course_code)

            return trend_data
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
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


def getOverallCoursePerformance():
    try:
        data_course_grade = db.session.query(
            CourseGrade, Course).join(Course, Course.CourseId == CourseGrade.CourseId).order_by(CourseGrade.Year, CourseGrade.CourseId).all()
        if data_course_grade:
            course_year_grades = defaultdict(dict)

            for course_grade in data_course_grade:
                year = course_grade.CourseGrade.Year
                course_id = course_grade.Course.CourseCode
                
                grade = convertGradeToPercentage(course_grade.CourseGrade.Grade)

                if year not in course_year_grades:
                    course_year_grades[year] = {"x": year}

                course_year_grades[year][course_id] = grade

            # Convert the data into a list of dictionaries
            formatted_data = list(course_year_grades.values())
            return formatted_data
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return e


def getAllClassData(skip, top, order_by, filter):
    try:
        # current_year = datetime.datetime.now().year

        class_grade_query = db.session.query(Class, Course, ClassGrade).join(Course, Course.CourseId == Class.CourseId).join(ClassGrade, ClassGrade.ClassId == Class.ClassId)
        
        # .filter(Class.Batch == current_year - 1)
        # DEFAULT QUERY
        # .order_by(desc(Class.Batch), desc(Class.CourseId), Class.Year, Class.Section)
        
        
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
                                    column_arr_2 = getattr(Class, 'Year')
                                else:
                                    year = batch_section
                                    column_arr_2 = getattr(Class, 'Year')
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
                                filter_conditions.append(Class.Year == int(year))
                                
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
                                column_arr_2 = Class.Year
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
                        column_num = Class.Batch
                    elif column_name.strip() == 'Semester':
                        column_num = Class.Semester
                    # elif column_name.strip() == 'Semester':
                    #     column_num = Class.Semester
                    
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
                order_attr = getattr(Class, "Batch")
            elif order_by.split(' ')[0] == 'Semester':
                order_attr = getattr(Class, 'Semester')
            elif order_by.split(' ')[0] == 'Grade':
                order_attr = getattr(ClassGrade, 'Grade')
            else:
                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(Course.CourseCode), desc(Class.Year), desc(Class.Section))
                else:
                    order_query = filter_query.order_by(Course.CourseCode, Class.Year, Class.Section)

            # Check if order_by contains space
            if not order_by.split(' ')[0] == "ClassName":
                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(order_attr))
                else:
                    order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(desc(Class.Batch), desc(Class.CourseId), Class.Year, Class.Section)
        
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
                        'ClassName': f"{class_subject_grade.Course.CourseCode} {class_subject_grade.Class.Year}-{class_subject_grade.Class.Section}",
                        'Semester': class_subject_grade.Class.Semester,
                        "Course": class_subject_grade.Course.Name,
                        "Batch": class_subject_grade.Class.Batch,
                        "Grade": grade_value
                    }

                    # Add class_id to the seen_class_ids set
                    seen_class_ids.add(class_id)

                    # Add class_obj to the list_classes
                    list_classes.append(class_obj)

            # Return the list of class objects
            return {'result': list_classes, 'count': 50}
        else:
            return None

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getClassPerformance(class_id):
    try:
        class_grade = (
            db.session.query(
                ClassGrade, Course, Class
            )
            .join(Class, Class.ClassId == ClassGrade.ClassId)
            .join(Course, Class.CourseId == Course.CourseId)
            .filter(ClassGrade.ClassId == class_id)
            .first()
        )

        
        if class_grade:

            # Calculate class name
            class_name = f"{class_grade.Course.CourseCode} {class_grade.Class.Year}-{class_grade.Class.Section} ({class_grade.Class.Batch})"
            num_class_batch = class_grade.Class.Batch
            num_class_section = class_grade.Class.Section

            dict_class_grade = {
                'Class': class_name,
                'Batch': num_class_batch,
                'ListGrade': [],
                'PresidentLister': class_grade.ClassGrade.PresidentsLister,
                'DeanLister': class_grade.ClassGrade.DeansLister
            }
            
            list_grade = []
            for i in range(1, class_grade.Class.Year+1):
                batch = class_grade.Class.Batch - class_grade.Class.Year + i
                class_grade_result = (
                    db.session.query(
                        Class,
                        ClassGrade,
                    )
                    .join(ClassGrade, ClassGrade.ClassId == Class.ClassId)
                    .filter(Class.Year == i, Class.Batch == batch, Class.Section == num_class_section)
                    .first()

                )

                list_grade.append(
                    {'x': class_grade_result.Class.Batch, 'y': convertGradeToPercentage(class_grade_result.ClassGrade.Grade)})
                
            dict_class_grade['ListGrade'].extend(list_grade)

            return (dict_class_grade)
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None

def is_valid_email(email):
    # Regular expression for a basic email validation
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(email_pattern, email)

def is_valid_phone_number(phone_number):
    
    
    # Regular expression for a phone number validation
    phone_pattern = r'^09\d{9}$'
    return re.match(phone_pattern, phone_number)

def processAddingStudents(file):
    try:
        # Check if the file is empty
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Check file extension
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400


        # Read the Excel file into a DataFrame
        df = pd.read_excel(file)
        
        # dict data list
        list_student_data = []
        errors = []
        
        for index, row in df.iterrows():
            student_number = row['Student Number'] # OK
            student_name = row['Name']
            student_email = row['Email']
            student_mobile =  str(row['Phone Number'])
            student_address = row['Address'] # OK
            
            student_gender = row['Gender'] # OK
            student_course = row['Course Code']
            student_date_enrolled = row['Date Enrolled']

            student_batch = row['Batch'] # OK

            if student_mobile:
                # Check for length of phone number if 10 add 0 in first
                if len(student_mobile) == 10:
                    student_mobile = '0' + student_mobile
                
        
            # Check if Date Enrolled is a valid date format
            if student_date_enrolled is not None:
                # Check if it is in date format then convert it into YYYY-MM-DD
                if isinstance(student_date_enrolled, datetime.datetime):
                    student_date_enrolled = student_date_enrolled.strftime("%Y-%m-%d")
                else:
                    errors.append({
                        'StudentNumber': student_number,
                        'Name': student_name,
                        'Email': student_email,
                        'Phone': student_mobile,
                        'Address': student_address,
                        'Gender': student_gender,
                        'CourseCode': student_course,
                        'DateEnrolled': student_date_enrolled,  # Adding the original string for reference
                        'Batch': student_batch,
                        'Error': 'Invalid Date Enrolled format'
                    })
                    continue
                
                
            # Check if Batch is a valid format (e.g., numeric)
            if not str(student_batch).isdigit():
                errors.append({
                    'StudentNumber': student_number,
                    'Name': student_name,
                    'Email': student_email,
                    'Phone': student_mobile,
                    'Address': student_address,
                    'Gender': student_gender,
                    'CourseCode': student_course,
                    'DateEnrolled': student_date_enrolled,  # Adding the original string for reference
                    'Batch': student_batch,
                    'Error': 'Invalid Batch format'
                })
                continue
            
            # Check if Email is a valid format
            if not is_valid_email(student_email):
                errors.append({
                    'StudentNumber': student_number,
                    'Name': student_name,
                    'Email': student_email,
                    'Phone': student_mobile,
                    'Address': student_address,
                    'Gender': student_gender,
                    'CourseCode': student_course,
                    'DateEnrolled': student_date_enrolled,  # Adding the original string for reference
                    'Batch': student_batch,
                    'Error': 'Invalid Email format'
                })
          
                continue
            
            # Check if Phone Number is a valid format
            if student_mobile and not is_valid_phone_number(student_mobile):
                errors.append({
                    'StudentNumber': student_number,
                    'Name': student_name,
                    'Email': student_email,
                    'Phone': student_mobile,
                    'Address': student_address,
                    'Gender': student_gender,
                    'CourseCode': student_course,
                    'DateEnrolled': student_date_enrolled,  # Adding the original string for reference
                    'Batch': student_batch,
                    'Error': 'Invalid Phone Number format'
                })
               
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

                course = db.session.query(Course).filter_by(CourseCode=student_course).first()

              # Add the new student in the database

                # Ensure the mobile number has a leading zero
                if not student_mobile.startswith('0'):
                    student_mobile = '0' + student_mobile

                new_student = Student(
                    StudentNumber=student_number,
                    Name=student_name,
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
                
                # mail.send(msg)
                
                if not gender:
                    list_student_data.append({
                        "Email": str(student_email),
                        "Gender": "N/A",
                        "Mobile Number": str(student_mobile),
                        "Name": str(student_name),
                        "Student Number": str(student_number)
                    })
                else:
                    list_student_data.append({
                        "Email": str(student_email),
                        "Gender": student_gender,
                        "Mobile Number": str(student_mobile),
                        "Name": str(student_name),
                        "Student Number": str(student_number)
                    })
            else:
                if student_number_data:
                    # Append the Student Number, Email and what type error it is
                    errors.append({
                        'StudentNumber': student_number,
                        'Name': student_name,
                        'Email': student_email,
                        'Phone': student_mobile,
                        'Address': student_address,
                        'Gender': student_gender,
                        'CourseCode': student_course,
                        'DateEnrolled': student_date_enrolled,  # Adding the original string for reference
                        'Batch': student_batch,
                        'Error': 'Student Number already exist'
                    })
                else:
                    errors.append({
                        'StudentNumber': student_number,
                        'Name': student_name,
                        'Email': student_email,
                        'Phone': student_mobile,
                        'Address': student_address,
                        'Gender': student_gender,
                        'CourseCode': student_course,
                        'DateEnrolled': student_date_enrolled,  # Adding the original string for reference
                        'Batch': student_batch,
                        'Error': 'Email already exist'
                    })
                   
        if errors and list_student_data:
            db.session.rollback()
            return jsonify({'warning': 'Some data cannot be added.', 'errors': errors, 'data': list_student_data}), 500
        if errors and not list_student_data:
            db.session.rollback()
            return jsonify({'error': 'Adding data failed.', 'errors': errors}), 500
        else:        
            return  jsonify({'result': 'Data added successfully', 'data': list_student_data}), 200
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'errorException': 'An error occurred while processing the file'}), 500
    
    
def processAddingClass(file):
    try:
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

        df = pd.read_excel(file)
        
        list_new_class_data = []
        
        list_course_not_exist = []
        curriculum_not_exist = []
        class_data_exist = []
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
                    
            metadata = db.session.query(Metadata).filter_by(CourseId=course.CourseId, YearLevel=year, Semester=semester, Batch=batch).first()

            if not metadata:
                errors.append({"CourseCode": course_code, "Section": section, "Year": year, "Semester": semester, "Batch": batch, "Error": "Curriculum not exist"})
                continue

            if course and metadata:
                curriculum = db.session.query(Curriculum).filter_by(MetadataId=metadata.MetadataId).all()
                if curriculum:
                    class_data = db.session.query(Class).filter_by(
                        CourseId=course.CourseId, Year=year, Section=section, Semester=semester, Batch=batch).first()

                    if not class_data:
                        class_name = f"{course_code} {year}-{section}"
                        course_name = course.Name
                        new_class = Class(
                            CourseId=course.CourseId,
                            Year=year,
                            Section=section,
                            Semester=semester,
                            Batch=batch,
                            IsGradeFinalized=False
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
                            "Semester": new_class.Semester,
                            "Batch": new_class.Batch
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
        db.session.rollback()
        return jsonify({'errorException': 'An error occurred while processing the file'}), 500

    #         if course:
    #             # Check if year is current year or + 1 only
    #             current_year = datetime.datetime.now().year
        
    #             if batch != current_year and batch != current_year + 1:
    #                 return jsonify({'error': 'Invalid year. Please select the current year or the next year.'}), 400
                
    #             # Check if course.id, year, section, semester and batch already existing in class
    #             class_data = db.session.query(Class).filter(
    #                 Class.CourseId == course.CourseId, Class.Year == year, Class.Section == section, Class.Semester == semester, Class.Batch == batch).first()
          
    #             # If existing throw an error
    #             if not class_data:             
    #                 new_class = Class(
    #                     CourseId=course.CourseId,
    #                     Year=year,
    #                     Section=section,
    #                     Semester=semester,
    #                     Batch=batch, 
    #                     IsGradeFinalized=False
    #                 )
                    
    #                 # Just add in session
    #                 db.session.add(new_class)
    #                 db.session.flush()
                    
                    
                    
    #                 # Make a ClassGrade
    #                 new_class_grade = ClassGrade(
    #                     ClassId=new_class.ClassId,
    #                     PresidentsLister=0,
    #                     DeansLister=0,
    #                     Grade= 5.00
    #                 )
    #                 db.session.add(new_class_grade)
                    
    #                 # Combine the course_code, year, section to class_name variable
    #                 class_name = f"{course_code} {year}-{section}"
    #                 list_class_data.append({'ClassId':new_class.ClassId,'ClassName':class_name,'Batch':batch, 'Course': course.Name, 'Grade': 'N/A'})
    #             else:
    #                 list_existing_class_data.append({
    #                     'CourseCode': course_code,
    #                     "Year": year,
    #                     "Section": section,
    #                     "Batch": batch,
    #                     "Semester": semester
    #                 })
    #         else:
    #             # check if course_code not existing in list_missing_course
    #             if course_code not in list_missing_courses:
    #                 list_missing_courses.append(course_code)
                
    #     if list_existing_class_data:
    #         db.session.rollback()
    #         return jsonify({'error': 'The class already exist in the database', 'existing_data': list_existing_class_data}), 500
    #     elif list_missing_courses:
    #         db.session.rollback()
    #         return jsonify({'error': 'Course Code does not exist in the database', 'missing_course': list_missing_courses}), 400  
    #     else:
    #         db.session.rollback()
    #         # db.session.commit()
    #         return jsonify({'result': "Data added successfully", 'data':list_class_data }), 200   
    # except Exception as e:
    #     db.session.rollback()
    #     return jsonify({'error': 'An error occurred while processing the file'}), 500
    


    #         if course:
    #             # Check if year is current year or + 1 only
    #             current_year = datetime.datetime.now().year
        
    #             if batch != current_year and batch != current_year + 1:
    #                 return jsonify({'error': 'Invalid year. Please select the current year or the next year.'}), 400
                
    #             # Check if course.id, year, section, semester and batch already existing in class
    #             class_data = db.session.query(Class).filter(
    #                 Class.CourseId == course.CourseId, Class.Year == year, Class.Section == section, Class.Semester == semester, Class.Batch == batch).first()
          
    #             # If existing throw an error
    #             if not class_data:             
    #                 new_class = Class(
    #                     CourseId=course.CourseId,
    #                     Year=year,
    #                     Section=section,
    #                     Semester=semester,
    #                     Batch=batch, 
    #                     IsGradeFinalized=False
    #                 )
                    
    #                 # Just add in session
    #                 db.session.add(new_class)
    #                 db.session.flush()
                    
                    
                    
    #                 # Make a ClassGrade
    #                 new_class_grade = ClassGrade(
    #                     ClassId=new_class.ClassId,
    #                     PresidentsLister=0,
    #                     DeansLister=0,
    #                     Grade= 5.00
    #                 )
    #                 db.session.add(new_class_grade)
                    
    #                 # Combine the course_code, year, section to class_name variable
    #                 class_name = f"{course_code} {year}-{section}"
    #                 list_class_data.append({'ClassId':new_class.ClassId,'ClassName':class_name,'Batch':batch, 'Course': course.Name, 'Grade': 'N/A'})
    #             else:
    #                 list_existing_class_data.append({
    #                     'CourseCode': course_code,
    #                     "Year": year,
    #                     "Section": section,
    #                     "Batch": batch,
    #                     "Semester": semester
    #                 })
    #         else:
    #             # check if course_code not existing in list_missing_course
    #             if course_code not in list_missing_courses:
    #                 list_missing_courses.append(course_code)
                
    #     if list_existing_class_data:
    #         db.session.rollback()
    #         return jsonify({'error': 'The class already exist in the database', 'existing_data': list_existing_class_data}), 500
    #     elif list_missing_courses:
    #         db.session.rollback()
    #         return jsonify({'error': 'Course Code does not exist in the database', 'missing_course': list_missing_courses}), 400  
    #     else:
    #         db.session.rollback()
    #         # db.session.commit()
    #         return jsonify({'result': "Data added successfully", 'data':list_class_data }), 200   
    # except Exception as e:
    #     db.session.rollback()
    #     return jsonify({'error': 'An error occurred while processing the file'}), 500
    

 
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
        class_data = db.session.query(Class).filter_by(ClassId=class_id).first()
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
                    if isinstance(student_date_enrolled, datetime.datetime):
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
                                    DateEnrolled=student_date_enrolled
                                )
                                db.session.add(new_student_class_subject_grade)
                                db.session.commit()
                            
                                # Append list_student_added
                                list_student_added.append({
                                    "StudentNumber": student_number,
                                    "SubjectCode": subject_data.SubjectCode
                                })
                            # Add If else here if there  is something error want to pop-up
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
            db.session.query(Student, CourseEnrolled, Course).join(CourseEnrolled, CourseEnrolled.StudentId == Student.StudentId).join(Course, Course.CourseId == CourseEnrolled.CourseId)
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
                    elif column_name.strip() == 'Name':
                        column_str = getattr(Student, 'Name')
                    elif column_name.strip() == 'Email':
                        column_str =  getattr(Student, 'Email')     
                    elif column_name.strip() == 'MobileNumber':
                        column_str = getattr(Student, 'MobileNumber')
                    elif column_name.strip() == 'CourseCode':
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
            elif order_by.split(' ')[0] == "Name":
                order_attr = getattr(Student, 'Name')
            elif order_by.split(' ')[0] == 'Email':
                order_attr = getattr(Student, 'Email')
            elif order_by.split(' ')[0] == 'Gender':
                order_attr = getattr(Student, 'Gender')
            elif order_by.split(' ')[0] == 'MobileNumber':
                order_attr = getattr(Student, 'MobileNumber')
            elif order_by.split(' ')[0] == 'CourseCode':
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
                    "StudentNumber": data.Student.StudentNumber,
                    "Name": data.Student.Name,
                    "Email": data.Student.Email,
                    "MobileNumber": data.Student.MobileNumber,
                    "Gender": "Male" if data.Student.Gender == 1 else "Female",
                    "CourseCode": data.Course.CourseCode,
                    "DateEnrolled": data.CourseEnrolled.DateEnrolled.strftime('%Y-%m-%d'),
                    "Batch": data.CourseEnrolled.CurriculumYear
                }
                # Append the data
                list_student_data.append(dict_student)
            return jsonify({"result": list_student_data, "count":total_count})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    
    
def getAllClassSubjectData():
    try:
        data_class_subject = (
            db.session.query(ClassSubject, Subject, Class, Course, Faculty).join(Subject, Subject.SubjectId == ClassSubject.SubjectId).join(Class, Class.ClassId == ClassSubject.ClassId).join(Course, Course.CourseId == Class.CourseId).join(Faculty, Faculty.TeacherId == ClassSubject.TeacherId).order_by(desc(Class.Batch),desc(Class.Semester), (Subject.Name)).all()
        )
        

        
        if data_class_subject:
                # For loop the data_student and put it in dictionary
            list_class_subject = []
            for class_subject in data_class_subject:
                # Combine the course_code, year, section to class_name variable
                class_name = f"{class_subject.Course.CourseCode} {class_subject.Class.Year}-{class_subject.Class.Section}"
                
                dict_class_subject = {
                    "Section Code": class_name,
                    "Subject": class_subject.Subject.Name,
                    "Teacher": class_subject.Faculty.Name,
                    "Schedule": class_subject.ClassSubject.Schedule,
                    'Batch': class_subject.Class.Batch,
                    'Semester': class_subject.Class.Semester
                }
                # # Append the data
                list_class_subject.append(dict_class_subject)
            return jsonify({'result': list_class_subject})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
def getClassSubject(class_id):
    try:
        data_class_subject = (
            db.session.query(Class, ClassSubject, Subject, ClassSubjectGrade, Course)
            .join(ClassSubject, ClassSubject.ClassId == Class.ClassId)
            .join(Subject, Subject.SubjectId == ClassSubject.SubjectId)
            .join(Course, Course.CourseId == Class.CourseId)
            .join(ClassSubjectGrade, ClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
            .filter(ClassSubject.ClassId == class_id)
            .all()
        )

        if data_class_subject:
            # For loop the data_student and put it in dictionary
            list_class_subject = []
            for class_subject in data_class_subject:
                # Combine the course_code, year, section to class_name variable
                class_name = f"{class_subject.Course.CourseCode} {class_subject.Class.Year}-{class_subject.Class.Section}"

                # Check if the class_subject.TeacherId exists, if yes, make a query for it
                if class_subject.ClassSubject.TeacherId or class_subject.ClassSubject.Schedule:
                    teacher_id = 0
                    if class_subject.ClassSubject.TeacherId:
                        teacher = db.session.query(Faculty).filter(Faculty.TeacherId == class_subject.ClassSubject.TeacherId).first()
                        if teacher:
                            teacher_id = teacher.TeacherId

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
                    'Batch': class_subject.Class.Batch if class_subject.Class else None,
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
        data_class_details = db.session.query(Class, Course).join(Course, Course.CourseId == Class.CourseId).filter(Class.ClassId == class_id).all()
        
        if data_class_details:
                # For loop the data_student and put it in dictionary
            for class_details in data_class_details:
                # Combine the course_code, year, section to class_name variable
                class_name = f"{class_details.Course.CourseCode} {class_details.Class.Year}-{class_details.Class.Section}"

                dict_class_details = {
                    "Course": class_details.Course.Name,
                    "Section Code": class_name,
                    'Batch': class_details.Class.Batch,
                    "Semester": class_details.Class.Semester
                }
                return jsonify({'data': dict_class_details})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    
def getStudentClassSubjectData(classSubjectId):
    try:
        data_class_details = db.session.query(ClassSubject).filter_by(ClassSubjectId = classSubjectId).first()
        # Get the StudentClassSubjectGrade
        if data_class_details:
            data_student_subject_grade = db.session.query(StudentClassSubjectGrade, Student).join(Student, Student.StudentId == StudentClassSubjectGrade.StudentId).filter(StudentClassSubjectGrade.ClassSubjectId == data_class_details.ClassSubjectId).all()
            if data_student_subject_grade:
                list_student_data = []
                    # For loop the data_student and put it in dictionary
                for student_subject_grade in data_student_subject_grade:
                    dict_student_subject_grade = {
                        "ClassSubjectId": student_subject_grade.StudentClassSubjectGrade.ClassSubjectId,
                        "StudentId": student_subject_grade.Student.StudentId,
                        "StudentNumber": student_subject_grade.Student.StudentNumber,
                        "Name": student_subject_grade.Student.Name,
                        "Email": student_subject_grade.Student.Email,
                        "Grade": student_subject_grade.StudentClassSubjectGrade.Grade
                    }
                    list_student_data.append(dict_student_subject_grade)
                return  jsonify({'data': list_student_data})
            else:
                return jsonify({'data': [], 'message': "No students"})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
def deleteStudent(class_subject_id, student_id):
    try:
        student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(ClassSubjectId = class_subject_id, StudentId = student_id).first()
        # Find class_subject
        class_subject = db.session.query(ClassSubject).filter_by(ClassSubjectId = class_subject_id).first()
        # Find the class_subject with same ClassId
        class_subjects = db.session.query(ClassSubject).filter_by(ClassId = class_subject.ClassId).all()
        # for loop the class_subjects and count the amount of subject of student
        total_subjects = 0
        
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
            return jsonify({'result': 'Data deleted successfully'})
        else:
            return jsonify({'error': 'Data cannot be deleted'})
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    # getCurriculumSubject

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
        # .order_by(desc(Metadata.Batch), desc(Metadata.YearLevel)).all()
        
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
                    
                    if column_name.strip() == 'Year':
                        column_num = Metadata.YearLevel
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
                order_attr = getattr(Metadata, order_by.split(' ')[0] + 'Level')
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
            order_query = filter_query.order_by(desc(Metadata.Batch), desc(Metadata.YearLevel))
        
        
        # Query for counting all records
        total_count = order_query.count()
        # Limitized query = 
        metadata_limit_offset = order_query.offset(skip).limit(top).all()

       
        
        # Get the StudentClassSubjectGrade
        if metadata_limit_offset:
            list_metadata = []
                # For loop the data_student and put it in dictionary
            for data in metadata_limit_offset:
                # Convert the YearLevel to 1st, 2nd, 3rd, 4th
                dict_metadata = {
                    "CurriculumId": data.Curriculum.CurriculumId,
                    "MetadataId": data.Metadata.MetadataId,
                    "Year": data.Metadata.YearLevel,
                    "Semester": data.Metadata.Semester,
                    "Batch": data.Metadata.Batch,
                    "CourseCode": data.Course.CourseCode,
                    "Subject": data.Subject.Name,
                    "SubjectCode": data.Subject.SubjectCode
                }
                list_metadata.append(dict_metadata)
            return jsonify({'result': list_metadata, 'count': total_count})

        else:
            return jsonify({'result': None, 'count': 0})
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
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
            
            current_year = datetime.datetime.now().year
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
        active_teacher = db.session.query(Faculty).filter_by(IsActive = True).all()
        # Get the StudentClassSubjectGrade
        if active_teacher:
            list_active_teacher = []
                # For loop the active_teacher and put it in dictionary
            for data in active_teacher:
                dict_active_teacher = {
                    "TeacherId": data.TeacherId,
                    "TeacherName": data.Name,
                }
                list_active_teacher.append(dict_active_teacher)
            return  jsonify({'data': list_active_teacher})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    
def processAddingCurriculumSubjects(data, excelType=False):
    # MANUAL ADDING DATA
    if excelType == False:
        # print("DATA: ", data,Cours)
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
            
            print("INVALID COURSE")
            # Return cannot added data. Course already exist
            return jsonify({'error': 'Invalid Course'}), 400
        else:
            # Check if already have classes and avoid adding curriculum.
            class_data = db.session.query(Class).filter_by(Year = year_level, Semester = semester, Batch = batch, CourseId = course.CourseId).first()
            if class_data:
                # Return cannot added data. Class already exist
                return jsonify({'error': 'Cannot add subject curriculum has already class existing.'}), 400
            
            metadata = db.session.query(Metadata).filter_by(YearLevel = year_level, Semester = semester, Batch = batch, CourseId = course.CourseId).first()
            # Check if have a class already with yhe same year_level, semester, batch and course id
            if metadata:
                # Check if subject is existing
                subject = db.session.query(Subject).filter_by(SubjectCode = subject_code).first()
                
                
                if subject:
                    # Check if Curriculum is existing
                    curriculum_subject_exist = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Metadata.CourseId == course.CourseId, Subject.SubjectCode == subject_code, Metadata.YearLevel == year_level, Metadata.Semester == semester, Metadata.Batch == batch).first()
                    
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
                        
                        print('dict_subject:: ', dict_subject)
                        
                        # Return data added successfully
                        return jsonify({'success': 'Data added successfully'}), 200
                    else:
                        # Return cannot added data. Curriculum already exist
                        return jsonify({'error': 'Curriculum already exist'}), 400
                else:
                    # Return cannot added data. Invalid Subject Code
                    return jsonify({'error': 'Invalid Subject Code'}), 400
            else:
                # Check if subject is existing
                subject = db.session.query(Subject).filter_by(SubjectCode = subject_code).first()   
        
                new_metadata = Metadata(
                    CourseId=course.CourseId,
                    YearLevel=year_level,
                    Semester=semester,
                    Batch=batch
                )
                    
                db.session.add(new_metadata)
                db.session.flush()
                                                    
                if subject:                       
                    curriculum_subject_exist = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Subject.SubjectCode == subject_code, Metadata.YearLevel == year_level, Metadata.Semester == semester, Metadata.Batch == batch).first()
                        
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
        
            course = db.session.query(Course).filter_by(CourseCode = course_code).first()
                
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
                class_data = db.session.query(Class).filter_by(Year = year_level, Semester = semester, Batch = batch, CourseId = course.CourseId).first()
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
                
                metadata = db.session.query(Metadata).filter_by(YearLevel = year_level, Semester = semester, Batch = batch, CourseId = course.CourseId).first()
                
                if metadata:
                    # Check if subject is existing
                    subject = db.session.query(Subject).filter_by(SubjectCode = subject_code).first()
                    
                    if subject:
                        # Check if Curriculum is existing
                        curriculum_subject_exist = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Metadata.CourseId == course.CourseId, Subject.SubjectCode == subject_code, Metadata.YearLevel == year_level, Metadata.Semester == semester, Metadata.Batch == batch).first()
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
                        
                else: # NO META DATA FIELD
                    # Check if subject is existing
                    subject = db.session.query(Subject).filter_by(SubjectCode = subject_code).first()   
            
                    new_metadata = Metadata(
                        CourseId=course.CourseId,
                        YearLevel=year_level,
                        Semester=semester,
                        Batch=batch
                    )
                        
                    db.session.add(new_metadata)
                    db.session.flush()
                                                        
                    if subject:                       
                        curriculum_subject_exist = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Subject.SubjectCode == subject_code, Metadata.YearLevel == year_level, Metadata.Semester == semester, Metadata.Batch == batch).first()
                            
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
            print("EXIST")
            # Find a class that has the same metadata value which is CourseId, YearLevel, Semester, Batch
            class_data = db.session.query(Class).filter_by(CourseId = curriculum.Metadata.CourseId, Year = curriculum.Metadata.YearLevel, Semester = curriculum.Metadata.Semester, Batch = curriculum.Metadata.Batch).first()
            
            if class_data:
                return jsonify({'error': 'Cannot delete subject. Already have class existing'}), 400
            else:
                # Delete the metadata 
                db.session.delete(curriculum.Metadata)
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


def processAddingStudentInSubject(file, class_subject_id):
    try:
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

        df = pd.read_excel(file)
        list_students_added = []
        
        # list_student_graduate = []
        errors = []

        class_subject = db.session.query(ClassSubject).filter_by(ClassSubjectId = class_subject_id).first()

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
                    if isinstance(student_date_enrolled, datetime.datetime):
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
                        student_class_grade = db.session.query(StudentClassGrade).filter_by(StudentId = student.StudentId, ClassId = class_subject.ClassId).first()
                        if not student_class_grade:
                            # Create StudentClassGrade
                            new_student_class_grade = StudentClassGrade(
                                StudentId=student.StudentId,
                                ClassId=class_subject.ClassId
                            )
                            
                            db.session.add(new_student_class_grade)
                            db.session.flush()
                        
                        # Create StudentClassSubjectGrade
                        new_student_class_subject_grade = StudentClassSubjectGrade(
                            StudentId=student.StudentId,
                            ClassSubjectId=class_subject_id,
                            DateEnrolled=student_date_enrolled
                        )
                        
                        db.session.add(new_student_class_subject_grade)
                        db.session.commit()
                        
                        dict_student_class_subject_grade = {
                            "ClassSubjectId": class_subject_id,
                            "StudentId": student.StudentId,
                            "StudentNumber": student.StudentNumber,
                            "Name": student.Name,
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
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    
 
def getMetadata(skip, top, order_by, filter):
    try:
        print("skip, top, order_by, filter: ", skip, top, order_by, filter)
        
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
                    print('column_name: ', column_name)
                    print('value: ', value)
                    
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
                    # elif column_name.strip() == 'Semester':
                    #     column_num = Class.Semester
                    
                    if column_num:
                        # Append column_num
                        filter_conditions.append(
                            column_num == int_value
                        )
                # END OF ELSE PART
            # END OF FOR LOOP
                
        
        # Apply all filter conditions with 'and'
  
        filter_query = metadata_query.filter(and_(*filter_conditions))
        print('FILTER: ', filter_query.statement.compile().params)
        
        if order_by:
            print('order_by: ', order_by)
            # Determine the order attribute
            if order_by.split(' ')[0] == 'CourseCode':
                print('IN COURSE CODE')
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
                print("IN QUERY")
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
                
                # Create a dict
                dict_metadata = {
                    'MetadataId': data.Metadata.MetadataId,
                    'Course': data.Course.Name,
                    'CourseCode': data.Course.CourseCode,
                    'Semester': data.Metadata.Semester,
                    'Batch': data.Metadata.Batch
                }

                # Append the dict to the list_metadata
                list_metadata.append(dict_metadata)
            
            return jsonify({'result': list_metadata, 'count': total_count})
        else:
            return jsonify({'result': None})
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return jsonify(error=str(e))


def finalizedGradesReport(metadata_id):
    try:
        data_metadata = db.session.query(Metadata, Course).join(Course, Course.CourseId == Metadata.CourseId).filter(Metadata.MetadataId == metadata_id).first()
        list_class = []
        if data_metadata:
            # Select class that has the same Batch, Semester and Course
            data_class = db.session.query(Class, Course).join(Course, Course.CourseId == Class.CourseId).filter(Class.Batch == data_metadata.Metadata.Batch, Class.Semester == data_metadata.Metadata.Semester, Class.CourseId == data_metadata.Course.CourseId).order_by(Class.Year, Class.Section).all()

            # if data class 
            if data_class:
                # for loop the data_class and make a dictionary and append to the list_class
                for class_data in data_class:
                    dict_class = {
                        'ClassId': class_data.Class.ClassId,
                        'CourseId': class_data.Class.CourseId,
                        'Course': class_data.Course.CourseCode,
                        'Year': class_data.Class.Year,
                        'Section': class_data.Class.Section,
                        'Semester': class_data.Class.Semester,
                        'Batch': class_data.Class.Batch
                    }
                    # Append th list_class
                    list_class.append(dict_class)
                
                if list_class:
                    # for loop it
                    for class_data in list_class:
                        # Get the class_subject
                        data_class_subject = db.session.query(ClassSubject, Subject, Faculty).join(Subject, Subject.SubjectId == ClassSubject.SubjectId).join(Faculty, Faculty.TeacherId == ClassSubject.TeacherId).filter(ClassSubject.ClassId == class_data['ClassId']).all()
                        list_class_subject = []
                        if data_class_subject:
                            # for loop the data_class_subject and make a dictionary and append to the list_class_subject
                            for class_subject in data_class_subject:
                                dict_class_subject = {
                                    'ClassSubjectId': class_subject.ClassSubject.ClassSubjectId,
                                    'SubjectCode': class_subject.Subject.SubjectCode,
                                    'Subject': class_subject.Subject.Name,
                                    'Teacher': class_subject.Faculty.Name,
                                    'Schedule': class_subject.ClassSubject.Schedule
                                }
                                # Append the list_class_subject
                                list_class_subject.append(dict_class_subject)
                                
                                # Get all student in the classSubject with the same classId
                                data_student_class_subject_grade = db.session.query(StudentClassSubjectGrade, Student).join(Student, Student.StudentId == StudentClassSubjectGrade.StudentId).filter(StudentClassSubjectGrade.ClassSubjectId == class_subject.ClassSubject.ClassSubjectId).all()
                                
                                if data_student_class_subject_grade:
                                    # for loop the data_student_class_subject_grade and make a dictionary and append to the list_student_class_subject_grade
                                    list_student_class_subject_grade = []
                                    for student_class_subject_grade in data_student_class_subject_grade:
                                        dict_student_class_subject_grade = {
                                            'StudentNumber': student_class_subject_grade.Student.StudentNumber,
                                            'Name': student_class_subject_grade.Student.Name,
                                            'Grade': student_class_subject_grade.StudentClassSubjectGrade.Grade
                                        }
                                        # Append the list_student_class_subject_grade
                                        list_student_class_subject_grade.append(dict_student_class_subject_grade)
                                        
                                    # Append the list_student_class_subject_grade to the dict_class_subject
                                    dict_class_subject['StudentClassSubjectGrade'] = list_student_class_subject_grade
                            # Append the list_class_subject to the class_data
                            class_data['ClassSubject'] = list_class_subject
                        else:
                            class_data['ClassSubject'] = None
                   
                
            else:
                return jsonify({"error": "There no class yet"})
            return jsonify({"message": "Hello"})
        else:
            return jsonify(None)
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return jsonify(error=str(e))
