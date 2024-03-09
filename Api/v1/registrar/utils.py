from models import StudentClassGrade, ClassGrade, Class, Course, CourseEnrolled, CourseGrade, StudentClassSubjectGrade, Subject, ClassSubject, Class, Faculty, db, UniversityAdmin, Metadata, Registrar, Student, StudentRequirements, LatestBatchSemester
from sqlalchemy import desc, distinct, func, and_
import re
from werkzeug.security import check_password_hash, generate_password_hash
from collections import defaultdict

from datetime import date, datetime


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
    return Registrar.query.get(current_user_id)


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
    

def getRegistrarData(str_registrar_id):
    try:
        data_university_admin = (
            db.session.query(Registrar).filter(
                Registrar.RegistrarId == str_registrar_id).first()
        )

        if data_university_admin:
          

            dict_student_data = {
                "UnivAdminNumber": data_university_admin.RegistrarNumber,
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


def updateRegistrarData(str_registrar_id, number, residentialAddress):
    try:
        print('number:', number)
        number = re.sub(r'\D', '', number)  # Remove non-digit characters
        number_pattern = re.compile(r'^09\d{9}$')

        if not number_pattern.match(number):
            print("ERROR HSADSAD")
            return {"type": "mobile", "status": 400}

        if residentialAddress is None or residentialAddress.strip() == "":
            return {"type": "residential", "status": 400}

        # Update the student data in the database
        data_registrar = db.session.query(Registrar).filter(Registrar.RegistrarId == str_registrar_id).first()
        
        if data_registrar:
            data_registrar.MobileNumber = number
            data_registrar.ResidentialAddress = residentialAddress
            db.session.commit()
                        
            return {"message": "Data updated successfully", "number": number, "residentialAddress": residentialAddress, "status": 200}
        else:
            return {"message": "Something went wrong", "status": 404}

    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}


def updatePassword(str_registrar_id, password, new_password, confirm_password):
    try:
        data_registrar = db.session.query(Registrar).filter(Registrar.RegistrarId == str_registrar_id).first()

  
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
            errorList.append({'type': 'confirm_password', 'message': "Confirm Password must match with New Password"})

        if error:
            return {"error": True, 'errorList': errorList, "status": 400}
            
        
        if data_registrar:
            # Assuming 'password' is the hashed password stored in the database
            hashed_password = data_registrar.Password

            if check_password_hash(hashed_password, password):
                # If the current password matches
                new_hashed_password = generate_password_hash(new_password)
                data_registrar.Password = new_hashed_password
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

def getStatistics():
    try:
        # Get the teacher active in Faculty
        teacher_active_count = db.session.query(Faculty).filter_by(Status = "Active").count()
        
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
        # Rollback the changes in case of an error
        db.session.rollback()
        # Return an error response
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    
    

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



def getOverallCoursePerformance():
    try:
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

        print('data_course_grade: ', data_course_grade)
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
            print('formatted_data: ', formatted_data)
            print('list_course: ', list_course)
            return jsonify({'success': True, 'list_course': list_course, 'course_performance': formatted_data})
        else:
            return None
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return e
    
    


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
                    "StudentId": data.Student.StudentId,
                    "StudentNumber": data.Student.StudentNumber,
                    "LastName": data.Student.LastName,
                    "FirstName": data.Student.FirstName,
                    "MiddleName": data.Student.MiddleName,
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
        print("ERROR: ", e)
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
                student_course = row['Course Code']
                student_date_enrolled = row['Date Enrolled']
                student_batch = row['Batch'] # OK

                if student_mobile:
                    # Check for length of phone number if 10 add 0 in first
                    if len(student_mobile) == 10:
                        student_mobile = '0' + student_mobile
                    elif len(student_mobile) != 11:
                        errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_course, student_date_enrolled, student_batch, 'Invalid Mobile Format']))
                        continue
                    
            
                # Check if Date Enrolled is a valid date format
                if student_date_enrolled is not None:
                    # Check if it is in date format then convert it into YYYY-MM-DD
                    if isinstance(student_date_enrolled, datetime):
                        student_date_enrolled = student_date_enrolled.strftime("%Y-%m-%d")
                    else:
                        errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_course, student_date_enrolled, student_batch, 'Invalid Date Enrolled format']))
                        continue
                else:
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_course, student_date_enrolled, student_batch, 'Invalid Date Enrolled']))
                    continue
                
                # Check if Batch is a valid format (e.g., numeric)
                if not str(student_batch).isdigit():
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_course, student_date_enrolled, student_batch, 'Invalid Batch format']))
                    continue
                elif not student_batch:
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_course, student_date_enrolled, student_batch, 'Invalid Batch']))
                    continue
                
                # Check if Email is a valid format
                if not is_valid_email(student_email):
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_course, student_date_enrolled, student_batch, 'Invalid Email format']))
                    continue
                elif not student_email:
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender  , student_course, student_date_enrolled, student_batch, 'Invalid Email format']))
                    continue
                
                # Check if Phone Number is a valid format
                if student_mobile and not is_valid_phone_number(student_mobile):
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_course, student_date_enrolled, student_batch, 'Invalid Phone Number format']))
                    continue
            
                if not student_course:
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_course, student_date_enrolled, student_batch, 'Invalid Course']))
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
                    
                    new_student_requirements = StudentRequirements(
                        StudentId=new_student.StudentId,
                    )
                    
                    # # Add the new course enrolled to the session
                    db.session.add(new_course_enrolled)
                    db.session.add(new_student_requirements)
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
                        errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_course, student_date_enrolled, student_batch, 'Student Number already exist']))
                    else:
                        errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_course, student_date_enrolled, student_batch, 'Email already exist']))
                    
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
                student_course = data['CourseCode'].strip()
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

                    course = db.session.query(Course).filter_by(CourseCode=student_course).first()
                    
                    
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
                    
                    new_student_requirements = StudentRequirements(
                        StudentId=new_student.StudentId,
                    )
                    # # Add the new course enrolled to the session
                    db.session.add(new_course_enrolled)
                    db.session.add(new_student_requirements)
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
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': e}), 500
    

def getStudentAddOptions():
    try:
      # Make gender options
        genderOptionList = [{"Gender":"Male"}, {"Gender":"Female"}]
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


from sqlalchemy import and_

def getStudentRequirements(skip, top, order_by, filter):
    try:
        # Fetch required columns only
        student_requirements_query = db.session.query(Student.StudentId, Student.StudentNumber, Student.LastName, Student.FirstName, Student.MiddleName,
                                                       StudentRequirements.F_137, StudentRequirements.F_138, StudentRequirements.GoodMoralSeal,
                                                       StudentRequirements.Grade12, StudentRequirements.Grade11, StudentRequirements.SARForm,
                                                       StudentRequirements.PSA, StudentRequirements.Diploma, StudentRequirements.Grade10WithoutSeal)\
                                                .join(Student, Student.StudentId == StudentRequirements.StudentId)
        filter_conditions = []
        
        if filter:
            filter_parts = filter.split(' and ')
            for part in filter_parts:
                # Check if part has to lower in value
                if '(tolower(' in part:
                    print('PART: ', part)
                    # Check if part contains startswith
                    if 'startswith(' in part:
                        
                        # Extracting column name and value
                        column_name = part.split("(")[3].split("),'")[0]
                        value = part.split("'")[1]
                        column_str = None
                        print('column_name: ', column_name)
                        print('value: ', value)
                    else:
                        # Extracting column name and value
                        column_name = part.split("(")[2].split(")")[0]
                        value = part.split("'")[1]
                        column_str = None
                        print('column_name: ', column_name)
                        print('value: ', value)
                    
                    if column_name.strip() == 'StudentNumber':
                        column_str = getattr(Student, 'StudentNumber')
                    elif column_name.strip() == 'LastName':
                        column_str = getattr(Student, 'LastName')
                    elif column_name.strip() == 'FirstName':
                        column_str = getattr(Student, 'FirstName')
                    elif column_name.strip() == 'MiddleName':
                        column_str = getattr(Student, 'MiddleName')
                    # Check if the column is F_137 then make a check for its value
                    elif column_name.strip() == 'F_137':
                        filter_conditions.append(
                            StudentRequirements.F_137 == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'F_138':
                        filter_conditions.append(
                            StudentRequirements.F_138 == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'GoodMoralSeal':
                        filter_conditions.append(
                            StudentRequirements.GoodMoralSeal == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'Grade12':
                        filter_conditions.append(
                            StudentRequirements.Grade12 == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'Grade11':
                        filter_conditions.append(
                            StudentRequirements.Grade11 == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'SARForm':
                        filter_conditions.append(
                            StudentRequirements.SARForm == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'PSA':
                        filter_conditions.append(
                            StudentRequirements.PSA == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'Diploma':
                        filter_conditions.append(
                            StudentRequirements.Diploma == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'Grade10WithoutSeal':
                        filter_conditions.append(
                            StudentRequirements.Grade10WithoutSeal == (True if value == 'submitted' else False)
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
  
        filter_query = student_requirements_query.filter(and_(*filter_conditions))

         # Apply sorting logic
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'StudentNumber':
                order_attr = getattr(Student, 'StudentNumber')
            elif order_by.split(' ')[0] == "LastName":
                order_attr = getattr(Student, "LastName")
            elif order_by.split(' ')[0] == "FirstName":
                order_attr = getattr(Student, "FirstName")
            elif order_by.split(' ')[0] == "MiddleName":
                order_attr = getattr(Student, "MiddleName")
            elif order_by.split(' ')[0] == "F_137":
                order_attr = getattr(StudentRequirements, "F_137")
            elif order_by.split(' ')[0] == "F_138":
                order_attr = getattr(StudentRequirements, "F_138")
            elif order_by.split(' ')[0] == "GoodMoralSeal":
                order_attr = getattr(StudentRequirements, "GoodMoralSeal")
            elif order_by.split(' ')[0] == "Grade12":
                order_attr = getattr(StudentRequirements, "Grade12")
            elif order_by.split(' ')[0] == "Grade11":
                order_attr = getattr(StudentRequirements, "Grade11")
            elif order_by.split(' ')[0] == "SARForm":
                order_attr = getattr(StudentRequirements, "SARForm")
            elif order_by.split(' ')[0] == "Diploma":
                order_attr = getattr(StudentRequirements, "Diploma")
            elif order_by.split(' ')[0] == "PSA":
                order_attr = getattr(StudentRequirements, "PSA")
            elif order_by.split(' ')[0] == "Grade10WithoutSeal":
                order_attr = getattr(StudentRequirements, "Grade10WithoutSeal")

            if order_attr:
                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(order_attr))
                else:
                    order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(desc(Student.StudentNumber))
        
        total_count = order_query.count()
        student_requirements_main_query = order_query.offset(skip).limit(top).all()

        if student_requirements_main_query:
            list_student_requirements = []
            for data in student_requirements_main_query:
                # Check if all requirements are met
                is_completed = all(data[5:])  # Check from index 5 to end for requirement columns
                
                student_data = {
                    "StudentId": data[0],
                    "StudentNumber": data[1],
                    "LastName": data[2],
                    "FirstName": data[3],
                    "MiddleName": data[4],
                    'F_137': 'Submitted' if data[5] else "Missing",
                    'F_138': 'Submitted' if data[6] else "Missing",
                    'GoodMoralSeal': 'Submitted' if data[7] else "Missing",
                    'Grade12': 'Submitted' if data[8] else "Missing",
                    'Grade11': 'Submitted' if data[9] else "Missing",
                    'SARForm': 'Submitted' if data[10] else "Missing",
                    'PSA': 'Submitted' if data[11] else "Missing",
                    'Diploma': 'Submitted' if data[12] else "Missing",
                    'Grade10WithoutSeal': 'Submitted' if data[13] else "Missing",
                    'Completed': is_completed
                }
                list_student_requirements.append(student_data)
                
            return jsonify({"result": list_student_requirements, 'count': total_count})

    except Exception as e:
        print("ERROR: ", e)
        # Handle exceptions
        return jsonify({"error": str(e)})

        
        # # print('FILTER: ', filter_query.statement.compile().params)
        
        
        
        
        # ##############################################################################
        
        

        # if data_university_admin:
          

        #     dict_student_data = {
        #         "UnivAdminNumber": data_university_admin.UnivAdminNumber,
        #         "Name": data_university_admin.Name,
        #         "PlaceOfBirth": data_university_admin.PlaceOfBirth,
        #         "ResidentialAddress": data_university_admin.ResidentialAddress,
        #         "Email": data_university_admin.Email,
        #         "MobileNumber": data_university_admin.MobileNumber,
        #         "Gender": "Male" if data_university_admin.Gender == 1 else "Female",
        #     }

        #     return (dict_student_data)
        # else:
        #     return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    
 
def processUpdatingStudentRequirements(file):
    try:
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

        df = pd.read_excel(file)
        
        submitted_data = False
        errors = []
        
        for index, row in df.iterrows():
            student_number = row['Student Number'].strip() if isinstance(row['Student Number'], str) else row['Student Number']
            f_137 = row['F-137'].strip() if isinstance(row['F-137'], str) else row['F-137']
            f_138 = row['F-138'].strip() if isinstance(row['F-138'], str) else row['F-138']
            good_moral = row['GoodMoralSeal'].strip() if isinstance(row['GoodMoralSeal'], str) else row['GoodMoralSeal']
            grade_12 = row['Grade12'].strip() if isinstance(row['Grade12'], str) else row['Grade12']
            grade_11 = row['Grade11'].strip() if isinstance(row['Grade11'], str) else row['Grade11']
            sar_form = row['SARForm'].strip() if isinstance(row['SARForm'], str) else row['SARForm']
            psa = row['PSA'].strip() if isinstance(row['PSA'], str) else row['PSA']
            diploma = row['Diploma'].strip() if isinstance(row['Diploma'], str) else row['Diploma']
            grade_10_without_seal = row['Grade10WithoutSeal'].strip() if isinstance(row['Grade10WithoutSeal'], str) else row['Grade10WithoutSeal']
            
            # Get student and student requirements
            student = db.session.query(Student, StudentRequirements).join(StudentRequirements, StudentRequirements.StudentId == Student.StudentId).filter(Student.StudentNumber == str(student_number.strip())).first()
            
            # Update the StudentRequirements
            if student:
                student.StudentRequirements.F_137 = True if f_137.lower() == 'submitted' else False
                student.StudentRequirements.F_138 = True if f_138.lower() == 'submitted' else False
                student.StudentRequirements.GoodMoralSeal = True if good_moral.lower() == 'submitted' else False
                student.StudentRequirements.Grade12 = True if grade_12.lower() == 'submitted' else False
                student.StudentRequirements.Grade11 = True if grade_11.lower() == 'submitted' else False
                student.StudentRequirements.SARForm = True if sar_form.lower() == 'submitted' else False
                student.StudentRequirements.PSA = True if psa.lower() == 'submitted' else False
                student.StudentRequirements.Diploma = True if diploma.lower() == 'submitted' else False
                student.StudentRequirements.Grade10WithoutSeal = True if grade_10_without_seal.lower() == 'submitted' else False
                submitted_data = True
            else:
                errors.append({
                    'StudentNumber': student_number,
                    'F_137': f_137,
                    'F_138': f_138,
                    'GoodMoralSeal': good_moral,
                    'Grade12': grade_12,
                    'Grade11': grade_11,
                    'SARForm': sar_form,
                    'PSA': psa,
                    'Diploma': diploma,
                    'Grade10WithoutSeal': grade_10_without_seal,
                    'Error': 'Student not found'
                })
                
        # Check if errors and submitted data
        if errors and submitted_data:
            db.session.commit()
            return jsonify({'warning': 'Some data cannot be updated.', 'errors': errors}), 400
        if errors and not submitted_data:
            db.session.commit()
            return jsonify({'error': 'Updating data failed.', 'errors': errors}), 400
        else:
            db.session.commit()
            return jsonify({'result': 'Data updated successfully'}), 200
        
    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()
        return jsonify({'errorException': 'An error occurred while processing the file'}), 500
    

    


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